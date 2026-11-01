"""The plant: mechanical patches per scenario (pumllint kg_experiment/PREREGISTRATION.md §5),
read from the subject's ``plants.toml``.

Each patch is a table with ``path`` and ``op``: ``replace`` (``old`` must be found exactly once,
or it is a hard error), ``drop`` (removes the artefact) or ``add`` (adds one with ``new``). On a
directory artefact a ``replace`` may name ``within``, the part (the file's relative path) the
match is confined to, so a hunk unique in its file need not be unique in the whole bundle.
"""

from __future__ import annotations

import re

from subject import BUNDLE_MARK, SUBJECT

INFERRED = SUBJECT.inferred


def _part_span(text: str, rel: str) -> tuple[int, int]:
    """(start, end) of the part ``rel`` of a bundle, marker line included."""
    marker = BUNDLE_MARK.format(rel=rel) + "\n"
    start = text.find(marker)
    if start < 0:
        raise RuntimeError(f"plant: no part {rel!r} in the bundle")
    m = re.compile(r"^==> .+? <==$", re.M).search(text, start + len(marker))
    return start, (m.start() if m else len(text))


def apply_plant(kit: dict[str, str], scenario: str, stage: int = 1) -> dict[str, str]:
    kit = dict(kit)
    for patch in SUBJECT.plants_for(scenario, stage):
        path, op = patch["path"], patch.get("op", "replace")
        if op == "drop":
            if path not in kit:
                raise RuntimeError(f"plant: cannot drop missing {path}")
            del kit[path]
            continue
        if op == "add":
            kit[path] = patch["new"]
            continue
        old, new = patch["old"], patch["new"]
        if patch.get("within"):
            s, e = _part_span(kit[path], patch["within"])
            part = kit[path][s:e]
            n = part.count(old)
            if n != 1:
                raise RuntimeError(f"plant: {scenario} patch on {path} within {patch['within']} matched {n} times:\n{old[:80]}")
            kit[path] = kit[path][:s] + part.replace(old, new) + kit[path][e:]
            continue
        n = kit[path].count(old)
        if n != 1:
            raise RuntimeError(f"plant: {scenario} patch on {path} matched {n} times:\n{old[:80]}")
        kit[path] = kit[path].replace(old, new)
    return kit
