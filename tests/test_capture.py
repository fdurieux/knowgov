"""Task-0009: the capture path. A questionnaire per owner from the gate's result (rebuilt here
from the CargoQuote record's S2 run file), with its denominator; an answered one checked and
normalised with ieam-register decision 0008's three fields; and no route by which a model's output
or a person's answer is verified by the harness. The store half (load, gate, the statuses after
the verifications run again) runs in harness.yml on rdflib."""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(Path(__file__).resolve().parent)]
import capture  # noqa: E402
from _subject_pin import CARGO_QUOTE  # noqa: E402

TODAY = dt.date(2026, 11, 2)


def _s2() -> dict:
    """S2's gate result as its run file holds it, the assertions' detail left empty."""
    det = json.loads((CARGO_QUOTE.record_dir / "S2" / "deterministic.json").read_text(encoding="utf-8"))
    return {**det["D6_gate"], "keys": {k: {"level": v["level"], "flags": v["flags"], "assertions": [], "declared_gaps": []}
                                       for k, v in det["gate_keys"].items()}}


def test_one_questionnaire_per_owner_with_its_open_keys_and_the_denominator():
    nodes = capture.register_nodes(ROOT / "demo" / "register")
    qs = capture.questionnaires(_s2(), CARGO_QUOTE, "S2", "codegen", nodes, TODAY)
    assert sorted(qs) == ["ORG-0001", "ORG-0002"], sorted(qs)   # every CargoQuote key concerns nodes both own
    doc = tomllib.loads(qs["ORG-0002"])
    q = doc["questionnaire"]
    assert (q["owner"], q["keys_owned"], q["open"]) == ("ORG-0002", 36, 3)
    assert {i["key"]: i["level"] for i in doc["item"]} == {"QuoteAPI|on_screening_outage": "declared_gap",
                                                          "response|hold_presence": "absent", "response|statuses": "validated"}
    assert all(i["answer"] == "" and i["nobody_knows"] is False for i in doc["item"])
    assert qs["ORG-0002"].startswith("# Questionnaire for ORG-0002 (Architecture stewardship (stand-in)): 3 of the 36 keys you own need an answer.")


def test_a_key_no_map_row_names_goes_to_unassigned():
    res = _s2()
    res["keys"]["made|up"] = {"level": "absent", "flags": [], "assertions": [], "declared_gaps": []}
    qs = capture.questionnaires(res, CARGO_QUOTE, "S2", "codegen", capture.register_nodes(ROOT / "demo" / "register"), TODAY)
    doc = tomllib.loads(qs[capture.UNASSIGNED])
    assert doc["questionnaire"]["keys_owned"] == 1 and [i["key"] for i in doc["item"]] == ["made|up"]


def _answered(**over) -> dict:
    nodes = capture.register_nodes(ROOT / "demo" / "register")
    doc = tomllib.loads(capture.questionnaires(_s2(), CARGO_QUOTE, "S2", "codegen", nodes, TODAY)["ORG-0002"])
    doc["answered"] = {"from": over.get("handle", "employee-1"), "on": over.get("on", "2026-11-02")}
    for it in doc["item"]:
        if it["key"] == "response|hold_presence":
            it["answer"] = over.get("answer", "present when status is review_hold")
        if it["key"] == "QuoteAPI|on_screening_outage":
            it["nobody_knows"] = over.get("nobody_knows", True)
            it["note"] = "compliance has not decided"
    return doc


def test_an_answered_questionnaire_is_normalised_with_the_registers_three_fields():
    keys = set(CARGO_QUOTE.tasks["codegen"]["keys"])
    pattern = capture.handle_pattern(ROOT / "demo" / "register")
    errs, cap = capture.check_answers(_answered(), pattern, keys, TODAY)
    assert errs == [], errs
    text = capture.capture_toml(cap, "captures/2026-11-02-ORG-0002-employee-1.toml")
    c = tomllib.loads(text)
    assert {k: c["capture"][k] for k in ("from", "on", "record")} == {"from": "employee-1", "on": dt.date(2026, 11, 2),
                                                                     "record": "captures/2026-11-02-ORG-0002-employee-1.toml"}
    assert c["answer"] == [{"key": "response|hold_presence", "value": "present when status is review_hold", "note": ""}]
    assert c["unknown"] == [{"key": "QuoteAPI|on_screening_outage", "note": "compliance has not decided"}]


def test_a_name_a_future_date_a_contradiction_or_nothing_answered_is_refused():
    keys = set(CARGO_QUOTE.tasks["codegen"]["keys"])
    pattern = capture.DEFAULT_HANDLE
    for over, expect in (({"handle": "Jane Doe"}, "not an opaque handle"), ({"handle": "jane@example.org"}, "not an opaque handle"),
                         ({"on": "2026-12-31"}, "in the future"), ({"on": "yesterday"}, "not a date"),
                         ({"answer": "x", "nobody_knows": True}, None)):
        doc = _answered(**over)
        if expect is None:   # both on one item
            for it in doc["item"]:
                if it["key"] == "QuoteAPI|on_screening_outage":
                    it["answer"] = "x"
            expect = "an answer and nobody_knows together"
        errs, _ = capture.check_answers(doc, pattern, keys, TODAY)
        assert any(expect in e for e in errs), (over, errs)
    doc = _answered(answer="", nobody_knows=False)
    assert "no item is answered" in capture.check_answers(doc, pattern, keys, TODAY)[0]


def test_ingest_refuses_a_handle_the_register_has_not_issued_by_the_answers_date():
    """task-0055: decision 0009's issued list, as review.check reads it; each refusal names the rule."""
    import review
    keys = set(CARGO_QUOTE.tasks["codegen"]["keys"])
    reg = ROOT / "demo" / "register"
    pattern, handles = capture.handle_pattern(reg), review.issued_handles(reg)
    assert handles and "employee-1" in handles, "the vendored register lists issued handles"
    assert capture.check_answers(_answered(), pattern, keys, TODAY, handles)[0] == []
    later = dict(handles, **{"employee-9": {"unit": "ORG-0002", "roles": {"gives"}, "issued": dt.date(2026, 11, 3), "withdrawn": None},
                             "employee-8": {"unit": "ORG-0002", "roles": {"gives"}, "issued": dt.date(2026, 1, 1),
                                            "withdrawn": dt.date(2026, 11, 2)}})
    for handle, expect in (("steward-1", "not an issued handle (decision 0009)"),
                           ("employee-9", "was issued on 2026-11-03, after the answer's date 2026-11-02"),
                           ("employee-8", "was withdrawn on 2026-11-02, by the answer's date 2026-11-02")):
        errs, _ = capture.check_answers(_answered(handle=handle), pattern, keys, TODAY, later)
        assert len(errs) == 1 and expect in errs[0], (handle, errs)
    # withdrawn after the answer: the answer stands
    late = dict(handles, **{"employee-8": dict(later["employee-8"], withdrawn=dt.date(2026, 11, 3))})
    assert capture.check_answers(_answered(handle="employee-8"), pattern, keys, TODAY, late)[0] == []
    # a name is refused by the pattern, once, not again by the list
    errs, _ = capture.check_answers(_answered(handle="Jane Doe"), pattern, keys, TODAY, handles)
    assert len(errs) == 1 and "not an opaque handle" in errs[0], errs
    # a register that lists none: the pattern alone
    for none in (None, {}):
        assert capture.check_answers(_answered(handle="steward-1"), pattern, keys, TODAY, none)[0] == []


def test_ingest_reads_the_registers_issued_list():
    src = (ROOT / "harness" / "capture.py").read_text(encoding="utf-8")
    block = src[src.index("def _ingest"):src.index("def _review")]
    assert "review.issued_handles(reg)" in block


def test_the_handle_pattern_is_the_registers_when_it_defines_one():
    reg = ROOT / "demo" / "register"
    types = (reg / "metamodel" / "types.toml").read_text(encoding="utf-8")
    want = tomllib.loads(types).get("elicited", {}).get("handle", capture.DEFAULT_HANDLE)
    assert capture.handle_pattern(reg) == want
    assert capture.DEFAULT_HANDLE == "^[a-z][a-z0-9-]{1,39}$", "the pattern ieam-register decision 0008 sets"


def test_no_verification_reaches_a_captured_or_a_model_statement():
    """AC 3: the store verifies extracted and authored assertions only, in both adapters, so basis
    elicited (a person's answer) and inferred (a model's) stay at proposed; nothing else sets a status."""
    neo = (ROOT / "harness" / "store_neo4j.py").read_text(encoding="utf-8")
    rdf = (ROOT / "harness" / "store_rdflib.py").read_text(encoding="utf-8")
    assert neo.count("x.basis IN ['extracted','authored']") >= 3, "execution, review and the structural rule"
    assert "x.basis='authored' AND x.status='proposed'" in neo
    assert rdf.count('in ("extracted", "authored")') >= 2 and 'basis="authored", status="proposed"' in rdf
    for src in (neo, rdf):
        assert "elicited" not in src and "'inferred' AND" not in src
    load = (ROOT / "harness" / "load.py").read_text(encoding="utf-8")
    block = load[load.index("def load_captures"):]
    assert '"basis": "elicited", "status": "proposed"' in block and not re.search(r'"status": "(verified|approved|validated)"', block)
