"""Task-0141.01 (ENV-04): the runner reports a test whose prerequisite is absent as skipped, never as
passed, and a prerequisite the job names in KG_TEST_REQUIRE fails when it is absent. Run on a copy of
the runner over a three-test sample, so the suite does not run itself."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SAMPLE = '''from tests._skip import skip, need_rdflib


def test_runs():
    assert True


def test_needs_a_live_hook():
    skip("hook-live", "KG_HOOK_LIVE is not 1")


def test_needs_rdflib():
    need_rdflib()
'''


def _run(require: str) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory() as td:
        tests = Path(td) / "tests"
        tests.mkdir()
        for f in ("run_tests.py", "_skip.py"):
            shutil.copy(HERE / f, tests / f)
        (tests / "test_sample.py").write_text(SAMPLE)
        env = {k: v for k, v in os.environ.items() if k not in ("KG_TEST_REQUIRE", "PYTHONPATH")}
        env["KG_TEST_REQUIRE"] = require
        env["PYTHONPATH"] = str(Path(td) / "nowhere")   # no store_rdflib on the path: the rdflib test lacks it
        return subprocess.run([sys.executable, "tests/run_tests.py"], cwd=td, env=env, capture_output=True, text=True, timeout=60)


def test_env_04_an_absent_optional_prerequisite_is_a_skip_and_never_prints_pass():
    p = _run("")
    assert p.returncode == 0, p.stdout + p.stderr
    lines = p.stdout.splitlines()
    assert "PASS test_runs" in lines
    assert "SKIP test_needs_a_live_hook (hook-live: KG_HOOK_LIVE is not 1)" in lines
    assert any(ln.startswith("SKIP test_needs_rdflib (rdflib: ") for ln in lines), lines
    assert not any(ln.startswith("PASS test_needs") for ln in lines), lines
    assert lines[-1] == "1/3 passed, 2 skipped, 0 failed", lines[-1]


def test_env_04_an_absent_prerequisite_the_job_requires_fails_it():
    p = _run("rdflib")
    assert p.returncode == 1, p.stdout + p.stderr
    lines = p.stdout.splitlines()
    assert any(ln.startswith("FAIL test_needs_rdflib (required prerequisite missing: rdflib: ") for ln in lines), lines
    assert "SKIP test_needs_a_live_hook (hook-live: KG_HOOK_LIVE is not 1)" in lines
    assert lines[-1] == "1/3 passed, 1 skipped, 1 failed", lines[-1]
