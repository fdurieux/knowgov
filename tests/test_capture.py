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
    assert sorted(qs) == ["ORG-0001", "ORG-0002"], sorted(qs)
    doc = tomllib.loads(qs["ORG-0002"])
    q = doc["questionnaire"]
    assert (q["owner"], q["keys_owned"], q["open"]) == ("ORG-0002", 7, 3)
    assert {i["key"]: i["level"] for i in doc["item"]} == {"QuoteAPI|on_screening_outage": "declared_gap",
                                                          "response|hold_presence": "absent", "response|statuses": "validated"}
    assert all(i["answer"] == "" and i["nobody_knows"] is False for i in doc["item"])
    assert qs["ORG-0002"].startswith("# Questionnaire for ORG-0002 (Architecture stewardship (stand-in)): 3 of the 7 keys you own need an answer.")


def test_each_key_has_one_answering_owner_so_the_questionnaires_do_not_overlap():
    """task-0043: the map's owner per row, one of its nodes' owners; S2's questionnaires share no key,
    and together they ask every key once. Who may rule stays every owner of the nodes (decision-0002)."""
    nodes = capture.register_nodes(ROOT / "demo" / "register")
    rows = CARGO_QUOTE.register_map()["row"]
    every = capture.owners_of(CARGO_QUOTE, nodes)
    for r in rows:
        assert r.get("owner") in every[r["key"]], (r["key"], r.get("owner"), every[r["key"]])
    answering = capture.answering_owners(CARGO_QUOTE, nodes)
    assert all(len(v) == 1 for v in answering.values()) and len(answering) == 36
    assert every["response|statuses"] == ["ORG-0001", "ORG-0002"], "a ruling may still come from either unit"
    qs = capture.questionnaires(_s2(), CARGO_QUOTE, "S2", "codegen", nodes, TODAY)
    owned = {o: tomllib.loads(t)["questionnaire"]["keys_owned"] for o, t in qs.items()}
    asked = {o: [i["key"] for i in tomllib.loads(t).get("item", [])] for o, t in qs.items()}
    assert owned == {"ORG-0001": 29, "ORG-0002": 7}, owned
    flat = [k for ks in asked.values() for k in ks]
    assert len(flat) == len(set(flat)) == 3, asked


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


def test_the_questionnaire_warns_that_a_note_must_not_identify_the_person():
    """task-0042, doc-0007 F6: a warning, not a check; no pattern can tell an identifying note."""
    qs = capture.questionnaires(_s2(), CARGO_QUOTE, "S2", "codegen", capture.register_nodes(ROOT / "demo" / "register"), TODAY)
    for text in qs.values():
        head = "\n".join(line for line in text.splitlines() if line.startswith("#"))
        assert "A note must not identify you" in head and "nothing checks it but the person who reviews it" in head, head
    readme = (ROOT / "instance" / "README.md").read_text(encoding="utf-8")
    assert "A `note` must not identify them" in readme and "capture.py review review.toml --show" in readme


def test_the_reviewer_sees_each_ruled_answers_note_before_ruling():
    caps = {"A:cap:2026-11-02-ORG-0002-employee-1:1@capture": {"from": "employee-1", "on": dt.date(2026, 11, 2),
                                                               "value": "present when status is review_hold",
                                                               "note": "as the author of the 2025 memo"},
            "A:cap:2026-11-02-ORG-0002-employee-1:2@capture": {"from": "employee-1", "on": dt.date(2026, 11, 2),
                                                               "value": "x", "note": ""}}
    doc = {"ruling": [{"assertion": a, "outcome": "approved"} for a in (*caps, "A:doc:1")]}
    out = capture.show_rulings(doc, caps)
    assert "note: 'as the author of the 2025 memo'" in out and "note: none" in out
    assert "ruling 3 (A:doc:1): not a captured answer" in out and "reject the statement if it does" in out
    assert "reject" not in capture.show_rulings({"ruling": doc["ruling"][1:]}, caps), "no note, no prompt"
    bound = {"ruling": [{"assertion": "A:doc:1", "key": "K", "value": "v", "sha256": "ab", "outcome": "approved"}]}
    shown = capture.show_rulings(bound, caps)   # task-0315 N3: a document statement shows what it was bound to
    assert "not a captured answer" in shown and "key 'K'" in shown and "value 'v'" in shown and "sha256 'ab'" in shown, shown


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



def test_ingest_refuses_a_handle_without_gives():
    """task-0091: an answer needs a handle holding gives (ieam-register decision 0009), as a ruling
    needs approves or closes; issued and in date is not enough."""
    import review
    keys = set(CARGO_QUOTE.tasks["codegen"]["keys"])
    reg = ROOT / "demo" / "register"
    pattern, handles = capture.handle_pattern(reg), review.issued_handles(reg)
    assert all("gives" in h["roles"] for h in handles.values()), "every handle the vendored register issues may give"
    approver = dict(handles, **{"employee-7": {"unit": "ORG-0002", "roles": {"approves", "closes"}, "issued": dt.date(2026, 1, 1), "withdrawn": None}})
    errs, cap = capture.check_answers(_answered(handle="employee-7"), pattern, keys, TODAY, approver)
    assert len(errs) == 1 and "employee-7 lacks the role gives" in errs[0], errs
    # the same handle with gives added answers
    giver = dict(approver, **{"employee-7": dict(approver["employee-7"], roles={"gives", "approves", "closes"})})
    assert capture.check_answers(_answered(handle="employee-7"), pattern, keys, TODAY, giver)[0] == []

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


# ---- task-0113: the questionnaire names the unit that closes a declared gap

def _s2_with_od1() -> dict:
    """S2's result with OD-1 held on its key, as the store holds it (the run file keeps no gap detail)."""
    rules = CARGO_QUOTE.rules
    res = _s2()
    res["keys"]["QuoteAPI|on_screening_outage"]["declared_gaps"] = [
        {"id": rules["declared_gap_id"], "text": rules["declared_gap_text"].format(req="REQ-06")}]
    return res


def test_s2s_questionnaire_for_org_0002_names_org_0004_as_closing_od_1():
    """AC1: the item on OD-1 names the closer the gate's finding names (task-0110), in a field and a
    comment; an item with no declared gap carries neither, and no other owner's questionnaire changes."""
    nodes = capture.register_nodes(ROOT / "demo" / "register")
    qs = capture.questionnaires(_s2_with_od1(), CARGO_QUOTE, "S2", "codegen", nodes, TODAY)
    doc = tomllib.loads(qs["ORG-0002"])
    item = next(i for i in doc["item"] if i["key"] == "QuoteAPI|on_screening_outage")
    assert (item["gap"], item["closed_by"], item["closed_by_name"]) == ("gap:declared:OD-1", "ORG-0004", "Compliance (stand-in)")
    assert ("# gap:declared:OD-1 is closed by ORG-0004 Compliance (stand-in), by a review under a handle with the role closes; "
            "an answer here does not close it.") in qs["ORG-0002"]
    for i in doc["item"]:
        if i["key"] != "QuoteAPI|on_screening_outage":
            assert not {"gap", "closed_by", "closed_by_name"} & set(i), i
    want = capture.gap_closers(CARGO_QUOTE, {"QuoteAPI|on_screening_outage": _s2_with_od1()["keys"]["QuoteAPI|on_screening_outage"]["declared_gaps"]})
    assert item["closed_by"] == want["QuoteAPI|on_screening_outage"]["unit"]
    before = capture.questionnaires(_s2(), CARGO_QUOTE, "S2", "codegen", nodes, TODAY)
    assert qs["ORG-0001"] == before["ORG-0001"] and "closed_by" not in before["ORG-0002"]


def test_ingest_is_unchanged_and_a_questionnaire_from_before_still_ingests():
    """AC2: the same answers give the same capture whether the questionnaire names the closer or not
    (one written before task-0113 carries no closed_by); ingest reads only key, answer, nobody_knows, note."""
    keys = set(CARGO_QUOTE.tasks["codegen"]["keys"])
    pattern = capture.handle_pattern(ROOT / "demo" / "register")
    nodes = capture.register_nodes(ROOT / "demo" / "register")
    new = tomllib.loads(capture.questionnaires(_s2_with_od1(), CARGO_QUOTE, "S2", "codegen", nodes, TODAY)["ORG-0002"])
    assert any("closed_by" in i for i in new["item"])
    old = {**new, "item": [{k: v for k, v in i.items() if k not in ("gap", "closed_by", "closed_by_name")} for i in new["item"]]}
    caps = []
    for doc in (new, old):
        doc["answered"] = {"from": "employee-1", "on": "2026-11-02"}
        for it in doc["item"]:
            if it["key"] == "response|hold_presence":
                it["answer"] = "present when status is review_hold"
            if it["key"] == "QuoteAPI|on_screening_outage":
                it["nobody_knows"], it["note"] = True, "compliance has not decided"
        errs, cap = capture.check_answers(doc, pattern, keys, TODAY)
        assert errs == [], errs
        caps.append(capture.capture_toml(cap, "captures/2026-11-02-ORG-0002-employee-1.toml"))
    assert caps[0] == caps[1]
    assert tomllib.loads(caps[0])["unknown"] == [{"key": "QuoteAPI|on_screening_outage", "note": "compliance has not decided"}]
