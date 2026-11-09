"""task-0257 (decision-0032, G9-17): the subject-check schema names every rule its checker emits.

``tools/check_subject.py`` emitted ``require-approved`` and ``rationale`` (task-0242's ``task_policy`` codes) and
``attestation`` (``check_attestations``, task-0199) as finding rules the schema's ``finding.rule`` enum lacked, so
the report on such a manifest failed its own schema, from the CLI's ``--json`` and from the MCP ``subject_check``
alike. Here every code the checker and ``task_policy.problems`` can emit is read from their source and run
through the schema, so a new code without its enum entry fails the suite; and the reports on J-F, the example
instance and a manifest with ``require_approved = "yes"`` and ``rationale = 5`` validate."""
from __future__ import annotations

import ast
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "harness")]
import check_instance  # noqa: E402
import check_subject  # noqa: E402
import example_instance  # noqa: E402
import schema_check  # noqa: E402

SCHEMA = schema_check.load("subject-check")
REGISTER = ROOT / "demo" / "register"
LEVEL = {"error": "error", "warning": "warning"}   # Report's finding methods and the level each writes


def _calls(path: Path) -> list[tuple[str, ast.expr]]:
    """(method, first argument) for every ``rep.error``, ``rep.warning`` and ``rep.note`` call in ``path``."""
    out = []
    for n in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ("error", "warning", "note")
                and isinstance(n.func.value, ast.Name) and n.func.value.id == "rep" and n.args):
            out.append((n.func.attr, n.args[0]))
    return out


def _policy_codes() -> set[str]:
    """Every ``"code"`` a ``task_policy`` or ``scenario_ids`` problem can carry, read from their dict literals."""
    codes = set()
    for n in (n for f in ("task_policy.py", "scenario_ids.py")
              for n in ast.walk(ast.parse((ROOT / "harness" / f).read_text(encoding="utf-8")))):
        if isinstance(n, ast.Dict):
            for k, v in zip(n.keys, n.values):
                if isinstance(k, ast.Constant) and k.value == "code":
                    assert isinstance(v, ast.Constant) and isinstance(v.value, str), ast.unparse(v)
                    codes.add(v.value)
    return codes


def emitted() -> dict[str, set[str]]:
    """{"error": codes, "warning": codes, "note": codes} that check_subject.py can write into a report."""
    out = {"error": set(), "warning": set(), "note": set()}
    dynamic = []
    for method, arg in _calls(ROOT / "tools" / "check_subject.py"):
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            out[method].add(arg.value)
        else:
            dynamic.append((method, ast.unparse(arg)))
    # the codes not written as literals are task_policy's (problems, name_problem), passed through as rep.error(p["code"], ...)
    assert dynamic and set(dynamic) == {("error", "p['code']")}, f"a rule code check_subject.py computes: add its source here {dynamic}"
    out["error"] |= _policy_codes()
    return out


def _report(findings: list[dict], notes: list[dict]) -> dict:
    rep = json.loads(json.dumps(check_subject.check(ROOT / "subjects" / "minimal", REGISTER, run_yield=False)))
    rep.update(findings=findings, notes=notes, exit_code=1 if findings else 0)
    return rep


def test_every_rule_code_the_checker_can_emit_is_in_the_schema():
    codes = emitted()
    assert {"require-approved", "rationale", "attestation"} <= codes["error"], codes   # task-0257's three
    assert "task-class" in codes["error"], codes                                         # task-0278's
    assert "scenario-id" in codes["error"], codes                                        # task-0295's
    assert {"required", "block-level", "share"} <= codes["error"] and "zero-yield" in codes["warning"], codes
    findings = [{"level": LEVEL[m], "rule": c, "where": "w", "message": "m", "fix": "f"}
                for m in ("error", "warning") for c in sorted(codes[m])]
    notes = [{"rule": c, "where": "w", "message": "m"} for c in sorted(codes["note"])]
    assert schema_check.validate(_report(findings, notes), SCHEMA) == []
    finding_enum = set(SCHEMA["$defs"]["finding"]["properties"]["rule"]["enum"])
    note_enum = set(SCHEMA["$defs"]["note"]["properties"]["rule"]["enum"])
    assert codes["error"] | codes["warning"] <= finding_enum and codes["note"] <= note_enum


def test_a_code_missing_from_the_enum_fails_the_schema():
    bad = _report([{"level": "error", "rule": "no-such-rule", "where": "w", "message": "m", "fix": "f"}], [])
    assert any("no-such-rule" in e for e in schema_check.validate(bad, SCHEMA))


def _variant(td: Path, edit) -> Path:
    root = td / "minimal"
    shutil.copytree(ROOT / "subjects" / "minimal", root)
    p = root / "subject.toml"
    p.write_text(edit(p.read_text(encoding="utf-8")), encoding="utf-8")
    return root


def test_the_reports_the_validation_pass_named_validate():
    for sid in ("jef_data_load", "cargo_quote", "minimal"):
        rep = json.loads(json.dumps(check_subject.check(ROOT / "subjects" / sid, REGISTER)))
        assert schema_check.validate(rep, SCHEMA) == [], (sid, schema_check.validate(rep, SCHEMA))
    with tempfile.TemporaryDirectory() as td:
        root = _variant(Path(td), lambda m: re.sub(r"(\[tasks\.[a-z]+\]\n)", r'\1require_approved = "yes"\nrationale = 5\n', m, count=1))
        rep = json.loads(json.dumps(check_subject.check(root, REGISTER, run_yield=False)))
        assert {f["rule"] for f in rep["findings"]} >= {"require-approved", "rationale"}, rep["findings"]
        assert schema_check.validate(rep, SCHEMA) == [], schema_check.validate(rep, SCHEMA)
    with tempfile.TemporaryDirectory() as td:
        root = _variant(Path(td), lambda m: m + '\n[verification]\nauthored = { scope = "authored" }\n')
        rep = json.loads(json.dumps(check_subject.check(root, REGISTER, run_yield=False)))
        assert "attestation" in {f["rule"] for f in rep["findings"]}, rep["findings"]
        assert schema_check.validate(rep, SCHEMA) == [], schema_check.validate(rep, SCHEMA)


def test_the_example_instances_subject_reports_validate():
    with tempfile.TemporaryDirectory() as td:
        inst = Path(td) / "instance"
        example_instance.build(inst)
        rep = json.loads(json.dumps(check_instance.check(inst)))
        found = []

        def walk(o):
            if isinstance(o, dict):
                if o.get("tool") == "check_subject":
                    found.append(o)
                    return
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(rep)
        assert found, "the instance check carries a subject report per subject"
        for sub in found:
            assert schema_check.validate(sub, SCHEMA) == [], (sub["subject"], schema_check.validate(sub, SCHEMA))
