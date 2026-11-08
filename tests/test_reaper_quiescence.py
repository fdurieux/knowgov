"""task-0233: the worker's reaper never takes one empty /proc scan for "nothing is left". A /proc listing is no
snapshot: a process that forks and exits between the listing and its read leaves a child the scan never saw, and
under load a fast fork chain outlived its job that way (1 of 260 hostile jobs in the emulated container). Here a
scan is made to miss a process it listed, deterministically: the reaper must still find it and kill it. In its
container the worker takes an empty scan only when its pid namespace's counter did not move across it; on a host,
the test path, it takes QUIET_SCANS empty scans in a row. tools/check_worker.py's EXEC-14 runs the hostile chain
against the real worker container."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness")]
from tests._skip import skip  # noqa: E402

# runs in a child process of its own, so the reaper (waitpid(-1)) reaps only that process's children
CHILD = r"""
import json, os, subprocess, sys, time
sys.path.insert(0, {harness!r})
import worker
mode = {mode!r}
victim = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])   # what a job left
time.sleep(0.2)
real, calls = worker._tree, []
def tree():
    t = real()
    calls.append(len(calls))
    if len(calls) == 1:
        t.pop(victim.pid, None)   # the first scan misses a process it listed, as the listing race does
    return t
worker._tree = tree
if mode == "counter":   # the worker as the init of its own pid namespace: the counter moved during the empty scan
    ticks = iter([100, 101] + [101] * 1000)
    worker._ns_counter = lambda: next(ticks)
t0 = time.monotonic()
killed = worker._reap_orphans(seconds=5)
took = time.monotonic() - t0
time.sleep(0.1)
alive = victim.poll() is None
victim.kill()
print(json.dumps({{"killed": killed, "alive": alive, "scans": len(calls), "took": took}}))
"""


def _run(mode: str) -> dict:
    if not Path("/proc/self/stat").exists():
        skip("linux-proc", "the reaper reads /proc")
    p = subprocess.run([sys.executable, "-c", CHILD.format(harness=str(ROOT / "harness"), mode=mode)],
                       capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, p.stderr[-2000:]
    return json.loads(p.stdout.strip().splitlines()[-1])


def test_a_scan_that_misses_a_listed_process_does_not_end_the_reaping():
    r = _run("host")
    assert not r["alive"] and r["killed"] >= 1, f"the reaper returned on a scan that missed a live process: {r}"
    import worker
    assert r["scans"] >= worker.QUIET_SCANS + 1, f"it took {worker.QUIET_SCANS} empty scans in a row before it returned: {r}"


def test_in_its_pid_namespace_an_empty_scan_counts_only_if_nothing_forked_across_it():
    r = _run("counter")
    assert not r["alive"] and r["killed"] >= 1, f"an empty scan across which the namespace forked ended the reaping: {r}"


def test_the_counter_is_the_namespaces_only_where_the_worker_is_its_init():
    import worker
    if os.getpid() != 1:
        assert worker._ns_counter() is None, "on a host the counter is the machine's, never the namespace's"
    src = (ROOT / "harness" / "worker.py").read_text(encoding="utf-8")
    body = src.split("def _reap_orphans(", 1)[1].split("\ndef ", 1)[0]
    assert "if not live:\n            return len(killed)" not in body, "one empty scan never ends the reaping"
    sec = (ROOT / "docs" / "security.md").read_text(encoding="utf-8")
    assert "task-0233" in sec and "QUIET_SCANS" in sec
