"""task-0329, second round (R1-R9, the old R3, N-4): each fix run, not read."""
from __future__ import annotations

import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tools"), str(ROOT / "instance" / "ci" / "claude"), str(Path(__file__).resolve().parent)]
import gate_cli  # noqa: E402
import knowgov_hook  # noqa: E402
import proposal_impact  # noqa: E402
import subject as subject_mod  # noqa: E402
import subject_ids  # noqa: E402
from _skip import need_rdflib  # noqa: E402

CQ = ROOT / "subjects" / "cargo_quote"


def _gate(subject: Path, *args: str, rdflib_file: str | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, "KG_SUBJECT": str(subject), "KG_STORE": "rdflib", "KG_REGISTER": str(ROOT / "demo" / "register"), "KG_CLOCK": "pinned"}
    env.pop("KG_RDFLIB_FILE", None)
    if rdflib_file:
        env["KG_RDFLIB_FILE"] = rdflib_file
    return subprocess.run([sys.executable, str(ROOT / "harness" / "gate_cli.py"), "--as-of", "record", *args],
                          capture_output=True, text=True, env=env, cwd=ROOT / "harness")


def _edited_copy(tmp: str, old: str, new: str) -> Path:
    dst = Path(tmp) / "subjects" / "cargo_quote"
    shutil.copytree(CQ, dst)
    toml = dst / "subject.toml"
    text = toml.read_text(encoding="utf-8")
    assert old in text, old
    toml.write_text(text.replace(old, new, 1), encoding="utf-8")
    return dst


def test_r1_no_load_resolves_the_held_scenario_before_the_baseline_is_checked():
    need_rdflib()
    with tempfile.TemporaryDirectory() as tmp:
        f = str(Path(tmp) / "held.ttl")
        assert _gate(CQ, "--scenario", "S3", "--publish", rdflib_file=f).returncode in (0, 1)
        p = _gate(CQ, "--no-load", "--baseline", "record", rdflib_file=f)
        assert p.returncode == 0 and "REGRESSION" not in p.stdout.replace("no regression", ""), p.stdout[-300:] + p.stderr[-300:]
        rep = Path(tmp) / "s3.json"
        assert _gate(CQ, "--no-load", "-f", "json", "-o", str(rep), rdflib_file=f).returncode in (0, 1)
        q = _gate(CQ, "--no-load", "--baseline", str(rep), rdflib_file=f)
        assert q.returncode == 0 and "this run's scenario" not in q.stderr, q.stderr[-300:]


def test_r1_the_help_says_no_load_reads_the_held_scenario():
    p = subprocess.run([sys.executable, str(ROOT / "harness" / "gate_cli.py"), "--help"], capture_output=True, text=True, cwd=ROOT / "harness")
    assert "with --no-load, the one the store holds" in " ".join(p.stdout.split())


def test_r2_the_hooks_summary_says_no_single_unit_for_an_ownerless_attestation_finding():
    rep = {"verdict": "BLOCKED", "subject": "s", "scenario": "S1", "task": "codegen", "as_of": "2026-11-12", "threshold": "blocker",
           "findings": [{"severity": "major", "kind": "attestation", "key": None, "message": "a is not attested", "owner": None, "route": "r"}]}
    text = knowgov_hook._summary(rep)
    assert "(owner no single unit in the register map)" in text and "owner none" not in text


def test_r3_a_register_staled_finding_names_the_remedy_not_the_questionnaire():
    rc = {"stale": [{"id": "A:s:k|a@v1", "key": "k|a", "invalidated_by": "the register at v1: decisions/0099.md"},
                    {"id": "A:s:k|b@v1", "key": "k|b", "invalidated_by": "version v2 of requirements.md"}]}
    fs = [{"kind": "key", "key": "k|a", "ref": None, "route": "python harness/capture.py questionnaire ..."},
          {"kind": "stale", "key": "k|a", "ref": "A:s:k|a@v1", "route": "python harness/capture.py questionnaire ..."},
          {"kind": "stale", "key": "k|b", "ref": "A:s:k|b@v1", "route": "q"},
          {"kind": "key", "key": "k|b", "ref": None, "route": "q"}]
    out = gate_cli.register_routes(fs, rc)
    assert [f["route"] == gate_cli.REGISTER_ROUTE for f in out] == [True, True, False, False]
    assert "re-map the key" in gate_cli.REGISTER_ROUTE and gate_cli.register_routes(fs[2:], {})[0]["route"] == "q"


def test_r4_a_suite_path_outside_the_instance_is_never_digested():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "a" / "b" / "sub"
        root.mkdir(parents=True)
        (root / "s.py").write_text("x", encoding="utf-8")
        _rel, parts, declared = subject_mod.code_files(root, {}, {"script": "s.py", "suite": ["/etc/hostname", "../../../../etc/hostname"]}, "suite")
        assert declared == {} and list(parts) == [""], (parts, declared)


def test_r5_each_path_sits_beside_its_own_role():
    import check_subject
    m = {"oracle": {"script": "smoke.py", "suite": ["t/e.py"]}}
    assert check_subject._owner(m, "suite", "oracle", "script", "smoke.py") == "[oracle] script smoke.py or a file [oracle] suite lists"


def test_r6_a_non_utf8_code_file_and_a_non_string_code_are_the_manifests_cause():
    need_rdflib()
    with tempfile.TemporaryDirectory() as tmp:
        sub = _edited_copy(tmp, 'code = "vendor/stack_experiment/cargo_quote/reference_impl.py"', "code = 5")
        p = _gate(sub, "--scenario", "S1")
        assert p.returncode == 2 and "store did not answer" not in p.stderr and "not a path" in p.stderr, p.stderr[-300:]
    with tempfile.TemporaryDirectory() as tmp:
        sub = _edited_copy(tmp, 'code = "vendor/stack_experiment/cargo_quote/reference_impl.py"', 'code = "vendor/stack_experiment/cargo_quote/reference_impl.py"')
        (sub / "vendor/stack_experiment/cargo_quote/reference_impl.py").write_bytes(b"\xff\xfe\x00bad")
        p = _gate(sub, "--scenario", "S1")
        assert p.returncode == 2 and "store did not answer" not in p.stderr and "not UTF-8" in p.stderr, p.stderr[-300:]


def test_r7_an_empty_code_path_is_a_missing_file_with_the_attestation_finding():
    need_rdflib()
    with tempfile.TemporaryDirectory() as tmp:
        sub = _edited_copy(tmp, 'code = "vendor/stack_experiment/cargo_quote/reference_impl.py"', 'code = ""')
        p = _gate(sub, "--scenario", "S1")
        assert p.returncode in (0, 1) and "is not the one the execution verification attests" in p.stdout, p.stdout[-400:] + p.stderr[-300:]


def test_r8_the_same_root_twice_is_one_root_and_a_dropped_root_is_named_with_the_one_kept():
    with tempfile.TemporaryDirectory() as tmp:
        roots = []
        for n in ("one", "two"):
            r = Path(tmp) / n
            r.mkdir()
            (r / "subject.toml").write_text('[subject]\nid = "dup"\nname = "d"\n', encoding="utf-8")
            roots.append(str(r))
        subject_ids._SAID.clear()
        old = os.environ.get("KG_SUBJECTS")
        err = io.StringIO()
        try:
            os.environ["KG_SUBJECTS"] = os.pathsep.join([roots[0], roots[0]])
            with contextlib.redirect_stderr(err):
                subject_ids.subjects()
            assert "also at" not in err.getvalue(), err.getvalue()
            os.environ["KG_SUBJECTS"] = os.pathsep.join(roots)
            with contextlib.redirect_stderr(err):
                subject_ids.subjects()
        finally:
            os.environ.pop("KG_SUBJECTS") if old is None else os.environ.update(KG_SUBJECTS=old)
        text = err.getvalue()
        assert str(Path(roots[1]).resolve()) in text and "the root kept is " + str(Path(roots[0]).resolve()) in text, text


def test_r9_a_review_lapse_gets_the_renew_step_with_the_kg_home_form_and_an_elicited_one_keeps_its_route():
    att = {"severity": "major", "kind": "attestation", "message": "a", "route": "r"}
    review = {"severity": "major", "kind": "lapsed", "message": "l", "route": "a reviewer who is not the author and holds the role renews it: ..."}
    elicited = {"severity": "major", "kind": "lapsed", "message": "l", "route": "python harness/capture.py questionnaire ..."}
    rep = {"findings": [{"severity": "blocker", "kind": "task", "message": "bar"}, att, review]}
    assert knowgov_hook._route_for(rep).endswith(knowgov_hook.LAPSE_STEP) and '"$KG_HOME"/harness/capture.py' in knowgov_hook.LAPSE_STEP
    rep["findings"][2] = elicited
    assert knowgov_hook._route_for(rep) == knowgov_hook.ATTESTATION_ROUTE


def test_r9_the_text_render_shows_what_the_branch_did_not_read_with_its_pointer():
    lines = proposal_impact._not_read_lines({"not_read": [{"path": "relationships/supports.toml [REL-06001]", "status": "M",
                                                           "why": proposal_impact._link_in_place({"state": "approved"}, {"state": "deprecated"})}]})
    assert len(lines) == 1 and "gate_cli --register-previous" in lines[0]


def test_old_r3_a_reused_node_says_what_changed():
    assert proposal_impact._what_changed({"parent": "CAP-0001", "name": "n"}, {"parent": "CAP-0006", "name": "n"}) == "parent CAP-0001 -> CAP-0006"
    proposal_impact._WHAT["CAP-0002"] = "parent CAP-0001 -> CAP-0006"
    try:
        assert "(parent CAP-0001 -> CAP-0006)" in proposal_impact._reuse_reason({"id": "CAP-0002", "mode": "changed"})
    finally:
        proposal_impact._WHAT.clear()
    assert proposal_impact._reason_suffix({"kind": "reuse", "reason": "why"}) == " (why)" and proposal_impact._reason_suffix({"kind": "link", "reason": "x"}) == ""


def test_n4_the_glossary_row_for_approved_says_a_ruling_approves_directly():
    row = next(ln for ln in (ROOT / "docs" / "guide.md").read_text(encoding="utf-8").splitlines() if ln.startswith("| status `approved`"))
    assert "approves it directly with no verification" in row


# ---- round three (L2-L8) ----
def test_l2_the_remedy_route_reads_the_same_on_a_load_a_no_load_read_and_the_mcp_gate_verdict():
    need_rdflib()
    import json as _json
    import register_fixture
    import mcp_server
    from store import open_store
    from subject import SUBJECT
    with tempfile.TemporaryDirectory() as tmp:
        changed = register_fixture.changed(Path(tmp) / "reg")
        f = str(Path(tmp) / "held.ttl")
        env = {**os.environ, "KG_SUBJECT": str(CQ), "KG_STORE": "rdflib", "KG_REGISTER": str(changed), "KG_CLOCK": "pinned", "KG_RDFLIB_FILE": f}
        gate = [sys.executable, str(ROOT / "harness" / "gate_cli.py"), "--as-of", "record"]
        load = Path(tmp) / "load.json"
        p = subprocess.run([*gate, "--scenario", "S1", "--register-previous", str(ROOT / "demo" / "register"), "--publish", "-f", "json",
                            "-o", str(load)], capture_output=True, text=True, env=env, cwd=ROOT / "harness")
        assert p.returncode in (0, 1), p.stderr[-300:]
        read = Path(tmp) / "read.json"
        p = subprocess.run([*gate, "--no-load", "-f", "json", "-o", str(read)], capture_output=True, text=True, env=env, cwd=ROOT / "harness")
        assert p.returncode in (0, 1), p.stderr[-300:]
        routes = lambda path: sorted((f_["kind"], str(f_["key"]), str(f_["ref"]), str(f_.get("route"))) for f_ in _json.loads(path.read_text())["findings"])  # noqa: E731
        assert routes(load) == routes(read) and any(r[3] == gate_cli.REGISTER_ROUTE for r in routes(read))
        old = {k: os.environ.get(k) for k in ("KG_STORE", "KG_RDFLIB_FILE", "KG_REGISTER", "KG_TODAY")}
        os.environ.update(KG_STORE="rdflib", KG_RDFLIB_FILE=f, KG_REGISTER=str(changed), KG_TODAY="2026-11-06")
        try:
            srv = mcp_server.Server(mcp_server.Tools(opener=lambda: mcp_server.ReadOnlyStore(open_store(instance=SUBJECT.id, access="read"))))
            r = srv.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "gate_verdict", "arguments": {}}})
            fs = r["result"]["structuredContent"]["findings"]
        finally:
            for k, v in old.items():
                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        assert any(x.get("route") == gate_cli.REGISTER_ROUTE for x in fs if x["kind"] == "stale")


def test_l3_an_unreadable_code_file_is_the_manifests_cause_not_the_stores():
    import types
    err = PermissionError(13, "Permission denied", "/x/reference_impl.py")
    assert "cannot be read" in gate_cli._own_cause(err) and "/x/reference_impl.py" in gate_cli._own_cause(err)
    sub = types.SimpleNamespace(id="s", reference={"code": "ref.py"}, path=lambda rel: _Unreadable())
    try:
        subject_mod.Subject.reference_code(sub)
    except subject_mod.CodeUnreadable as e:
        assert "permission denied" in str(e)
    else:
        raise AssertionError("no refusal")


class _Unreadable:
    """A path that exists and is a file but cannot be read (root ignores chmod, so it is simulated)."""
    def exists(self):
        return True

    def is_dir(self):
        return False

    def read_text(self, encoding=None):
        raise PermissionError(13, "Permission denied")


def test_l4_check_subject_gives_a_path_error_for_a_non_string_code_or_script():
    import check_subject
    for m in ({"reference": {"code": 5}}, {"reference": {"code": []}}, {"oracle": {"script": 5}}):
        rep = check_subject.Report(CQ)
        check_subject.check_code_paths(rep, m)
        assert [f["rule"] for f in rep.findings] == ["path"] and "not a path" in rep.findings[0]["message"], m
    rep = check_subject.Report(CQ)
    check_subject.check_code_paths(rep, {"reference": {"code": "a.py"}, "oracle": {}})
    assert rep.findings == []


def test_l5_a_suite_entry_that_is_not_a_path_is_named():
    import check_subject
    assert "entry 0 (5)" in check_subject._suite_refusal([5]) and "entry 1 ('')" in check_subject._suite_refusal(["a.py", ""])
    assert "write suite = ['a.py']" in check_subject._suite_refusal("a.py") and check_subject._suite_refusal("a.py").startswith("is not a list of paths")


def test_l6_only_the_root_actually_kept_is_named():
    with tempfile.TemporaryDirectory() as tmp:
        repo, inst = Path(tmp) / "repo", Path(tmp) / "inst"
        for base in (repo, inst):
            (base / "subjects" / "cq").mkdir(parents=True)
            (base / "subjects" / "cq" / "subject.toml").write_text('[subject]\nid = "cargo_quote"\nname = "c"\n', encoding="utf-8")
        own = inst / "subjects" / "cq"
        old = {k: os.environ.get(k) for k in ("KG_SUBJECTS", "KG_SUBJECT")}
        os.environ["KG_SUBJECTS"] = os.pathsep.join([str(repo / "subjects"), str(inst / "subjects")])
        os.environ["KG_SUBJECT"] = str(own)
        subject_ids._SAID.clear()
        err = io.StringIO()
        saved = subject_mod.SUBJECT
        try:
            subject_mod.SUBJECT = types_ns = type("S", (), {"root": own, "id": "cargo_quote", "name": "c", "order": []})()
            with contextlib.redirect_stderr(err):
                got = subject_ids.subjects()
        finally:
            subject_mod.SUBJECT = saved
            for k, v in old.items():
                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        del types_ns
        text = err.getvalue()
        assert [x["root"] for x in got if x["id"] == "cargo_quote"] == [own.resolve()]
        assert text.count("the root kept is") == 1 and f"the root kept is {own.resolve()}" in text, text


def test_l7_an_empty_or_blank_code_path_is_said_as_an_empty_path():
    for blank in ("", "  "):
        rel, parts, declared = subject_mod.code_files(CQ, {"code": blank}, {}, "implementation")
        assert (rel, parts, declared) == ("", {}, {}), blank
    import check_subject
    with tempfile.TemporaryDirectory() as tmp:
        rep = check_subject.Report(Path(tmp))
        check_subject._execution_listing(rep, {"reference": {"code": "  "}}, Path(tmp), {"versions": [], "implementation": ["a" * 64]},
                                         "implementation", "reference", "code")
        assert rep.findings and all("(an empty path)" in f["message"] for f in rep.findings), rep.findings


def test_l8_a_symlink_out_of_a_code_directory_is_refused_by_the_load_and_the_checker_and_never_digested():
    import check_subject
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "a" / "b" / "sub"
        (root / "src").mkdir(parents=True)
        (root / "src" / "ok.py").write_text("x", encoding="utf-8")
        outside = Path(tmp) / "elsewhere.py"
        outside.write_text("secret", encoding="utf-8")
        (root / "src" / "escape.py").symlink_to(outside)
        assert subject_mod.escaping_file(root, "src") == "escape.py"
        rep = check_subject.Report(root)
        assert check_subject._outside(rep, {"reference": {"code": "src"}}, root, "reference", "code")
        assert "escape.py" in rep.findings[0]["message"]
        _rel, _parts, declared = subject_mod.code_files(root, {}, {"script": "src/ok.py", "suite": ["src"]}, "suite")
        assert declared == {}, declared
        fake = type("S", (), {"id": "s", "root": root, "reference": {"code": "src"}, "oracle": {}})()
        fake._code_paths = lambda: subject_mod.Subject._code_paths(fake)
        try:
            subject_mod.Subject.require_code_inside(fake)
        except subject_mod.CodePathOutside as e:
            assert "escape.py" in str(e)
        else:
            raise AssertionError("no refusal")


def test_l2_the_gate_report_schema_describes_the_remedy_and_review_routes():
    import json as _json
    d = _json.loads((ROOT / "harness" / "schemas" / "gate-report.schema.json").read_text(encoding="utf-8"))
    desc = d["$defs"]["finding"]["properties"]["route"]["description"]
    assert "usually the owner's questionnaire" in desc and "--register-previous" in desc and "lapsed review" in desc
