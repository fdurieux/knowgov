"""task-0250 (doc-0033): the advisory SonarQube scan. The workflow runs on a release tag, on demand with a ref
and on its own pull requests, pins the server and the scanner, needs no secret and fails only when the scan
cannot run; the profile is pinned in the repository without the two rules that fight the stdlib runner; the
coverage comes from tools/coverage_stdlib.py through a stdlib converter; the delta reads the previous release
and the triage baseline, each accepted finding with its reason. Standard library only."""
from __future__ import annotations

import json
import re
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUALITY = ROOT / "tools" / "quality"
WORKFLOW = ROOT / ".github" / "workflows" / "quality.yml"
sys.path[:0] = [str(QUALITY), str(ROOT / "tools")]
import coverage_stdlib  # noqa: E402
import coverage_xml  # noqa: E402
import report  # noqa: E402


def test_the_workflow_runs_on_a_tag_on_demand_with_a_ref_and_on_its_own_pull_requests():
    text = WORKFLOW.read_text(encoding="utf-8")
    on = text.split("\npermissions:", 1)[0]
    assert re.search(r'push:\n    tags: \["v\*"\]', on), "on a release tag, as release.yml"
    assert re.search(r"workflow_dispatch:\n    inputs:\n      ref:\n", on) and "required: true" in on
    paths = on.split("pull_request:", 1)[1]
    for p in (".github/workflows/quality.yml", "tools/quality/**", "tools/coverage_stdlib.py"):
        assert f'"{p}"' in paths, p


def test_the_server_and_the_scanner_are_pinned_and_no_secret_is_needed():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert re.search(r"image: sonarqube:\d+\.\d+\.\d+\.\d+-community@sha256:[0-9a-f]{64}\n", text)
    version = re.search(r"SONAR_SCANNER_VERSION: (\d+\.\d+\.\d+\.\d+)\n", text)
    assert version and re.search(r"SONAR_SCANNER_SHA256: [0-9a-f]{64}\n", text) and "sha256sum -c" in text
    assert "${{ secrets." not in text, "the token is minted on the service container, never a repository secret"
    assert "::add-mask::" in text and "api/user_tokens/generate" in text and "api/users/change_password" in text
    assert "127.0.0.1:9000:9000" in text, "the server is published on loopback only"


def test_it_fails_only_when_the_scan_cannot_run():
    text = WORKFLOW.read_text(encoding="utf-8")
    steps = re.split(r"(?m)^      - ", text.split("\n    steps:\n", 1)[1])
    advisory = [s for s in steps if s.startswith("name: The previous release") or s.startswith("name: The debt delta")]
    assert len(advisory) == 2 and all("continue-on-error: true" in s for s in advisory)
    cov = next(s for s in steps if s.startswith("name: Coverage"))
    assert cov.count("|| echo \"::warning::") == 2, "a red suite or no coverage does not stop the scan"
    assert "sonar.qualitygate.wait=false" in (QUALITY / "sonar-project.properties").read_text(encoding="utf-8")
    for required in ("tests.yml", "harness.yml", "demo.yml"):   # never a step of the gating workflows
        assert "sonar" not in (ROOT / ".github" / "workflows" / required).read_text(encoding="utf-8").lower(), required


def test_the_profile_is_pinned_without_the_two_rules_that_fight_the_stdlib_runner():
    prof = ET.parse(QUALITY / "knowgov-python.xml").getroot()
    assert prof.findtext("name") == "knowgov" and prof.findtext("language") == "py"
    keys = {r.findtext("key") for r in prof.iter("rule")}
    assert "S9073" not in keys and "S8997" not in keys, "split composite assertions; the pytest monkeypatch fixture"
    assert {"S3776", "S1192", "S5332", "S4790", "S2068"} <= keys, "complexity, duplication and the security rules stay"
    assert "knowgov-python.xml" in WORKFLOW.read_text(encoding="utf-8")


def test_the_exclusions_leave_out_what_is_not_ours():
    props = (QUALITY / "sonar-project.properties").read_text(encoding="utf-8")
    excl = re.search(r"sonar\.exclusions=((?:.*\\\n)*.*)", props).group(1).replace("\\\n", "").replace(" ", "")
    for pattern in ("demo/register/**", "demo/model/**", "subjects/*/vendor/**", "subjects/*/record/**",
                    "tools/fixtures/**", "backlog/**", "docs/**", "**/*.dockerignore"):
        assert pattern in excl.split(","), pattern
    assert "sonar.docker.file.patterns=**/Dockerfile" in props


def test_coverage_converts_per_line_with_branches_and_refuses_a_report_without_lines():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "m.py"
        f.write_text("def f(x):\n    if x:\n        return 1\n    return 2\n", encoding="utf-8")
        lines, branches, _t = coverage_stdlib.denominator(f)
        taken = {b for b in branches if b[2] == "taken"}
        detail = coverage_stdlib.line_detail(f, lines, {1, 2, 3}, branches, taken)
        assert detail["lines_hit"] == sorted({1, 2, 3} & lines) and detail["branch_lines"] == {"2": [2, 1]}, detail
    rep = {"modules": [{"module": "harness/m.py", **detail}],
           "totals": {"statements": 0, "statements_hit": 0, "statement_pct": 0, "branches": 0, "branches_hit": 0, "branch_pct": 0}}
    root = ET.fromstring(coverage_xml.convert(rep))
    cells = {int(e.get("lineNumber")): e.attrib for e in root.iter("lineToCover")}
    assert root.get("version") == "1" and root.find("file").get("path") == "harness/m.py"
    assert cells[2]["covered"] == "true" and cells[2]["branchesToCover"] == "2" and cells[2]["coveredBranches"] == "1"
    assert cells[4]["covered"] == "false"
    try:
        coverage_xml.convert({"modules": [{"module": "a.py", "statements": 1}]})
    except ValueError as e:
        assert "--lines" in str(e)
    else:
        raise AssertionError("a report without line detail must be refused")


def _issue(rule, path, line, msg="m", t="CODE_SMELL", sev="MAJOR"):
    return {"rule": rule, "path": path, "line": line, "message": msg, "type": t, "severity": sev}


def test_the_baseline_accepts_at_most_its_count_and_every_entry_has_a_reason():
    base = [{"rule": "python:S5332", "path": "a.py", "count": 2, "reason": "namespaces"}]
    issues = [_issue("python:S5332", "a.py", n) for n in (3, 1, 2)] + [_issue("python:S5332", "b.py", 1)]
    open_, acc = report.split(issues, base)
    assert [i["line"] for i in acc] == [1, 2] and sorted((i["path"], i["line"]) for i in open_) == [("a.py", 3), ("b.py", 1)]
    shipped = json.loads((QUALITY / "baseline.json").read_text(encoding="utf-8"))["accepted"]
    assert shipped and all(e.get("reason") and e.get("rule") and e.get("path") for e in shipped)
    assert all((ROOT / e["path"]).is_file() for e in shipped), "every accepted finding names a file that exists"


def test_the_delta_names_new_and_gone_issues_hotspots_and_measures_against_the_previous_release():
    cx = "Refactor this function to reduce its Cognitive Complexity from {} to the 15 allowed."
    with tempfile.TemporaryDirectory() as d:
        now, was = Path(d, "now"), Path(d, "was")
        for p, issues, meas, ref in ((now, [_issue("python:S3776", "x.py", 5, cx.format(40)), _issue("python:S1192", "y.py", 9)],
                                      {"coverage": "60.0"}, "v0.10.0"),
                                     (was, [_issue("python:S3776", "x.py", 4, cx.format(40)), _issue("python:S1481", "z.py", 2)],
                                      {"coverage": "57.5"}, "v0.9.0")):
            p.mkdir()
            (p / "issues.json").write_text(json.dumps(issues), encoding="utf-8")
            (p / "measures.json").write_text(json.dumps(meas), encoding="utf-8")
            (p / "meta.json").write_text(json.dumps({"ref": ref}), encoding="utf-8")
        md = report.delta(now, was, [])
        assert "Compared with **v0.9.0**" in md and "New since v0.9.0: 1; gone: 1" in md
        assert "`python:S1192` +1" in md and "| 40 | x.py:5 | same |" in md, md
        assert "| coverage | 60.0 | 57.5 | +2.5 |" in md
        first = report.delta(now, None, [])
        assert "this run is the baseline" in first and "New since" not in first


def test_the_accepting_comment_is_the_form_the_analyser_reads():
    doc = (ROOT / "docs" / "quality-scan.md").read_text(encoding="utf-8")
    assert "# NOSONAR(S" in doc and "never a gate" in doc
    assert "# NOSONAR: " not in re.sub(r"`# NOSONAR: <why>` suppresses nothing", "", doc), \
        "the colon form suppresses nothing and is itself flagged (python:S7632)"
