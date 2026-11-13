"""task-0329: the redone review's fix-only items that a pure function can hold."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "instance" / "ci" / "claude")]
import gate_cli  # noqa: E402
import knowgov_hook  # noqa: E402


def test_p1_the_preload_identity_ignores_the_path_it_sits_at():
    a = {"path": "/ci/pre.json", "sha256": "a" * 64, "why": None}
    b = {"path": "/home/me/pre.json", "sha256": "a" * 64, "why": None}
    assert not gate_cli._moved(a, b, True)
    assert gate_cli._moved(a, {**b, "sha256": "b" * 64}, True)


def test_q2_a_configuration_difference_names_the_files_that_moved_not_both_maps():
    was = {"subject.toml": "1" * 64, "scenarios.toml": "2" * 64}
    now = {"subject.toml": "1" * 64, "scenarios.toml": "3" * 64}
    (line,) = gate_cli.drift_lines("b.json", [{"field": "configuration", "baseline": was, "now": now}])
    assert "scenarios.toml" in line and "subject.toml" not in line and len(line) < 200


def test_h7_one_slot_per_bar_kind_so_lapses_cannot_crowd_attestation_out():
    fs = [{"severity": "blocker", "kind": "key"}] + [{"severity": "major", "kind": "lapsed", "message": str(i)} for i in range(3)] \
        + [{"severity": "major", "kind": "attestation"}]
    shown = knowgov_hook._shown({"findings": fs})
    assert [f["kind"] for f in shown] == ["key", "attestation", "lapsed"]


def test_c_n6_an_ownerless_finding_does_not_read_none_in_the_register_map():
    src = (ROOT / "harness" / "gate_cli.py").read_text(encoding="utf-8")
    assert "owner {f['owner'] or 'none in the register map'}" not in src


# ---- the rest of task-0329's fixes, one assertion each ----
import json  # noqa: E402
import os  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402

sys.path[:0] = [str(ROOT / "tools")]
import check_subject  # noqa: E402
import proposal_impact  # noqa: E402
import subject_ids  # noqa: E402
import trace  # noqa: E402
from gate import _suspect_note  # noqa: E402
from _skip import need_rdflib  # noqa: E402

CQ = ROOT / "subjects" / "cargo_quote"


def _gate(subject: Path, *args: str, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, "KG_SUBJECT": str(subject), "KG_STORE": "rdflib", "KG_REGISTER": str(ROOT / "demo" / "register"),
           "KG_CLOCK": "pinned", **(env_extra or {})}
    env.pop("KG_RDFLIB_FILE", None) if not env_extra else None
    return subprocess.run([sys.executable, str(ROOT / "harness" / "gate_cli.py"), "--as-of", "record", *args],
                          capture_output=True, text=True, env=env, cwd=ROOT / "harness")


def _copy_cq(tmp: str) -> Path:
    dst = Path(tmp) / "subjects" / "cargo_quote"
    shutil.copytree(CQ, dst)
    return dst


def test_s1_a_deleted_single_file_code_or_script_reads_as_the_attestation_finding_not_a_crash():
    need_rdflib()
    for rel in ("vendor/stack_experiment/cargo_quote/reference_impl.py", "vendor/stack_experiment/smoke_test.py"):
        with tempfile.TemporaryDirectory() as tmp:
            sub = _copy_cq(tmp)
            (sub / rel).unlink()
            p = _gate(sub, "--scenario", "S1")
            assert p.returncode in (0, 1) and "FileNotFoundError" not in p.stdout + p.stderr, (rel, p.stderr[-300:])
            assert "is not the one the execution verification attests" in p.stdout, rel


def test_a_n5_no_load_without_a_scenario_reads_the_one_the_store_holds():
    need_rdflib()
    with tempfile.TemporaryDirectory() as tmp:
        f = str(Path(tmp) / "held.ttl")
        ex = {"KG_RDFLIB_FILE": f}
        load = _gate(CQ, "--scenario", "S2", "--publish", env_extra=ex)
        assert load.returncode in (0, 1), load.stderr[-300:]
        out = Path(tmp) / "r.json"
        _gate(CQ, "--no-load", "-f", "json", "-o", str(out), env_extra=ex)
        assert json.loads(out.read_text())["scenario"] == "S2"


def test_a_n4_a_proceed_with_a_suspect_output_says_so_in_its_why():
    assert "suspect" in _suspect_note([{"id": "d"}], "PROCEED") and _suspect_note([{"id": "d"}], "BLOCKED") == ""
    assert _suspect_note([], "PROCEED") == ""


def test_b_n6_an_equal_value_under_a_changed_source_is_said_so():
    was = {"s": {"value": 3, "sha256": "a" * 64}}
    now = {"s": {"value": 3, "sha256": "b" * 64}}
    assert "unchanged, its source changed" in trace._was_now("s", was, now)
    assert "now 4" in trace._was_now("s", was, {"s": {"value": 4, "sha256": "b" * 64}})


def test_b_n8_a_relative_kg_subject_is_made_absolute_by_the_two_check_tools():
    need_rdflib()
    for tool in ("check_gate_after_change", "check_register_change"):
        code = f"import os,sys; sys.path.insert(0,'tools'); import {tool}; print(os.environ['KG_SUBJECT'])"
        p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=ROOT,
                           env={**os.environ, "KG_SUBJECT": "subjects/cargo_quote", "KG_CLOCK": "pinned"})
        assert Path(p.stdout.strip().splitlines()[-1]).is_absolute(), (tool, p.stderr[-300:])


def test_b_n2_the_remedy_for_a_register_update_is_named_only_when_statements_were_staled():
    assert "re-map the key" in gate_cli._remedy({"invalidated": ["x"]})[0]
    assert gate_cli._remedy({"invalidated": []}) == []


def test_r1_a_link_withdrawn_in_place_points_at_register_previous():
    assert "--register-previous" in proposal_impact._link_in_place({"state": "approved"}, {"state": "deprecated"})
    assert "--register-previous" not in proposal_impact._link_in_place({"state": "approved"}, {"state": "approved", "x": 1})


def test_r2_the_branch_report_says_its_gate_is_not_a_verdict_on_the_proposal():
    assert "not a verdict on this proposal" in (ROOT / "harness" / "proposal_impact.py").read_text(encoding="utf-8")


def test_h8_the_unlisted_count_says_it_is_from_any_cause():
    f = gate_cli.unlisted_finding({"declaration": "execution", "unattested": [{"artefact": "a", "sha256": "x", "keys": ["k|a"]}],
                                   "attester": None}, {"k|a"})
    assert "from any cause" in f["message"]


def test_h9_the_unchanged_code_note_does_not_read_as_a_relisting():
    rep = check_subject.Report(CQ)
    check_subject._unchanged_code_note.__globals__["Report"]  # the module is the one under test
    src = (ROOT / "tools" / "check_subject.py").read_text(encoding="utf-8")
    assert "a document was edited since it was attested" in src and "lists a document digest for an edited document" not in src
    assert rep.notes == []


def test_the_capture_warning_is_plural_for_several_files():
    src = (ROOT / "harness" / "capture.py").read_text(encoding="utf-8")
    assert "'other reviewers'" in src and "'rulings'" in src


def test_q3_the_configuration_description_does_not_repeat_its_prefix():
    d = json.loads((ROOT / "harness" / "schemas" / "trace-report.schema.json").read_text(encoding="utf-8"))
    text = d["properties"]["gate"]["properties"]["configuration"]["description"] if "gate" in d["properties"] else \
        json.dumps(d)
    assert text.count("task-0335 (decision-0039 §3.2), optional and additive: as the gate report's") <= 1


def test_p2_the_code_difference_names_the_paths_that_moved():
    was, now = {"a.py": "1" * 64, "b.py": "2" * 64}, {"a.py": "1" * 64, "b.py": "9" * 64}
    (line,) = gate_cli.drift_lines("b.json", [{"field": "code", "baseline": was, "now": now}])
    assert "b.py" in line and "a.py" not in line


def test_s1_a_path_outside_the_instance_is_said_as_itself():
    from subject import CodePathOutside
    assert gate_cli._own_cause(CodePathOutside("the manifest names ../../x")) == "the manifest names ../../x"
    assert gate_cli._own_cause(ValueError("x")) is None


def test_s2_the_command_line_check_confines_code_and_script_as_the_load_does():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "a" / "b" / "sub"
        root.mkdir(parents=True)
        rep = check_subject.Report(root)
        m = {"reference": {"code": "/etc/passwd"}, "oracle": {"script": "../../../../x.py"}}
        assert check_subject._outside(rep, m, root, "reference", "code") and check_subject._outside(rep, m, root, "oracle", "script")
        assert not check_subject._outside(rep, {"reference": {"code": "src/x.py"}}, root, "reference", "code")


def test_s3_the_owning_field_of_a_stale_digest_names_the_suite_files():
    m = {"oracle": {"script": "s.py", "suite": ["t/e.py"]}}
    assert check_subject._owner(m, "suite", "oracle", "script") == "[oracle] script or a file [oracle] suite lists"
    assert check_subject._owner({"oracle": {"script": "s.py"}}, "suite", "oracle", "script") == "[oracle] script"


def test_task_0339_a_duplicate_subject_id_is_named_on_stderr_once():
    import contextlib
    import io
    with tempfile.TemporaryDirectory() as tmp:
        roots = []
        for n in ("one", "two"):
            r = Path(tmp) / n
            r.mkdir()
            (r / "subject.toml").write_text('[subject]\nid = "dup"\nname = "d"\n', encoding="utf-8")
            roots.append(str(r))
        old = os.environ.get("KG_SUBJECTS")
        os.environ["KG_SUBJECTS"] = os.pathsep.join(roots)
        err = io.StringIO()
        try:
            with contextlib.redirect_stderr(err):
                subject_ids.subjects()
                subject_ids.subjects()
        finally:
            os.environ.pop("KG_SUBJECTS") if old is None else os.environ.update(KG_SUBJECTS=old)
        assert err.getvalue().count("'dup'") == 1 and "first root's is kept" in err.getvalue()
