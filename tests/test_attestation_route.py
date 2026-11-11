"""task-0324, task-0325 (doc-0038 §4 P1, P2): the attestation route is one step per declaration, execution only after the
suite has run; a declaration listing no Version is named by the gate."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for d in ("harness", "tools"):
    sys.path.insert(0, str(ROOT / d))
sys.path.insert(0, str(ROOT / "tests"))

import gate_cli
import check_subject

SHA = "a" * 64


def test_route_names_one_step_per_declaration_and_never_one_reader_for_all_four():
    route = gate_cli.attestation_route(["authored", "approval", "review", "execution"], SHA, "agent:m")
    steps = route.split("; ")
    assert len(steps) == 4, steps
    ex = [s for s in steps if "execution versions" in s][0]
    assert "changed to this Version's values and run" in ex and "implementation and suite" in ex and "asserts the old result" in ex, ex
    assert "the approver" in route and "the reviewer" in route and "the author" in route
    assert "reads the document and lists sha256" not in ex
    assert "under [verification] approval, authored, execution and review versions" not in route


def test_unattested_artefact_finding_route_is_per_declaration():
    rows = [{"declaration": n, "bound": True, "attester": "agent:m",
             "unattested": [{"artefact": "a.md", "sha256": SHA, "parts": [], "keys": ["k"]}]} for n in ("execution", "approval")]
    f = gate_cli.attestation_findings(rows, {"k": {"unit": "u"}}, None)[0]
    assert f["route"].count("; ") == 1 and "the approver" in f["route"] and "values and run" in f["route"], f["route"]


def test_check_subject_fix_for_execution_says_run_the_suite():
    fx = check_subject._relist_fix("execution")
    assert "to the new Version's values, run them" in fx and "all three digests" in fx and "asserts the old result" in fx, fx
    assert "old result" not in check_subject._relist_fix("approval")
    assert "approver" in check_subject._relist_fix("approval", restore=True)


def test_declaration_listing_no_version_is_an_attestation_finding():
    rows = [{"declaration": n, "bound": False, "attester": "agent:m", "unattested": []} for n in ("execution", "review")]
    fs = gate_cli.attestation_findings(rows, None, None)
    assert [f["kind"] for f in fs] == ["attestation", "attestation"], fs
    for f, n in zip(fs, ("execution", "review")):
        assert n in f["message"] and "lists no Version" in f["message"] and f["severity"] == "info", f
        assert f["route"], f


def test_consequence_names_only_the_bound_declarations():
    """task-0330 AC4."""
    rows = [{"declaration": "review", "bound": True, "attester": "a",
             "unattested": [{"artefact": "a.md", "sha256": SHA, "parts": [], "keys": ["k"]}]}]
    m = gate_cli.attestation_findings(rows, None, None)[0]["message"]
    assert "authored statements read proposed" not in m and "verified by review is lost" in m, m
    rows[0]["declaration"] = "approval"
    assert "authored statements read proposed" in gate_cli.attestation_findings(rows, None, None)[0]["message"]


def test_review_wording_agrees_and_approver_and_reviewer_are_not_the_author():
    """task-0330 AC5, AC6, AC7."""
    gate = gate_cli.attestation_route(["review"], SHA)
    fix = check_subject._relist_fix("review")
    for text in (gate, fix):
        assert "reviewer (not the author, decision-0002) reads the" in text and "re-dates every listed Version" in text, text
        assert "its own date" in text, text
    for text in (gate_cli.attestation_route(["approval"], SHA), check_subject._relist_fix("approval")):
        assert "approver (not the author, decision-0002)" in text, text


def test_check_subject_notes_an_edited_execution_document_with_unchanged_code():
    """task-0330 AC2: a note, never an error, naming the limit."""
    import tempfile
    import example_instance
    from _skip import need_rdflib
    need_rdflib()
    with tempfile.TemporaryDirectory() as t:
        inst = example_instance.build(Path(t) / "inst")
        f = next(inst.rglob("decision_table.md"))
        f.write_text(f.read_text(encoding="utf-8").replace("316.00", "341.00"), encoding="utf-8")
        rep = check_subject.check(inst / "subjects" / "cargo_quote", run_yield=False)
    assert [n for n in rep["notes"] if "cannot know whether the suite covers" in n["message"]], rep["notes"]
    assert not [x for x in rep["findings"] if "cannot know whether" in x["message"]]
