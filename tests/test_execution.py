"""Task-0141.05 (X1), decision-0012: the one path model output takes, tested here without a container:
the job protocol against a worker loop on this machine (its attestation stood in for, since this machine
is not a confined worker), the refusals, the result as untrusted data, the whole process group killed at
the time, the allowlisted environment, and the agent's symlink-safe writes (EXEC-04) and monotonic
deadline (EXEC-08). The containment itself (no network, no host files, the quotas, a loosened worker
refused) is proven on the real worker in the stack job: tools/check_worker.py."""
from __future__ import annotations

import contextlib
import json
import os
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness")]
import execution  # noqa: E402
import execution_guard  # noqa: E402

FAKE = {"ok": True, "checks": {c: True for c in execution.ATTEST_CHECKS}}
PUBLIC = {"KG_SUBJECT": str(ROOT / "subjects" / "cargo_quote"), "KG_SUBJECTS": str(ROOT / "subjects"),
          "KG_REGISTER": str(ROOT / "demo" / "register")}


@contextlib.contextmanager
def _env(**kw):
    names = set(kw) | {execution.JOBS_VAR, execution_guard.OPT_IN}
    keep = {k: os.environ.get(k) for k in names}
    for k in names:
        os.environ.pop(k, None)
    os.environ.update({k: v for k, v in kw.items() if v is not None})
    try:
        yield
    finally:
        for k, v in keep.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)


@contextlib.contextmanager
def _worker(attestation=FAKE):
    import worker
    with tempfile.TemporaryDirectory() as td:
        jobs, work = Path(td) / "jobs", Path(td) / "work"
        jobs.mkdir()
        work.mkdir()
        stop = threading.Event()
        t = threading.Thread(target=worker.serve, args=(jobs, work), kwargs={"attestation": attestation, "stop": stop}, daemon=True)
        t.start()
        end = time.monotonic() + 10
        while not (jobs / "attest.json").exists() and time.monotonic() < end:
            time.sleep(0.02)
        try:
            with _env(**PUBLIC, KG_WORKER_JOBS=str(jobs)):
                yield jobs
        finally:
            stop.set()
            t.join(timeout=10)


def _refused(fn) -> str:
    try:
        fn()
    except execution_guard.ExecutionRefused as e:
        return str(e)
    raise AssertionError("it ran")


def test_exec_07_no_backend_refuses_and_never_falls_back_to_the_host():
    import measures
    with tempfile.TemporaryDirectory() as td, _env(**PUBLIC):
        sentinel = Path(td) / "ran"
        code = f"open({str(sentinel)!r}, 'w').write('x')\n"
        why = _refused(lambda: measures.run_suite(code, "S1"))
        assert "no contained worker" in why and execution_guard.OPT_IN in why, why
        box = Path(td) / "box"
        box.mkdir()
        (box / "main.py").write_text(code)
        for fn in (lambda: measures.run_suite_dir(box, "S1"), lambda: measures.feedback_runner({}, "x")):
            assert "no contained worker" in _refused(fn)
        assert not sentinel.exists()
        assert execution.refusal() and "no contained worker" in execution.refusal()
        with _env(**PUBLIC, **{execution_guard.OPT_IN: "1"}):
            assert execution.backend() == "host" and execution.refusal() is None   # the only escape, named


def test_exec_07_an_absent_stale_loosened_or_malformed_attestation_refuses_the_job():
    with tempfile.TemporaryDirectory() as td:
        jobs = Path(td)
        assert "has not attested" in _refused(lambda: execution.attested(jobs))
        now = time.time()
        for att, want in (({**FAKE, "heartbeat": now - 60}, "stale"),
                          ({"ok": False, "checks": {**FAKE["checks"], "loopback_only": False}, "heartbeat": now}, "loopback_only"),
                          ({"ok": True, "checks": {**FAKE["checks"], "no_secret_variables": False}, "heartbeat": now}, "no_secret_variables"),
                          ({"ok": True, "heartbeat": now}, "malformed"), ([1, 2], "malformed")):
            (jobs / "attest.json").write_text(json.dumps(att))
            assert want in _refused(lambda: execution.attested(jobs)), att
            with _env(**PUBLIC, KG_WORKER_JOBS=str(jobs)):
                assert execution.refusal(), "an arms run refuses before its first model call"
        (jobs / "attest.json").write_text(json.dumps({**FAKE, "heartbeat": now}))
        assert execution.attested(jobs)["ok"]


def test_the_worker_attests_its_confinement_and_this_machine_is_not_a_worker():
    import worker
    a = worker.attest({"PATH": "/bin", "KG_SUBJECT": "x", "GPG_KEY": "public"})
    assert set(a["checks"]) == set(execution.ATTEST_CHECKS)
    for leaked in ({"OPENAI_API_KEY": "x"}, {"KG_NEO4J_PASSWORD": "x"}, {"KG_MODEL_API_KEY": "x"}, {"KG_PAGE_TOKEN": "x"},
                   {"AWS_SECRET_ACCESS_KEY": "x"}, {"LITELLM_MASTER_KEY": "x"}, {"KG_ANTHROPIC_KEY": "x"}):
        assert not worker.attest(leaked)["checks"]["no_secret_variables"], leaked
    assert worker.attest({"GPG_KEY": "public", "PYTHON_SHA256": "x"})["checks"]["no_secret_variables"]
    if os.getuid() != 65534:   # this machine: the worker refuses to serve here
        assert not a["ok"]
        with tempfile.TemporaryDirectory() as td:
            assert worker.serve(Path(td), Path(td)) == 3 and not json.loads((Path(td) / "attest.json").read_text())["ok"]


def test_exec_01_the_job_gets_an_allowlisted_environment_never_the_apps():
    with _worker() as jobs:
        os.environ["KG_CANARY_ANYNAME_7f3"] = "canary-value-91c"
        try:
            r = execution.submit(jobs, "probe", {}, {"probe.py": b"import os, json; print(json.dumps(dict(os.environ)))"}, seconds=30)
        finally:
            os.environ.pop("KG_CANARY_ANYNAME_7f3", None)
        env = json.loads(r["stdout"].strip().splitlines()[-1])
        assert set(env) <= {"PATH", "LANG", "HOME", "TMPDIR", "PYTHONDONTWRITEBYTECODE", "KG_SUBJECT", "KG_CLOCK"}, sorted(env)
        assert "canary-value-91c" not in r["stdout"]


def test_exec_05_a_hanging_job_and_the_child_it_left_are_killed_and_the_next_job_runs():
    marker = f"kg-exec05-{os.getpid()}"
    # one child stays in the job's group; another leaves it with setsid, as code trying to outlive the job would
    code = (f"import subprocess, sys, time\nsubprocess.Popen([sys.executable, '-c', 'import time; time.sleep(300)', '{marker}'])\n"
            f"subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(300)', '{marker}'], start_new_session=True)\n"
            "time.sleep(300)\n").encode()
    with _worker() as jobs:
        t0 = time.monotonic()
        r = execution.submit(jobs, "probe", {}, {"probe.py": code}, seconds=3)
        assert r.get("stage") == "timeout" and time.monotonic() - t0 < 20, r
        end = time.monotonic() + 10
        while time.monotonic() < end:
            left = [p for p in os.listdir("/proc") if p.isdigit() and _cmdline(p).find(marker) >= 0]
            if not left:
                break
            time.sleep(0.1)
        assert not left, left
        assert execution.submit(jobs, "probe", {}, {"probe.py": b"print('next')"}, seconds=30)["stdout"].strip() == "next"


def _cmdline(pid: str) -> str:
    try:
        return Path(f"/proc/{pid}/cmdline").read_bytes().decode("utf-8", "replace")
    except OSError:
        return ""


def test_the_result_is_untrusted_data_capped_and_checked():
    for kind, bad in (("suite", {"ran": True, "passed": 2, "total": 1, "per_scenario": {"a": {"passed": True}}}),
                      ("suite", {"ran": "yes", "passed": 0, "total": 0, "per_scenario": {}}),
                      ("suite", [1]), ("feedback", {"passed": True, "total": 1, "features": {}}),
                      ("nope", {})):
        assert "malformed" in _refused(lambda: execution.check_result(kind, bad)), (kind, bad)
    ok = execution.check_result("suite", {"ran": True, "passed": 1, "total": 1,
                                          "per_scenario": {"a": {"passed": True, "stage": "ok", "detail": "x" * 5000, "extra": "drop"}}})
    assert len(ok["per_scenario"]["a"]["detail"]) == 200 and "extra" not in ok["per_scenario"]["a"]
    with tempfile.TemporaryDirectory() as td:
        jobs = Path(td)
        (jobs / "attest.json").write_text(json.dumps({**FAKE, "heartbeat": time.time()}))

        def answer(payload: bytes):
            end = time.monotonic() + 10
            while time.monotonic() < end:
                for jd in jobs.glob("job-*"):
                    (jd / "result.json").write_bytes(payload)
                    return
                time.sleep(0.01)
        for payload, want in ((b"x" * (execution.RESULT_MAX + 1), "exceeds"), (b"\xff\xfe", "not JSON"), (b'{"ran": 1}', "malformed")):
            t = threading.Thread(target=answer, args=(payload,))
            t.start()
            with _env(**PUBLIC):
                assert want in _refused(lambda: execution.submit(jobs, "suite", {"scenario": "S1"}, {"artifact.py": b"x"}, seconds=5))
            t.join()
        assert not list(jobs.glob("job-*")), "the job's folder is removed whatever the answer"


def test_a_job_naming_a_path_or_an_unknown_subject_is_refused_by_the_worker():
    import worker
    with tempfile.TemporaryDirectory() as td:
        jd = Path(td) / "job-x"
        (jd / "files").mkdir(parents=True)
        for subject in ("../../etc", "/tmp", "no_such_subject", 7):
            (jd / "job.json").write_text(json.dumps({"kind": "probe", "subject": subject, "payload": {}}))
            assert worker.run_job(jd, Path(td))["stage"] == "job", subject
        (jd / "job.json").write_text(json.dumps({"kind": "shell", "subject": "cargo_quote"}))
        assert worker.run_job(jd, Path(td))["stage"] == "job"


def test_exec_09_the_reference_code_grades_the_same_in_the_worker_as_in_process():
    import measures
    from subject import SUBJECT
    if SUBJECT.id != "cargo_quote":
        from tests._skip import skip
        skip("cargo-quote-subject", "J-F's whole suite takes minutes; the stack job runs it in the real worker (tools/check_worker.py)")
    code = (SUBJECT.root / "vendor" / "stack_experiment" / "cargo_quote" / "reference_impl.py").read_text(encoding="utf-8")
    with _worker():
        via = measures.run_suite(code, SUBJECT.order[0])
    assert via == measures.local_run_suite(code, SUBJECT.order[0]) and via["passed"] == via["total"] > 0, via


def test_exec_04_a_symlink_at_any_step_of_an_agent_write_is_refused_and_the_target_untouched():
    import agent
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        outside = td / "outside"
        outside.mkdir()
        sentinel = outside / "sentinel.txt"
        sentinel.write_text("untouched")
        box = agent.Sandbox(td / "box")
        (box.root / "linkdir").symlink_to(outside, target_is_directory=True)
        (box.root / "linkfile.txt").symlink_to(sentinel)
        (box.root / "a").mkdir()
        (box.root / "a" / "b").symlink_to(outside, target_is_directory=True)
        for rel in ("linkdir/sentinel.txt", "linkfile.txt", "a/b/new.txt", "linkdir/x/y.txt"):
            try:
                box.write(rel, "overwritten")
            except ValueError:
                continue
            raise AssertionError(f"{rel} written through a link")
        assert sentinel.read_text() == "untouched" and sorted(p.name for p in outside.iterdir()) == ["sentinel.txt"]
        assert box.write("ok/deep/file.py", "print(1)") == "ok/deep/file.py" and (box.root / "ok/deep/file.py").read_text() == "print(1)"
        assert "linkfile.txt" not in box.files() and "ok/deep/file.py" in box.files()
        assert "linkfile.txt" not in execution.collect(box.root) and "ok/deep/file.py" in execution.collect(box.root)
        # replaced during the write: a directory swapped for a link between two writes is refused too
        (box.root / "ok" / "deep").rename(box.root / "ok" / "gone")
        (box.root / "ok" / "deep").symlink_to(outside, target_is_directory=True)
        try:
            box.write("ok/deep/file.py", "swapped")
        except ValueError:
            pass
        else:
            raise AssertionError("written through a swapped-in link")
        assert sorted(p.name for p in outside.iterdir()) == ["sentinel.txt"]


def test_exec_08_a_stalled_or_trickling_stream_stops_at_the_monotonic_deadline():
    import agent

    def stalled():
        yield 1
        time.sleep(30)
        yield 2

    def trickle():
        while True:
            time.sleep(0.2)
            yield "x"
    t0 = time.monotonic()
    got = []
    try:
        for x in agent.bounded(stalled(), deadline=None, idle=0.5):
            got.append(x)
    except TimeoutError as e:
        assert "nothing for" in str(e)
    else:
        raise AssertionError("a stalled stream was waited out")
    assert got == [1] and time.monotonic() - t0 < 3
    t0 = time.monotonic()
    try:
        for _ in agent.bounded(trickle(), deadline=time.monotonic() + 1.0, idle=5.0):
            pass
    except TimeoutError as e:
        assert "deadline" in str(e)
    assert 0.9 < time.monotonic() - t0 < 3, "the idle bound alone never stops a trickle; the total one does"
    keep = time.time
    try:   # a wall-clock jump moves nothing: the deadline is monotonic
        time.time = lambda: keep() + 10 ** 6
        assert list(agent.bounded(iter([1, 2, 3]), deadline=time.monotonic() + 5, idle=5)) == [1, 2, 3]
    finally:
        time.time = keep
    seen = {}

    def responder(messages, tools, deadline=None):
        seen["deadline"] = deadline
        return {"content": json.dumps({"decision": "ABSTAIN"}), "tool_calls": [], "usage": {}}
    with tempfile.TemporaryDirectory() as td:
        agent.run("s", "u", sandbox=Path(td), read_text=lambda p: "", feedback=lambda r, f: {}, tag="t", responder=responder,
                  limits={"seconds": 50})
    assert isinstance(seen["deadline"], float) and 45 < seen["deadline"] - time.monotonic() <= 50, seen


def test_a_job_cannot_write_the_jobs_folder_so_it_cannot_forge_a_result_or_the_attestation():
    """Landlock (decision-0012's untrusted results): the job's child writes only beneath its own folder."""
    import worker
    if worker.landlock_abi() < 1:
        from tests._skip import skip
        skip("landlock", "this kernel has no Landlock; the worker attests write_confined false and refuses to serve")
    with _worker() as jobs:
        code = f"""
import glob, json, os
out = {{}}
for target in [{str(jobs / "attest.json")!r}] + glob.glob({str(jobs / "job-*")!r}) + [{str(jobs / "forged")!r}]:
    path = target if target.endswith(("json", "forged")) else os.path.join(target, "result.json")
    try:
        open(path, "w").write(json.dumps({{"ran": True, "passed": 99, "total": 99, "per_scenario": {{}}}}))
        out[path] = "written"
    except OSError as e:
        out[path] = type(e).__name__
open("mine.txt", "w").write("ok")   # its own folder stays writable
print(json.dumps(out))
""".encode()
        r = execution.submit(jobs, "probe", {}, {"probe.py": code}, seconds=30)
        tried = json.loads(r["stdout"].strip().splitlines()[-1])
        assert tried and all(v == "PermissionError" for v in tried.values()), tried
        assert json.loads((jobs / "attest.json").read_text())["ok"] and not (jobs / "forged").exists()
