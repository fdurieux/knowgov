"""task-0338 (decision-0039 §3.5 (a), doc-0038 §3.5, group A's N-2 on task-0330): the suite digest binds its declared
files.

``[verification] execution``'s ``suite`` bound only ``[oracle] script``'s own bytes, so CargoQuote's expectations, in
``vendor/tools/acceptance/cargo_quote_suite.py``, which the script imports, moved no digest: an honest suite change left
it unchanged, and editing the expectations to match a wrong implementation went unseen. An optional ``[oracle] suite``
lists such files; each is digested into ``suite`` in sorted path order. Missing, the suite is the script alone.

- AC1: with the field listing the acceptance module, editing it moves the suite digest, ``check_subject`` names it, and
  the gate's attestation finding names it (major, not PROCEED); without the field, the edit moves nothing, as before.
- AC2: subjects/README and the adopter guide document the field; CargoQuote's manifest lists its acceptance module and
  its execution lists hold its digest (the record holds: harness.yml's comparator); check_subject reads the field.
Standard library; the store-backed part skips without the pins. No network; the clock pinned."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / "harness"
sys.path[:0] = [str(HARNESS), str(ROOT / "tools"), str(Path(__file__).resolve().parent)]
from _skip import need_rdflib  # noqa: E402

CQ = ROOT / "subjects" / "cargo_quote"
MODULE = "vendor/tools/acceptance/cargo_quote_suite.py"
SCRIPT = "vendor/stack_experiment/smoke_test.py"
WRONG = (b'"require_re": r"3186"', b'"require_re": r"3211"')   # group A's repro: the expectation moved to a new price


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _copy(td: str) -> Path:
    root = Path(td) / "cargo_quote"
    shutil.copytree(CQ, root, ignore=shutil.ignore_patterns("__pycache__"))
    return root


def _manifest(root: Path) -> dict:
    return tomllib.loads((root / "subject.toml").read_text(encoding="utf-8"))


def _edit_expectations(root: Path) -> None:
    p = root / MODULE
    raw = p.read_bytes()
    assert raw.count(WRONG[0]) == 1, "the expectation group A edited"
    p.write_bytes(raw.replace(*WRONG))


def _without_field(root: Path) -> None:
    """The manifest as it was before task-0338: no [oracle] suite, the suite listing the script alone."""
    p = root / "subject.toml"
    text = p.read_text(encoding="utf-8")
    text = re.sub(r'(?m)^suite = \["vendor/tools/acceptance/cargo_quote_suite\.py"\]\n', "", text)
    text = text.replace(f', "{_sha(CQ / MODULE)}"] }}', "] }")
    p.write_text(text, encoding="utf-8")
    m = _manifest(root)
    assert "suite" not in m["oracle"] and m["verification"]["execution"]["suite"] == [_sha(CQ / SCRIPT)]


def _check(root: Path) -> list[dict]:
    import check_subject
    m = _manifest(root)
    rep = check_subject.Report(root)
    check_subject.check_oracle_suite(rep, m, root)
    check_subject.check_execution_code(rep, m, root, m["verification"]["execution"])
    return rep.findings


# ---- AC1: the digest moves, check_subject and the gate name the file
def test_ac1_the_suite_digest_is_the_script_with_each_declared_file_in_sorted_path_order():
    import subject
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "s.py").write_bytes(b"import b, a\n")
        (root / "a.py").write_bytes(b"A = 1\n")
        (root / "b").mkdir()
        (root / "b" / "x.py").write_bytes(b"X = 1\n")
        alone = subject.code_files(root, {}, {"script": "s.py"}, "suite")
        assert alone == ("s.py", {"": _sha(root / "s.py")}, {}), "no [oracle] suite: the script alone, as before"
        rel, parts, declared = subject.code_files(root, {}, {"script": "s.py", "suite": ["b", "a.py", "gone.py"]}, "suite")
        assert rel == "s.py" and list(declared) == ["a.py", "b/x.py", "gone.py"], "sorted by path, a directory's files under it"
        assert parts == {"": _sha(root / "s.py"), "a.py": _sha(root / "a.py"), "b/x.py": _sha(root / "b" / "x.py"), "gone.py": ""}
        before = parts["a.py"]
        (root / "a.py").write_bytes(b"A = 2\n")
        assert subject.code_files(root, {}, {"script": "s.py", "suite": ["a.py"]}, "suite")[1]["a.py"] != before
        assert subject.code_files(root, {"code": "s.py"}, {"suite": ["a.py"]}, "implementation")[1] == {"": _sha(root / "s.py")}, \
            "[oracle] suite never enters the implementation"


def test_ac1_editing_the_expectations_alone_is_named_by_check_subject():
    with tempfile.TemporaryDirectory() as td:
        root = _copy(td)
        assert _check(root) == [], "CargoQuote as committed: every listed digest is the file as it is"
        _edit_expectations(root)
        found = _check(root)
        assert [f["level"] for f in found] == ["error"], found
        assert MODULE in found[0]["message"] and _sha(root / MODULE) in found[0]["message"] \
            and "or a file [oracle] suite lists changed" in found[0]["message"] and "decision-0038" in found[0]["message"], found
        (root / MODULE).unlink()
        found = _check(root)
        assert [f["rule"] for f in found] == ["path", "attestation"] and f"{MODULE} (no file there)" in found[1]["message"], found


def test_ac1_without_the_field_editing_the_expectations_moves_nothing_as_before():
    with tempfile.TemporaryDirectory() as td:
        root = _copy(td)
        _without_field(root)
        _edit_expectations(root)
        assert _check(root) == [], "the script alone: the module is no part of the suite digest"


def _gate(root: Path) -> dict:
    env = {**os.environ, "KG_SUBJECT": str(root), "KG_SUBJECTS": str(root.parent), "KG_STORE": "rdflib", "KG_CLOCK": "pinned",
           "KG_REGISTER": str(ROOT / "demo" / "register"), "PYTHONDONTWRITEBYTECODE": "1"}   # the copy's own register, named
    env.pop("KG_RDFLIB_FILE", None)
    p = subprocess.run([sys.executable, str(HARNESS / "gate_cli.py"), "--scenario", "S1", "-f", "json", "--as-of", "record"],
                       capture_output=True, text=True, env=env, timeout=600)
    assert p.returncode in (0, 1), p.stderr[-800:]
    return json.loads(p.stdout)


def test_ac1_the_gate_names_the_edited_expectations_and_without_the_field_does_not():
    need_rdflib()
    with tempfile.TemporaryDirectory() as td:
        root = _copy(td)
        assert _gate(root)["verdict"] == "PROCEED"
        _edit_expectations(root)
        rep = _gate(root)
        named = [f for f in rep["findings"] if f["kind"] == "attestation" and f["ref"] == SCRIPT]
        assert len(named) == 1 and named[0]["severity"] == "major", rep["findings"]
        msg = named[0]["message"]
        assert f"{MODULE} ({_sha(root / MODULE)[:12]})" in msg and "[oracle] script and suite" in msg, msg
        assert "[oracle] suite" in named[0]["route"], named[0]["route"]
        assert rep["verdict"] != "PROCEED", "the expectations changed: nothing is verified by execution"
    with tempfile.TemporaryDirectory() as td:
        root = _copy(td)
        _without_field(root)
        _edit_expectations(root)
        rep = _gate(root)
        assert rep["verdict"] == "PROCEED" and not [f for f in rep["findings"] if f["kind"] == "attestation"], \
            "without [oracle] suite the suite is the script alone, as before task-0338"


# ---- AC2: documented, CargoQuote lists it, check_subject reads it
def test_ac2_cargo_quote_lists_its_acceptance_module_and_its_execution_holds_the_digest():
    m = _manifest(CQ)
    assert m["oracle"]["suite"] == [MODULE]
    assert _sha(CQ / MODULE) in m["verification"]["execution"]["suite"] and _sha(CQ / SCRIPT) in m["verification"]["execution"]["suite"]


def test_ac2_check_subject_reads_the_field_and_refuses_a_malformed_one():
    import check_subject
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "subjects" / "s"
        root.mkdir(parents=True)
        (root / "run.py").write_text("x = 1\n", encoding="utf-8")
        for suite, want in (([MODULE], [("path", f"{MODULE} does not exist")]),
                            ("tests.py", [("path", "is not a list of paths")]),
                            (["/etc/passwd"], [("path", "is not a relative path inside")]),
                            (["../../../outside.py"], [("path", "is not a relative path inside")]),
                            (["run.py"], [])):
            rep = check_subject.Report(root)
            check_subject.check_oracle_suite(rep, {"oracle": {"script": "run.py", "suite": suite}}, root)
            assert [(f["rule"], next((w for r, w in want if w in f["message"]), None)) for f in rep.findings] == want, (suite, rep.findings)
        rep = check_subject.Report(root)
        check_subject.check_oracle_suite(rep, {"oracle": {"script": "run.py"}}, root)
        assert rep.findings == [], "the field is optional"


def test_ac2_the_proposed_subject_check_confines_oracle_suite_paths():
    import subject_check
    m = 'format = 1\n[subject]\nid = "s"\n[oracle]\nscript = "run.py"\nsuite = ["%s"]\n'
    subject_check.confine_manifest(m % "tests/expect.py", "s")
    for bad in ("/etc/passwd", "../../../x.py"):
        try:
            subject_check.confine_manifest(m % bad, "s")
        except subject_check.SubjectCheckError as e:
            assert "oracle.suite" in str(e) or "leaves the instance" in str(e), e
        else:
            raise AssertionError(f"{bad} is confined")


def test_ac2_subjects_readme_and_the_guide_document_the_field():
    readme = (ROOT / "subjects" / "README.md").read_text(encoding="utf-8")
    guide = (ROOT / "instance" / "README.md").read_text(encoding="utf-8")
    assert re.search(r'(?m)^suite = \[.*\]\s+# .*', readme) and "task-0338" in readme, "subjects/README's [oracle] block"
    assert "[oracle] suite" in guide and "suite = [" in guide, "the adopter guide's execution section"


def test_ac1_the_attestation_hook_refuses_an_assistant_unbinding_or_rebinding_the_suite():
    """Removing [oracle] suite while [verification] stays leaves the script's digest listed, so the expectations would be
    unbound with no finding; the hook refuses it, as it refuses removing [provenance] while [verification] stays."""
    hook = ROOT / "instance" / "ci" / "claude" / "attestation_paths.py"
    m = ('[subject]\nid = "probe"\n\n[oracle]\nscript = "run.py"\nsuite = ["expect.py"]\n\n'
         '[verification]\nexecution = { versions = [], suite = [] }\n\n[tasks.codegen]\nkeys = ["REQ-01|text"]\n')
    with tempfile.TemporaryDirectory() as td:
        inst = Path(td)
        (inst / "subjects" / "probe").mkdir(parents=True)
        (inst / "subjects" / "probe" / "subject.toml").write_text(m, encoding="utf-8")

        def edit(old, new):
            ev = {"hook_event_name": "PreToolUse", "tool_name": "Edit", "cwd": str(inst),
                  "tool_input": {"file_path": "subjects/probe/subject.toml", "old_string": old, "new_string": new}}
            env = {k: v for k, v in os.environ.items() if not k.startswith(("KG_", "CLAUDE_"))}
            env["CLAUDE_PROJECT_DIR"] = str(inst)
            return subprocess.run([sys.executable, str(hook)], input=json.dumps(ev), capture_output=True, text=True, env=env, timeout=60)
        for old, new in (('suite = ["expect.py"]\n', ""), ('["expect.py"]', '["expect.py", "more.py"]'), ('["expect.py"]', '["other.py"]')):
            p = edit(old, new)
            assert p.returncode == 2 and "[oracle] suite while [verification] stays" in p.stderr, (new, p.stderr)
        assert edit('keys = ["REQ-01|text"]', 'keys = ["REQ-01|text", "REQ-02|text"]').returncode == 0, "an ordinary edit passes"
        both = '[verification]\nexecution = { versions = [], suite = [] }\n'
        assert edit('suite = ["expect.py"]\n\n' + both, "\n").returncode == 0, "removing both attests nothing"
