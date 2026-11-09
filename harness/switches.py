"""The on/off settings, each read through one parser (task-0276, decision-0033 choice 2).

A flag is on with ``1``; ``0``, empty or unset is off. A setting documented with a word keeps that word:
``KG_LOAD_MEMORY_CHECK=off`` and ``KG_KEY_CHECK=off`` turn their check off, ``on``, empty or unset leaves it on,
in any case. Any other value raises ``BadSwitch``, a ``ValueError`` naming the setting and the spellings it
accepts, which a command's ``cli_exit.run`` turns into exit 2 with that line. Before, ``KG_NO_LOAD=true`` or
``KG_TRACEBACK=yes`` silently meant off.

``SWITCHES`` is the list: every on/off ``KG_*`` setting the harness, the page or the CI wrappers read, with
its spellings and where it is documented. ``instance/ci/knowgov-gate.sh`` reads ``KG_NO_LOAD`` and
``KG_PUBLISH`` under the same rule in shell (its ``flag``), and ``tests/test_switches.py`` holds the two equal.
Standard library only.
"""
from __future__ import annotations

import os

FLAG = {"1": True, "0": False, "": False}            # 1 on; 0, empty or unset off
WORD_ON = {"on": True, "off": False, "": True}       # a check that is on unless switched off by name

# name -> (spellings, where it is documented, who reads it)
SWITCHES = {
    "KG_NO_LOAD": (FLAG, "instance/README.md", "instance/ci/knowgov-gate.sh"),
    "KG_PUBLISH": (FLAG, "instance/README.md", "instance/ci/knowgov-gate.sh"),
    "KG_ALLOW_UNCONTAINED_EXECUTION": (FLAG, "docs/security.md", "harness/execution_guard.py, harness/execution.py"),
    "KG_TRACEBACK": (FLAG, "harness/cli_exit.py", "harness/cli_exit.py"),
    "KG_THINKING_UNCOUNTED": (FLAG, "demo/models.toml (thinking_uncounted)", "harness/arms.py"),
    "KG_LOAD_MEMORY_CHECK": (WORD_ON, "instance/README.md, docs/security.md", "harness/load_memory.py"),
    "KG_KEY_CHECK": (WORD_ON, "demo/README.md, docs/security.md", "harness/key_check.py"),
}


class BadSwitch(ValueError):
    """An on/off setting holds a value outside its spellings."""


def accepted(name: str) -> str:
    """The spellings ``name`` accepts, as a refusal names them."""
    spellings = SWITCHES[name][0]
    if spellings is FLAG:
        return "1 (on), or 0, empty or unset (off)"
    return "off (off), or on, empty or unset (on), in any case"


def parse(name: str, raw: str | None) -> bool:
    """``raw`` read as ``name``'s spellings: True for on; BadSwitch for anything they do not name."""
    spellings = SWITCHES[name][0]
    value = (raw or "").strip()
    if spellings is WORD_ON:
        value = value.lower()
    if value not in spellings:
        raise BadSwitch(f"{name}={raw!r} is not a value it accepts: {accepted(name)}")
    return spellings[value]


def on(name: str, env=None) -> bool:
    """Whether ``name`` is on in ``env`` (the process's environment by default)."""
    env = os.environ if env is None else env
    return parse(name, env.get(name))


def check(env=None, names=None) -> None:
    """BadSwitch for the first of ``names`` (every switch by default) set to a value it does not accept."""
    for name in names or SWITCHES:
        on(name, env)
