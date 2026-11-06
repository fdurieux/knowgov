"""task-0159 (V1 completion): every CI job has a timeout above its worst run seen, never at the
12-minute budget, so a slow, honest run is not killed; a change to the instance template runs the
stack job; every container a workflow starts is torn down on failure as on success; a server a check
tool starts ends with it."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"

# The worst execution of each job, in minutes: first attempts, job start to completion (not the run's
# span, which includes queueing), from the GitHub API over 2026-11-04..06 (task-0159's notes). rdflib's
# is a push to main, which runs the full J-F set; stack's likewise.
OBSERVED_WORST = {("tests.yml", "tests"): 2.9, ("harness.yml", "rdflib"): 71.8,
                  ("demo.yml", "stack"): 25.4, ("demo.yml", "publish"): 0.9}
BUDGET = 12   # task-0084: a pull request's rdflib and stack, uncontended


def _jobs(path: Path) -> dict[str, str]:
    """Each job's block of text in a workflow, by name (two-space indented keys under ``jobs:``)."""
    text = path.read_text(encoding="utf-8")
    body = text.split("\njobs:\n", 1)[1]
    parts = re.split(r"(?m)^  ([A-Za-z0-9_-]+):\s*$", body)
    return {parts[i]: parts[i + 1] for i in range(1, len(parts), 2)}


def test_every_job_has_a_timeout_above_its_worst_run_and_never_at_the_budget():
    seen = set()
    for wf in ("tests.yml", "harness.yml", "demo.yml"):
        for job, block in _jobs(WORKFLOWS / wf).items():
            m = re.search(r"(?m)^    timeout-minutes: (\d+)", block)
            assert m, f"{wf} {job}: no timeout-minutes"
            minutes = int(m.group(1))
            worst = OBSERVED_WORST.get((wf, job))
            assert worst is not None, f"{wf} {job}: no recorded worst case; measure it before setting a timeout"
            assert minutes >= max(1.5 * worst, worst + 10) and minutes > BUDGET, (wf, job, minutes, worst)
            seen.add((wf, job))
    assert seen == set(OBSERVED_WORST), sorted(set(OBSERVED_WORST) ^ seen)


def test_a_change_to_the_instance_template_runs_the_stack_job():
    text = (WORKFLOWS / "demo.yml").read_text(encoding="utf-8")
    on = text.split("\njobs:\n", 1)[0]
    for event in ("pull_request", "push"):
        block = on.split(f"\n  {event}:\n", 1)[1].split("\n  schedule:", 1)[0].split("\n  workflow_dispatch:", 1)[0]
        assert '- "instance/**"' in block, event


def test_every_container_a_workflow_starts_is_torn_down_on_failure_as_on_success():
    for wf in sorted(WORKFLOWS.glob("*.yml")):
        text = wf.read_text(encoding="utf-8")
        for job, block in _jobs(wf).items():
            steps = re.split(r"(?m)^      - ", block)
            ups = [i for i, s in enumerate(steps) if re.search(r"docker compose [^\n]*\bup\b", s)]
            if ups:
                downs = [i for i, s in enumerate(steps) if "if: always()" in s and "docker compose down" in s]
                assert downs and max(downs) > max(ups), f"{wf.name} {job}: compose started without an always() teardown after it"
        for line in re.findall(r"docker run [^\n]*", text):
            assert "--rm" in line and not re.search(r"\s-d\b|--detach", line), f"{wf.name}: {line[:80]}"


def test_a_server_a_check_tool_starts_ends_with_it():
    """Every check tool that starts a process holds it to a bounded wait and kills it after."""
    for path in sorted((ROOT / "tools").glob("check_*.py")) + sorted((ROOT / "demo" / "tools").glob("check_*.py")):
        code = re.sub(r"(?s)'''.*?'''|\"\"\".*?\"\"\"", "", path.read_text(encoding="utf-8"))
        if "subprocess.Popen(" not in code:
            continue
        assert "def _stop(" in code and "p.kill()" in code, f"{path.name} starts a process it may not stop"
