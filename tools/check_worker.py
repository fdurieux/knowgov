"""The contained worker's boundary, proven on the real thing (task-0141.05, X1; decision-0012): run in
the stack job inside the app container, against the worker container compose starts beside it.

    docker compose exec -T app python tools/check_worker.py

Each check sends model-like code through the app's one execution path (harness/execution.py) and
reads what came back as untrusted data:
  EXEC-01  a secret-shaped variable set in the app, under a name no list knows, and the app's own
           store password, appear nowhere in the job's environment or output
  EXEC-02  a file only the app has is not visible; writes outside the job's folder fail; neither
           the app's runs nor an instance is mounted
  EXEC-03  a connection to the store and to the app fails: no network
  EXEC-10  the worker attests no_socket_escape, every probe refused, and a job opens no AF_VSOCK or
           AF_PACKET socket either: no path out that a network namespace does not confine
  EXEC-05  a job that spawns children and hangs is killed whole at its time; the next job runs
  EXEC-06  memory, processes, output and disk each stop at their bound, classified, the worker alive
  EXEC-07  a job without a fresh attestation is refused (a jobs folder no worker serves)
  EXEC-09  the CargoQuote reference code and the J-F reference rebuild grade in the worker as the
           record says (all pass), no model called
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
sys.path[:0] = [str(ROOT / "harness")]


def probe(code: str, seconds: float = 60) -> dict:
    import execution
    return execution.submit(Path(os.environ[execution.JOBS_VAR]), "probe", {}, {"probe.py": code.encode()}, seconds=seconds)


def last_json(r: dict):
    lines = [ln for ln in (r.get("stdout") or "").splitlines() if ln.strip()]
    return json.loads(lines[-1]) if lines else None


def main() -> int:
    import execution
    failures: list[str] = []

    def check(cond, label):
        print(("ok   " if cond else "FAIL ") + label, flush=True)
        if not cond:
            failures.append(label)

    jobs = Path(os.environ.get(execution.JOBS_VAR) or "")
    a = execution.attested(jobs)
    check(all(a["checks"].values()), f"the worker attests {', '.join(k for k, v in a['checks'].items() if v)}")

    # EXEC-01
    name, value = "KG_UNLISTED_" + secrets.token_hex(4).upper(), "canary-" + secrets.token_hex(8)
    os.environ[name] = value
    store_pw = os.environ.get("KG_NEO4J_PASSWORD", "")
    r = probe("import os, json\nprint(json.dumps({'env': dict(os.environ), 'pid1': open('/proc/1/environ','rb').read().decode('latin-1')}))")
    os.environ.pop(name)
    got = last_json(r) or {}
    blob = json.dumps(got) + (r.get("stdout") or "")
    check(name not in blob and value not in blob, "EXEC-01 an unlisted secret-shaped variable of the app never reaches the job")
    check(not store_pw or store_pw not in blob, "EXEC-01 the app's store password is in neither the job's nor the worker's environment")
    check(set(got.get("env", {})) <= {"PATH", "LANG", "HOME", "TMPDIR", "PYTHONDONTWRITEBYTECODE", "KG_SUBJECT", "KG_CLOCK"},
          f"EXEC-01 the job's environment is the allowlist: {sorted(got.get('env', {}))}")

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

    print("worker: " + ("every check holds" if not failures else f"{len(failures)} failure(s)"))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
