"""Task-0215 (decision-0018 point 4, doc-0032 §3 gap 2): the intended bar.

A task class may declare ``require_approved = true``. A key verified but not approved, a behaviour shown to
hold and intended by nobody, then reads below the class's bar: an ``intended`` finding (major) names its owner
and route from ``capture.routing``, and the verdict counts it as the class counts a key below verified. Opt-in:
a class without the declaration, and every record verdict, reads as before. Stdlib: the store is
test_mcp_server's stub, every codegen key verified but one, which is absent."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tools")]
import check_subject  # noqa: E402
import gate  # noqa: E402
import gate_cli  # noqa: E402
import schema_check  # noqa: E402
from subject import SUBJECT  # noqa: E402
from tasks import TASKS  # noqa: E402
from tests.test_mcp_server import DAY, Stub  # noqa: E402

SCHEMA = schema_check.load("gate-report")


def _store(approved: int) -> tuple[Stub, list[str]]:
    """The stub with its first ``approved`` verified keys raised to approved; the absent key stays absent."""
    st = Stub()
    keys = [k for k in TASKS["codegen"]["keys"] if k in st.rows]
    for k in keys[:approved]:
        st.rows[k][0]["status"] = "approved"
    return st, keys


def _spec(**kw) -> dict:
    """The codegen class with nothing blocking, so the bar alone decides between PROCEED and QUALIFIED."""
    keys = [k for k in TASKS["codegen"]["keys"] if k in Stub().rows]
    return {**TASKS["codegen"], "keys": keys, "block_levels": set(), "max_unverified_share": 1.0, **kw}


def test_without_the_declaration_every_task_class_reads_as_today():
    """AC2, AC5: no class of the public subjects declares the bar, a class that does not declare it reads exactly
    as one with require_approved false, and the report carries no new field."""
    for sid in ("cargo_quote", "jef_data_load"):
        import tomllib
        m = tomllib.loads((ROOT / "subjects" / sid / "subject.toml").read_text(encoding="utf-8"))
        assert not any("require_approved" in t for t in m.get("tasks", {}).values()), sid
    assert all(t["require_approved"] is False for t in TASKS.values())
    st, _ = _store(0)
    plain = {k: v for k, v in TASKS["codegen"].items() if k != "require_approved"}
    for spec in (plain, dict(TASKS["codegen"], require_approved=False)):
        res = gate.resolve_spec(st, "codegen", spec, DAY)
        assert "unintended" not in res, res.keys()
    assert gate.resolve_spec(st, "codegen", plain, DAY) == gate.resolve_spec(st, "codegen", dict(TASKS["codegen"], require_approved=False), DAY)
    rep = gate_cli.evaluate(st, subject=SUBJECT.id, scenario=st.scenario, task="codegen", spec=TASKS["codegen"], threshold="blocker",
                            baseline=None, loaded=False, as_of=DAY)
    assert "unintended" not in rep["keys"] and not [f for f in rep["findings"] if f["kind"] == "intended"]
    assert schema_check.validate(rep, SCHEMA) == []
    # every key verified, nothing blocking: PROCEED, as before the bar existed
    assert gate.resolve_spec(st, "codegen", _spec(), DAY)["verdict"] == "PROCEED"


def test_a_class_requiring_approved_reads_a_verified_key_below_its_bar():
    """AC1: verified but not approved is below the bar; the verdict follows the class's rule: QUALIFIED under
    the share, BLOCKED past it, PROCEED only when every key is approved."""
    st, keys = _store(len(_spec()["keys"]) // 2)
    res = gate.resolve_spec(st, "codegen", _spec(require_approved=True), DAY)
    want = sorted(k for k in keys if st.rows[k][0]["status"] == "verified")
    assert sorted(res["unintended"]) == want and want and res["below_verified"] == []
    assert res["verdict"] == "QUALIFIED" and "below approved" in res["why"], res["why"]
    tight = gate.resolve_spec(st, "codegen", _spec(require_approved=True, max_unverified_share=0.25), DAY)
    assert tight["verdict"] == "BLOCKED" and "below approved" in tight["why"], tight["why"]
    loose = gate.resolve_spec(st, "codegen", _spec(max_unverified_share=0.25), DAY)
    assert loose["verdict"] == "PROCEED" and "unintended" not in loose   # the same store, no bar: as today
    st, _ = _store(len(keys))
    done = gate.resolve_spec(st, "codegen", _spec(require_approved=True), DAY)
    assert done["verdict"] == "PROCEED" and done["unintended"] == [] and "approved, none flagged" in done["why"]


def test_the_intended_finding_names_the_keys_owner_and_route_and_the_schema_carries_it():
    """AC1, AC3: one major ``intended`` finding per verified key, with the owner and the questionnaire route
    capture.routing gives the key's ordinary finding; a pipeline at --fail-on major fails on it."""
    st, keys = _store(1)
    spec = _spec(require_approved=True)
    rep = gate_cli.evaluate(st, subject=SUBJECT.id, scenario=st.scenario, task="codegen", spec=spec, threshold="blocker",
                            baseline=None, loaded=False, as_of=DAY, route_task="codegen")
    assert schema_check.validate(rep, SCHEMA) == [], schema_check.validate(rep, SCHEMA)[:3]
    found = [f for f in rep["findings"] if f["kind"] == "intended"]
    assert sorted(f["key"] for f in found) == sorted(keys[1:]) and rep["keys"]["unintended"] == len(found)
    assert all(f["severity"] == "major" and f["level"] == "verified" and "route" in f and "owner" in f for f in found)
    plain = gate_cli.evaluate(st, subject=SUBJECT.id, scenario=st.scenario, task="codegen", spec=dict(spec, keys=keys[1:2], require_approved=False),
                              threshold="info", baseline=None, loaded=False, as_of=DAY, route_task="codegen")
    from capture import finding_owners
    owners = finding_owners(SUBJECT)
    for f in found:
        assert f["owner"] == (owners.get(f["key"]) or {}).get("unit"), f
        if f["owner"]:
            assert "capture.py questionnaire" in f["route"] and f["owner"] in f["route"], f["route"]
    assert rep["verdict"] == "QUALIFIED" and rep["exit_code"] == 0
    strict = gate_cli.evaluate(st, subject=SUBJECT.id, scenario=st.scenario, task="codegen", spec=spec, threshold="major",
                               baseline=None, loaded=False, as_of=DAY)
    assert strict["exit_code"] == 1
    assert plain["verdict"] == "PROCEED" and not [f for f in plain["findings"] if f["kind"] == "intended"]
    bad = json.loads(json.dumps(rep))
    bad["findings"][0]["kind"] = "intent"
    assert schema_check.validate(bad, SCHEMA), "an unknown finding kind passed"
    text = gate_cli.render_text(rep) if hasattr(gate_cli, "render_text") else ""
    assert not text or "requires approved" in text


def test_check_subject_reads_the_field_and_refuses_anything_but_a_boolean():
    """AC3: the manifest field is documented and checked."""
    readme = (ROOT / "subjects" / "README.md").read_text(encoding="utf-8")
    assert "require_approved = true" in readme and "task-0215" in readme
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "minimal"
        shutil.copytree(ROOT / "subjects" / "minimal", root)
        manifest = root / "subject.toml"
        base = manifest.read_text(encoding="utf-8")
        for value, ok in (("true", True), ("false", True), ('"yes"', False), ("1", False)):
            manifest.write_text(base.replace("max_unverified_share = 0.25", f"max_unverified_share = 0.25\nrequire_approved = {value}", 1),
                                encoding="utf-8")
            rep = check_subject.check(root, ROOT / "demo" / "register", run_yield=False)
            errors = [f for f in rep["findings"] if f["level"] == "error"]
            assert ("require-approved" not in [f["rule"] for f in errors]) == ok, (value, errors)
            assert not [f for f in errors if f["rule"] == "field"], errors   # documented, so never an unknown field


def test_the_changelog_names_it_under_contract_changes():
    log = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").split("\n## 0.9.0 ", 1)[1].split("\n## ", 1)[0]
    contract = log.split("### Contract changes", 1)[1].split("### Changes", 1)[0]
    assert "task-0215" in contract and "require_approved" in contract
