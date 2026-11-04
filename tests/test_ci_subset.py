"""Task-0084: a pull request runs J-F on a named subset, every other event the full set.

The subset is one value, ``KG_JF_SCENARIOS``, set the same in harness.yml and demo.yml and named
in CLAUDE.md; every J-F command that takes ``--scenarios`` passes it; the full set runs on a push to
main, a nightly schedule and a manual dispatch. Standard library only: the workflows are read as text.
"""
from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WF = ROOT / ".github" / "workflows"
EXPR = re.compile(r"^\s+KG_JF_SCENARIOS: \$\{\{ github\.event_name == 'pull_request' && '([A-Z0-9,]+)' \|\| '' \}\}$", re.M)


def _subset(name: str) -> str:
    text = (WF / name).read_text(encoding="utf-8")
    (subset,) = EXPR.findall(text)
    return subset


def test_the_subset_is_one_value_named_in_both_workflows_and_claude_md():
    subset = _subset("harness.yml")
    assert subset == _subset("demo.yml") == "C,D3"
    scenarios = {s["id"] for s in tomllib.loads((ROOT / "subjects" / "jef_data_load" / "scenarios.toml").read_text(encoding="utf-8"))["scenario"]}
    assert set(subset.split(",")) < scenarios, "a proper subset of J-F's scenarios"
    assert f"KG_JF_SCENARIOS={subset}" in (ROOT / "CLAUDE.md").read_text(encoding="utf-8")


def test_every_jf_check_on_a_pull_request_takes_the_subset():
    for name in ("harness.yml", "demo.yml"):
        for line in (WF / name).read_text(encoding="utf-8").splitlines():
            if "jef_data_load" in line and re.search(r"check_(round_trip|mcp_server)\.py", line):
                assert '${KG_JF_SCENARIOS:+--scenarios "$KG_JF_SCENARIOS"}' in line, f"{name}: {line.strip()}"
            if "lighthouse_evidence.py" in line and not line.lstrip().startswith("#"):
                assert '${KG_JF_SCENARIOS:+--only "jef_data_load=$KG_JF_SCENARIOS"}' in line, f"{name}: {line.strip()}"


def test_the_full_set_runs_on_main_nightly_and_on_demand():
    for name in ("harness.yml", "demo.yml"):
        on = (WF / name).read_text(encoding="utf-8").split("\njobs:")[0]
        assert re.search(r"^  push:\n    branches: \[main\]", on, re.M), name
        assert re.search(r'^  schedule:\n    - cron: "17 3 \* \* \*"', on, re.M), name
        assert re.search(r"^  workflow_dispatch:", on, re.M), name
        assert "Budget (task-0084)" in on and "within 12 minutes" in on, name


CQ = re.compile(r"^\s+KG_CQ_SCENARIOS: \$\{\{ github\.event_name == 'pull_request' && '([A-Z0-9,]+)' \|\| '' \}\}$", re.M)


def test_cargo_quote_subsets_only_its_non_record_steps():
    text = (WF / "harness.yml").read_text(encoding="utf-8")
    (subset,) = CQ.findall(text)
    assert subset == "S1,S2,S6" and f"KG_CQ_SCENARIOS={subset}" in (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    flag = "KG_CQ_SCENARIOS"
    for line in text.splitlines():
        if line.lstrip().startswith("#") or "jef_data_load python" in line:
            continue
        if re.search(r"check_round_trip\.py|compare_deterministic\.py|run\.py --deterministic", line):
            assert flag not in line, f"the scored record runs whole: {line.strip()}"
        if re.search(r"check_mcp_server\.py$|check_mcp_server\.py \$|lighthouse_evidence\.py", line):
            assert '${KG_CQ_SCENARIOS:+' in line, line.strip()
