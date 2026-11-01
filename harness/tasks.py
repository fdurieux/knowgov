"""Required keys per task class (pre-registration §6), frozen in the subject's manifest."""

from subject import SUBJECT

TASKS = {name: {"keys": list(spec.get("keys", [])),
                "block_levels": set(spec.get("block_levels", ["absent", "declared_gap", "disputed", "invalidated"])),
                "max_unverified_share": float(spec.get("max_unverified_share", 0.25))}
         for name, spec in SUBJECT.tasks.items()}
