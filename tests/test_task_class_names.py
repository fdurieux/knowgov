"""task-0278 (decision-0033 choice 4, G9-17): a task class's name is `[a-z][a-z0-9_-]{0,31}`, and never `keys`.

`keys` is the task a report on an agent-chosen key set names (doc-0014 C4). `[tasks.keys]`, `[tasks.""]` and
`[tasks."code gen"]` passed `check_subject` and `check_instance`. Now `harness/task_policy.py`'s `name_problem`
refuses them, and so does every reader built on it:
- the checker and the MCP `subject_check` report an error, rule `task-class`;
- `task_policy.build`, which `harness/tasks.py` runs for every runtime reader, raises `TaskPolicyError` naming
  the class, so a command exits 2.

The public subjects' `codegen` and `design` are unchanged."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "harness")]
import check_instance  # noqa: E402
import check_subject  # noqa: E402
import example_instance  # noqa: E402
import schema_check  # noqa: E402
import subject_check  # noqa: E402
import task_policy  # noqa: E402

REGISTER = ROOT / "demo" / "register"
GOOD = ["codegen", "design", "a", "review-2", "spec_v1", "a" * 32]
BAD = {"keys": "reserved", "": "is not", "code gen": "is not", "Codegen": "is not", "1st": "is not", "-x": "is not",
       "a" * 33: "is not", "codé": "is not", "code.gen": "is not"}
SPEC = {"keys": ["k|v"], "block_levels": ["absent"], "max_unverified_share": 0.25}


def _renamed(td: Path, name: str, base: Path = ROOT / "subjects" / "minimal") -> Path:
    """A copy of ``base`` whose first task class is renamed ``name`` (TOML-quoted)."""
    root = td / "subject"
    shutil.copytree(base, root)
    p = root / "subject.toml"
    text, n = re.subn(r"^\[tasks\.[a-z]+\]$", f"[tasks.{json.dumps(name)}]", p.read_text(encoding="utf-8"), count=1, flags=re.M)
    assert n == 1
    p.write_text(text, encoding="utf-8")
    return root


def test_a_class_name_is_lower_case_ascii_and_never_keys():
    for name in GOOD:
        assert task_policy.name_problem(name) is None, name
        assert task_policy.build(name, SPEC)["keys"] == ["k|v"]
    for name, why in BAD.items():
        p = task_policy.name_problem(name)
        assert p and p["code"] == "task-class" and why in p["message"] and repr(name) in p["message"], (name, p)
        try:
            task_policy.build(name, SPEC)
        except task_policy.TaskPolicyError as e:
            assert e.task == name and e.field == "name" and task_policy.table(name) in str(e), e
        else:
            raise AssertionError(f"{name!r} built")
    assert task_policy.name_problem(None) and task_policy.table("code gen") == '[tasks."code gen"]'


def test_the_checker_reports_each_bad_name_and_its_report_validates():
    schema = schema_check.load("subject-check")
    for name in ("keys", "", "code gen"):
        with tempfile.TemporaryDirectory() as td:
            rep = json.loads(json.dumps(check_subject.check(_renamed(Path(td), name), REGISTER, run_yield=False)))
            found = [f for f in rep["findings"] if f["rule"] == "task-class"]
            assert rep["exit_code"] == 1 and len(found) == 1, (name, rep["findings"])
            assert found[0]["where"] == task_policy.table(name) and found[0]["level"] == "error", found
            assert schema_check.validate(rep, schema) == [], schema_check.validate(rep, schema)
    for sid in ("cargo_quote", "jef_data_load", "minimal"):   # codegen and design hold
        rep = check_subject.check(ROOT / "subjects" / sid, REGISTER, run_yield=False)
        assert not [f for f in rep["findings"] if f["rule"] == "task-class"], (sid, rep["findings"])


def test_the_mcp_subject_check_reports_it():
    with tempfile.TemporaryDirectory() as td:
        root = _renamed(Path(td), "keys")
        rep = subject_check.evaluate({"subject_toml": (root / "subject.toml").read_text(encoding="utf-8"),
                                      "scenarios_toml": (root / "scenarios.toml").read_text(encoding="utf-8"),
                                      "root": "probe"}, REGISTER)
        assert rep["exit_code"] == 1 and "task-class" in {f["rule"] for f in rep["findings"]}, rep["findings"]


def test_the_instance_check_reports_it():
    with tempfile.TemporaryDirectory() as td:
        inst = Path(td) / "instance"
        example_instance.build(inst)
        mf = next((inst / "subjects").glob("*/subject.toml"))
        mf.write_text(re.sub(r"^\[tasks\.codegen\]$", '[tasks."code gen"]', mf.read_text(encoding="utf-8"), count=1, flags=re.M),
                      encoding="utf-8")
        rep = check_instance.check(inst)
        [sub] = rep["subjects"]
        assert [f["where"] for f in sub["check"]["findings"] if f["rule"] == "task-class"] == ['[tasks."code gen"]'], sub["check"]
        assert any('[tasks."code gen"]' in e and "is not [a-z]" in e for e in rep["errors"]), rep["errors"]
        assert check_instance.main([str(inst)]) == 1


def test_the_runtime_refuses_the_manifest_exit_2_naming_the_class():
    for name in ("keys", "", "code gen"):
        with tempfile.TemporaryDirectory() as td:
            root = _renamed(Path(td), name)
            env = {**os.environ, "KG_SUBJECT": str(root), "KG_STORE": "rdflib", "KG_RDFLIB_FILE": str(Path(td) / "never.ttl"),
                   "KG_CLOCK": "pinned", "KG_TODAY": "2026-11-09"}
            r = subprocess.run([sys.executable, str(ROOT / "harness" / "gate_cli.py"), "--scenario", "S0", "--no-load"],
                               cwd=ROOT, env=env, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=120)
            assert r.returncode == 2 and task_policy.table(name) in r.stderr and "name" in r.stderr, (name, r.returncode, r.stderr[-300:])
            assert not (Path(td) / "never.ttl").exists(), "a refused manifest opens no store"
