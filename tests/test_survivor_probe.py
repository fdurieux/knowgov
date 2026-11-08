"""task-0232: the worker's survivor probe (tools/worker_probes.py ``survivors``, EXEC-11 and R4) counts a process
of the worker's user only when a second full scan, about a second after the first, also finds one, and trusts no
command line. The stack's EXEC-11 once counted the Docker healthcheck (``worker.py --attest-only``) in the instant
it exited, its command line already empty; and a job could carry ``--attest-only`` in its own argv to drop out
of the count. Here the probe runs as the worker's user beside a helper process of that user."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "tools")]
import worker_probes  # noqa: E402
from tests._skip import skip  # noqa: E402

ROOTED = hasattr(os, "getuid") and os.getuid() == 0
UID = 65534 if ROOTED else (os.getuid() if hasattr(os, "getuid") else None)
PY = getattr(sys, "_base_executable", sys.executable) if ROOTED else sys.executable   # 65534 reads no private venv


def _as_user(args, **kw):
    if ROOTED:
        kw.update(user=UID, group=UID, extra_groups=[])
    return subprocess.Popen(args, cwd="/", **kw)


def _probe(helper, *, on_first_scan=None) -> list[str]:
    """Run ``survivors`` as the worker's user, beside ``helper`` (that user too), with what that user owned
    before set aside; ``on_first_scan`` runs once the probe has scanned once and before it scans again."""
    if not Path("/proc/self/stat").exists():
        skip("linux-proc", "the probe reads /proc")
    before = worker_probes.user_processes(UID)
    code = worker_probes.survivors(worker_probes.marker(), before)
    with tempfile.TemporaryDirectory() as td:
        os.chmod(td, 0o777)
        flag = Path(td) / "first-scan"
        code = code.replace("    time.sleep(1.0)", f"    open({str(flag)!r}, 'w').close()\n    time.sleep(1.0)")
        h = _as_user([PY, "-I", "-c", helper[0], *helper[1:]], start_new_session=True)
        try:
            time.sleep(0.2)   # the helper is up
            p = _as_user([PY, "-I", "-c", code], stdout=subprocess.PIPE, text=True)
            if on_first_scan is not None:
                end = time.monotonic() + 20
                while not flag.exists() and p.poll() is None and time.monotonic() < end:
                    time.sleep(0.005)
                if flag.exists():
                    on_first_scan(h)
            out, _ = p.communicate(timeout=60)
        finally:
            try:
                os.killpg(h.pid, 9)
            except OSError:
                pass
            h.wait(timeout=10)
    return out.splitlines()


def test_a_process_caught_exiting_is_not_counted():
    """The healthcheck's case: found by the first scan, gone (a zombie, then reaped) by the second."""
    def end(h):
        h.kill()
        h.wait(timeout=10)
    out = _probe(["import time; time.sleep(30)"], on_first_scan=end)
    assert out[0].split() == ["0", "0"], f"a process that ended between the two scans was counted: {out}"


def test_a_lingerer_is_counted_whatever_its_command_line_says():
    out = _probe(["import time; time.sleep(30)", "--attest-only"])
    assert out[0].split()[1] == "1", f"a process carrying --attest-only in its own argv dropped out of the count: {out}"
    assert len(out) == 2 and out[1].startswith("OTHER ") and "--attest-only" in out[1], out
    pid, ppid, state = out[1].split()[1:4]
    assert pid.isdigit() and ppid.isdigit() and state not in ("Z", "X"), out


def test_a_chain_of_short_lived_forks_is_counted():
    """Each process forks the next and exits: no pid lives through both scans, but the chain does."""
    chain = ("import os, time\nend = time.time() + 8\nwhile time.time() < end:\n"
             "    if os.fork():\n        os._exit(0)\n    time.sleep(0.05)\n")
    out = _probe([chain])
    assert int(out[0].split()[1]) >= 1, f"a fork chain slipped through the two scans: {out}"
    assert all(ln.startswith("OTHER ") for ln in out[1:]) and len(out) >= 2, out


def test_the_probe_trusts_no_command_line_and_names_what_it_counts():
    code = worker_probes.survivors(worker_probes.marker())
    assert "--attest-only" not in code, "a job writes its own command line"
    assert "ppid != 0" in code, "a process entered from outside the pid namespace (docker exec) is not the job's"
    assert code.count("window()") == 3 and "time.sleep(1.0)" in code, "counted only when a second scan finds one too"
    check = (ROOT / "tools" / "check_worker.py").read_text(encoding="utf-8")
    assert 'left == ["0", "0"]' in check and "worker_probes.survivors(mark))" in check, "EXEC-11 stays strict, no snapshot"
