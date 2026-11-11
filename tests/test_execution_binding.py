"""An execution verification holds only for the document Versions it was attested on (task-0306, decision-0036).

The functional review's repro (doc-0037 §3.1, groups A F1 and C C2-2): the example instance's S1, with P2's
surcharge edited from 316.00 to 341.00 in its decision table. Before, the load wrote ``verify_by_execution`` for
every live statement whose value the documents on disk state, so the edit read verified by execution (QUALIFIED,
P2|surcharge verified at 341), and with the manifest's ``versions`` removed the gate said PROCEED. No suite runs at
load: the execution verification is the subject's attested result, bound to the Versions ``[verification]
execution`` lists, and an unlisted Version is not verified by it, nor approved."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / "harness"
sys.path[:0] = [str(ROOT / "tools"), str(HARNESS), str(ROOT / "tests")]
import example_instance  # noqa: E402
from _skip import need_rdflib  # noqa: E402

TABLE = "artefacts/decision-tables/decision_table.md"
KEY = "P2|surcharge"
BELOW = ("absent", "declared_gap", "disputed", "invalidated", "proposed", "validated")

PROBE = """
import json, sys
sys.path.insert(0, '.')
import gate, gate_cli, store
with store.scratch_store() as st:
    gate_cli._load(st, 'S1')
    print(json.dumps([{"value": r["value"], "status": r["status"], "methods": sorted(v["method"] for v in r["verifications"]),
                       "approved": bool(r["approvals"])} for r in st.key_evidence(sys.argv[1], gate.LIVE)]))
"""


WITHDRAW = """
import json, sys
sys.path.insert(0, '.')
import gate, gate_cli, store
with store.scratch_store() as st:
    gate_cli._load(st, 'S1')
    [x] = [r for r in st.key_evidence(sys.argv[1], gate.LIVE) if r["value"] == "316.00"]
    n = st.withdraw_construction([x["artefact"]])
    [y] = [r for r in st.key_evidence(sys.argv[1], gate.LIVE) if r["id"] == x["id"]]
    print(json.dumps({"before": sorted(v["method"] for v in x["verifications"]), "after": sorted(v["method"] for v in y["verifications"]),
                      "status": [x["status"], y["status"]], "approved": bool(y["approvals"]), "n": n}))
"""


def _env(inst: Path) -> dict:
    return {**os.environ, "KG_SUBJECT": str(inst / "subjects" / "cargo_quote"), "KG_REGISTER": str(inst / "register"),
            "KG_CLOCK": "pinned", "KG_TODAY": "2026-10-30", "KG_STORE": "rdflib", "PYTHONDONTWRITEBYTECODE": "1"}


def _gate(inst: Path) -> dict:
    p = subprocess.run([sys.executable, "gate_cli.py", "--scenario", "S1", "--as-of", "record", "-f", "json"], cwd=HARNESS,
                       env=_env(inst), capture_output=True, text=True)
    assert p.returncode in (0, 1), p.stderr[-1500:]
    return json.loads(p.stdout)


def _statements(inst: Path) -> list[dict]:
    p = subprocess.run([sys.executable, "-c", PROBE, KEY], cwd=HARNESS, env=_env(inst), capture_output=True, text=True)
    assert p.returncode == 0, p.stderr[-1500:]
    return json.loads(p.stdout.strip().splitlines()[-1])


def _edit(inst: Path) -> None:
    t = inst / TABLE
    text = t.read_text(encoding="utf-8")
    assert "add `316.00` (flat)" in text
    t.write_text(text.replace("add `316.00` (flat)", "add `341.00` (flat)", 1), encoding="utf-8")


def test_the_pristine_documents_read_as_before():
    need_rdflib()
    with tempfile.TemporaryDirectory() as t:
        inst = example_instance.build(Path(t) / "inst")
        rep = _gate(inst)
        assert rep["verdict"] == "PROCEED" and rep["levels"][KEY] == "approved", (rep["verdict"], rep["levels"][KEY])
        assert any("execution" in s["methods"] and s["value"] == "316.00" for s in _statements(inst))


def test_an_edited_value_is_not_verified_by_execution_nor_approved_and_the_gate_is_not_proceed():
    """With the shipped versions: the edited table is a Version no declaration lists, so 341.00 is neither verified
    by execution nor approved, P2|surcharge falls below verified, and the gate does not proceed on it."""
    need_rdflib()
    with tempfile.TemporaryDirectory() as t:
        inst = example_instance.build(Path(t) / "inst")
        _edit(inst)
        rep = _gate(inst)
        assert rep["verdict"] != "PROCEED" and rep["levels"][KEY] in BELOW, (rep["verdict"], rep["levels"][KEY])
        live = [s for s in _statements(inst) if s["value"] == "341.00"]
        assert live and all("execution" not in s["methods"] and not s["approved"] for s in live), live


def test_with_every_list_removed_an_edited_value_is_still_not_verified_by_execution():
    """With versions removed from every declaration: authored and approval fall to decision-0019's read rule, but an
    execution or a review attestation that lists nothing verifies nothing, so the edit still does not proceed."""
    need_rdflib()
    with tempfile.TemporaryDirectory() as t:
        inst = example_instance.build(Path(t) / "inst")
        mf = inst / "subjects" / "cargo_quote" / "subject.toml"
        text = mf.read_text(encoding="utf-8")
        for form in (r"versions = \[[^\]]*\], ", r", versions = \[[^\]]*\]", r"versions = \[[^\]]*\]"):   # each place a list sits
            text = re.sub(form, "", text)
        mf.write_text(text, encoding="utf-8")
        assert "versions" not in text.split("[verification]", 1)[1].split("\n[", 1)[0]
        _edit(inst)
        rep = _gate(inst)
        assert rep["verdict"] != "PROCEED" and rep["levels"][KEY] in BELOW, (rep["verdict"], rep["levels"][KEY])
        live = [s for s in _statements(inst) if s["value"] == "341.00"]
        assert live and all("execution" not in s["methods"] for s in live), live


def test_stage_two_takes_back_the_execution_verifications_of_an_unlisted_version():
    """Stage 2 reads as a fresh load of its documents (task-0221): ``withdraw_construction`` takes back, with the review
    and the approval by construction, a statement's execution verification, which an earlier load gave a Version the
    later one no longer lists; the load calls it before it verifies, so what is still listed is written again."""
    need_rdflib()
    with tempfile.TemporaryDirectory() as t:
        inst = example_instance.build(Path(t) / "inst")
        p = subprocess.run([sys.executable, "-c", WITHDRAW, KEY], cwd=HARNESS, env=_env(inst), capture_output=True, text=True)
        assert p.returncode == 0, p.stderr[-1500:]
        got = json.loads(p.stdout.strip().splitlines()[-1])
    assert "execution" in got["before"] and "execution" not in got["after"], got
    assert got["status"][0] == "approved" and got["status"][1] in BELOW and not got["approved"] and got["n"] >= 1, got
    src = (HARNESS / "load.py").read_text(encoding="utf-8")
    assert src.index("st.withdraw_construction(unlisted)") < src.index("st.verify_by_execution(")


API = "artefacts/api-contracts/openapi.yaml"


def _attestation(rep: dict) -> list[dict]:
    return [f for f in rep["findings"] if f["kind"] == "attestation" and "is not attested" in f["message"]]


def test_the_not_attested_finding_names_every_declaration_and_its_route_lists_them():
    """task-0318: after the P2 edit the finding names authored, approval, execution and review, cites decision-0036
    beside decision-0019, and its route lists them all (not approval and authored only)."""
    need_rdflib()
    with tempfile.TemporaryDirectory() as t:
        inst = example_instance.build(Path(t) / "inst")
        _edit(inst)
        found = [f for f in _attestation(_gate(inst)) if "decision_table" in f["message"]]
    assert len(found) == 1, found
    [f] = found
    assert "approval, authored, execution and review" in f["message"] and "decision-0036" in f["message"], f["message"]
    for decl in ("authored", "approval", "execution", "review"):   # task-0324: one step per declaration, never one reader for all
        assert f"[verification] {decl} versions" in f["route"], f["route"]
    assert "decision-0036" in f["route"] and "decision-0019" in f["route"], f["route"]


def test_following_the_route_brings_the_gate_back_to_proceed():
    """Listing the new digest in every declaration the finding names leaves no not-attested finding and PROCEED."""
    need_rdflib()
    with tempfile.TemporaryDirectory() as t:
        inst = example_instance.build(Path(t) / "inst")
        _edit(inst)
        route = _attestation(_gate(inst))[0]["route"]
        assert set(re.findall(r"\[verification\] (\w+) versions", route)) == {"approval", "authored", "execution", "review"}, route
        example_instance.attest(inst, inst / TABLE)
        rep = _gate(inst)
    assert not _attestation(rep) and rep["verdict"] == "PROCEED", (rep["verdict"], _attestation(rep))


def test_a_comment_only_edit_to_a_review_verified_document_names_review():
    need_rdflib()
    with tempfile.TemporaryDirectory() as t:
        inst = example_instance.build(Path(t) / "inst")
        f = inst / API
        f.write_text(f.read_text(encoding="utf-8") + "\n# a comment\n", encoding="utf-8")
        found = [x for x in _attestation(_gate(inst)) if "openapi.yaml" in x["message"]]
    assert found and "review" in found[0]["message"] and "decision-0036" in found[0]["message"], found


def _check(inst: Path) -> dict:
    sys.path.insert(0, str(ROOT / "tools"))
    import check_subject
    root = inst / "subjects" / "cargo_quote"
    return check_subject.check(root, run_yield=False)


def _att(rep: dict) -> list[dict]:
    return [f for f in rep["findings"] if f["rule"] == "attestation"]


def test_an_empty_versions_list_in_execution_or_review_is_noted_as_verifying_nothing():
    """task-0318 N-a: `versions = []` is noted as a missing list is (decision-0036), for execution and for review."""
    with tempfile.TemporaryDirectory() as t:
        inst = example_instance.build(Path(t) / "inst")
        mf = inst / "subjects" / "cargo_quote" / "subject.toml"
        text = mf.read_text(encoding="utf-8")
        for name in ("execution", "review"):
            text = re.sub(rf"({name}\s*=\s*\{{[^}}]*?)versions = \[[^\]]*\]", r"\1versions = []", text)
        mf.write_text(text, encoding="utf-8")
        rep = _check(inst)
    notes = [f for f in rep["notes"] if f["rule"] == "attestation" and "decision-0036" in f["message"]]
    assert {f["where"] for f in notes} >= {"[verification] execution", "[verification] review"}, notes


def test_an_edited_document_is_one_error_per_artefact_and_declaration_naming_it_and_the_new_digest():
    """task-0318 N-c: one error per artefact and declaration, not one per stale digest."""
    import hashlib
    with tempfile.TemporaryDirectory() as t:
        inst = example_instance.build(Path(t) / "inst")
        _edit(inst)
        new = hashlib.sha256((inst / TABLE).read_bytes()).hexdigest()
        errs = [f for f in _att(_check(inst)) if f["level"] == "error"]
    assert len(errs) == 4 and len({f["where"] for f in errs}) == 4, [f["where"] for f in errs]
    assert all("decision_table" in f["message"] and "changed since it was attested" in f["message"] and new in f["message"]
               for f in errs), errs
