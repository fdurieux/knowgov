"""The numeric settings, each read through one parser (task-0264, decision-0032 group 1 F13, group 2 F7-F9).

A value must parse as its kind (an int or a float), be finite, and sit within the setting's bounds; anything else
raises ``BadSetting``, a ``ValueError`` naming the setting, the value and the bounds, which a command turns into
exit 2 with that line. Unset or empty reads the default. Before, ``KG_SUBJECT_CALL_TIMEOUT=nan`` gave a call no
timeout, ``KG_MCP_READ_TIMEOUT=inf`` disabled the absolute deadline, ``KG_WORKER_JOB_SECONDS=abc`` read as the
default and ``KG_MCP_PORT=abc`` ended the server with a traceback.

``NUMBERS`` is the list: every numeric ``KG_*`` setting these readers take, with its kind, bounds and default.
``check`` reads them all at start, as ``switches.check`` reads the on/off ones. ``token`` reads a bearer token: a
value blank once stripped is no token, so a wide bind still needs a real one and a blank bearer never passes.
``port`` reads a TCP port, 1 to 65535. Standard library only.
"""
from __future__ import annotations

import math
import os
from urllib.parse import urlsplit

DAY = 86400.0   # the longest any wait or timeout here may be set to, in seconds
PORT_MIN, PORT_MAX = 1, 65535


class BadSetting(ValueError):
    """A numeric setting holds a value that is not its kind, not finite, or outside its bounds."""


# name -> (kind, low, high, default, low_inclusive): high is always inclusive
NUMBERS = {
    "KG_SUBJECT_CALL_TIMEOUT": (float, 0.0, DAY, 300.0, False),     # mcp_server.route_to_child, per call
    "KG_RDFLIB_LOCK_TIMEOUT": (float, 0.0, DAY, 60.0, True),       # store_rdflib: 0 waits for no other writer
    "KG_WORKER_JOB_SECONDS": (float, 0.0, DAY, 900.0, False),       # execution.submit and run
    "KG_WORKER_MAX_JOB_SECONDS": (float, 0.0, DAY, 900.0, False),   # worker: the cap on one job
    "KG_WORKER_MEMORY": (int, 1, 1 << 40, 4 << 30, True),           # worker: RLIMIT_AS, bytes
    "KG_WORKER_PROCESSES": (int, 1, 1 << 20, 128, True),            # worker: RLIMIT_NPROC
    "KG_WORKER_FILE_BYTES": (int, 1, 1 << 40, 64 << 20, True),      # worker: RLIMIT_FSIZE, bytes
    "KG_MCP_PORT": (int, PORT_MIN, PORT_MAX, 8765, True),          # mcp_server --http
    "KG_DEMO_PORT": (int, PORT_MIN, PORT_MAX, 8080, True),         # the page
}
for _p in ("KG_MCP", "KG_PAGE"):   # http_boundary.Limits.from_env: each transport's bounds
    NUMBERS.update({
        f"{_p}_MAX_BODY": (int, 1, 1 << 30, None, True),
        f"{_p}_READ_TIMEOUT": (float, 0.0, DAY, None, False),
        f"{_p}_IDLE_TIMEOUT": (float, 0.0, DAY, None, False),
        f"{_p}_MAX_CONNECTIONS": (int, 1, 4096, None, True),
    })


def parse(name: str, raw, default=None, *, kind=None, low=None, high=None, inclusive=None):
    """``raw`` read as ``name``: its kind, finite, within its bounds (``NUMBERS``, or the keywords for a setting
    not listed there); unset or empty is ``default`` (the listed one when none is passed). BadSetting else."""
    kind, low, high, listed, inclusive = _spec(name, kind, low, high, inclusive)
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return default if default is not None else listed
    want = _describe(kind, low, high, inclusive)
    v = _convert(name, raw, kind, want)
    if (v < low or (v == low and not inclusive)) or v > high:
        raise BadSetting(f"{name}={raw!r} is out of bounds; it must be {want}")
    return v


def _spec(name, kind, low, high, inclusive):
    """The listed spec of ``name``, each part overridden where a keyword names it."""
    k, lo, hi, d, inc = NUMBERS.get(name, (kind, low, high, None, inclusive))
    return (kind or k, lo if low is None else low, hi if high is None else high, d,
            inc if inclusive is None else inclusive)


def _convert(name: str, raw, kind, want: str):
    """``raw`` as ``kind``, finite: BadSetting naming ``name`` and what it must be, else the value."""
    try:
        v = kind(raw.strip() if isinstance(raw, str) else raw)
    except (TypeError, ValueError):
        raise BadSetting(f"{name}={raw!r} is not {'an integer' if kind is int else 'a number'}; it must be {want}") from None
    if kind is float and not math.isfinite(v):
        raise BadSetting(f"{name}={raw!r} is not finite; it must be {want}")
    return v


def _describe(kind, low, high, inclusive) -> str:
    unit, fmt = ("an integer", "d") if kind is int else ("a finite number", "g")
    return f"{unit} {'from' if inclusive else 'above'} {low:{fmt}} {'to' if inclusive else 'up to'} {high:{fmt}}"


def number(name: str, default=None, env=None):
    """``name`` from ``env`` (the process's environment by default), as ``parse`` reads it."""
    env = os.environ if env is None else env
    return parse(name, env.get(name), default)


def check(env=None, names=None) -> None:
    """BadSetting for the first of ``names`` (every listed setting by default) whose value it refuses."""
    for name in names or NUMBERS:
        number(name, env=env)


def port(name: str, raw, default: int) -> int:
    """A TCP port, 1 to 65535: ``raw`` (a flag's value) as ``name`` reads it."""
    return parse(name, raw, default, kind=int, low=PORT_MIN, high=PORT_MAX, inclusive=True)


def token(name: str, env=None) -> str | None:
    """A bearer token: ``name``'s value, or None when it is unset or blank once stripped (task-0264, AC #3), so
    a blank token never permits a wide bind and a blank bearer never passes."""
    env = os.environ if env is None else env
    value = (env.get(name) or "").strip()
    return value or None


def neo4j_uri(env=None) -> str:
    """``KG_NEO4J_URI`` with its port checked (1 to 65535) when it names one: 99999 no longer wraps."""
    env = os.environ if env is None else env
    uri = env.get("KG_NEO4J_URI") or "bolt://localhost:7687"
    try:
        p = urlsplit(uri).port
    except ValueError:
        raise BadSetting(f"KG_NEO4J_URI={uri!r} names a port that is not 1 to 65535") from None
    if p is not None and not PORT_MIN <= p <= PORT_MAX:
        raise BadSetting(f"KG_NEO4J_URI={uri!r} names a port that is not 1 to 65535")
    return uri
