"""The plant: mechanical patches per scenario (pumllint kg_experiment/PREREGISTRATION.md §5),
read from the subject's ``plants.toml``.

Each patch is a table with ``path`` and ``op``: ``replace`` (``old`` must be found exactly once,
or it is a hard error), ``drop`` (removes the artefact) or ``add`` (adds one with ``new``).
"""

from __future__ import annotations

from subject import SUBJECT

INFERRED = SUBJECT.inferred


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
        n = kit[path].count(old)
        if n != 1:
            raise RuntimeError(f"plant: {scenario} patch on {path} matched {n} times:\n{old[:80]}")
        kit[path] = kit[path].replace(old, new)
    return kit
