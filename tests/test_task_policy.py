"""task-0242 (doc-0033 R1): one task-policy validator, ``harness/task_policy.py``, serves the checker and the runtime. The reviewer's
probe is the regression case: ``block_levels = "absent"`` once became the set of its letters, so nothing
blocked and the gate read QUALIFIED, exit 0; ``7`` passed the checker and failed later. Now both are a checker
error and, unchecked, the gate's exit 2 naming the field, on gate_cli and on the MCP reader's gate_verdict,
while ``["absent"]`` blocks as before."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / "harness"
sys.path.insert(0, str(HARNESS))
import task_policy  # noqa: E402
from tests._skip import need_rdflib  # noqa: E402

PROBE = {"string": '"absent"', "integer": "7", "list": '["absent"]'}
CODEGEN_LEVELS = 'block_levels = ["absent", "declared_gap", "disputed", "invalidated"]'


def test_one_validator_types_values_and_ranges_never_coerced():
    good = {"keys": ["a|x"], "block_levels": ["absent"], "max_unverified_share": 0.25, "require_approved": True, "rationale": "why"}
    assert task_policy.problems(good) == []
    built = task_policy.build("codegen", good)
    assert built == {"keys": ["a|x"], "block_levels": {"absent"}, "max_unverified_share": 0.25, "require_approved": True, "rationale": "why"}
    assert task_policy.build("c", {"max_unverified_share": 1})["max_unverified_share"] == 1.0, "an int 0 or 1 is that share"
    bad = {"block_levels": "absent", "max_unverified_share": "0.25"}
    for field, value in (("block_levels", "absent"), ("block_levels", 7), ("block_levels", ["absent", 7]),
                         ("block_levels", ["nope"]), ("max_unverified_share", "0.25"), ("max_unverified_share", True),
                         ("max_unverified_share", 1.5), ("keys", "a|x"), ("keys", []), ("keys", [3]),
                         ("require_approved", "yes"), ("require_approved", 1), ("rationale", 5)):
        found = task_policy.problems({field: value})
        assert found and found[0]["field"] == field, (field, value, found)
        try:
            task_policy.build("codegen", {field: value})
            raise AssertionError(f"{field}={value!r} was built")
        except task_policy.TaskPolicyError as e:
            assert e.field == field and str(e).startswith(f"[tasks.codegen] {field}:"), str(e)
    assert task_policy.problems(bad) and task_policy.problems("not a table")[0]["message"] == "not a table"
    import gate
    assert list(task_policy.LEVELS) == gate.ORDER, "the validator's levels are the gate's"
    tasks_src = (HARNESS / "tasks.py").read_text(encoding="utf-8")
    assert "build(" in tasks_src and "set(" not in tasks_src and "float(" not in tasks_src, "the runtime builds through the validator"
    checker = (ROOT / "tools" / "check_subject.py").read_text(encoding="utf-8")
    assert "task_policy.problems(t)" in checker and "task_policy.LEVELS" in checker


def _subject(td: Path, levels: str) -> Path:
    root = td / "cargo_quote"
    shutil.copytree(ROOT / "subjects" / "cargo_quote", root, ignore=shutil.ignore_patterns("__pycache__"))
    toml = root / "subject.toml"
    text = toml.read_text(encoding="utf-8")
    assert text.count(CODEGEN_LEVELS) == 2   # codegen's, then design's
    toml.write_text(text.replace(CODEGEN_LEVELS, f"block_levels = {levels}", 1), encoding="utf-8")
    return root


def _env(root: Path, **kw) -> dict:
    return {**os.environ, "KG_SUBJECT": str(root), "KG_SUBJECTS": str(root.parent), "KG_STORE": "rdflib", "KG_CLOCK": "pinned",
            "PYTHONDONTWRITEBYTECODE": "1", "KG_REGISTER": os.environ.get("KG_REGISTER") or str(ROOT / "demo" / "register"), **kw}


def _gate_verdict(root: Path, **env) -> dict:
    """The MCP reader's gate_verdict over stdio, on S2 as of the record."""
    msgs = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                                                                           "clientInfo": {"name": "t", "version": "0"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "gate_verdict",
                                                                          "arguments": {"scenario": "S2", "as_of": "record"}}}]
    p = subprocess.run([sys.executable, str(HARNESS / "mcp_server.py")], input="".join(json.dumps(m) + "\n" for m in msgs),
                       capture_output=True, text=True, env=_env(root, KG_TODAY="2026-10-30", **env), timeout=300)   # the clock pinned (task-0075)
    out = [json.loads(line) for line in p.stdout.splitlines() if line.strip()]
    return next(r for r in out if r.get("id") == 2)["result"]


def test_the_reviewers_probe_a_string_and_an_integer_are_refused_a_list_blocks():
    with tempfile.TemporaryDirectory() as td:
        for name, levels in PROBE.items():
            root = _subject(Path(td) / name, levels)
            chk = subprocess.run([sys.executable, str(ROOT / "tools" / "check_subject.py"), str(root), "--json"],
                                 capture_output=True, text=True, env=_env(root), timeout=300)
            errs = [f for f in json.loads(chk.stdout)["findings"] if f["level"] == "error" and f["where"] == "[tasks.codegen]"]
            if name == "list":
                assert not errs, errs
                continue
            assert [f["rule"] for f in errs] == ["block-level"] and "not a list of gate levels" in errs[0]["message"], errs
            gate = subprocess.run([sys.executable, str(HARNESS / "gate_cli.py"), "--scenario", "S2", "--as-of", "record", "-f", "json"],
                                  capture_output=True, text=True, env=_env(root), timeout=300)
            assert gate.returncode == 2 and "[tasks.codegen] block_levels:" in gate.stderr and not gate.stdout.strip(), \
                (name, gate.returncode, gate.stderr[-400:])
            res = _gate_verdict(root)
            text = res["content"][0]["text"]
            assert res["isError"] and "[tasks.codegen] block_levels:" in text and "task policy" in text, (name, text)
        # the list blocks, as the subject's own policy does: S2 holds response|hold_presence absent
        need_rdflib()
        root = Path(td) / "list" / "cargo_quote"
        store = Path(td) / "list" / "store.ttl"
        gate = subprocess.run([sys.executable, str(HARNESS / "gate_cli.py"), "--scenario", "S2", "--as-of", "record", "--publish", "-f", "json"],
                              capture_output=True, text=True, env=_env(root, KG_RDFLIB_FILE=str(store)), timeout=600)
        rep = json.loads(gate.stdout)
        assert gate.returncode == 1 and rep["verdict"] == "BLOCKED" and rep["levels"]["response|hold_presence"] == "absent", \
            (gate.returncode, rep.get("verdict"), gate.stderr[-400:])
        res = _gate_verdict(root, KG_RDFLIB_FILE=str(store))
        assert not res["isError"] and res["structuredContent"]["verdict"] == "BLOCKED", res["content"][0]["text"][:400]
