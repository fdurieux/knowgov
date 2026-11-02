"""Read the subject's artefacts into memory, then apply a scenario's plant (plant.py).
Nothing here touches the committed files.

Keys are the artefact keys the subject manifest declares (the record's names for the
documents); the bytes come from the paths it names, relative to the subject root.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from subject import SUBJECT, ROOT, HERE

# Fixed order: the baseline arm concatenates in this order (pre-registration §7).
KIT_FILES: list[tuple[str, Path]] = SUBJECT.kit_files
FAMILY: dict[str, tuple[str, str]] = SUBJECT.families


def pristine() -> dict[str, str]:
    return SUBJECT.pristine()


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def kit_for(scenario: str, stage: int = 1) -> dict[str, str]:
    """The in-memory kit for a scenario. A scenario with a stage 2 has two kits: the
    first is the pristine one, the second applies the stage-2 change."""
    from plant import apply_plant  # local import: plant imports nothing

    kit = pristine()
    return apply_plant(kit, scenario, stage)


def kit_text(kit: dict[str, str], path: str) -> str:
    """The text of one kit file as the scenario's kit holds it: ``path`` is an artefact key, or an
    artefact key that names a directory plus the part's relative path inside its bundle
    (``contracts/universe.toml`` is the part ``universe.toml`` of the artefact ``contracts/``). A
    plant on the file reaches the caller, since the kit is the scenario's."""
    from subject import bundle_parts  # stdlib: the tests job has no yaml, which extract needs

    if path in kit:
        return kit[path]
    keys = sorted((k for k in kit if k.endswith("/") and path.startswith(k)), key=len, reverse=True)
    for key in keys:
        rel = path[len(key):]
        for part, text in bundle_parts(kit[key]):
            if part == rel:
                return text
    raise KeyError(f"{path}: not a kit file of this scenario (artefact keys: {sorted(kit)})")
