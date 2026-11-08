"""task-0203 (doc-0030 F8: R2, R3, R4, R7, R10): the worker's job isolation and the run folder's lifecycle,
on a worker loop on this machine. The worker runs in a process of its own, as uid 65534 when the tests run as
root (as in its container), with its real Landlock domain where the kernel has one; its attestation is
stood in for, since this machine is not a confined container. The stack job proves the same probes on the
real worker container (tools/check_worker.py EXEC-11 to EXEC-13)."""
from __future__ import annotations

import contextlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tools")]
import execution  # noqa: E402
import worker_probes  # noqa: E402
from tests._skip import skip  # noqa: E402

PUBLIC = {"KG_SUBJECT": str(ROOT / "subjects" / "cargo_quote"), "KG_SUBJECTS": str(ROOT / "subjects"),
          "KG_REGISTER": str(ROOT / "demo" / "register")}

SERVE = """
import os, sys, threading
sys.path.insert(0, {harness!r})
if os.getuid() == 0:   # as in its container: uid 65534, no privilege
    os.setgroups([])
    os.setgid(65534)
    os.setuid(65534)
import execution, worker
fake = {{"ok": True, "checks": {{c: True for c in execution.ATTEST_CHECKS}}}}
sys.exit(worker.serve({jobs!r}, {work!r}, attestation=fake))
"""


@contextlib.contextmanager
def _env(**kw):
    keep = {k: os.environ.get(k) for k in kw}
    os.environ.update({k: v for k, v in kw.items() if v is not None})
    for k, v in kw.items():
        if v is None:
            os.environ.pop(k, None)
    try:
        yield
    finally:
        for k, v in keep.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)


@contextlib.contextmanager
def _worker():
    """A worker loop in its own process, as uid 65534 when the tests run as root."""
    if not hasattr(os, "fork") or not Path("/proc/self/stat").exists():
        skip("linux-proc", "the worker reads /proc")
    td = tempfile.mkdtemp(prefix="kg-worker-")
    os.chmod(td, 0o755)
    jobs, work = Path(td) / "jobs", Path(td) / "work"
    for d in (jobs, work):
        d.mkdir()
        os.chmod(d, 0o777)
    # as root the worker drops to uid 65534, which may not reach a virtual environment in a private folder:
    # it runs on the interpreter the environment was made from (the worker needs only the standard library)
    python = getattr(sys, "_base_executable", sys.executable) if os.getuid() == 0 else sys.executable
    # RLIMIT_NPROC counts every process of the user: in its container the worker's uid owns only the worker's
    # processes, but a CI runner's user owns dozens more, so the job's process bound here leaves the probe's
    # 70-deep chain room beside them (the stack's worker keeps its default, 128)
    env = {k: v for k, v in os.environ.items() if not k.startswith(("OPENAI", "GEMINI", "AWS", "KG_ANTHROPIC", "KG_MODEL_API"))}
    env["KG_WORKER_PROCESSES"] = "4096"
    p = subprocess.Popen([python, "-c", SERVE.format(harness=str(ROOT / "harness"), jobs=str(jobs), work=str(work))],
                         env=env,
                         stderr=subprocess.PIPE, start_new_session=True)
    try:
        end = time.monotonic() + 15
        while not (jobs / "attest.json").exists() and time.monotonic() < end:
            if p.poll() is not None:
                raise AssertionError(f"the worker did not start: {p.stderr.read().decode()[-500:]}")
            time.sleep(0.05)
        with _env(**PUBLIC, KG_WORKER_JOBS=str(jobs)):
            yield jobs, p.pid
    finally:
        try:
            os.killpg(p.pid, 9)
        except OSError:
            pass
        p.wait(timeout=10)
        shutil.rmtree(td, ignore_errors=True)


def _probe(code: str, seconds: float = 60) -> dict:
    return execution.submit(Path(os.environ[execution.JOBS_VAR]), "probe", {}, {"probe.py": code.encode()}, seconds=seconds)


def test_r4_a_deep_setsid_chain_is_killed_whole_after_its_job_within_the_bound():
    mark = worker_probes.marker()
    with _worker() as (_jobs, pid):
        # the worker's user may own more than the worker (a CI runner's user owns the runner and the tests):
        # what it owned before the job is set aside, and every process born since must be gone
        uid = next(int(line.split()[1]) for line in open(f"/proc/{pid}/status") if line.startswith("Uid:"))
        before = worker_probes.user_processes(uid)
        t0 = time.monotonic()
        r = _probe(worker_probes.chain(mark), seconds=60)
        took = time.monotonic() - t0
        assert r.get("stage") == "ok" and r["stdout"].strip() == f"built {worker_probes.DEPTH}", r
        marked, others = map(int, _probe(worker_probes.survivors(mark, before))["stdout"].split())
    assert marked == 0, f"{marked} of the {worker_probes.DEPTH}-deep chain outlived its job"
    assert others == 0, f"{others} process(es) of the worker's user born during the job outlived it"
    import worker
    assert took < 20 + worker.REAP_S, f"the job and its reaping took {took:.1f} s"


def test_r7_the_job_cannot_forge_its_answer():
    if os.getuid() != 0 and os.geteuid() != os.getuid():
        skip("same-uid", "the forge is a same-user attack")
    mark = "genuine-" + worker_probes.marker()
    with _worker():
        r = _probe(worker_probes.forge(mark), seconds=30)
    assert r.get("stdout", "").split()[:1] == [mark] and "FORGED" not in json.dumps(r), r
    assert r["stdout"].split()[1] == "0", f"the job opened its runner's descriptors: {r['stdout']!r}"


def test_r2_a_job_stage_error_is_the_kinds_failed_cell_and_the_run_goes_on():
    """A job that hangs past its time: the worker answers a timeout, and ``run`` turns that answer into the
    suite's failed cell rather than raising. The job is CargoQuote's whichever subject the suite runs under
    (its oracle needs nothing beyond the standard library, so the code's hang is what the worker meets)."""
    hang = {"artifact.py": b"import time\ntime.sleep(600)\n"}
    with _worker() as (jobs, _pid):
        raw = execution.submit(jobs, "suite", {"scenario": "S1"}, hang, seconds=4, subject="cargo_quote")
        assert raw.get("stage") == "timeout" and "error" in raw, raw
        keep = execution.submit
        execution.submit = lambda *a, **k: raw   # run()'s own path, on the worker's real answer
        try:
            r = execution.run("suite", {"scenario": "S1"}, hang, deadline=time.monotonic() + 4)
        finally:
            execution.submit = keep
    assert r["ran"] is True and r["passed"] == 0 and r["stage"] in execution.MODEL_STAGES and r["error"], r
    for kind, want in (("suite", {"ran", "passed", "total", "per_scenario"}), ("suite_dir", {"ran", "passed", "total", "per_scenario"}),
                       ("feedback", {"features", "passed", "total"}), ("probe", {"exit", "stdout"})):
        cell = execution.failed_cell(kind, {"error": "the job exceeded its 4 s", "stage": "timeout"})
        assert want <= set(cell) and cell["stage"] == "timeout", (kind, cell)
    assert set(execution.MODEL_STAGES) == {"timeout", "killed", "output", "harness_error"}, "a job the app wrote wrong still raises"


def test_r10_write_confined_is_attested_only_from_landlock_abi_3_and_the_page_says_why():
    import worker
    keep = worker.landlock_abi
    try:
        for abi, want in ((0, False), (1, False), (2, False), (3, True), (7, True)):
            worker.landlock_abi = lambda abi=abi: abi
            a = worker.attest({"PATH": "/bin"}, socket_probe=lambda: {"ok": True, "probes": {}})
            assert a["checks"]["write_confined"] is want and a["landlock_abi"] == abi, (abi, a["checks"])
    finally:
        worker.landlock_abi = keep
    with tempfile.TemporaryDirectory() as td:
        a = {"ok": False, "checks": {c: True for c in execution.ATTEST_CHECKS}, "landlock_abi": 2, "heartbeat": time.time()}
        a["checks"]["write_confined"] = False
        (Path(td) / "attest.json").write_text(json.dumps(a))
        try:
            execution.attested(Path(td))
            raise AssertionError("an ABI 2 worker was taken as confined")
        except execution.ExecutionRefused as e:
            why = str(e)
    assert "write_confined" in why and "Landlock is ABI 2" in why and "ABI 3" in why, why
    import re
    page = (ROOT / "demo" / "app" / "index.html").read_text(encoding="utf-8")
    pattern = re.search(r"const abi = /(.+?)/\.exec\(w\.why", page).group(1).replace("\\\\", "\\")
    assert re.search(pattern, why).group(1) == "2" and "3 needed" in page


def test_r3_a_reused_out_folder_carries_nothing_into_a_fresh_run():
    try:
        import run
    except ModuleNotFoundError as e:   # run.py imports the pins (pyshacl, rdflib): the rdflib job runs this
        skip("rdflib", f"{e.name} is not installed")
    with tempfile.TemporaryDirectory() as td:
        out = Path(td)
        (out / "S1").mkdir()
        left = out / "S1" / "run1_G.py"
        left.write_text("print('an earlier attempt')\n")

        class Args:
            stage2_derived = None
            resume = False
        derived = {"from_scenario": "S1", "file": "run1_G.py"}
        assert run.stage2_derived(Args, out, "S6", derived) is None, "a leftover file is never stage 2's input"
        Args.resume = True
        assert run.stage2_derived(Args, out, "S6", derived) == left, "under --resume the earlier attempt's cells are this run's"
        Args.resume, Args.stage2_derived = False, str(out / "named.py")
        assert run.stage2_derived(Args, out, "S6", derived) == out / "named.py"
        Args.stage2_derived = None
        run.WRITTEN.add(left.resolve())
        try:
            assert run.stage2_derived(Args, out, "S6", derived) == left, "the file this invocation wrote"
        finally:
            run.WRITTEN.discard(left.resolve())
        # usage.json adds an earlier attempt's only under --resume
        (out / "usage.json").write_text(json.dumps({"calls": 7, "tokens": 70, "retries": [], "per_call": [{}] * 7}))
        run._write_usage(out, {})
        assert json.loads((out / "usage.json").read_text())["calls"] == run.arms.usage()["calls"]
        (out / "usage.json").write_text(json.dumps({"calls": 7, "tokens": 70, "retries": [], "per_call": [{}] * 7}))
        run._write_usage(out, {}, resume=True)
        assert json.loads((out / "usage.json").read_text())["calls"] == 7 + run.arms.usage()["calls"]
    src = (ROOT / "harness" / "run.py").read_text(encoding="utf-8")
    agent_cell = src.split("    def one_agent(i: int) -> dict:", 1)[1]
    assert agent_cell.index("shutil.rmtree(box, ignore_errors=True)") < agent_cell.index("agent.run("), "a fresh cell empties its sandbox first"
    assert "--stage2-derived" in src and "stage2_derived(args, out_root, sc, derived)" in src
