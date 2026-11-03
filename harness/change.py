"""A scenario's second stage (the subject's ``[scenario.stage2]``) in two steps, shared by
``run.py``'s ``stage2`` and the gate command's ``--stage 2`` (task-0049):

1. ``apply_change``: register the earlier governed output as derived, re-ingest the changed
   artefact as a new version, invalidate what rested on the changed fragments (R-STALE), run
   R-STRUCT again. The gate after this step is the record's ``gate_before_reverification``.
2. ``reverify``: the owner stand-in's recorded re-verification of the new statements on the named
   keys, then the corroboration of the new version's statements against the pristine values. The
   gate after this step is the record's ``gate_after_reverification``.

The store port only; nothing here names a subject, a scenario or a document.
"""
from __future__ import annotations

from kitio import kit_for, sha256
from load import HUMAN, load_scenario, load_verifications
from rules import r_stale, run_all


def version_of(cfg2: dict) -> str:
    return cfg2.get("version", "v2")


def apply_change(sc: str, cfg2: dict, s, derived_code: str | None, derived_ids: list[str]) -> dict:
    """Step 1; returns {load_v2, D3_stale, R-STRUCT_after, kit2, derived}."""
    version = version_of(cfg2)
    derived = cfg2.get("derived", {})
    did = None
    if derived_code:
        did = derived.get("id", f"derived:{sc}")
        s.register_derived(did, derived.get("kind", "artefact"), sha256(derived_code), derived_ids)
    kit2 = kit_for(sc, 2)
    art = cfg2["artefact"]
    load2 = load_scenario(s, sc, {art: kit2[art]}, activity_note=cfg2.get("note", f"{sc} stage 2: re-ingestion of the changed {art}"),
                          version_tag=version, reingest=True)
    stale = r_stale(s, version)
    return {"load_v2": load2, "D3_stale": stale, "R-STRUCT_after": run_all(s, sc)["R-STRUCT"], "kit2": kit2, "derived": did}


def reverify(sc: str, cfg2: dict, pv: dict, s, kit2: dict) -> list[str]:
    """Step 2; returns the re-verified statements' ids."""
    rever = s.reverify(version_of(cfg2), list(cfg2.get("reverify_keys", [])), HUMAN["id"], cfg2.get("at", ""),
                       cfg2.get("reverify_scope", "re-verification"), cfg2.get("reapproval_record", "re-approval"))
    # new-version assertions of unchanged fragments inherit nothing automatically: they are new statements.
    # Corroboration and verification of them against the pristine values:
    load_verifications(s, sc, dict(pv), kit2)
    return rever
