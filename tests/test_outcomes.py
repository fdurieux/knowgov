"""task-0159 (V1 completion, AC #4): the test runner and the check tools write machine-readable outcomes,
pass, fail and skip per test or check with the skip's reason, when the job names a file for them, and
behave exactly as before when it does not."""
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

SUITE = '''
from tests._skip import Skip


def test_holds():
    pass


def test_breaks():
    raise AssertionError("two is not three")


def test_needs_a_thing():
    raise Skip("a-thing", "a thing is not installed here")
'''


def _clean_env(**kv) -> dict:
    env = {k: v for k, v in os.environ.items() if k not in ("KG_TEST_REPORT", "KG_OUTCOMES", "KG_TEST_REQUIRE")}
    env.update(kv)
    return env


def test_the_runner_writes_each_tests_outcome_and_the_skips_reason():
    with tempfile.TemporaryDirectory() as td:
        tests = Path(td) / "tests"
        tests.mkdir()
        for name in ("run_tests.py", "_skip.py", "__init__.py"):
            if (ROOT / "tests" / name).exists():
                shutil.copy(ROOT / "tests" / name, tests / name)
        (tests / "test_sample.py").write_text(SUITE, encoding="utf-8")
        report = Path(td) / "out" / "tests.json"
        p = subprocess.run([sys.executable, "tests/run_tests.py"], cwd=td, capture_output=True, text=True,
                           env=_clean_env(KG_TEST_REPORT=str(report)), timeout=120)
        assert p.returncode == 1 and "1/3 passed, 1 skipped, 1 failed" in p.stdout, p.stdout + p.stderr
        got = json.loads(report.read_text(encoding="utf-8"))
        by = {t["test"]: t for t in got["tests"]}
        assert got["schema"] == "test-outcomes" and got["totals"] == {"tests": 3, "passed": 1, "skipped": 1, "failed": 1}
        assert by["test_holds"]["outcome"] == "pass"
        assert by["test_breaks"]["outcome"] == "fail" and "two is not three" in by["test_breaks"]["reason"]
        skip = by["test_needs_a_thing"]
        assert skip["outcome"] == "skip" and skip["prerequisite"] == "a-thing" and "a thing is not installed here" in skip["reason"], skip
        # a required prerequisite's skip is a failure, and says so
        p = subprocess.run([sys.executable, "tests/run_tests.py"], cwd=td, capture_output=True, text=True,
                           env=_clean_env(KG_TEST_REPORT=str(report), KG_TEST_REQUIRE="a-thing"), timeout=120)
        row = {t["test"]: t for t in json.loads(report.read_text(encoding="utf-8"))["tests"]}["test_needs_a_thing"]
        assert row["outcome"] == "fail" and "required prerequisite missing" in row["reason"]
        # without KG_TEST_REPORT nothing is written
        report.unlink()
        subprocess.run([sys.executable, "tests/run_tests.py"], cwd=td, capture_output=True, text=True, env=_clean_env(), timeout=120)
        assert not report.exists()


TOOL = '''
import sys
sys.path.insert(0, {tools!r})
import _outcomes


def main():
    _outcomes.check("the first holds", True)
    _outcomes.check("the second breaks", False)
    _outcomes.skip("the third", "its backend is not here")
    {end}


if __name__ == "__main__":
    sys.exit(_outcomes.run(main))
'''


def test_a_check_tool_records_its_exit_and_each_check_with_the_skips_reason():
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "outcomes.jsonl"
        rows = []
        for end, code in (("return 1", 1), ("sys.exit('FAIL: the second broke')", 1), ("return 0", 0),
                          ("raise RuntimeError('the store did not answer')", 1)):
            script = Path(td) / "check_sample.py"
            script.write_text(TOOL.format(tools=str(ROOT / "tools"), end=end), encoding="utf-8")
            p = subprocess.run([sys.executable, str(script), "--flag"], capture_output=True, text=True,
                               env=_clean_env(KG_OUTCOMES=str(out)), timeout=60)
            assert p.returncode == code, (end, p.returncode, p.stderr)
        rows = [json.loads(x) for x in out.read_text(encoding="utf-8").splitlines()]
        assert [(r["exit"], r["outcome"]) for r in rows] == [(1, "fail"), (1, "fail"), (0, "pass"), (1, "error")], rows
        assert rows[0]["tool"] == "check_sample.py" and rows[0]["argv"] == ["--flag"]
        assert rows[0]["checks"] == [{"check": "the first holds", "outcome": "pass"},
                                     {"check": "the second breaks", "outcome": "fail"},
                                     {"check": "the third", "outcome": "skip", "reason": "its backend is not here"}]
        assert "the store did not answer" in rows[3]["error"]
        # without KG_OUTCOMES nothing is written
        out.unlink()
        subprocess.run([sys.executable, str(script)], capture_output=True, text=True, env=_clean_env(), timeout=60)
        assert not out.exists()


def test_every_check_tool_exits_through_the_outcome_helper():
    tools = sorted((ROOT / "tools").glob("check_*.py")) + sorted((ROOT / "demo" / "tools").glob("check_*.py")) \
        + [ROOT / "demo" / "tools" / "compare_deterministic.py"]
    for path in tools:
        main_block = path.read_text(encoding="utf-8").split('if __name__ == "__main__":', 1)[1]
        assert re.search(r"sys\.exit\(_outcomes\.run\(", main_block), f"{path.name} does not exit through _outcomes.run"


def test_the_workflows_name_the_outcome_files():
    wf = ROOT / ".github" / "workflows"
    for name in ("tests.yml", "harness.yml", "demo.yml"):
        text = (wf / name).read_text(encoding="utf-8")
        assert "KG_TEST_REPORT" in text or "KG_OUTCOMES" in text, name
    assert "KG_OUTCOMES: ${KG_OUTCOMES:-}" in (ROOT / "demo" / "docker-compose.yml").read_text(encoding="utf-8")
