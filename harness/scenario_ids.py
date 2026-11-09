"""A subject's scenario ids (task-0295, decision-0034 choice 2(a), G9-17).

A scenario id names the scenario on every surface: the gate's report and ``--scenario``, ``run.py``'s output folder,
the page's run and the MCP servers' ``scenario``. So each ``[[scenario]]`` of ``scenarios.toml`` carries an ``id``
that matches ``[A-Za-z0-9][A-Za-z0-9_-]{0,31}``, and no two in a subject are the same. Before, ``id = ""`` and
``id = "../x"`` passed the checker and reached the gate, ``run.py`` wrote ``<out>/../x``, and of two scenarios with one
id the loader kept the last without a word.

``problems`` lists every breach, as ``{code, id, message, hint}`` (code ``scenario-id``); ``tools/check_subject.py``
reports each one and ``harness/subject.py``'s loader raises ``ScenarioIdError`` on the first, so every command that
loads the subject refuses it naming the id, before it writes anything. ``[[scenario.sources]]`` ids and a stage-2
``derived`` id name other things and are not read here.

Standard library only; no subject, no store.
"""
from __future__ import annotations

import re

PATTERN = "[A-Za-z0-9][A-Za-z0-9_-]{0,31}"
_ID = re.compile(PATTERN)   # ASCII only: a letter or digit first, then letters, digits, '_' or '-'
HINT = "give the scenario an id of a letter or digit, then letters, digits, '_' or '-', at most 32 characters (S1, billing-S0)"


class ScenarioIdError(ValueError):
    """A scenarios.toml the loader cannot name its scenarios from: the id and the rule it breaks."""


def problems(scenarios) -> list[dict]:
    """Every breach of the rule in ``scenarios``, the ``[[scenario]]`` tables in file order."""
    out, seen = [], {}
    for i, sc in enumerate(scenarios if isinstance(scenarios, list) else []):
        where = f"[[scenario]] #{i + 1}"
        sid = sc.get("id") if isinstance(sc, dict) else None
        if not isinstance(sc, dict) or "id" not in sc:
            out.append({"code": "scenario-id", "id": None, "where": where,
                        "message": f"{where} has no id: the gate, run.py, the page and the MCP servers name a scenario by it",
                        "hint": HINT})
        elif not isinstance(sid, str) or not _ID.fullmatch(sid):
            out.append({"code": "scenario-id", "id": sid, "where": where,
                        "message": f"scenario id {sid!r} is not {PATTERN}", "hint": HINT})
        elif sid in seen:
            out.append({"code": "scenario-id", "id": sid, "where": where,
                        "message": f"scenario id {sid!r} is also {seen[sid]}'s: one id names one scenario",
                        "hint": "give each scenario its own id"})
        else:
            seen[sid] = where
    return out


def check(scenarios, where: str = "scenarios.toml") -> None:
    """``ScenarioIdError`` on the first breach, naming ``where``, the id and the rule."""
    found = problems(scenarios)
    if found:
        p = found[0]
        more = f" ({len(found) - 1} more)" if len(found) > 1 else ""
        raise ScenarioIdError(f"{where}: {p['message']}{more}")
