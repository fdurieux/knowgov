"""Task-0083: harness/annotate.py turns each report KG_REPORT can hold into GitHub workflow commands,
a job-summary table, GitLab code quality and SARIF. The reports here are schema-valid samples of
S6's change (a suspect derived output, stale statements, a key below verified); the converter runs
on S6's real reports in harness.yml (the action) and tools/check_ci_wrappers.py (the GitLab job)."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness"))
import annotate  # noqa: E402
import schema_check  # noqa: E402


def _f(severity, kind, key, ref, message, related=()):
    return {"severity": severity, "kind": kind, "key": key, "level": "invalidated" if kind != "suspect_derived" else None,
            "flags": [], "ref": ref, "related": list(related), "message": message}


GATE = {
    "schema_version": 2, "tool": "knowgov gate", "subject": "s", "scenario": "S6", "task": "codegen", "store": "rdflib",
    "loaded": True, "verdict": "BLOCKED", "why": "1 required key(s) at a blocking level: P2|surcharge (invalidated)",
    "threshold": "major",
    "findings": [
        _f("blocker", "key", "P2|surcharge", None, "P2|surcharge is invalidated: the task cannot proceed on it"),
        _f("blocker", "suspect_derived", None, "derived:S1:G:run1", "derived:S1:G:run1 used 1 statement(s) now invalidated", ["A:dt:P2|surcharge@v1"]),
        _f("major", "stale", "P2|surcharge", "A:dt:P2|surcharge@v1", "invalidated by v2, 100%, line one\nline two"),
        _f("minor", "key", "P5|note", None, "P5|note is proposed"),
        _f("info", "stale", "P3|order", "A:dt:P3|order@v1", "superseded by A:dt:P3|order#1@v1", ["A:dt:P3|order#1@v1"]),
    ],
    "counts": {"blocker": 2, "critical": 0, "major": 1, "minor": 1, "info": 1},
    "keys": {"total": 3, "below_verified": 2, "flagged": 0}, "conflicts": 0,
    "stale": ["A:dt:P2|surcharge@v1", "A:dt:P3|order@v1"], "suspect_derived": ["derived:S1:G:run1"],
    "levels": {"P2|surcharge": "invalidated"}, "baseline": None, "exit_code": 1,
}

TRACE = {
    "schema_version": 1, "tool": "knowgov trace", "command": "check", "store": "rdflib", "task": "codegen", "commit": "abc",
    "code_root": "code", "ledger": "ledger.json", "changed": ["impl.py", "notify.py"], "registered": [],
    "gate": {"task": "codegen", "verdict": "BLOCKED", "why": "P2|surcharge (invalidated)"},
    "findings": [
        {"severity": "blocker", "kind": "suspect", "app": "APP-0001", "path": "impl.py", "ref": "derived:code@abc:impl.py",
         "related": ["A:dt:P2|surcharge@v1"], "message": "impl.py (APP-0001) was built from 1 statement now invalidated"},
        {"severity": "major", "kind": "unmapped", "app": None, "path": "notify.py", "ref": None, "related": [], "message": "notify.py is unmapped"},
        {"severity": "minor", "kind": "drift", "app": "APP-0001", "path": "impl.py", "ref": "derived:code@abc:impl.py", "related": [], "message": "impl.py changed"},
        {"severity": "major", "kind": "gate:stale", "app": "APP-0001", "path": None, "ref": "A:dt:P2|surcharge@v1", "related": [], "message": "codegen: stale"},
    ],
    "counts": {"blocker": 1, "critical": 0, "major": 2, "minor": 1, "info": 0}, "threshold": "major", "exit_code": 1,
}

PRELOAD = {
    "schema_version": 1, "tool": "knowgov preload check", "instance": "/i", "scope": "changed", "threshold": "major",
    "files": [
        {"file": "artefacts/sequence-diagrams/q.puml", "kind": "sequence-diagrams", "tool": "pumllint", "state": "findings", "why": "1 finding",
         "findings": [{"rule": "PUML001", "severity": "major", "line": 7, "message": "unbalanced"}]},
        {"file": "artefacts/stories/s.md", "kind": "stories", "tool": "none", "state": "unchecked", "why": "no linter here", "findings": []},
    ],
    "linters": [], "counts": {"clean": 0, "findings": 1, "unchecked": 1, "cannot_run": 0, "skipped": 0}, "exit_code": 1, "note": "form only",
}


def test_the_samples_are_the_reports_their_schemas_pin():
    for rep, name in ((GATE, "gate-report"), (TRACE, "trace-report"), (PRELOAD, "preload-report")):
        assert not schema_check.validate(rep, schema_check.load(name)), name


def test_github_commands_error_at_the_threshold_and_escape_what_the_runner_parses():
    root = Path("/w")
    out = annotate.convert(GATE, "github", subject=root / "inst" / "subjects" / "s", root=root).splitlines()
    assert [ln.split(" ", 1)[0] for ln in out] == ["::error", "::error", "::error", "::warning", "::notice"]
    assert all("file=inst/subjects/s/subject.toml,line=1," in ln for ln in out), out[0]
    assert "title=knowgov gate suspect_derived derived%3AS1%3AG%3Arun1 (blocker)::" in out[1]
    assert out[2].endswith("::invalidated by v2, 100%25, line one%0Aline two"), out[2]


def test_a_finding_on_code_points_at_the_file_under_the_instance_and_the_rest_at_subject_toml():
    inst, root = Path("/w/inst"), Path("/w")
    fs = annotate.findings(TRACE, instance=inst, subject=inst / "subjects" / "s", root=root)
    assert [f["path"] for f in fs] == ["inst/code/impl.py", "inst/code/notify.py", "inst/code/impl.py", "inst/subjects/s/subject.toml"]
    assert [annotate.level(f["severity"], TRACE["threshold"]) for f in fs] == ["error", "error", "warning", "error"]
    pre = annotate.findings(PRELOAD, instance=inst, root=root)
    assert [(f["path"], f["line"], f["severity"]) for f in pre] == [
        ("inst/artefacts/sequence-diagrams/q.puml", 7, "major"), ("inst/artefacts/stories/s.md", 1, "info")]


def test_gitlab_code_quality_keeps_the_ladder_and_a_distinct_fingerprint_per_issue():
    for rep in (GATE, TRACE, PRELOAD):
        issues = json.loads(annotate.convert(rep, "gitlab", instance=Path("/w/inst"), subject=Path("/w/inst/s"), root=Path("/w")))
        assert len(issues) == len(annotate.findings(rep))
        assert len({i["fingerprint"] for i in issues}) == len(issues)
        for i in issues:
            assert set(i) == {"description", "check_name", "fingerprint", "severity", "location"}
            assert i["severity"] in annotate.LADDER and i["location"]["path"] and i["location"]["lines"]["begin"] >= 1
    issues = json.loads(annotate.convert(GATE, "gitlab"))
    assert [i["severity"] for i in issues] == [f["severity"] for f in GATE["findings"]]
    assert issues[0]["location"]["path"] == "."   # no subject named: the repository, still a valid issue
    again = json.loads(annotate.convert(GATE, "gitlab"))
    assert [i["fingerprint"] for i in issues] == [i["fingerprint"] for i in again], "stable across runs, so GitLab can diff the base"


def test_sarif_is_one_run_with_a_rule_per_kind():
    doc = json.loads(annotate.convert(TRACE, "sarif", instance=Path("/w/inst"), root=Path("/w")))
    assert doc["version"] == "2.1.0" and len(doc["runs"]) == 1
    run = doc["runs"][0]
    ids = [r["id"] for r in run["tool"]["driver"]["rules"]]
    assert ids == sorted({f["kind"] for f in TRACE["findings"]})
    assert [r["level"] for r in run["results"]] == ["error", "error", "warning", "error"]
    assert all(ids[r["ruleIndex"]] == r["ruleId"] for r in run["results"])
    assert run["results"][0]["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "inst/code/impl.py"


def test_the_summary_states_the_verdict_and_one_row_per_finding():
    text = annotate.convert(GATE, "summary")
    assert "### knowgov gate: exit 1" in text and "BLOCKED: 1 required key(s)" in text
    rows = [ln for ln in text.splitlines() if ln.startswith("| ") and not ln.startswith("| severity")]
    assert len(rows) == len(GATE["findings"]) and "P2\\|surcharge" in rows[0]


def test_the_command_exits_2_on_what_is_not_a_knowgov_report():
    with tempfile.TemporaryDirectory() as td:
        bad, good = Path(td) / "bad.json", Path(td) / "gate.json"
        bad.write_text('{"tool": "something else"}', encoding="utf-8")
        good.write_text(json.dumps(GATE), encoding="utf-8")
        cli = [sys.executable, str(ROOT / "harness" / "annotate.py")]
        p = subprocess.run([*cli, str(bad), "-t", "github"], capture_output=True, text=True)
        assert p.returncode == 2 and "not a knowgov" in p.stderr
        p = subprocess.run([*cli, str(Path(td) / "none.json"), "-t", "gitlab"], capture_output=True, text=True)
        assert p.returncode == 2
        p = subprocess.run([*cli, str(good), "-t", "sarif", "-o", str(Path(td) / "out.sarif")], capture_output=True, text=True)
        assert p.returncode == 0 and json.loads((Path(td) / "out.sarif").read_text())["version"] == "2.1.0"
