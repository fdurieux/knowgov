"""The contained worker (task-0141.05, X1; decision-0012): runs model output for the app, inside a sibling
container of the same image that has no network, a read-only root, no capabilities, uid 65534, bounded
memory, processes and CPU, and no secret in its environment (demo/docker-compose.yml, service worker).

    python harness/worker.py [--jobs DIR] [--attest-only]

At start it attests its own confinement and refuses to serve when any check fails: only the loopback
interface, no secret-shaped variable in its environment, a read-only root filesystem, uid 65534, no
container-engine socket. It writes the attestation to ``<jobs>/attest.json`` and refreshes its heartbeat
there; the app (harness/execution.py) refuses a job unless the attestation holds and is fresh.

Each job (``<jobs>/job-<id>/``, written by the app) runs as its own process group in a child
(harness/worker_job.py) with an allowlisted environment, a private working folder, resource limits
(address space, processes, file size, CPU) and a wall time; at the time, or when it ends, the whole
group is killed and reaped. Its stdout is read up to a cap, and the result written beside the job for
the app to read as untrusted data. Nothing here opens the network or reads the app's secrets: it has none.
"""
from __future__ import annotations

import argparse
import errno
import json
import os
import re
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

HARNESS = Path(__file__).resolve().parent
ROOT = HARNESS.parent
SECRET_NAMES = re.compile(r"(^KG_.*KEY.*|.*_API_KEY$|.*PASSWORD.*|.*SECRET.*|.*_TOKEN$|^AWS_.*|^LITELLM_MASTER_KEY$)", re.I)
SOCKETS = ("/var/run/docker.sock", "/run/docker.sock", "/run/containerd/containerd.sock", "/run/podman/podman.sock")
OUTPUT_MAX = 1 << 20          # bytes of a job's stdout read
JOB_MAX_SECONDS = 900.0       # the longest wall time a job may ask for, unless KG_WORKER_MAX_JOB_SECONDS says
JOB_SPEC_MAX = 4 << 20        # bytes of job.json read (features text for the agent's feedback included)
BEAT_S = 5.0


# Landlock (Linux, unprivileged): the job's child may write only beneath its own folder, never the jobs
# folder the worker answers through, so model output cannot forge a result or the attestation
_SYS_CREATE, _SYS_ADD_RULE, _SYS_RESTRICT = 444, 445, 446
_FS_WRITE = sum(1 << b for b in (1, 4, 5, 6, 7, 8, 9, 10, 11, 12))   # write file, remove, make char/dir/reg/sock/fifo/block/sym
_REFER, _TRUNCATE, _SCOPE_SIGNAL = 1 << 13, 1 << 14, 1 << 1
# write_confined is attested only from ABI 3 (Linux 6.2), where Landlock also handles truncation: below it a
# job could truncate a file it may only read (task-0203, doc-0030 R10)
LANDLOCK_MIN_ABI = 3
REAP_S = 10.0   # how long after a job ends every process it left is killed (task-0203, R4)
QUIET_SCANS = 5   # outside a pid namespace of its own: the empty scans in a row the reaper needs (task-0233)


def landlock_abi() -> int:
    """The kernel's Landlock ABI version, 0 when it has none (or a seccomp profile refuses it)."""
    try:
        import ctypes
        libc = ctypes.CDLL(None, use_errno=True)
        v = libc.syscall(_SYS_CREATE, None, ctypes.c_size_t(0), ctypes.c_uint32(1))
        return max(int(v), 0)
    except (OSError, AttributeError):
        return 0


def landlock_writes_only(paths: list[str]) -> None:
    """Restrict this process and every process it starts: writes beneath ``paths`` only; reads are left
    alone; on ABI 6 and later, no signal to a process outside this domain (the worker loop included).
    Raises OSError when the kernel refuses, so a job never runs unconfined by mistake."""
    import ctypes
    libc = ctypes.CDLL(None, use_errno=True)
    abi = landlock_abi()
    if abi < 1:
        raise OSError("Landlock is not available")
    handled = _FS_WRITE | (_REFER if abi >= 2 else 0) | (_TRUNCATE if abi >= 3 else 0)

    class Ruleset(ctypes.Structure):
        _fields_ = [("handled_access_fs", ctypes.c_uint64), ("handled_access_net", ctypes.c_uint64), ("scoped", ctypes.c_uint64)]

    class PathBeneath(ctypes.Structure):
        _pack_ = 1
        _fields_ = [("allowed_access", ctypes.c_uint64), ("parent_fd", ctypes.c_int32)]
    attr = Ruleset(handled, 0, _SCOPE_SIGNAL if abi >= 6 else 0)
    size = ctypes.sizeof(Ruleset) if abi >= 6 else 8
    rfd = libc.syscall(_SYS_CREATE, ctypes.byref(attr), ctypes.c_size_t(size), ctypes.c_uint32(0))
    if rfd < 0:
        raise OSError(ctypes.get_errno(), "landlock_create_ruleset")
    try:
        for p in paths:
            fd = os.open(p, os.O_PATH | os.O_CLOEXEC)
            try:
                rights = handled if os.path.isdir(p) else handled & ((1 << 1) | _TRUNCATE)   # a file: write and truncate only
                rule = PathBeneath(rights, fd)
                if libc.syscall(_SYS_ADD_RULE, ctypes.c_int(rfd), ctypes.c_int(1), ctypes.byref(rule), ctypes.c_uint32(0)) < 0:
                    raise OSError(ctypes.get_errno(), f"landlock_add_rule {p}")
            finally:
                os.close(fd)
        if libc.prctl(38, 1, 0, 0, 0) != 0:   # PR_SET_NO_NEW_PRIVS, which Landlock requires
            raise OSError(ctypes.get_errno(), "no_new_privs")
        if libc.syscall(_SYS_RESTRICT, ctypes.c_int(rfd), ctypes.c_uint32(0)) < 0:
            raise OSError(ctypes.get_errno(), "landlock_restrict_self")
    finally:
        os.close(rfd)


def _num(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name) or default)
    except ValueError:
        return default


IFF_UP = 0x1
CAP_NET_ADMIN = 12


def network(sys_root: str = "/sys", proc_root: str = "/proc") -> dict:
    """What ``loopback_only`` reads: each interface and its state, the routes over any device but lo,
    and whether this process holds CAP_NET_ADMIN, effective or in its bounding set. It holds when no
    interface but lo is up, no route leaves lo, and nothing here can bring a device up. A down device is
    allowed: Docker Desktop's kernel puts tunl0, gre0, sit0, ip6tnl0 and the like, down, in every
    network namespace, ``network_mode: none`` included, with the bonding driver's bonding_masters file
    beside them. Whatever cannot be read fails the check."""
    net = Path(sys_root) / "class" / "net"
    try:   # a regular file there is no interface: the bonding driver's bonding_masters
        names = sorted(n for n in os.listdir(net) if not (net / n).is_file())
    except OSError:
        names = None
    states = {}
    for n in names or ():
        try:
            states[n] = "down" if not int((net / n / "flags").read_text().strip(), 16) & IFF_UP else "up"
        except (OSError, ValueError):
            states[n] = "up"   # unread counts as up
    routes: list | None = []
    for table, dev_field, header in (("route", 0, True), ("ipv6_route", -1, False)):
        try:
            lines = (Path(proc_root) / "net" / table).read_text().splitlines()[1 if header else 0:]
        except FileNotFoundError:
            if table == "ipv6_route":
                continue   # IPv6 disabled in the kernel: no table, no route
            routes = None
            break
        except OSError:
            routes = None
            break
        routes += [f"{table}:{f[dev_field]}" for f in (ln.split() for ln in lines) if f and f[dev_field] != "lo"]
    caps = {}
    try:
        for ln in (Path(proc_root) / "self" / "status").read_text().splitlines():
            k, _, v = ln.partition(":")
            if k in ("CapEff", "CapBnd"):
                caps[k] = int(v.strip(), 16)
    except (OSError, ValueError):
        pass
    net_admin = len(caps) < 2 or any(c >> CAP_NET_ADMIN & 1 for c in caps.values())
    up = sorted(n for n, s in states.items() if s == "up" and n != "lo")
    ok = names is not None and "lo" in states and not up and routes == [] and not net_admin
    return {"ok": ok, "interfaces": states if names is not None else None, "routes": routes, "cap_net_admin": net_admin}


AF_VSOCK, AF_PACKET = 40, 17
OUTSIDE = ("192.0.2.1", 9)   # TEST-NET-1 (RFC 5737), the discard port: never routed, so nothing real is reached
_NO_NETWORK = {errno.ENETUNREACH, errno.EPERM, errno.EACCES}


def sockets(*, opener=None, connect=None, timeout: float = 0.5) -> dict:
    """What ``no_socket_escape`` reads: whether this process can open an AF_VSOCK socket, which no network
    namespace confines (on Docker Desktop the VM's host side answers on it), or an AF_PACKET one, or
    reach an outside address. Each probe records how it ended, and the check holds only when every one
    was refused. A connect that ends any other way than "no network" (connected, timed out, a port or a
    router answering) counts as reaching out. Today the engine's default seccomp profile refuses the
    two families; this proves it rather than assume it."""
    opener = opener or socket.socket
    connect = connect or (lambda: socket.create_connection(OUTSIDE, timeout=timeout).close())

    def name(e: OSError) -> str:
        return errno.errorcode.get(e.errno, type(e).__name__) if e.errno is not None else type(e).__name__
    probes = {}
    for label, family, kind in (("AF_VSOCK", AF_VSOCK, socket.SOCK_STREAM), ("AF_PACKET", AF_PACKET, socket.SOCK_RAW)):
        try:
            opener(family, kind).close()
            probes[label] = "opened"
        except OSError as e:
            probes[label] = f"refused {name(e)}"
    try:
        connect()
        probes["outside"] = "connected"
    except OSError as e:
        probes["outside"] = f"refused {name(e)}" if e.errno in _NO_NETWORK else f"reached {name(e)}"
    return {"ok": all(v.startswith("refused ") for v in probes.values()), "probes": probes}


ENGINE_MARKS = ((".dockerenv", "docker"), ("run/.containerenv", "podman"))   # the files each engine leaves at the root


def host_facts(uname=None, root: str = "/") -> dict:
    """Where the worker runs, as it reads it from inside its container (task-0169): the kernel's
    ``os.uname()`` (system, release, machine) and the engine by the marker file it leaves at the root,
    else ``unknown``. Facts only, no check: nothing here decides whether the worker serves, and no
    network is asked (a cloud is the app's reading of the kernel release, harness/execution.py)."""
    u = os.uname() if uname is None else uname
    engine = next((name for mark, name in ENGINE_MARKS if os.path.exists(os.path.join(root, mark))), "unknown")
    return {"system": u.sysname, "kernel": u.release, "machine": u.machine, "engine": engine}


def attest(env=None, *, sys_root: str = "/sys", proc_root: str = "/proc", socket_probe=None) -> dict:
    """The confinement checks, each True or False, and ok when all hold (decision-0012; the network
    check's reading per ``network``, the sockets' per ``sockets``). ``socket_probe`` stands in for
    ``sockets`` in a test."""
    env = os.environ if env is None else env
    nw = network(sys_root, proc_root)
    sk = (socket_probe or sockets)()
    try:
        ro = bool(os.statvfs("/").f_flag & os.ST_RDONLY)
    except OSError:
        ro = False
    leaked = sorted(k for k in env if SECRET_NAMES.match(k))
    checks = {"loopback_only": nw["ok"], "no_secret_variables": not leaked, "read_only_root": ro,
              "uid_65534": os.getuid() == 65534, "no_docker_socket": not any(os.path.exists(s) for s in SOCKETS),
              "write_confined": landlock_abi() >= LANDLOCK_MIN_ABI, "no_socket_escape": sk["ok"]}
    return {"ok": all(checks.values()), "checks": checks, "landlock_abi": landlock_abi(), "interfaces": nw["interfaces"], "routes": nw["routes"],
            "cap_net_admin": nw["cap_net_admin"], "sockets": sk["probes"], "secret_names": leaked,
            "host": host_facts(), "pid": os.getpid(), "heartbeat": time.time()}


def _write_atomic(path: Path, data: dict) -> None:
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(data), encoding="utf-8")
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)


def _limits(seconds: float, writable: list[str] | None = None):
    """The child's resource limits and, with ``writable``, its Landlock domain, set before it runs (in
    the child, after fork); a refusal there fails the job rather than run it unconfined."""
    import resource
    mem = int(_num("KG_WORKER_MEMORY", 4 << 30))
    procs = int(_num("KG_WORKER_PROCESSES", 128))
    fsize = int(_num("KG_WORKER_FILE_BYTES", 64 << 20))

    def apply():
        os.setsid()
        resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
        resource.setrlimit(resource.RLIMIT_NPROC, (procs, procs))
        resource.setrlimit(resource.RLIMIT_FSIZE, (fsize, fsize))
        cpu = int(seconds) + 5
        resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        if writable is not None:
            landlock_writes_only(writable)
    return apply


def _subreaper() -> bool:
    """Become the reaper of every orphan a job leaves (Linux PR_SET_CHILD_SUBREAPER), so a process that
    left the job's group with setsid is still this worker's child, and still killed after the job."""
    try:
        import ctypes
        return ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0) == 0
    except (OSError, AttributeError):
        return False


def _children() -> set[int]:
    me, kids = os.getpid(), set()
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            stat = Path(f"/proc/{pid}/stat").read_text()
        except OSError:
            continue
        if int(stat.rsplit(")", 1)[1].split()[1]) == me:   # the ppid field, after the command name
            kids.add(int(pid))
    return kids


def _group_settled(pgid: int, seconds: float = 5.0) -> bool:
    """Wait until no process of the killed group is still running (a zombie has finished exiting, so
    its children are already reparented to this subreaper): only then does a scan of this worker's
    children see every escapee. False if one still runs at the bound."""
    end = time.monotonic() + seconds
    while True:
        alive = False
        for pid in os.listdir("/proc"):
            if not pid.isdigit():
                continue
            try:
                fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
            except OSError:
                continue
            if int(fields[2]) == pgid and fields[0] not in ("Z", "X"):   # state, then ppid, then pgrp
                alive = True
                break
        if not alive:
            return True
        if time.monotonic() >= end:
            return False
        time.sleep(0.02)


def _tree() -> dict[int, tuple[int, str]]:
    """Every process this worker can see: pid -> (ppid, state)."""
    out = {}
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
        except OSError:
            continue
        out[int(pid)] = (int(fields[1]), fields[0])
    return out


def _descendants(root: int, tree: dict[int, tuple[int, str]]) -> set[int]:
    """Every process below ``root`` at any depth, by the ppid links."""
    kids: dict[int, list[int]] = {}
    for pid, (ppid, _state) in tree.items():
        kids.setdefault(ppid, []).append(pid)
    out, todo = set(), [root]
    while todo:
        for k in kids.get(todo.pop(), []):
            if k not in out:
                out.add(k)
                todo.append(k)
    return out


class ReapIncomplete(RuntimeError):
    """What a job left was not confirmed gone within REAP_S (task-0233): the worker stops serving rather than
    run the next job beside it. As its container's init, its exit takes every process of the namespace with it,
    and the app refuses a job without a fresh attestation."""


def _ns_counter() -> int | None:
    """The pid namespace's last allocated pid (``/proc/sys/kernel/ns_last_pid``), when this worker is the init
    of a pid namespace of its own, as in its container: every fork in the namespace moves it. None elsewhere
    (a worker loop on a host), where the counter is the whole machine's and never settles (task-0233)."""
    if os.getpid() != 1:   # pid 1 only as the init of a namespace of its own: a host's pid 1 is its own init
        return None
    try:
        return int(Path("/proc/sys/kernel/ns_last_pid").read_text())
    except (OSError, ValueError):
        return None


def _reap_orphans(before: set[int] = frozenset(), seconds: float = REAP_S) -> int:
    """Kill and reap every process the job left (task-0203, R4): each round kills every descendant of this
    worker at any depth at once, not one level a round, and reaps the dead, until none is left or the bound
    passes. A job's escapee that left its group with setsid is still a descendant: this worker is its
    subreaper. A process this worker had before the job (``before``, with its own descendants) is not the
    job's. Returns how many were killed; past the bound, ReapIncomplete.

    "None is left" is never one empty scan (task-0233): a /proc listing is no snapshot, and a process that
    forks and exits between the listing and its read leaves a child the scan never saw, so under load a fast
    fork chain could read as gone and outlive its job. In its container (the init of its own pid namespace)
    the worker takes an empty scan only when the namespace's pid counter did not move across it: a process
    alive after it was either listed and read, or forked after the first read of the counter, which moved it.
    Elsewhere (a worker loop on a host, the test path) it takes QUIET_SCANS empty scans in a row, which is
    weaker."""
    me, killed, quiet = os.getpid(), set(), 0
    end = time.monotonic() + seconds
    while True:
        while True:   # reap whatever has died, so a zombie is not counted again
            try:
                pid, _ = os.waitpid(-1, os.WNOHANG)
            except ChildProcessError:
                break
            if pid == 0:
                break
        c1 = _ns_counter()
        tree = _tree()
        keep = set(before)
        for b in before:
            keep |= _descendants(b, tree)
        live = {p for p in _descendants(me, tree) - keep if tree.get(p, (0, "X"))[1] not in ("Z", "X")}
        if not live:
            if c1 is not None:
                if _ns_counter() == c1:
                    return len(killed)   # nothing forked during an empty scan: nothing is left
            else:
                quiet += 1
                if quiet >= QUIET_SCANS:
                    return len(killed)
        else:
            quiet = 0
        if time.monotonic() >= end:
            raise ReapIncomplete(f"{len(live)} process(es) the job left are still alive after {seconds:g} s" if live else
                                 f"after {seconds:g} s no scan of what the job left was confirmed empty")
        for pid in live:
            try:
                os.kill(pid, signal.SIGKILL)
                killed.add(pid)
            except OSError:
                pass
        time.sleep(0.01)


def _subject_root(sid) -> Path | None:
    """A job names its subject by id; only a subject this image ships answers (never a path)."""
    if not isinstance(sid, str) or not re.fullmatch(r"[a-z0-9_]{1,64}", sid):
        return None
    root = ROOT / "subjects" / sid
    return root if (root / "subject.toml").is_file() else None


def run_job(jobdir: Path, workdir: Path, confine: bool = True) -> dict:
    """One job, its result as a dict (an error or the child's answer)."""
    try:
        with open(jobdir / "job.json", "rb") as fh:
            spec = json.loads(fh.read(JOB_SPEC_MAX))
    except (OSError, ValueError) as e:
        return {"error": f"unreadable job ({type(e).__name__})", "stage": "job"}
    if not isinstance(spec, dict) or spec.get("kind") not in ("suite", "suite_dir", "feedback", "probe"):
        return {"error": "unknown job kind", "stage": "job"}
    sroot = _subject_root(spec.get("subject"))
    if sroot is None:
        return {"error": "the job names no subject this worker ships", "stage": "job"}
    cap = _num("KG_WORKER_MAX_JOB_SECONDS", JOB_MAX_SECONDS)
    try:
        seconds = max(1.0, min(float(spec.get("seconds") or cap), cap))
    except (TypeError, ValueError):
        seconds = cap
    before = _children()
    import tempfile
    workdir = Path(tempfile.mkdtemp(prefix="job-", dir=workdir))   # the job's own folder, the only place it may write
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "LANG": "C.UTF-8", "HOME": str(workdir), "TMPDIR": str(workdir),
           "PYTHONDONTWRITEBYTECODE": "1", "KG_SUBJECT": str(sroot), "KG_CLOCK": "pinned"}
    proc = subprocess.Popen([sys.executable, "-I", str(HARNESS / "worker_job.py"), str(jobdir), str(workdir)],
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                            env=env, cwd=str(workdir), preexec_fn=_limits(seconds, [str(workdir), "/dev/null"] if confine else None),
                            close_fds=True)
    out = bytearray()
    over = threading.Event()

    def pump():
        while True:
            chunk = proc.stdout.read(65536)
            if not chunk:
                return
            if len(out) < OUTPUT_MAX:
                out.extend(chunk[:OUTPUT_MAX - len(out)])
            else:
                over.set()   # keep draining so the child is never blocked on a full pipe
    t = threading.Thread(target=pump, daemon=True)
    t.start()
    stage = None
    try:
        proc.wait(timeout=seconds)
    except subprocess.TimeoutExpired:
        stage = "timeout"
    finally:
        try:
            os.killpg(proc.pid, signal.SIGKILL)   # the whole group: a child it spawned and left goes too
        except ProcessLookupError:
            pass
        proc.wait()
        _group_settled(proc.pid)   # every killed member exited, so its escapees are this worker's children now
        t.join(timeout=5)
        _reap_orphans(before)   # and one that left the group, reparented here by the subreaper
        import shutil
        shutil.rmtree(workdir, ignore_errors=True)
    if stage == "timeout":
        return {"error": f"the job exceeded its {seconds:g} s", "stage": "timeout"}
    if over.is_set():
        return {"error": f"the job's output exceeded {OUTPUT_MAX} bytes", "stage": "output"}
    if proc.returncode < 0:
        return {"error": f"the job was killed by signal {-proc.returncode}", "stage": "killed"}
    lines = [ln for ln in bytes(out).decode("utf-8", "replace").splitlines() if ln.strip()]
    try:
        return json.loads(lines[-1]) if lines else {"error": "the job answered nothing", "stage": "harness_error"}
    except ValueError:
        return {"error": "the job's answer is not JSON", "stage": "harness_error"}


def serve(jobs: Path, workdir: Path, *, once: bool = False, attestation: dict | None = None, stop=None) -> int:
    """Attest, then serve jobs until stopped. ``attestation`` stands in for the real checks in a test
    on a machine that is not a confined worker (tests/test_worker.py); main() never passes one."""
    jobs, workdir = Path(jobs), Path(workdir)
    a = attest() if attestation is None else dict(attestation)
    if not a["ok"]:
        _write_atomic(jobs / "attest.json", a)
        failed = [k for k, v in a["checks"].items() if not v]
        print(f"worker: refusing to serve, not confined: {', '.join(failed)}", file=sys.stderr)
        return 3
    stop = stop or threading.Event()
    _subreaper()

    def beat():
        while not stop.is_set():
            _write_atomic(jobs / "attest.json", dict(attest() if attestation is None else a, heartbeat=time.time()))
            stop.wait(BEAT_S)
    _write_atomic(jobs / "attest.json", dict(a, heartbeat=time.time()))
    beating = threading.Thread(target=beat, daemon=True)
    beating.start()
    print(f"worker: confined ({', '.join(a['checks'])}), serving {jobs}", file=sys.stderr, flush=True)
    try:
        while not stop.is_set():
            for jd in sorted(jobs.glob("job-*")):
                try:
                    os.mkdir(jd / "claimed")   # one worker takes a job, once
                except OSError:
                    continue
                try:
                    r = run_job(jd, workdir)
                except ReapIncomplete as e:   # fail closed (task-0233): no next job beside what this one left
                    stop.set()
                    beating.join(BEAT_S + 30)   # no heartbeat lands after the refusal
                    why = f"the worker stopped serving: {e}"
                    for path, body in ((jd / "result.json", {"error": why, "stage": "harness_error"}),
                                       (jobs / "attest.json", dict(a, ok=False, heartbeat=time.time(), refused=why))):
                        try:
                            _write_atomic(path, body)
                        except OSError:
                            pass
                    print(f"worker: {why}", file=sys.stderr, flush=True)
                    return 4
                try:
                    _write_atomic(jd / "result.json", r)
                except OSError:
                    pass   # the app gave up on it and removed the folder
            if once:
                return 0
            stop.wait(0.05)
        return 0
    finally:
        stop.set()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--jobs", default=os.environ.get("KG_WORKER_JOBS", "/jobs"))
    ap.add_argument("--work", default=os.environ.get("KG_WORKER_WORK", "/work"))
    ap.add_argument("--attest-only", action="store_true", help="print the attestation and exit 0 when confined, else 3")
    args = ap.parse_args(argv)
    if args.attest_only:
        a = attest()
        print(json.dumps(a, indent=1))
        return 0 if a["ok"] else 3
    return serve(Path(args.jobs), Path(args.work))


if __name__ == "__main__":
    sys.exit(main())
