"""Task-0193, doc-0030 P6: demo.yml and harness.yml run every step under bash with pipefail. GitHub runs
``shell: bash`` as ``bash --noprofile --norc -eo pipefail {0}``, while a step with no shell runs
``bash -e {0}``: there, ``check_saved_queries.py | tee`` reports tee's exit and a failing query passes."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ("demo.yml", "harness.yml")
GITHUB_BASH = ["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c"]   # what shell: bash runs


def test_both_workflows_default_every_run_step_to_bash_and_none_overrides_it():
    for name in WORKFLOWS:
        text = (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
        assert re.search(r"(?m)^defaults:\n  run:\n    shell: bash\n", text), f"{name}: no defaults.run.shell bash"
        assert text.index("\ndefaults:") < text.index("\njobs:"), f"{name}: defaults must be top level"
        others = [ln.strip() for ln in text.splitlines() if re.match(r"\s+shell:", ln) and ln.strip() != "shell: bash"]
        assert not others, f"{name}: a step overrides the shell: {others}"


def test_under_that_shell_a_failing_command_before_a_pipe_fails_the_step():
    step = 'python3 -c "import sys; sys.exit(1)" | tee /dev/null; echo reached'
    with_pipefail = subprocess.run([*GITHUB_BASH, step], capture_output=True, text=True)
    assert with_pipefail.returncode == 1 and "reached" not in with_pipefail.stdout
    without = subprocess.run(["bash", "-e", "-c", step], capture_output=True, text=True)   # the old default
    assert without.returncode == 0 and "reached" in without.stdout, "the hazard P6 names: the exit is discarded"


def test_the_saved_queries_steps_pipe_through_tee_and_so_rest_on_pipefail():
    text = (ROOT / ".github" / "workflows" / "demo.yml").read_text(encoding="utf-8")
    assert len(re.findall(r"check_saved_queries\.py[^\n]*\| *tee", text)) >= 1


def test_the_held_store_check_reads_the_generation_where_it_is_defined_and_fails_without_one():
    """Task-0317: ``generation()`` lives on the store's publication (``_pub``), not on ``Neo4jStore``; the check once called
    ``_inner.generation()``, raised under ``set +e`` and compared two empty strings."""
    text = (ROOT / ".github" / "workflows" / "demo.yml").read_text(encoding="utf-8")
    assert "_inner.generation(" not in text
    assert "_inner._pub.generation()" in text
    store = (ROOT / "harness" / "store_neo4j.py").read_text(encoding="utf-8")
    assert re.search(r"(?m)^class _Unit\b", store) and "    def generation(self)" in store.split("class _Unit", 1)[1].split("\nclass ", 1)[0]
    assert re.search(r"before=\$\(gen\) \|\| ", text) and re.search(r"after=\$\(gen\) \|\| ", text)
