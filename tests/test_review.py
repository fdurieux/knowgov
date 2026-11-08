"""Task-0037: a person's review under decision-0002 and ieam-register decision 0009. The checks in
harness/review.py against a store stand-in: who may approve what a person gave, rule on a
document, settle a dispute and close a declared gap, and what is refused; the six-month lapse; the
issued handles read from the vendored register. The store half (S2' from BLOCKED to PROCEED by
command, S4 settled, the lapse) runs in harness.yml on rdflib and in the stack job on Neo4j."""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(Path(__file__).resolve().parent)]
import review  # noqa: E402

REG = ROOT / "demo" / "register"
NOW = dt.date(2026, 11, 3)
OUT = "QuoteAPI|on_screening_outage"
CAP = "A:cap:2026-11-02-ORG-0002-employee-1:1@capture"
HELD = "priced=yes;status=held_unscreened;notified=no;hold=true"
FAIL = "priced=no;status=error: screening_unavailable;notified=no"


def compatible(a, b, _pred=""):
    return "equal" if a == b else "conflict"


class FakeStore:
    """What review.check reads: assertion_brief, key_evidence over disputed, declared_gap."""

    def __init__(self, assertions: list[dict], gaps: list[dict] | None = None):
        self.a = {x["id"]: x for x in assertions}
        self.g = {x["id"]: x for x in gaps or []}

    def assertion_brief(self, aid):
        return dict(self.a[aid]) if aid in self.a else None

    def key_evidence(self, key, live):
        return [x for x in self.a.values() if x["key"] == key and x["status"] in live]

    def declared_gap(self, gid):
        return self.g.get(gid)


def _a(aid, key=OUT, value=HELD, basis="extracted", status="proposed", agent="harness"):
    return {"id": aid, "key": key, "value": value, "basis": basis, "status": status, "agent": agent}


def _check(doc, st, **over):
    kw = {"handles": review.issued_handles(REG), "owners": {OUT: ["ORG-0001", "ORG-0002"]},
          "units": review.organisation_units(REG), "captures": {CAP: {"from": "employee-1", "on": dt.date(2026, 11, 2)}},
          "now": NOW, "compatible": compatible}
    kw.update(over)
    return review.check(doc, st, **kw)


def _doc(by, rulings=(), closes=(), on="2026-11-03"):
    return {"review": {"by": by, "on": on, "record": "minutes/2026-11-03.md"},
            "ruling": [{"assertion": a, "outcome": o} for a, o in rulings], "closes": [{"gap": g} for g in closes]}


def _person():
    return FakeStore([_a(CAP, basis="elicited", agent="employee-1")])


def test_the_vendored_register_issues_four_handles_with_their_roles():
    h = review.issued_handles(REG)
    assert {k: (v["unit"], sorted(v["roles"])) for k, v in h.items()} == {
        "employee-1": ("ORG-0002", ["gives"]), "employee-2": ("ORG-0002", ["approves", "gives"]),
        "employee-3": ("ORG-0001", ["approves", "closes", "gives"]),
        "employee-4": ("ORG-0004", ["approves", "closes", "gives"])}   # the compliance stand-in (register decision 0011)


def test_another_handle_with_approves_of_an_owning_unit_approves_what_a_person_gave():
    errs, rv = _check(_doc("employee-2", [(CAP, "approved")]), _person())
    assert errs == [] and rv["by"] == "employee-2" and rv["on"] == NOW


def test_refused_the_giver_a_handle_without_approves_a_name_and_a_future_date():
    errs, _ = _check(_doc("employee-1", [(CAP, "approved")]), _person())
    assert any("gave this statement" in e for e in errs) and any("lacks the role approves" in e for e in errs)
    errs, _ = _check(_doc("John Doe", [(CAP, "approved")]), _person())
    assert any("is not an issued handle" in e for e in errs)
    errs, _ = _check(_doc("employee-2", [(CAP, "approved")], on="2026-12-01"), _person())
    assert any("in the future" in e for e in errs)


def test_refused_a_ruling_on_an_assertion_the_store_does_not_hold_and_an_unknown_outcome():
    errs, _ = _check(_doc("employee-2", [("A:nope@v1", "approved"), (CAP, "maybe")]), _person())
    assert any("holds no assertion 'A:nope@v1'" in e for e in errs) and any("outcome 'maybe'" in e for e in errs)


def test_a_withdrawn_handle_or_one_issued_after_the_review_is_refused():
    h = review.issued_handles(REG)
    h["employee-2"]["withdrawn"] = dt.date(2026, 11, 3)
    errs, _ = _check(_doc("employee-2", [(CAP, "approved")]), _person(), handles=h)
    assert any("was withdrawn" in e for e in errs)
    errs, _ = _check(_doc("employee-2", [(CAP, "approved")], on="2026-11-01"), _person())
    assert any("issued on 2026-11-02, after" in e for e in errs)


def test_a_unit_that_does_not_own_the_key_is_refused():
    errs, _ = _check(_doc("employee-2", [(CAP, "approved")]), _person(), owners={OUT: ["ORG-0001"]})
    assert any("does not own" in e for e in errs)


def test_overruling_a_document_needs_closes():
    st = FakeStore([_a("A:oas:x@v1", status="validated")])
    assert any("needs the role closes" in e for e in _check(_doc("employee-2", [("A:oas:x@v1", "rejected")]), st)[0])
    assert _check(_doc("employee-3", [("A:oas:x@v1", "rejected")]), st)[0] == []


def _dispute():
    return FakeStore([_a("A:dt:o@v1", status="disputed"), _a("A:spec:o@v1", status="disputed"),
                      _a("A:seq:o@v1", value=FAIL, status="disputed"), _a("A:bpmn:o@v1", value=FAIL, status="disputed")])


def test_a_dispute_is_settled_only_whole_and_on_one_value():
    st = _dispute()
    errs, _ = _check(_doc("employee-3", [("A:dt:o@v1", "approved")]), st)
    assert any("half-settled, 3 disputed statement(s) left unruled" in e for e in errs), errs
    errs, _ = _check(_doc("employee-3", [("A:dt:o@v1", "approved"), ("A:spec:o@v1", "approved"),
                                         ("A:seq:o@v1", "approved"), ("A:bpmn:o@v1", "rejected")]), st)
    assert any("disagree with each other" in e for e in errs)
    errs, _ = _check(_doc("employee-3", [("A:dt:o@v1", "approved"), ("A:spec:o@v1", "approved"),
                                         ("A:seq:o@v1", "rejected"), ("A:bpmn:o@v1", "referred")]), st)
    assert any("half-settled" in e for e in errs)
    errs, _ = _check(_doc("employee-3", [("A:dt:o@v1", "approved"), ("A:spec:o@v1", "approved"),
                                         ("A:seq:o@v1", "rejected"), ("A:bpmn:o@v1", "rejected")]), st)
    assert errs == []
    errs, _ = _check(_doc("employee-2", [("A:dt:o@v1", "approved"), ("A:spec:o@v1", "approved"),
                                         ("A:seq:o@v1", "rejected"), ("A:bpmn:o@v1", "rejected")]), st)
    assert any("settling a dispute needs the role closes" in e for e in errs)


def test_a_declared_gap_is_closed_only_by_its_owner():
    units = review.organisation_units(REG)
    od1 = {"id": "gap:declared:OD-1", "text": "REQ-06 is NOT YET SPECIFIED (open decision OD-1, owner: compliance)", "keys": [OUT]}
    st = FakeStore([], [od1])
    # OD-1's owner, compliance, is ORG-0004 since register v0.2.6 (its decision 0011): only that unit's closes handle closes it
    assert review.gap_owner(od1["text"], units) == (["ORG-0004"], "compliance")
    errs, _ = _check(_doc("employee-3", closes=["gap:declared:OD-1"]), st)
    assert any("names 'compliance' (ORG-0004) as its owner; employee-3's unit is ORG-0001" in e for e in errs), errs
    assert _check(_doc("employee-4", closes=["gap:declared:OD-1"]), st)[0] == []
    # an owner the register does not hold: nobody closes it
    st.g["gap:declared:OD-1"] = {**od1, "text": "REQ-06 is NOT YET SPECIFIED (open decision OD-1, owner: legal)"}
    errs, _ = _check(_doc("employee-3", closes=["gap:declared:OD-1"]), st)
    assert any("names 'legal' as its owner, which is no unit of the register" in e for e in errs), errs
    # an owner the register holds: only its unit closes it, and only with closes
    st.g["gap:declared:OD-1"] = {**od1, "text": "REQ-06 is NOT YET SPECIFIED (open decision OD-1, owner: CargoQuote product owner)"}
    assert _check(_doc("employee-3", closes=["gap:declared:OD-1"]), st)[0] == []
    errs, _ = _check(_doc("employee-2", closes=["gap:declared:OD-1"]), st)
    assert any("lacks the role closes" in e for e in errs) and any("names 'CargoQuote product owner' (ORG-0001)" in e for e in errs)
    # no owner named: the key's owners close it
    st.g["gap:declared:OD-1"] = {**od1, "text": "REQ-06 is NOT YET SPECIFIED"}
    assert _check(_doc("employee-3", closes=["gap:declared:OD-1"]), st, owners={OUT: ["ORG-0002"]})[0] != []
    assert _check(_doc("employee-3", closes=["gap:declared:OD-1"]), st)[0] == []
    assert review.gap_owner("x (owner: ORG-0002)", units) == (["ORG-0002"], "ORG-0002")
    assert any("no open declared gap" in e for e in _check(_doc("employee-3", closes=["gap:nope"]), st)[0])


def test_an_approval_of_what_a_person_gave_lapses_six_months_after_the_capture():
    caps = {CAP: {"from": "employee-1", "on": dt.date(2026, 11, 2)}}
    assert review.until_for(_a(CAP, basis="elicited"), caps) == dt.date(2027, 5, 2)
    assert review.until_for(_a("A:dt:o@v1"), caps) is None          # a document's statement does not lapse
    assert review.add_months(dt.date(2026, 8, 31), 6) == dt.date(2027, 2, 28)


def test_the_written_review_reads_back_as_it_was_checked():
    import tomllib
    _errs, rv = _check(_doc("employee-2", [(CAP, "approved")]), _person())
    rv["scenario"] = "S2"
    back = tomllib.loads(review.review_toml(rv))
    assert back["review"] == {"by": "employee-2", "on": NOW, "record": "minutes/2026-11-03.md", "scenario": "S2"}
    # task-0199: the ruling records what it ruled on, as the store held it (a person's answer has no fragment)
    assert back["ruling"] == [{"assertion": CAP, "key": OUT, "value": HELD, "sha256": review.content_digest([]),
                               "outcome": "approved", "note": ""}]


def test_the_adapters_rule_without_naming_a_basis():
    """decision-0002 lives in review.py; the adapters only apply what it accepted, and never name
    the basis a person's statement carries (test_capture's guard)."""
    for name in ("store_neo4j.py", "store_rdflib.py"):
        src = (ROOT / "harness" / name).read_text(encoding="utf-8")
        assert "def apply_ruling" in src and "def close_declared_gap" in src and "elicited" not in src
