"""The kit's claim (task-0214, decision-0018 point 3, doc-0032 §3), on the store KG_STORE names (rdflib in memory
by default, Neo4j where it runs), on the probe kit ``tools/fixtures/claim_probe``:

    python tools/check_claim_probe.py

- Every mapping. Each of the five bundle mappers reads a statement's claim into its basis: observed to
  extracted, inferred to inferred, intended to authored. A statement without one reads as before
  (requirements_json's extracted, the other four's authored). An assertion resting on statements of different
  claims takes the most conservative: CLM-004's contracts, the decision table and the probe feature.
- The ceiling. The probe declares execution derived from its suite, the authored attestation and the approval.
  After the load, every inferred statement is proposed, with no verification and no approval. CLM-005, observed,
  whose only verifying scenario is inferred, derives no execution and stays proposed. Intended statements are
  approved through the attestation, observed ones through execution.
- The gate (codegen) reads CLM-002|statement proposed and CLM-005|statement proposed: QUALIFIED.
- I4 (task-0199). A ruling approving CLM-002's inferred statement is refused by ``review.check``; one rejecting it
  is not refused for that reason.
- check_subject. The probe is not refused. A copy whose CLM-001 claims ``guessed`` is refused under rule
  ``claim``, and its mapper raises, so its load fails rather than guess.

The clock is pinned to the probe's record date (task-0075). Exit 0 when every check holds, 1 naming each that
does not.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tools" / "fixtures" / "claim_probe"
os.environ["KG_SUBJECT"] = str(FIXTURE)   # the harness binds its subject at import
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tools")]

SC = "C"
DONE = ("approved",)   # what an observed or intended statement reaches here: execution or attestation, then approval
# key -> (basis, status) after the load: every mapping, the collapse, the ceiling
EXPECTED = {
    # requirements_json: an item's "claim"
    "CLM-001|statement": ("extracted", "approved"),     # observed, verified by execution, approved
    "CLM-002|statement": ("inferred", "proposed"),      # inferred: no verification, no approval, ever
    "CLM-003|statement": ("authored", "approved"),      # intended: the attestation, then approval
    "CLM-004|statement": ("extracted", "approved"),     # no claim: as before
    "CLM-005|statement": ("extracted", "proposed"),     # observed, but its only verifying scenario is inferred
    # contracts_markdown: a part's "Claim:" line
    "CLM-001|elaborated_by": ("extracted", "proposed"),  # observed: nothing here verifies a link by execution
    "CLM-002|elaborated_by": ("inferred", "proposed"),
    "CLM-003|elaborated_by": ("authored", "approved"),   # no claim: as before
    "CLM-004|elaborated_by": ("inferred", "proposed"),   # an inferred part and a plain one: the most conservative
    # dmn_decisions: "claim:" in a decision's or a rule's description
    "dmn:value_gate|rules": ("inferred", "proposed"),    # one inferred rule among three
    "CLM-001|decided_by": ("extracted", "proposed"),     # the rule's claim
    "CLM-002|decided_by": ("inferred", "proposed"),
    "CLM-003|decided_by": ("authored", "approved"),      # the decision's claim, intended
    # plantuml_realises: a "' claim:" comment line
    "diagram:inferred|type": ("inferred", "proposed"),
    "diagram:inferred|elements": ("inferred", "proposed"),
    "CLM-002|realised_by": ("inferred", "proposed"),
    "diagram:plain|type": ("authored", "approved"),      # no claim: as before
    "CLM-001|realised_by": ("authored", "approved"),
    # gherkin_tagged: "@claim:" on the Feature, a Rule or a Scenario, the nearest winning
    "CLM-001|verified_by": ("extracted", "proposed"),    # the Feature's observed
    "CLM-003|verified_by": ("authored", "approved"),     # the Scenario's intended over the Feature's observed
    "CLM-002|verified_by": ("inferred", "proposed"),     # the Rule's inferred
    "CLM-005|verified_by": ("inferred", "proposed"),
    "feature:probe|scenarios": ("inferred", "proposed"),  # two inferred scenarios among four
    "CLM-004|verified_by": ("authored", "approved"),     # no claim: as before
    "feature:plain|scenarios": ("authored", "approved"),
}
INFERRED_AID = "A:req:CLM-002|statement@v1"
LIVE = ["proposed", "validated", "verified", "approved", "disputed"]


def open_kind():
    from store import open_store
    kind = (os.environ.get("KG_STORE") or "rdflib").lower()
    return kind, open_store(kind, access="write", **({"path": ""} if kind == "rdflib" else {}))


def load(st) -> None:
    """What a deterministic run does before its gate (gate_cli._load)."""
    from kitio import kit_for
    from load import load_captures, load_reviews, load_scenario, load_verifications, pristine_values
    from rules import run_all
    kit = kit_for(SC)
    st.wipe()
    st.apply_constraints()
    load_scenario(st, SC, kit, activity_note=f"{SC}: the claim probe", version_tag="v1")
    load_verifications(st, SC, pristine_values(), kit)
    load_captures(st, SC)
    run_all(st, SC)
    load_reviews(st, SC)


def mappings(st) -> list[str]:
    errs = []
    for key, (basis, status) in EXPECTED.items():
        rows = st.key_evidence(key, LIVE)
        if len(rows) != 1:
            errs.append(f"{key}: {len(rows)} live statement(s), expected 1: {[r['id'] for r in rows]}")
            continue
        r = rows[0]
        if (r["basis"], r["status"]) != (basis, status):
            errs.append(f"{key}: {r['basis']}, {r['status']}; expected {basis}, {status}")
        if r["basis"] == "inferred" and (r["verifications"] or r["approvals"]):
            errs.append(f"{key}: inferred, yet {len(r['verifications'])} verification(s) and {len(r['approvals'])} approval(s)")
    return errs


def gate(st) -> list[str]:
    import cadence
    import gate_cli
    from subject import SUBJECT
    from tasks import TASKS
    rep = gate_cli.evaluate(st, subject=SUBJECT.id, scenario=SC, task="codegen", spec=TASKS["codegen"], threshold="blocker",
                            baseline=None, loaded=True, as_of=cadence.as_of("record").isoformat())
    want = {"CLM-001|statement": "approved", "CLM-002|statement": "proposed", "CLM-003|statement": "approved",
            "CLM-004|statement": "approved", "CLM-005|statement": "proposed"}
    errs = [f"gate: {k} reads {rep['levels'].get(k)}, expected {v}" for k, v in want.items() if rep["levels"].get(k) != v]
    if rep["verdict"] != "QUALIFIED":
        errs.append(f"gate: {rep['verdict']}, expected QUALIFIED (two of five keys proposed, under no blocking level)")
    print(f"gate codegen: {rep['verdict']}; levels {rep['levels']}")
    return errs


def ruling(st) -> list[str]:
    import review
    import rules
    b = review.statement(st, INFERRED_AID)
    if b is None:
        return [f"I4: the store holds no {INFERRED_AID}"]
    handles = {"probe-1": {"issued": None, "withdrawn": None, "roles": {"approves", "closes"}, "unit": "ORG-0001"}}
    owners = {b["key"]: ["ORG-0001"]}
    errs = []
    for outcome, refused in (("approved", True), ("rejected", False)):
        doc = {"review": {"by": "probe-1", "on": "2026-11-08", "record": "the claim probe", "scenario": SC},
               "ruling": [{"assertion": INFERRED_AID, "outcome": outcome, "key": b["key"], "value": str(b["value"]), "sha256": b["sha256"]}]}
        why, _norm = review.check(doc, st, handles=handles, owners=owners, units={"ORG-0001": "probe unit"}, captures={},
                                  now=dt.date(2026, 11, 8), compatible=rules.compatible)
        hit = [w for w in why if "never approve it" in w]
        if refused and not hit:
            errs.append(f"I4: a ruling approving the inferred {INFERRED_AID} was not refused: {why}")
        if not refused and hit:
            errs.append(f"I4: a ruling rejecting the inferred {INFERRED_AID} was refused for its basis: {hit}")
        print(f"I4: a ruling {outcome} on {INFERRED_AID}: " + ("refused, " + hit[0] if hit else f"not refused for its basis ({len(why)} other reason(s))"))
    return errs


def subject_check() -> list[str]:
    import check_subject
    import extract
    errs = []
    rep = check_subject.check(FIXTURE)
    claims = [f for f in rep["findings"] if f["rule"] == "claim"]
    if rep["exit_code"] != 0 or claims:
        errs.append(f"check_subject refuses the probe: {[f['message'] for f in rep['findings'] if f['level'] == 'error']}")
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "claim_probe_bad"
        shutil.copytree(FIXTURE, bad)
        p = bad / "kit" / "requirements.json"
        items = json.loads(p.read_text(encoding="utf-8"))
        items[0]["claim"] = "guessed"
        text = json.dumps(items, indent=1)
        p.write_text(text, encoding="utf-8")
        rep = check_subject.check(bad)
        claims = [f for f in rep["findings"] if f["rule"] == "claim"]
        if rep["exit_code"] != 1 or not claims or "guessed" not in claims[0]["message"]:
            errs.append(f"check_subject: a claim 'guessed' is not refused under rule claim: {rep['findings']}")
        else:
            print(f"check_subject: {claims[0]['where']}: {claims[0]['message']}")
        try:
            extract.extract_requirements_json("requirements.json", text)
            errs.append("the load: the requirements mapper read a claim 'guessed' instead of refusing it")
        except extract.UnknownClaim as e:
            print(f"the load fails on it: UnknownClaim: {e}")
    return errs


def main() -> int:
    import cadence
    os.environ.update(cadence.pin_record({}))   # the probe's record date, the wall clock refused (task-0075)
    kind, st = open_kind()
    try:
        load(st)
        errs = mappings(st) + gate(st) + ruling(st)
        st.commit()
    finally:
        st.close()
    errs += subject_check()
    for e in errs:
        print("FAIL", e)
    print(f"the claim probe on {kind}: " + (f"every check holds, {len(EXPECTED)} statements in five mappers" if not errs else f"{len(errs)} failure(s)"))
    return 1 if errs else 0


if __name__ == "__main__":
    import _outcomes   # task-0314 R5
    _outcomes.help_exit(__doc__)
    import _outcomes   # task-0159: the outcome recorded when KG_OUTCOMES names a file
    sys.exit(_outcomes.run(main))
