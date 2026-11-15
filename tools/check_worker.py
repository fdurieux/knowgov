"""The contained worker's boundary, proven on the real thing (task-0141.05, X1; decision-0012): run in
the stack job inside the app container, against the worker container compose starts beside it.

    docker compose exec -T app python tools/check_worker.py

Each check sends model-like code through the app's one execution path (harness/execution.py) and
reads what came back as untrusted data:
  EXEC-01  a secret-shaped variable set in the app, under a name no list knows, and the app's own
           store password, appear nowhere in the job's environment or output
           (task-0349: only once the probe ran, exit 0, answered in shape and carried its witnesses,
           the worker's PATH and the subject's KG_SUBJECT; the parent's environ read or refused by name)
  EXEC-02  a file only the app has is not visible; writes outside the job's folder fail; neither
           the app's runs nor an instance is mounted
  EXEC-03  a connection to the store and to the app fails: no network
  EXEC-10  the worker attests no_socket_escape, every probe refused, and a job opens no AF_VSOCK or
           AF_PACKET socket either: no path out that a network namespace does not confine
  EXEC-05  a job that spawns children and hangs is killed whole at its time; the next job runs
  EXEC-06  memory, processes, output and disk each stop at their bound, classified, the worker alive
  EXEC-07  a job without a fresh attestation is refused (a jobs folder no worker serves)
  host     the attestation names the worker's host (Linux, its kernel and machine, engine docker),
           read inside its container, and adds no check (task-0169)
  EXEC-09  the CargoQuote reference code and the J-F reference rebuild grade in the worker as the
           record says (all pass), no model called
  EXEC-11  (task-0203, R4) a 70-deep chain of processes, each in its own session, is killed whole once its
           job ends: the next job sees none of it and no other process of the worker's user but its own
           ancestry, within the job's time and the worker's reaping bound
  EXEC-12  (R7) a job that opens its runner's descriptors through /proc and has a detached child write a
           forged answer after it exits opens none, and the answer is the job's own
  EXEC-13  (R2) a job whose time runs out comes back as the kind's failed cell (nothing passed, the stage
           and the error kept), not an exception that would end the run
  attest   (R10) write_confined is attested with the kernel's Landlock ABI, and only from ABI 3
  EXEC-14  (task-0233) a hostile job's fast fork chain, each process living a millisecond in a session of its
           own, ends with its job: the next job finds the worker's pid namespace quiet and no process of it
A loosened worker (network on, a key in its environment) refusing to serve is run by the workflow,
which can start containers: ``python harness/worker.py --attest-only`` exits 3 there.
Exit 0 when every check holds, 1 otherwise; nothing here calls a model.
"""
from __future__ import annotations

import json
import os
import secrets
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import _outcomes  # noqa: E402 — task-0159: each check's outcome, when KG_OUTCOMES names a file
sys.path[:0] = [str(ROOT / "harness")]


def probe(code: str, seconds: float = 60) -> dict:
    import execution
    return execution.submit(Path(os.environ[execution.JOBS_VAR]), "probe", {}, {"probe.py": code.encode()}, seconds=seconds)


def last_json(r: dict):
    lines = [ln for ln in (r.get("stdout") or "").splitlines() if ln.strip()]
    return json.loads(lines[-1]) if lines else None


# EXEC-01's probe (task-0349): the job's environment on its own line, flushed, before the worker parent's is
# tried, so a refused /proc/1/environ can never suppress it; the parent's access is its own field, read or
# refused with the error's name, never silent.
EXEC01_PROBE = """import os, json, sys
print(json.dumps({'env': dict(os.environ)}), flush=True)
try:
    parent = {'read': open('/proc/1/environ', 'rb').read().decode('latin-1')}
except Exception as e:
    parent = {'refused': type(e).__name__}
print(json.dumps({'parent': parent}), flush=True)
"""


def _exec01_result(r) -> tuple[dict, str]:
    """The probe's result as an object and its stdout as text, whatever came back."""
    r = r if isinstance(r, dict) else {}
    return r, r.get("stdout") if isinstance(r.get("stdout"), str) else ""


def _exec01_lines(stdout: str) -> tuple:
    """The probe's two lines as (env, parent), each None unless it is the one-key object expected."""
    docs = []
    for ln in (ln for ln in stdout.splitlines() if ln.strip()):
        try:
            docs.append(json.loads(ln))
        except ValueError:
            docs.append(None)
    if len(docs) != 2:
        return None, None
    env, parent = ((d.get(k) if isinstance(d, dict) and set(d) == {k} else None) for d, k in zip(docs, ("env", "parent")))
    return env, parent


def _exec01_shaped(env, parent) -> tuple[bool, bool]:
    """The job's environment a non-empty object of strings; the parent's access read, or refused by a name."""
    env_ok = isinstance(env, dict) and bool(env) and all(isinstance(k, str) and isinstance(v, str) for k, v in env.items())
    parent_ok = isinstance(parent, dict) and len(parent) == 1 and (
        isinstance(parent.get("read"), str) or (isinstance(parent.get("refused"), str) and bool(parent["refused"])))
    return env_ok, parent_ok


def _exec01_witnessed(env: dict, path: str, subject_id: str) -> bool:
    """The job's PATH the worker's, and its KG_SUBJECT the absolute root of the app's subject."""
    subject = Path(env.get("KG_SUBJECT", ""))
    return env.get("PATH") == path and subject.is_absolute() and subject.parts[-2:] == ("subjects", subject_id)


def exec_01(r: dict, *, canaries: tuple[str, ...], store_pw: str, subject_id: str) -> list[tuple[bool, str]]:
    """EXEC-01's verdict on the probe's result ``r`` (untrusted), pure (task-0349, V-F2). The probe must have
    run: exit 0, its two lines, the job's environment a non-empty object of strings and the parent's access
    read or refused by name. Positive witnesses next: the job's PATH the worker's and its KG_SUBJECT the
    subject's root. Only then are the canaries' absence and the allowlist judged; each later check fails with
    the first, so an empty or failed probe never prints ok."""
    import worker
    r, stdout = _exec01_result(r)
    ran = r.get("exit") == 0 and r.get("stage") == "ok"
    env, parent = _exec01_lines(stdout)
    env_ok, parent_ok = _exec01_shaped(env, parent)
    shaped = ran and env_ok and parent_ok
    access = "read" if parent_ok and "read" in parent else parent
    out = [(ran, f"EXEC-01 the probe ran: exit {r.get('exit')!r}, stage {r.get('stage')!r}"),
           (shaped, f"EXEC-01 the probe's answer has its shape: the job's environment "
                    f"({len(env) if env_ok else 'missing'} variables) and the worker parent's access ({access!r})")]
    env = env if env_ok else {}
    witnessed = shaped and _exec01_witnessed(env, worker.JOB_PATH, subject_id)
    out.append((witnessed, f"EXEC-01 the job's environment carries its witnesses: PATH={env.get('PATH')!r} "
                           f"(expected {worker.JOB_PATH!r}), KG_SUBJECT={env.get('KG_SUBJECT', '')!r} "
                           f"(expected .../subjects/{subject_id})"))
    blob = stdout + json.dumps(env) + (json.dumps(parent) if parent_ok else "")
    leaked = [c for c in canaries if c and c in blob]
    out.append((witnessed and not leaked, "EXEC-01 an unlisted secret-shaped variable of the app never reaches the job"
                                          + (f": {len(leaked)} of its canaries leaked" if leaked else "")))
    out.append((witnessed and not (store_pw and store_pw in blob),
                "EXEC-01 the app's store password is in neither the job's nor the worker's environment"))
    out.append((witnessed and set(env) <= set(worker.JOB_ENV), f"EXEC-01 the job's environment is the allowlist: {sorted(env)}"))
    return out

def main() -> int:
    import execution
    failures: list[str] = []

    def check(cond, label):
        _outcomes.check(label, cond)
        print(("ok   " if cond else "FAIL ") + label, flush=True)
        if not cond:
            failures.append(label)

    jobs = Path(os.environ.get(execution.JOBS_VAR) or "")
    a = execution.attested(jobs)
    check(all(a["checks"].values()), f"the worker attests {', '.join(k for k, v in a['checks'].items() if v)}")
    # task-0169: and where it runs, as it read it inside its container: facts beside the checks, never one of them
    place = execution.placement()
    host = place.get("host") or {}
    check(place["attested"] and host.get("system") == "Linux" and bool(host.get("kernel")) and bool(host.get("machine"))
          and host.get("engine") == "docker" and set(a["checks"]) == set(execution.ATTEST_CHECKS),
          f"the worker attests its host, no check added: {host} (cloud reading: {place.get('cloud')})")

    # EXEC-01 (task-0349, V-F2: a failed or empty probe proves nothing, so it fails)
    from subject import SUBJECT
    name, value = "KG_UNLISTED_" + secrets.token_hex(4).upper(), "canary-" + secrets.token_hex(8)
    os.environ[name] = value
    store_pw = os.environ.get("KG_NEO4J_PASSWORD", "")
    r = probe(EXEC01_PROBE)
    os.environ.pop(name)
    for cond, label in exec_01(r, canaries=(name, value), store_pw=store_pw, subject_id=SUBJECT.id):
        check(cond, label)

    # EXEC-02
    canary = ROOT / "runs" / f"exec02-{secrets.token_hex(6)}"
    canary.parent.mkdir(parents=True, exist_ok=True)
    canary.write_text("host-only")
    try:
        r = probe(f"""
import json, os
out = {{}}
for p in [{str(canary)!r}, "/repo/runs", "/instance"]:
    out["exists " + p] = os.path.exists(p)
for p in ["/repo/x", "/etc/x", "/jobs/x", "/tmp/x", "/x"]:
    try:
        open(p, "w").write("x"); out["wrote " + p] = True
    except OSError as e:
        out["wrote " + p] = type(e).__name__
open("own.txt", "w").write("x"); out["own"] = os.path.exists("own.txt")
out["mounts"] = [ln.split()[1] for ln in open("/proc/mounts")]
print(json.dumps(out))""")
        got = last_json(r) or {}
        check(got.get(f"exists {canary}") is False, "EXEC-02 a file only the app has is not visible to the job")
        check(not any(got.get(f"wrote {p}") is True for p in ("/repo/x", "/etc/x", "/jobs/x", "/tmp/x", "/x")),
              f"EXEC-02 writes outside the job's folder fail: {[k for k, v in got.items() if k.startswith('wrote') and v is True]}")
        check(got.get("own") is True, "EXEC-02 the job's own folder is writable")
        mounts = got.get("mounts") or []
        check(not any(m.startswith(("/instance", "/repo/runs")) for m in mounts), f"EXEC-02 no instance and no app runs mounted: {mounts}")
    finally:
        canary.unlink(missing_ok=True)

    # EXEC-03
    r = probe("""
import json, socket
out = {}
for host, port in (("neo4j", 7687), ("app", 8080), ("1.1.1.1", 443)):
    try:
        socket.create_connection((host, port), timeout=3).close(); out[f"{host}:{port}"] = "connected"
    except OSError as e:
        out[f"{host}:{port}"] = type(e).__name__
print(json.dumps(out))""")
    got = last_json(r) or {}
    check(got and "connected" not in got.values(), f"EXEC-03 no connection leaves the worker: {got}")

    # EXEC-10
    probes = a.get("sockets") or {}
    check(a["checks"].get("no_socket_escape") is True and probes and all(v.startswith("refused ") for v in probes.values()),
          f"EXEC-10 the worker attests no_socket_escape, every probe refused: {probes}")
    r = probe("""
import json, socket
out = {}
for label, family, kind in (("AF_VSOCK", 40, socket.SOCK_STREAM), ("AF_PACKET", 17, socket.SOCK_RAW)):
    try:
        socket.socket(family, kind).close(); out[label] = "opened"
    except OSError as e:
        out[label] = type(e).__name__
print(json.dumps(out))""")
    got = last_json(r) or {}
    check(got and "opened" not in got.values(), f"EXEC-10 a job opens no AF_VSOCK or AF_PACKET socket: {got}")

    # EXEC-05
    marker = "exec05-" + secrets.token_hex(4)
    t0 = time.monotonic()
    r = probe(f"""
import subprocess, sys, time
subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(600)', '{marker}'])
subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(600)', '{marker}'], start_new_session=True)
time.sleep(600)""", seconds=5)
    check(r.get("stage") == "timeout" and time.monotonic() - t0 < 60, f"EXEC-05 a hanging job is killed at its time: {r}")
    # the marker is assembled at run time: a probe runs as ``python -c <code>``, so a literal marker in
    # this code would match the counting probe's own command line
    head, tail = marker.split("-", 1)
    r = probe(f"""
import os
marker = {head!r} + '-' + {tail!r}
mine = {{os.getpid(), os.getppid()}}
left = []
for pid in os.listdir('/proc'):
    if pid.isdigit() and int(pid) not in mine:
        try:
            if marker in open(f'/proc/{{pid}}/cmdline','rb').read().decode('latin-1'):
                left.append(pid + ' ' + open(f'/proc/{{pid}}/cmdline','rb').read().decode('latin-1').replace(chr(0), ' ')[:80])
        except OSError:
            pass
print(len(left), left)""")
    check((r.get("stdout") or "").strip().startswith("0 "), f"EXEC-05 no descendant of the killed job is left: {(r.get('stdout') or '')[-300:]}")

    # EXEC-06
    r = probe("b = bytearray(16 * 1024 ** 3)\nprint('allocated')")
    check("allocated" not in (r.get("stdout") or ""), f"EXEC-06 memory beyond the bound is refused: {r.get('stage')} {r.get('exit')}")
    r = probe("""
import subprocess, sys
n = 0
procs = []
try:
    for _ in range(1000):
        procs.append(subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(5)'])); n += 1
except OSError:
    pass
print(n)""", seconds=60)
    try:
        n = int((r.get("stdout") or "0").strip().splitlines()[-1])
    except ValueError:
        n = -1
    check(0 <= n < 1000, f"EXEC-06 processes stop at the bound: {n} started of 1000 asked")
    r = probe("import sys\nsys.stdout.write('x' * (8 * 1024 * 1024))\nprint()")
    check(len(r.get("stdout") or "") <= 20000, "EXEC-06 output is capped")
    r = probe("""
try:
    with open('big', 'wb') as fh:
        for _ in range(4096):
            fh.write(b'x' * (1024 * 1024))
    print('wrote 4 GiB')
except OSError as e:
    print(type(e).__name__)""", seconds=120)
    check("wrote 4 GiB" not in (r.get("stdout") or "") and r.get("stage") in ("ok", "killed"), f"EXEC-06 disk stops at its bound: {r}")
    check(probe("print('alive')")["stdout"].strip() == "alive", "EXEC-06 the worker serves the next job after each bound")

    # EXEC-07
    with tempfile.TemporaryDirectory() as td:
        try:
            execution.submit(Path(td), "probe", {}, {"probe.py": b"print(1)"}, seconds=5)
            check(False, "EXEC-07 a jobs folder no worker serves refuses the job")
        except execution.ExecutionRefused as e:
            check("has not attested" in str(e), "EXEC-07 a jobs folder no worker serves refuses the job")

    # EXEC-09
    code = (ROOT / "subjects" / "cargo_quote" / "vendor" / "stack_experiment" / "cargo_quote" / "reference_impl.py").read_text(encoding="utf-8")
    r = execution.submit(jobs, "suite", {"scenario": "S1"}, {"artifact.py": code.encode()}, subject="cargo_quote")
    check(r.get("ran") and r["passed"] == r["total"] > 0, f"EXEC-09 CargoQuote's reference code passes in the worker: {r.get('passed')}/{r.get('total')}")
    rebuild = ROOT / "subjects" / "jef_data_load" / "vendor" / "recreate_experiment" / "rebuilds" / "codex-2026-10-24"
    r = execution.submit(jobs, "suite_dir", {"scenario": "C"}, execution.collect(rebuild), subject="jef_data_load")
    failed = {k: f"{v.get('stage')}: {v.get('detail')}" for k, v in (r.get("per_scenario") or {}).items() if not v.get("passed")}
    check(r.get("ran") and r["passed"] == r["total"] > 0,
          f"EXEC-09 the J-F reference rebuild passes in the worker: {r.get('passed')}/{r.get('total')}"
          + "".join(f"\n       {k}: {v}" for k, v in failed.items()) + ("" if r.get("ran") else f"\n       {r}"))

    # EXEC-11, EXEC-12, EXEC-13, R10 (task-0203, doc-0030 F8): fixture code, never a model
    import worker
    import worker_probes
    mark = worker_probes.marker()
    t0 = time.monotonic()
    r = probe(worker_probes.chain(mark), seconds=60)
    took = time.monotonic() - t0
    check((r.get("stdout") or "").strip() == f"built {worker_probes.DEPTH}", f"EXEC-11 the job built its {worker_probes.DEPTH}-deep setsid chain: {r}")
    seen = (probe(worker_probes.survivors(mark)).get("stdout") or "").splitlines()
    left = seen[0].split() if seen else []
    check(left == ["0", "0"] and took < 60 + worker.REAP_S,
          f"EXEC-11 none of the chain and no other process of the worker's user outlives the job, within {60 + worker.REAP_S:g} s "
          f"({took:.1f} s): marked, others = {left}" + "".join(f"\n       {ln}" for ln in seen[1:]))
    genuine = "genuine-" + worker_probes.marker()
    r = probe(worker_probes.forge(genuine), seconds=30)
    out = (r.get("stdout") or "").split()
    check(out[:2] == [genuine, "0"] and "FORGED" not in json.dumps(r),
          f"EXEC-12 the job opens none of its runner's descriptors and cannot forge its answer: {r}")
    r = execution.run("suite", {"scenario": "S1"}, {"artifact.py": b"import time\ntime.sleep(600)\n"}, deadline=time.monotonic() + 5)
    check(r.get("ran") is True and r.get("passed") == 0 and r.get("stage") in execution.MODEL_STAGES and r.get("error"),
          f"EXEC-13 a job whose time ran out is the suite's failed cell, the run going on: {r}")
    a = execution.attested(jobs)
    check(isinstance(a.get("landlock_abi"), int) and a["landlock_abi"] >= worker.LANDLOCK_MIN_ABI and a["checks"]["write_confined"] is True,
          f"R10 write_confined is attested at Landlock ABI {a.get('landlock_abi')}, {worker.LANDLOCK_MIN_ABI} or later")

    exec_14(check)

    print("worker: " + ("every check holds" if not failures else f"{len(failures)} failure(s)"))
    return 1 if failures else 0


# EXEC-14's witness, two consecutive one-second windows of the worker's pid namespace (task-0233). A chain that
# outlived its job forks in every window: 121 to 800 pids a second in the emulated container, at 1 to 10 ms a
# process, under load too. The worker itself forks nothing while idle. What else may allocate pids there is a
# process entered from outside, Docker's healthcheck (``docker exec`` every 10 s, a handful of pids: 6 once, on
# main's stack job at ec4e693), and it runs once in ten seconds, so it lands in at most one of two windows. So a
# round fails when both windows allocate more than QUIET_PIDS, or when any process carries the chain's mark: a
# chain fails both, a healthcheck at most one.
QUIET_PIDS = 20


def quiet_round(witness: list[str]) -> bool:
    """One round's verdict from ``ns_quiet``'s line (two windows' allocations, the marked count, init)."""
    if len(witness) != 4 or not all(w.lstrip("-").isdigit() for w in witness):
        return False
    first, second, marked = (int(w) for w in witness[:3])
    return marked == 0 and not (first > QUIET_PIDS and second > QUIET_PIDS)


def exec_14(check, rounds: int = 5) -> None:
    """EXEC-14 (task-0233): a hostile job leaves a fast fork chain in a session of its own, each process living
    a millisecond, and the worker's reaper still ends it with its job. The witness is the next job's: the worker's
    pid namespace is quiet in at least one of two consecutive seconds after (``quiet_round``), and no process
    carries the chain's mark."""
    import worker_probes
    seen = []
    for _ in range(rounds):
        mark = worker_probes.marker()
        r = probe(worker_probes.fork_chain(mark), seconds=30)
        q = (probe(worker_probes.ns_quiet(mark), seconds=30).get("stdout") or "").split()
        seen.append(((r.get("stdout") or "").strip(), q))
    started = all(s == "started" for s, _ in seen)
    init = all(len(q) == 4 and q[3] == "1" for _, q in seen)
    check(started and init, f"EXEC-14 each hostile job started its chain, and the worker is the init of its own pid namespace, "
                            f"where its reaper confirms quiet by the namespace's counter: {seen}")
    check(all(quiet_round(q) for _, q in seen),
          f"EXEC-14 no chain outlives its job: in one of the two seconds after each, the namespace allocated at most {QUIET_PIDS} "
          f"pids, and no process carries the chain's mark (allocated, allocated, marked, init): {[q for _, q in seen]}")

if __name__ == "__main__":
    import _outcomes   # task-0314 R5
    _outcomes.help_exit(__doc__)
    sys.exit(_outcomes.run(main))
