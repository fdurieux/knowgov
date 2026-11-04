"""knowgov-trace on the example instance, S6 as acceptance (task-0051; doc-0011 point 3), on the
store KG_STORE names (CI: rdflib, persisted to a file under OUT_DIR so each command reads what the
last one left).

    python tools/check_trace_walkthrough.py OUT_DIR

1. Build the example instance under OUT_DIR; load S6's stage 1 (``gate_cli.py --scenario S6``).
2. ``trace.py register`` the reference code, as a merge would after the build: exit 0, one entry
   in the ledger, APP-0001 from code_map.toml.
3. ``trace.py check``: unchanged, PROCEED, exit 0.
4. The decision table's change (``gate_cli.py --scenario S6 --stage 2``): a reload, so the store loses
   the registration; the ledger keeps it.
5. ``trace.py check``: the registered build is suspect, built from statements the change invalidated,
   a blocker naming APP-0001; exit 1.
6. ``trace.py check --changed``: an edit to the registered file is drift; a new code file no row maps
   is unmapped; a change to a file that is not code reaches nothing.
Every JSON report is valid against harness/schemas/trace-report.schema.json.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "harness"
sys.path[:0] = [str(HARNESS), str(ROOT / "tools")]
import cadence  # noqa: E402
import example_instance  # noqa: E402
import schema_check  # noqa: E402

APP = "APP-0001"
CODE = "reference_impl.py"


def run(env: dict, *args: str) -> tuple[int, str]:
    p = subprocess.run([sys.executable, *args], cwd=HARNESS, env=env, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def trace(env: dict, out: Path, name: str, *args: str) -> tuple[int, dict]:
    report = out / f"trace-{name}.json"
    code, text = run(env, "trace.py", *args, "--instance", str(out / "inst"), "--ledger", str(out / "ledger.json"), "-o", str(report))
    if code not in (0, 1) or not report.exists():
        sys.exit(f"FAIL: trace.py {' '.join(args)} could not run (exit {code}):\n{text}")
    rep = json.loads(report.read_text(encoding="utf-8"))
    errs = schema_check.validate(rep, schema_check.load("trace-report"))
    if errs:
        sys.exit(f"FAIL: trace {name}: the report does not match its schema: {errs[:5]}")
    print(f"exit {code}: trace.py {' '.join(args)}\n    " + "\n    ".join(text.strip().splitlines()))
    return code, rep


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    out = Path(sys.argv[1]).resolve()
    if out.exists() and any(out.iterdir()):
        sys.exit(f"FAIL: {out} is not empty")
    out.mkdir(parents=True, exist_ok=True)
    inst = example_instance.build(out / "inst")
    env = cadence.pin_record(dict(os.environ, KG_SUBJECT=str(inst / "subjects" / "cargo_quote"), KG_RDFLIB_FILE=str(out / "store.ttl"),
                                    PYTHONDONTWRITEBYTECODE="1"))   # the record's day, the wall clock refused (task-0075)
    code, text = run(env, "gate_cli.py", "--scenario", "S6")
    if code != 0:
        sys.exit(f"FAIL: S6 stage 1 exited {code}, want 0:\n{text}")

    code, rep = trace(env, out, "register", "register", "--commit", "c0ffee1", "--file", CODE)
    [e] = json.loads((out / "ledger.json").read_text(encoding="utf-8"))["entries"]
    if code != 0 or e["app"] != APP or e["id"] != f"derived:code@c0ffee1:{CODE}" or not e["assertions"]:
        sys.exit(f"FAIL: register: want exit 0 and one {APP} entry:\n{json.dumps(rep, indent=1)}")

    code, rep = trace(env, out, "stage1", "check")
    if code != 0 or rep["gate"]["verdict"] != "PROCEED" or [r["state"] for r in rep["registered"]] != ["unchanged"] or rep["findings"]:
        sys.exit(f"FAIL: check at stage 1: want exit 0, PROCEED, unchanged, no finding:\n{json.dumps(rep, indent=1)}")

    code, text = run(env, "gate_cli.py", "--scenario", "S6", "--stage", "2")
    if code != 1:
        sys.exit(f"FAIL: S6 stage 2 exited {code}, want 1:\n{text}")

    code, rep = trace(env, out, "stage2", "check")
    sus = [f for f in rep["findings"] if f["kind"] == "suspect"]
    if code != 1 or len(sus) != 1 or sus[0]["severity"] != "blocker" or sus[0]["app"] != APP or APP not in sus[0]["message"] \
            or not sus[0]["related"] or rep["registered"][0]["used_invalidated"] != sus[0]["related"]:
        sys.exit(f"FAIL: check after the change: want exit 1 and one suspect blocker naming {APP}:\n{json.dumps(rep, indent=1)}")

    root = inst / rep["code_root"]
    (root / CODE).write_text((root / CODE).read_text(encoding="utf-8") + "\n# an edit after the registration\n", encoding="utf-8")
    (root / "notify.py").write_text("# new code no row maps\n", encoding="utf-8")
    (root / "NOTES.txt").write_text("not code\n", encoding="utf-8")
    code, rep = trace(env, out, "changed", "check", "--changed", CODE, "--changed", "notify.py", "--changed", "NOTES.txt", "--fail-on", "major")
    kinds = sorted((f["kind"], f["severity"], f["path"]) for f in rep["findings"] if not f["kind"].startswith("gate:"))
    if code != 1 or kinds != [("drift", "minor", CODE), ("suspect", "blocker", CODE), ("unmapped", "major", "notify.py")]:
        sys.exit(f"FAIL: check --changed: want drift, suspect and unmapped, nothing on NOTES.txt:\n{json.dumps(rep, indent=1)}")
    print(f"knowgov-trace: a registered build of {APP} turns suspect after S6's change, and check exits 1 naming it")


if __name__ == "__main__":
    main()
