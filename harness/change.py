"""A scenario's second stage (the subject's ``[scenario.stage2]``) in two steps, shared by
``run.py``'s ``stage2`` and the gate command's ``--stage 2`` (task-0049):

1. ``apply_change``: register the earlier governed output as derived, re-load the later kit whole as
   a new version (task-0197: every document extracted, so symbols resolve from all of them; a version
   written only for the artefacts whose bytes changed; each statement diffed by its id stem on value
   and fragment set), invalidate what the change replaced (R-STALE, which also withdraws a declared gap
   whose declaration it invalidated), and run the rules again across versions on the live statements.
   A review's acts stand: no rule re-run undoes one (R-REQ never reopens a closed gap; a settled
   dispute's rejected side is dead); its rulings are bound again to what the change left current, and one
   whose statement changed is reported, never moved onto the successor (task-0199). The gate after this step is the record's ``gate_before_reverification``.
2. ``reverify``: the owner stand-in's recorded re-verification of the new statements on the named
   keys, then the corroboration of the new version's statements against the pristine values. The
   gate after this step is the record's ``gate_after_reverification``.

The store port only; nothing here names a subject, a scenario or a document.
"""
from __future__ import annotations

from kitio import kit_for, sha256
from load import ATTESTER, attestation, load_reviews, load_scenario, load_verifications
from rules import r_stale, run_all


def version_of(cfg2: dict) -> str:
    return cfg2.get("version", "v2")


def apply_change(sc: str, cfg2: dict, s, derived_code: str | None, derived_ids: list[str],
                 kit2: dict[str, str] | None = None, kit1: dict[str, str] | None = None) -> dict:
    """Step 1; returns {load_v2, D3_stale, R-STRUCT_after, kit2, derived}. ``kit2`` and ``kit1`` default to the
    scenario's later and first kits; a test passes its own to plant a change."""
    version = version_of(cfg2)
    derived = cfg2.get("derived", {})
    did = None
    if derived_code:
        did = derived.get("id", f"derived:{sc}")
        s.register_derived(did, derived.get("kind", "artefact"), sha256(derived_code), derived_ids)
    kit2 = kit_for(sc, 2) if kit2 is None else kit2
    kit1 = kit_for(sc) if kit1 is None else kit1
    art = cfg2["artefact"]
    changed = {p for p in kit2 if kit1.get(p) != kit2.get(p)} | {art}
    load2 = load_scenario(s, sc, kit2, activity_note=cfg2.get("note", f"{sc} stage 2: re-ingestion of the changed {art}"),
                          version_tag=version, reingest=True, changed=changed)
    stale = r_stale(s, version)
    struct = run_all(s, sc)["R-STRUCT"]
    # task-0199 (doc-0032 §6 item 7): every ruling again, against what the change left current: one whose
    # statement the change replaced is not applied to its successor, and the gate reports it (an ``act`` finding)
    load_reviews(s, sc, recheck=True)
    return {"load_v2": load2, "D3_stale": stale, "R-STRUCT_after": struct, "kit2": kit2, "derived": did}


def reverify(sc: str, cfg2: dict, pv: dict, s, kit2: dict) -> list[str]:
    """Step 2; returns the re-verified statements' ids. The owner's re-verification is an attestation: with no
    ``at`` or no attester it is not applied (task-0199, doc-0030 I9), and ``check_subject`` refuses it."""
    act = attestation(f"[scenario.stage2] of {sc}", cfg2)
    rever = s.reverify(version_of(cfg2), list(cfg2.get("reverify_keys", [])), ATTESTER, act["at"],
                       cfg2.get("reverify_scope", "re-verification"), cfg2.get("reapproval_record", "re-approval")) if act else []
    # new-version assertions of unchanged fragments inherit nothing automatically: they are new statements.
    # Corroboration and verification of them against the pristine values:
    load_verifications(s, sc, dict(pv), kit2)
    return rever
