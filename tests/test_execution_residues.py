"""task-0340 (task-0338's residues, decision-0039 §3.5): an execution attestation binds every file it lists, and only
the instance's.

- AC1 (R1): a listed implementation or suite digest no current file holds (a file deleted from a listed directory) verifies
  nothing by execution; the gate's attestation finding and ``check_subject`` name it. The load is store-independent
  (``load.execution_code`` runs before any store write), so the gate runs here on rdflib.
- AC2 (R2): a code, script or suite path outside the instance is refused at the load, exit 2, naming it.
- AC3 (R4): the attestation hook refuses re-pointing ``[oracle] script`` or ``[reference] code`` while ``[verification]``
  stays; ``check_subject`` notes a script also listed in ``[oracle] suite``.
Standard library; the gate parts skip without the pins. No network; the clock pinned."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / "harness"
sys.path[:0] = [str(HARNESS), str(ROOT / "tools"), str(Path(__file__).resolve().parent)]
from _skip import need_rdflib  # noqa: E402

CQ = ROOT / "subjects" / "cargo_quote"
ACC = "vendor/tools/acceptance"
SCRIPT = "vendor/stack_experiment/smoke_test.py"


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _copy(td: str, whole_dir: bool = True) -> Path:
    root = Path(td) / "subjects" / "cargo_quote"
    shutil.copytree(CQ, root, ignore=shutil.ignore_patterns("__pycache__"))
    if whole_dir:   # group A's repro: list every file of the acceptance directory
        p = root / "subject.toml"
        t = p.read_text(encoding="utf-8")
        t = t.replace(f'suite = ["{ACC}/cargo_quote_suite.py"]', f'suite = ["{ACC}"]')
        digs = [_sha(root / SCRIPT)] + [_sha(f) for f in sorted((root / ACC).glob("*.py"))]
        t, n = re.subn(r'(execution = \{.*?\bsuite = )\[[^\]]*\]', lambda m: m.group(1) + json.dumps(digs), t, flags=re.S)
        assert n == 1
        p.write_text(t, encoding="utf-8")
    return root


def _env(root: Path) -> dict:
    env = {**os.environ, "KG_SUBJECT": str(root), "KG_SUBJECTS": str(root.parent), "KG_STORE": "rdflib", "KG_CLOCK": "pinned",
           "KG_REGISTER": str(ROOT / "demo" / "register"), "PYTHONDONTWRITEBYTECODE": "1"}
    env.pop("KG_RDFLIB_FILE", None)
    return env


def _gate(root: Path):
    p = subprocess.run([sys.executable, str(HARNESS / "gate_cli.py"), "--scenario", "S1", "-f", "json", "--as-of", "record"],
                       capture_output=True, text=True, env=_env(root), timeout=600)
    return p, (json.loads(p.stdout) if p.returncode in (0, 1) and p.stdout else None)


def _check(root: Path) -> list[dict]:
    import check_subject
    import tomllib
    m = tomllib.loads((root / "subject.toml").read_text(encoding="utf-8"))
    rep = check_subject.Report(root)
    check_subject.check_oracle_suite(rep, m, root)
    check_subject.check_execution_code(rep, m, root, m["verification"]["execution"])
    return rep.findings


def test_ac1_a_deleted_file_of_a_listed_suite_directory_is_stale_in_check_subject_and_the_gate():
    need_rdflib()
    with tempfile.TemporaryDirectory() as td:
        root = _copy(td)
        assert _check(root) == [], "every file of the directory listed: nothing to name"
        p, rep = _gate(root)
        assert rep["verdict"] == "PROCEED", rep["verdict"]
        gone = _sha(root / ACC / "runner_child.py")
        (root / ACC / "runner_child.py").unlink()
        found = _check(root)
        assert [f["rule"] for f in found] == ["attestation"] and gone in found[0]["message"] \
            and "matches no current file" in found[0]["message"], found
        p, rep = _gate(root)
        named = [f for f in rep["findings"] if f["kind"] == "attestation" and f["ref"] == SCRIPT]
        assert len(named) == 1 and gone[:12] in named[0]["message"] and "no current file holds" in named[0]["message"], rep["findings"]
        assert rep["verdict"] != "PROCEED", "a listed file is gone: nothing is verified by execution"


def test_ac1_a_deleted_implementation_file_is_stale_too():
    import load
    import subject
    with tempfile.TemporaryDirectory() as td:
        root = _copy(td, whole_dir=False)
        s = subject.Subject(root) if hasattr(subject, "Subject") else None
        load.SUBJECT = s
        decl = dict(load.VER["execution"]) if isinstance(load.VER, dict) else None
        decl["implementation"] = list(decl["implementation"]) + ["0" * 64]
        rows = load.execution_code(decl, ["K"])
        assert [r["code"] for r in rows] == ["implementation"] and rows[0]["stale"] == ["0" * 64], rows


def test_ac2_a_path_outside_the_instance_is_refused_at_the_load_with_exit_2():
    need_rdflib()
    for bad in ("/etc/hostname", "../../../outside.py"):
        with tempfile.TemporaryDirectory() as td:
            root = _copy(td, whole_dir=False)
            p = root / "subject.toml"
            p.write_text(p.read_text(encoding="utf-8").replace(f'suite = ["{ACC}/cargo_quote_suite.py"]', f'suite = ["{bad}"]'),
                         encoding="utf-8")
            proc, _rep = _gate(root)
            assert proc.returncode == 2 and bad in proc.stderr and "not a relative path inside" in proc.stderr, (bad, proc.returncode, proc.stderr[-500:])


def test_ac3_the_hook_refuses_repointing_the_script_or_the_code_while_verification_stays():
    hook = ROOT / "instance" / "ci" / "claude" / "attestation_paths.py"
    m = ('[subject]\nid = "probe"\n\n[reference]\ncode = "impl.py"\n\n[oracle]\nscript = "run.py"\n\n'
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
        for old, new, field in (('script = "run.py"', 'script = "other.py"', "[oracle] script"),
                                ('code = "impl.py"', 'code = "other.py"', "[reference] code")):
            p = edit(old, new)
            assert p.returncode == 2 and f"{field} while [verification] stays" in p.stderr, (field, p.stderr)
        assert edit('keys = ["REQ-01|text"]', 'keys = ["REQ-01|text", "REQ-02|text"]').returncode == 0


def test_ac3_check_subject_notes_a_script_also_listed_in_the_suite():
    import check_subject
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "subjects" / "s"
        root.mkdir(parents=True)
        (root / "run.py").write_text("x = 1\n", encoding="utf-8")
        rep = check_subject.Report(root)
        check_subject.check_oracle_suite(rep, {"oracle": {"script": "run.py", "suite": ["run.py"]}}, root)
        assert [f["level"] for f in rep.findings] == ["note"] and "also lists the script run.py" in rep.findings[0]["message"], rep.findings
