"""One job inside the contained worker (task-0141.05): run by harness/worker.py as its own process group
with an allowlisted environment and resource limits. Reads ``<jobdir>/job.json`` and the files the app
wrote beside it, runs them on the subject's oracle in a private folder (``workdir``), and prints the
result as its last line of output. The kinds: ``suite`` (a single-reply arm's code), ``suite_dir`` (an
agent's sandbox), ``feedback`` (the agent's own run_suite tool) and ``probe`` (code run as it is, which
the containment checks use: no more trusted than any other model output)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parent
sys.path.insert(0, str(HARNESS))


def main(jobdir: str, workdir: str) -> int:
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
    print(json.dumps(out, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
