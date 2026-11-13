"""The gate command after S6's change (task-0048, doc-0011 point 3; task-0049), by exit code, on
the store KG_STORE names (CI: rdflib in harness.yml, Neo4j in the stack job).

    python tools/check_gate_after_change.py OUT_DIR

Three runs of ``harness/gate_cli.py --scenario S6``, each loading the store itself, each JSON report
written under OUT_DIR, valid against the schema and held to the subject's scored record of S6:

1. ``--stage 2``: the changed decision table brought in as v2. The report names v2 and the four
   statements the change invalidated, the record's; BLOCKED, on the record's keys, exit 1.
2. ``--stage 2 --reverify``: after the owner's re-verification, PROCEED, the record's verdict, yet
   exit 1: derived:S1:G:run1, generated from statements the change invalidated, is a blocker, and
   the invalidated statements are findings (doc-0011 measured exit 0 here before task-0048), and
   ``superseded_by`` names, for each, the verified or approved successors the record lists (task-0071).
3. Stage 1: PROCEED, v1, exit 0. The change and the derived output, nothing else, move the exit code.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "harness"
SCENARIO = "S6"
sys.path.insert(0, str(HARNESS))
if os.environ.get("KG_SUBJECT"):   # B-N8: the children run with cwd=harness, so a relative root is made absolute here
    os.environ["KG_SUBJECT"] = str(Path(os.environ["KG_SUBJECT"]).resolve())
import cadence  # noqa: E402
import schema_check  # noqa: E402
from subject import SUBJECT  # noqa: E402


def gate(out: Path, name: str, *args: str) -> tuple[int, dict, str]:
    """The command's exit code, its JSON report (checked against the schema) and its text."""
    report = out / f"gate-s6-{name}.json"
    base = [sys.executable, "gate_cli.py", "--scenario", SCENARIO, "--as-of", "record", *args]   # the record's date (decision-0005)
    p = subprocess.run([*base, "-f", "json", "-o", str(report)], cwd=HARNESS, capture_output=True, text=True)
    if p.returncode not in (0, 1) or not report.exists():
        sys.exit(f"FAIL: gate_cli.py {' '.join(args)} could not run (exit {p.returncode}):\n{p.stdout}{p.stderr}")
    rep = json.loads(report.read_text(encoding="utf-8"))
    errs = schema_check.validate(rep, schema_check.load("gate-report"))
    if errs:
        sys.exit(f"FAIL: the report of {' '.join(args) or 'stage 1'} does not match its schema: {errs[:5]}")
    text = subprocess.run(base, cwd=HARNESS, capture_output=True, text=True).stdout
    return p.returncode, rep, text


def superseded(stale: list[dict]) -> dict[str, list[str]]:
    """The record's stale statements and their verified or approved successors."""
    out = {x["id"]: sorted({t["id"] for t in x["successors"] if t.get("id") and t.get("status") in ("verified", "approved")}) for x in stale}
    return {k: v for k, v in out.items() if v}


def show(code: int, args: str, rep: dict, text: str) -> None:
    print(f"exit {code}: gate_cli.py --scenario {SCENARIO} {args}: {rep['verdict']}, version {rep['version']}")
    print("    " + "\n    ".join(text.strip().splitlines()))


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1].startswith("-"):   # task-0314 B-X7: --help is not an output directory
        sys.exit(__doc__)
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    os.environ.update(cadence.pin_record({}))   # the record's day, the wall clock refused (task-0075)
    s2 = json.loads((SUBJECT.record_dir / SCENARIO / "deterministic.json").read_text(encoding="utf-8"))["stage2"]
    cfg2 = SUBJECT.scenario(SCENARIO)["stage2"]
    did = cfg2["derived"]["id"]
    invalidated = sorted(x["id"] for x in s2["D3_stale"]["invalidated"])
    before, after = s2["gate_before_reverification"], s2["gate_after_reverification"]

    code, rep, text = gate(out, "stage2", "--stage", "2")
    ch = rep["change"]
    if (code, rep["verdict"], rep["version"]) != (1, before["verdict"], cfg2["version"]) or len(invalidated) != 4 \
            or ch["invalidated"] != invalidated or ch["artefact"] != cfg2["artefact"] or ch["reverified"] \
            or sorted(f["key"] for f in rep["findings"] if f["kind"] == "key" and f["level"] == "invalidated") != sorted(before["blocked_keys"]):
        sys.exit(f"FAIL: want the record's {before['verdict']} on {before['blocked_keys']}, exit 1, version {cfg2['version']}, "
                 f"invalidated {invalidated}:\n{json.dumps(rep, indent=1)}")
    show(code, "--stage 2", rep, text)

    code, rep, text = gate(out, "after-change", "--stage", "2", "--reverify")
    blockers = [f for f in rep["findings"] if f["severity"] == "blocker"]
    stale = [f for f in rep["findings"] if f["kind"] == "stale"]
    if (code, rep["verdict"]) != (1, after["verdict"]) or rep["verdict"] != "PROCEED" or not rep["change"]["reverified"] \
            or [(f["kind"], f["ref"]) for f in blockers] != [("suspect_derived", did)] or rep["change"]["derived"] != did \
            or {f["ref"] for f in stale} != {x["id"] for x in after["stale"]} \
            or rep.get("superseded_by") != superseded(after["stale"]) or not rep.get("superseded_by"):
        sys.exit(f"FAIL: want the record's PROCEED, exit 1, a blocker on {did} alone, the stale statements as findings and superseded_by as the record's successors:\n{json.dumps(rep, indent=1)}")
    show(code, "--stage 2 --reverify", rep, text)

    code, rep, text = gate(out, "stage1")
    if (code, rep["verdict"], rep["version"], rep["change"]) != (0, "PROCEED", "v1", None):
        sys.exit(f"FAIL: S6's stage 1 exited {code}, want 0, PROCEED, v1:\n{text}")
    show(code, "", rep, text)
    print("the gate command brings in S6's later version: BLOCKED before re-verification, and after it "
          "exit 1 while a derived output is suspect")


if __name__ == "__main__":
    import _outcomes   # task-0314 R5
    _outcomes.help_exit(__doc__)
    import _outcomes   # task-0159: the outcome recorded when KG_OUTCOMES names a file
    sys.exit(_outcomes.run(main))
