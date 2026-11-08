"""One job inside the contained worker (task-0141.05): run by harness/worker.py as its own process group
with an allowlisted environment and resource limits. Reads ``<jobdir>/job.json`` and the files the app
wrote beside it, runs them on the subject's oracle in a private folder (``workdir``), and writes the
result, one line, to its own output, which no process it starts can reach (task-0203, R7). The kinds: ``suite`` (a single-reply arm's code), ``suite_dir`` (an
agent's sandbox), ``feedback`` (the agent's own run_suite tool) and ``probe`` (code run as it is, which
the containment checks use: no more trusted than any other model output)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parent
sys.path.insert(0, str(HARNESS))


def _private_output():
    """The job's answer channel (task-0203, R7): this process is made non-dumpable, so a process of the
    same user (the code it runs) cannot open its descriptors or memory through /proc; its stdout, the pipe
    the worker reads, moves to a private descriptor no child inherits, and fd 1 points at /dev/null, so
    nothing the code starts, now or left behind, can write a line the worker would read as the answer."""
    try:
        import ctypes
        ctypes.CDLL(None, use_errno=True).prctl(4, 0, 0, 0, 0)   # PR_SET_DUMPABLE, 0
    except (OSError, AttributeError):
        pass
    sys.stdout.flush()
    out = os.dup(1)   # O_CLOEXEC by default (PEP 446): not inherited by a child
    null = os.open(os.devnull, os.O_WRONLY)
    os.dup2(null, 1)
    os.close(null)
    return out


def _answer(fd: int, out: dict) -> None:
    """The answer, written once to the private descriptor, which is then closed: the worker's pipe has no
    writer left in this process once the answer is given."""
    data = (json.dumps(out, default=str) + "\n").encode("utf-8")
    while data:
        data = data[os.write(fd, data):]
    os.close(fd)


def main(jobdir: str, workdir: str) -> int:
    fd = _private_output()
    import execution
    job = json.loads((Path(jobdir) / "job.json").read_text(encoding="utf-8"))
    files = execution.collect(Path(jobdir) / "files")
    kind, payload = job["kind"], job.get("payload") or {}
    if kind == "probe":
        code = files.get("probe.py", b"").decode("utf-8", "replace")
        # no time of its own: the worker kills the whole job at the job's time
        p = subprocess.run([sys.executable, "-I", "-c", code], cwd=workdir, capture_output=True, text=True)
        out = {"exit": p.returncode, "stdout": (p.stdout or "")[-20000:], "stage": "ok"}
    else:
        out = execution.run_here(kind, payload, files, Path(workdir))
    _answer(fd, out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
