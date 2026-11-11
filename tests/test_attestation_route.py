"""task-0324, task-0325 (doc-0038 §4 P1, P2): the attestation route is one step per declaration, execution only after the
suite has run; a declaration listing no Version is named by the gate."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for d in ("harness", "tools"):
    sys.path.insert(0, str(ROOT / d))

import gate_cli
import check_subject

SHA = "a" * 64


def test_route_names_one_step_per_declaration_and_never_one_reader_for_all_four():
    route = gate_cli.attestation_route(["authored", "approval", "review", "execution"], SHA, "agent:m")
    steps = route.split("; ")
    assert len(steps) == 4, steps
    ex = [s for s in steps if "execution versions" in s][0]
    assert "suite is run on this Version" in ex and "implementation and suite" in ex, ex
    assert "the approver" in route and "the reviewer" in route and "the author" in route
    assert "reads the document and lists sha256" not in ex
    assert "under [verification] approval, authored, execution and review versions" not in route


def test_unattested_artefact_finding_route_is_per_declaration():
    rows = [{"declaration": n, "bound": True, "attester": "agent:m",
             "unattested": [{"artefact": "a.md", "sha256": SHA, "parts": [], "keys": ["k"]}]} for n in ("execution", "approval")]
    f = gate_cli.attestation_findings(rows, {"k": {"unit": "u"}}, None)[0]
    assert f["route"].count("; ") == 1 and "the approver" in f["route"] and "suite is run" in f["route"], f["route"]


def test_check_subject_fix_for_execution_says_run_the_suite():
    fx = check_subject._relist_fix("execution")
    assert "run the suite on the new Version" in fx and "implementation and suite digests" in fx, fx
    assert "run the suite" not in check_subject._relist_fix("approval")
    assert "approver" in check_subject._relist_fix("approval", restore=True)


def test_declaration_listing_no_version_is_an_attestation_finding():
    rows = [{"declaration": n, "bound": False, "attester": "agent:m", "unattested": []} for n in ("execution", "review")]
    fs = gate_cli.attestation_findings(rows, None, None)
    assert [f["kind"] for f in fs] == ["attestation", "attestation"], fs
    for f, n in zip(fs, ("execution", "review")):
        assert n in f["message"] and "lists no Version" in f["message"] and f["severity"] == "info", f
        assert f["route"], f
