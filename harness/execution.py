"""The one path model output takes to run (task-0141.05, X1; decision-0012): the arms' single-reply
grading, the agent's feedback suite and its final grading all come here, and here only.

The backend is the contained worker (harness/worker.py), a sibling container of the same image with no
network, a read-only root, no capabilities, uid 65534, bounded memory, processes and CPU, and no
secret in its environment. The app is the trusted supervisor: it writes each job into the shared jobs
folder (``KG_WORKER_JOBS``), the worker runs it and writes a result, and the app reads that result as
untrusted data: capped in size, checked against its shape, never executed. Before each job the app
reads the worker's attestation of its own confinement (``attest.json``, refreshed by a heartbeat) and
refuses the job unless every check holds and the heartbeat is fresh.

Without a worker the code runs nowhere: ``ExecutionRefused``, never a silent fall back to the host.
task-0141.07's opt-in (``KG_ALLOW_UNCONTAINED_EXECUTION=1``) is the only escape: with it and no worker,
the code runs on the host, uncontained, as before X1. A configured worker grades only the
subjects its image ships (``not_shipped``), whatever is mounted; the host stays refused by
execution_guard unless the opt-in is set."""
from __future__ import annotations

import json
import os
import stat
import time
import uuid
from pathlib import Path

import execution_guard
from execution_guard import ExecutionRefused

JOBS_VAR = "KG_WORKER_JOBS"
ATTEST = "attest.json"
HEARTBEAT_S = 15.0            # an attestation older than this is a worker that is not there
RESULT_MAX = 256 * 1024       # bytes of result the app reads; more is refused
JOB_SECONDS = 900.0           # the default wall time one job may take, unless KG_WORKER_JOB_SECONDS says
COLLECT_MAX_FILES = 2000
COLLECT_MAX_BYTES = 32 * 1024 * 1024
KINDS = ("suite", "suite_dir", "feedback", "probe")
ATTEST_CHECKS = ("loopback_only", "no_secret_variables", "read_only_root", "uid_65534", "no_docker_socket", "write_confined",
                 "no_socket_escape")


def backend(env=None) -> str:
    """``worker`` when a jobs folder is configured, else ``host`` under the opt-in; refused otherwise."""
    env = os.environ if env is None else env
    if (env.get(JOBS_VAR) or "").strip():
        return "worker"
    if execution_guard.switches.on(execution_guard.OPT_IN, env):   # 1 only, else BadSwitch (task-0276)
        return "host"
    raise ExecutionRefused(
        "refused: no contained worker is configured (KG_WORKER_JOBS), and code a model wrote never runs on the "
        f"host by default (task-0141.05, decision-0012). Start the stack's worker service, or set {execution_guard.OPT_IN}=1 "
        "to run it here uncontained")


def refusal(env=None, subject=None) -> str | None:
    """None when model output may run now (the instance guard passes and a backend is there), else why
    not; the worker's attestation is read too when it is the backend, so an arms run refuses before its
    first model call rather than after paying for it. ``subject`` is the one the call is for (the page's request
    names its own), else the process's."""
    try:
        where = check(env, subject)
        if where == "worker":
            attested(Path((os.environ if env is None else env)[JOBS_VAR]))
    except ExecutionRefused as e:
        return str(e)
    return None


def check(env=None, subject=None) -> str:
    """Refused unless something may run model output now: a backend (a configured worker, which grades only the
    subjects its image ships, so a subject it does not ship is refused), and on the host the instance guard, which
    refuses first unless the opt-in is set."""
    env = os.environ if env is None else env
    if (env.get(JOBS_VAR) or "").strip():
        unshipped = not_shipped(subject)
        if unshipped:
            raise ExecutionRefused(unshipped)
        return "worker"
    execution_guard.check(env)
    return backend(env)


def not_shipped(subject=None) -> str | None:
    """None when the worker's image ships the loaded subject (the same id, the same resolved root under this
    checkout's ``subjects/``, which is what ``worker._subject_root`` answers), else why it cannot grade it: refused
    before any model call, never after paying for one (a colliding id would otherwise grade the public oracle's)."""
    if subject is None:
        from subject import SUBJECT as subject
    shipped = (execution_guard.ROOT / "subjects" / str(subject.id)).resolve()
    inside = (execution_guard.ROOT / "subjects").resolve() in shipped.parents   # a link out of subjects/ ships nothing
    if inside and Path(subject.root).resolve() == shipped:
        return None
    return (f"refused: the worker grades only the subjects its image ships (subjects/<id> of this checkout), and the "
            f"subject loaded, {subject.id} at {Path(subject.root).resolve()}, is not one; arms runs on an instance's own "
            f"subject need a worker image that ships it, or no worker and {execution_guard.OPT_IN}=1 to run it here uncontained")


def attested(jobs: Path, now: float | None = None) -> dict:
    """The worker's attestation, when it holds; else ExecutionRefused naming what does not."""
    p = Path(jobs) / ATTEST
    try:
        raw = p.read_bytes()
        if len(raw) > 64 * 1024:
            raise ValueError("oversized")
        a = json.loads(raw)
    except (OSError, ValueError) as e:
        raise ExecutionRefused(f"refused: the worker has not attested its confinement ({p}: {type(e).__name__})") from None
    if not isinstance(a, dict) or not isinstance(a.get("checks"), dict):
        raise ExecutionRefused("refused: the worker's attestation is malformed")
    failed = [c for c in ATTEST_CHECKS if a["checks"].get(c) is not True]
    if failed or a.get("ok") is not True:
        abi = a.get("landlock_abi")
        why = (f"; write_confined: this kernel's Landlock is ABI {abi}, and the worker attests writes confined only from "
               "ABI 3 (Linux 6.2), where truncation is confined too (task-0203)"
               if "write_confined" in failed and isinstance(abi, int) and not isinstance(abi, bool) and 0 < abi < 3 else "")
        raise ExecutionRefused(f"refused: the worker is not confined: {', '.join(failed) or 'it says so'} (decision-0012){why}")
    beat = a.get("heartbeat")
    now = time.time() if now is None else now
    if not isinstance(beat, (int, float)) or abs(now - beat) > HEARTBEAT_S:
        raise ExecutionRefused("refused: the worker's attestation is stale; it is not running")
    return a


# a cloud vendor's kernel flavour, by the suffix its distribution gives the release (Ubuntu's -aws, -azure,
# -gcp, -oracle): a reading of a fact the worker attested, never a check and never asked of the network
KERNEL_CLOUDS = {"aws": "AWS", "azure": "Azure", "gcp": "Google Cloud", "oracle": "Oracle Cloud"}
HOST_FIELDS = ("system", "kernel", "machine", "engine")
FACT_MAX = 128


def _fact(v) -> str | None:
    """One host fact as the page may show it: a printable string of at most FACT_MAX characters, else None
    (the attestation is the worker's word, read as data)."""
    if not isinstance(v, str):
        return None
    v = "".join(c for c in v if c.isprintable())[:FACT_MAX].strip()
    return v or None


def cloud_reading(kernel: str | None) -> dict | None:
    """The cloud a kernel release names by its flavour suffix (``7.0.0-1014-aws`` reads AWS), labelled as
    a reading, or None when it names none."""
    suffix = (kernel or "").rsplit("-", 1)[-1].lower() if "-" in (kernel or "") else ""
    name = KERNEL_CLOUDS.get(suffix)
    return {"name": name, "basis": f"read from the kernel release's -{suffix} suffix, not checked"} if name else None


def placement(env=None, now: float | None = None) -> dict:
    """Where model output would run, as the worker attested it (task-0169): ``backend`` (``worker``,
    ``host`` under the opt-in, or None), ``attested`` (the same ``attested()`` a job is refused by),
    ``host`` (the worker's own host facts, sanitised) and ``cloud`` (``cloud_reading`` of its kernel),
    or ``why`` it did not attest. The instance guard is ``refusal()``'s, not this."""
    env = os.environ if env is None else env
    try:
        where = backend(env)
    except ExecutionRefused as e:
        return {"backend": None, "attested": False, "host": None, "cloud": None, "why": str(e)}
    if where == "host":
        return {"backend": "host", "attested": False, "host": None, "cloud": None,
                "why": f"no contained worker: {execution_guard.OPT_IN}=1 runs model output on the app's host, uncontained"}
    try:
        a = attested(Path(env[JOBS_VAR]), now=now)
    except ExecutionRefused as e:
        return {"backend": "worker", "attested": False, "host": None, "cloud": None, "why": str(e)}
    raw = a.get("host") if isinstance(a.get("host"), dict) else {}
    host = {k: _fact(raw.get(k)) for k in HOST_FIELDS}
    return {"backend": "worker", "attested": True, "host": host, "cloud": cloud_reading(host["kernel"]), "why": None}


def collect(root: Path) -> dict[str, bytes]:
    """A directory's regular files by relative path, never following a symlink (a link, at any depth,
    is left out, as is anything not a regular file), bounded in count and bytes."""
    root = Path(root)
    out: dict[str, bytes] = {}
    if not root.is_dir() or root.is_symlink():
        return out
    total = 0
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [d for d in dirnames if d != "__pycache__" and not os.path.islink(os.path.join(dirpath, d))]
        for name in filenames:
            full = os.path.join(dirpath, name)
            try:
                fd = os.open(full, os.O_RDONLY | os.O_NOFOLLOW)
            except OSError:
                continue   # a symlink (ELOOP) or gone
            try:
                if not stat.S_ISREG(os.fstat(fd).st_mode):
                    continue
                with os.fdopen(fd, "rb", closefd=False) as fh:
                    data = fh.read(COLLECT_MAX_BYTES + 1)
            finally:
                os.close(fd)
            total += len(data)
            if len(out) >= COLLECT_MAX_FILES or total > COLLECT_MAX_BYTES:
                raise ExecutionRefused(f"refused: the sandbox exceeds {COLLECT_MAX_FILES} files or {COLLECT_MAX_BYTES} bytes")
            out[os.path.relpath(full, root).replace(os.sep, "/")] = data
    return out


def _valid_rel(rel: str) -> bool:
    parts = rel.split("/")
    return bool(rel) and not rel.startswith("/") and all(p not in ("", ".", "..") for p in parts) and "\x00" not in rel


def check_result(kind: str, r) -> dict:
    """A result as untrusted data: its shape for the kind, every string bounded; anything else refused."""
    def bad(why):
        raise ExecutionRefused(f"refused: the worker's result is malformed ({why})")
    if not isinstance(r, dict):
        bad("not an object")
    if r.get("error") is not None:
        if not isinstance(r["error"], str):
            bad("error")
        return {"error": r["error"][:500], "stage": str(r.get("stage") or "error")[:40]}
    if kind in ("suite", "suite_dir"):
        if not isinstance(r.get("ran"), bool) or not all(isinstance(r.get(k), int) and not isinstance(r.get(k), bool) for k in ("passed", "total")):
            bad("ran, passed, total")
        per = r.get("per_scenario")
        if not isinstance(per, dict) or len(per) > 1000:
            bad("per_scenario")
        clean = {}
        for name, v in per.items():
            if not isinstance(name, str) or not isinstance(v, dict) or not isinstance(v.get("passed"), bool):
                bad(f"scenario {str(name)[:40]}")
            clean[name[:200]] = {"passed": v["passed"], "stage": str(v.get("stage"))[:40] if v.get("stage") is not None else None,
                                 "detail": str(v.get("detail") or "")[:200]}
        if r["passed"] != sum(1 for v in clean.values() if v["passed"]) or r["total"] != len(clean):
            bad("totals disagree with per_scenario")
        return {"ran": r["ran"], "passed": r["passed"], "total": r["total"], "per_scenario": clean}
    if kind == "feedback":
        if not all(isinstance(r.get(k), int) and not isinstance(r.get(k), bool) for k in ("passed", "total")) or not isinstance(r.get("features"), dict):
            bad("passed, total, features")
        feats = {}
        for f, v in r["features"].items():
            if not isinstance(f, str) or not isinstance(v, dict):
                bad("feature")
            feats[f[:200]] = {"passed": int(v.get("passed") or 0), "total": int(v.get("total") or 0),
                              "failed": [str(x)[:200] for x in (v.get("failed") or [])][:50], "stage": str(v.get("stage"))[:40]}
        return {"features": feats, "passed": r["passed"], "total": r["total"]}
    if kind == "probe":
        return {"exit": int(r.get("exit") or 0), "stdout": str(r.get("stdout") or "")[:20000], "stage": str(r.get("stage") or "")[:40]}
    bad(f"unknown kind {kind}")


def submit(jobs: Path, kind: str, payload: dict, files: dict[str, bytes], *, seconds: float | None = None,
           subject: str | None = None) -> dict:
    """One job through the jobs folder: written privately, published by a rename, its result awaited
    until the job's time plus a margin, read capped and checked, then the job's folder removed."""
    from subject import SUBJECT
    jobs = Path(jobs)
    attested(jobs)
    if kind not in KINDS:
        raise ValueError(kind)
    import settings   # task-0264: finite, above 0 up to a day, or refused naming it
    seconds = float(seconds or settings.number("KG_WORKER_JOB_SECONDS", JOB_SECONDS))
    jid = uuid.uuid4().hex
    tmp, ready = jobs / f".new-{jid}", jobs / f"job-{jid}"
    tmp.mkdir(mode=0o777)
    os.chmod(tmp, 0o777)   # the worker, uid 65534, writes its result here
    try:
        (tmp / "files").mkdir(mode=0o755)
        for rel, data in files.items():
            if not _valid_rel(rel):
                raise ExecutionRefused(f"refused: not a sandbox path: {rel[:80]!r}")
            dest = tmp / "files" / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        spec = {"kind": kind, "subject": subject or SUBJECT.id, "payload": payload, "seconds": seconds}
        (tmp / "job.json").write_text(json.dumps(spec), encoding="utf-8")
        os.rename(tmp, ready)
    except BaseException:
        _remove(tmp)
        raise
    deadline = time.monotonic() + seconds + 30.0
    result_path = ready / "result.json"
    try:
        while time.monotonic() < deadline:
            if result_path.exists():
                break
            time.sleep(0.05)
        else:
            raise ExecutionRefused(f"refused: the worker returned nothing within {seconds + 30:g} s")
        with open(result_path, "rb") as fh:
            raw = fh.read(RESULT_MAX + 1)
        if len(raw) > RESULT_MAX:
            raise ExecutionRefused(f"refused: the worker's result exceeds {RESULT_MAX} bytes")
        try:
            r = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            raise ExecutionRefused("refused: the worker's result is not JSON") from None
        return check_result(kind, r)
    finally:
        _remove(ready)


def _remove(p: Path) -> None:
    import shutil
    shutil.rmtree(p, ignore_errors=True)


# The worker's job stages that are the model output's own outcome (task-0203, doc-0030 R2): its time ran
# out, it was killed (a bound it hit), its output overran, or what it ran broke the job's answer. Each is the
# kind's failed cell, as the host records a crash, and the run goes on; a stage the worker reports about the
# job itself ("job": unreadable, unknown kind, no subject) is the app's fault and still raises.
MODEL_STAGES = ("timeout", "killed", "output", "harness_error")


def failed_cell(kind: str, r: dict) -> dict:
    """The kind's failed result for a job-stage error ``r`` ({error, stage}): nothing passed, the error kept."""
    err = {"error": str(r.get("error") or "")[:500], "stage": str(r.get("stage") or "error")[:40]}
    if kind in ("suite", "suite_dir"):
        import measures
        return {"ran": True, "passed": 0, "total": measures.SUITE_TOTAL, "per_scenario": {}, **err}
    if kind == "feedback":
        return {"features": {}, "passed": 0, "total": 0, **err}
    return {"exit": -1, "stdout": "", **err}


def run(kind: str, payload: dict, files: dict[str, bytes], deadline: float | None = None) -> dict:
    """Model output run on the one path: refused, or in the worker, or on the host under the opt-in.
    ``deadline`` (monotonic, the agent's run) caps the job's time to what remains of the run."""
    where = check()
    if where == "worker":
        seconds = None
        if deadline is not None:
            seconds = deadline - time.monotonic()
            if seconds <= 1:
                raise TimeoutError("the run's deadline passed before the suite could run")
            import settings
            seconds = min(seconds, settings.number("KG_WORKER_JOB_SECONDS", JOB_SECONDS))
        r = submit(Path(os.environ[JOBS_VAR]), kind, payload, files, seconds=seconds)
        if "error" in r:
            if r.get("stage") in MODEL_STAGES:   # task-0203, R2: what the model's code did, a failed cell as on the host
                return failed_cell(kind, r)
            raise RuntimeError(f"the worker could not run the job: {r['error']}")
        return r
    return run_here(kind, payload, files)


def run_here(kind: str, payload: dict, files: dict[str, bytes], workdir: Path | None = None) -> dict:
    """The job itself, in this process: the worker's job runner, or the host under the opt-in."""
    import tempfile
    import measures
    with tempfile.TemporaryDirectory(dir=workdir) as td:
        root = Path(td) / "sandbox"
        root.mkdir()
        for rel, data in files.items():
            if not _valid_rel(rel):
                raise ExecutionRefused(f"refused: not a sandbox path: {rel[:80]!r}")
            dest = root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        if kind == "suite":
            return measures.local_run_suite((root / "artifact.py").read_text(encoding="utf-8"), payload["scenario"])
        if kind == "suite_dir":
            return measures.local_run_suite_dir(root, payload["scenario"])
        if kind == "feedback":
            return measures.local_feedback(root, payload["features"], payload.get("feature"))
        raise ValueError(f"{kind} runs only in the worker")
