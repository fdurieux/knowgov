"""Whose load the store holds, for every reader (task-0195, doc-0030 F1, H1; decision-0013 with A1).

One store serves every subject of an instance, and two subjects may declare the same scenario id, so the
held scenario alone never says whose it is. The load records its subject on the extraction activity, and
the port's ``held()`` reads it back. This module is the one rule every reader applies: ``gate_cli
--no-load``, the MCP reader's store-backed tools, ``proposal_impact``, the page and the snapshot checks.

- The store holds the subject's load when ``held()`` names that subject. Its scenario is then the held one.
- It holds another subject's load when ``held()`` names another subject, whatever the scenario id.
- A store loaded before task-0195 recorded no subject (``subject`` None). It reads as unknown and fails
  closed: it counts as the subject's only when that subject is the only one under ``KG_SUBJECTS`` and
  declares the held scenario. Any other reader is refused and told to reload.
"""
from __future__ import annotations

LEGACY = ("the store was loaded before it recorded whose load it holds (task-0195), and more than one subject "
          "could declare its scenario; reload the scenario to read it")


def _only_subject() -> str | None:
    try:
        import subject_ids
        ids = [s["id"] for s in subject_ids.subjects()]
    except Exception:  # noqa: BLE001 — no readable KG_SUBJECTS: nothing is the only subject
        return None
    return ids[0] if len(ids) == 1 else None


def owner(held: dict | None) -> str | None:
    """The subject whose load is held: the recorded one, or for a store loaded before task-0195 the
    instance's only subject when it declares the held scenario, else None (unknown)."""
    if not held:
        return None
    if held.get("subject"):
        return held["subject"]
    only = _only_subject()
    if only is None:
        return None
    try:
        import subject_ids
        mine = next(s for s in subject_ids.subjects() if s["id"] == only)
    except Exception:  # noqa: BLE001
        return None
    return only if held.get("scenario") in mine.get("scenarios", []) else None


def scenario_for(held: dict | None, subject_id: str) -> str | None:
    """The held scenario when the held load is ``subject_id``'s, else None."""
    return held.get("scenario") if held and owner(held) == subject_id else None


def foreign(held: dict | None, subject_id: str) -> bool:
    """True when the store holds a load that is not ``subject_id``'s, or whose owner is unknown."""
    return bool(held) and owner(held) != subject_id


def refusal(held: dict | None, subject_id: str, scenario: str | None = None) -> str | None:
    """Why ``subject_id`` may not read the held state (for ``scenario`` when one is named), else None."""
    if not held:
        return "the store holds no scenario"
    who = owner(held)
    if who is None:
        return f"the store holds {held.get('scenario') or 'a load'} of an unknown subject: {LEGACY}"
    if who != subject_id:
        return (f"the store holds {held.get('scenario')} of subject {who}, not of {subject_id}; "
                "a store-backed read answers for the subject whose load is held only")
    if scenario and scenario != held.get("scenario"):
        return f"the store holds {held.get('scenario')}, not {scenario!r}"
    return None
