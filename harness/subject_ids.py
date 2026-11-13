"""The subjects one server answers for, by id (task-0157, B7; decision-0013 with amendment A1).

A client names a subject by its id, never by a path: the id is the ``[subject] id`` of a manifest under
``KG_SUBJECTS``, resolved as the page resolves ``?subject=`` (``demo/app/server.py``,
``_subject_roots`` and ``_load_subjects``): one or more roots, separated by commas or the path separator,
each a subject (its folder holds ``subject.toml``) or a folder of subjects, a fixture (``listed =
false``) skipped in a folder scan but listed when named directly; ``KG_SUBJECTS`` unset, the
repository's ``subjects/`` folder, and a ``KG_SUBJECT`` outside it listed too. The process's own subject
(``KG_SUBJECT``, the harness's ``SUBJECT``) is the default and answers when a call names none, so a
client that names none sees no change. Standard library only; nothing here reads a store.
"""
from __future__ import annotations

import os
import sys
import re
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}")


class UnknownSubject(ValueError):
    """A subject named by something that is not the id of a subject under KG_SUBJECTS."""


def _manifest(root: Path) -> dict:
    try:
        return tomllib.loads((root / "subject.toml").read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return {}


_SAID: set = set()


def _roots() -> list[Path]:
    raw = os.environ.get("KG_SUBJECTS") or str(ROOT / "subjects")
    out: list[Path] = []
    for part in re.split(r"[,%s]" % re.escape(os.pathsep), raw):
        root = Path(part.strip())
        if not part.strip() or not root.is_dir():
            continue
        if (root / "subject.toml").exists():
            out.append(root)
        else:
            out += sorted(d for d in root.iterdir() if (d / "subject.toml").exists()
                          and _manifest(d).get("subject", {}).get("listed", True) is not False)
    named = os.environ.get("KG_SUBJECT")
    if named and not os.environ.get("KG_SUBJECTS") and Path(named).is_dir() \
            and Path(named).resolve() not in {r.resolve() for r in out}:
        out.insert(0, Path(named))
    return out


def _said(sid: str, dropped: Path, kept: Path) -> None:
    """task-0339 (R8): a duplicate id dropped, named once on stderr with the root kept."""
    if (sid, str(dropped)) not in _SAID:
        _SAID.add((sid, str(dropped)))
        print(f"subjects: id {sid!r} is also at {dropped}; the root kept is {kept}", file=sys.stderr)


def subjects() -> list[dict]:
    """Every subject this process may answer for: id, name, root (resolved) and scenarios, in the page's
    order, ids unique (the first root with an id wins, as on the page), the default first."""
    from subject import SUBJECT
    listed, kept, seen_roots, dropped = [], {}, set(), []
    for root in _roots():
        if root.resolve() in seen_roots:   # the same root named twice is one root
            continue
        seen_roots.add(root.resolve())
        m = _manifest(root)
        s = m.get("subject", {})
        sid = s.get("id", root.name)
        if sid in kept and m:
            dropped.append((sid, root.resolve()))
        if sid in kept or not m:
            continue
        kept[sid] = root.resolve()
        listed.append({"id": sid, "name": s.get("name", sid), "root": root.resolve(), "scenarios": _scenarios(root)})
    own = Path(SUBJECT.root).resolve()
    if not any(x["root"] == own for x in listed):   # the process's own subject is always answerable
        dropped += [(x["id"], x["root"]) for x in listed if x["id"] == SUBJECT.id]
        kept[SUBJECT.id] = own   # L6: only the root actually kept is named, below
        listed = [x for x in listed if x["id"] != SUBJECT.id]   # task-0339: an id is named once, the default's
        listed.insert(0, {"id": SUBJECT.id, "name": SUBJECT.name, "root": own, "scenarios": list(SUBJECT.order)})
    for sid, root in dropped:
        if root != kept[sid]:   # the own subject's root, first dropped as a duplicate, is the one kept
            _said(sid, root, kept[sid])
    first = [x for x in listed if x["root"] == own]
    return first + [x for x in listed if x not in first]


def _scenarios(root: Path) -> list[str]:
    try:
        sc = tomllib.loads((root / "scenarios.toml").read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return []
    return [s.get("id") for s in sc.get("scenario", []) if s.get("id")]


def resolve(subject_id) -> dict | None:
    """None when no subject is named (the process's own answers); else that subject's entry. A path, an
    id of the wrong shape or one not under KG_SUBJECTS is refused, never resolved as a path."""
    if subject_id is None:
        return None
    if not isinstance(subject_id, str) or not ID.fullmatch(subject_id) or ".." in subject_id:
        raise UnknownSubject(f"subject is the id of a subject under KG_SUBJECTS (list_subjects), never a path: {subject_id!r}")
    listed = subjects()
    hit = next((x for x in listed if x["id"] == subject_id), None)
    if hit is None:
        raise UnknownSubject(f"no subject {subject_id!r} under KG_SUBJECTS; this server answers for {[x['id'] for x in listed]}")
    return hit


def is_own(entry: dict | None) -> bool:
    from subject import SUBJECT
    return entry is None or entry["root"] == Path(SUBJECT.root).resolve()


def declaring(scenario: str | None) -> list[str]:
    """The ids of the subjects under KG_SUBJECTS whose scenarios include ``scenario``: the store records
    a held scenario by its id alone, so this is who it may belong to."""
    if not scenario:
        return []
    return [x["id"] for x in subjects() if scenario in x["scenarios"]]
