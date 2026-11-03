"""The gate command after S6's change (task-0048, doc-0011 point 3), by exit code, on the store
KG_STORE names (CI: rdflib in harness.yml).

    python tools/check_gate_after_change.py OUT_DIR

doc-0011 measured that after S6's re-verification the gate reads PROCEED while derived:S1:G:run1,
generated from statements the change invalidated, is still suspect, and that the command exited 0
because it reported stale statements and suspect derived outputs as counts. This script puts the
store in that state and runs the command on it:

1. Through the store port, what ``run.py`` does for S6: stage 1 as ``gate_cli._load`` loads it,
   S1's governed code from the subject's scored record (``S1/run1_G.py``) registered as derived
   with the statements the stage-1 gate served, then ``run.stage2``: the changed decision table
   re-ingested, the stale rule, the owner's re-verification. With rdflib the graph is written to
   ``OUT_DIR/s6-stage2.ttl`` (KG_RDFLIB_FILE) so the command, a separate process, reads it.
2. ``gate_cli.py --scenario S6 --no-load``: PROCEED, exit 1, a blocker on derived:S1:G:run1 and
   the invalidated statements as findings; the JSON report valid against version 2.
3. The same command on S6's stage 1 (it loads, so it runs last): PROCEED, exit 0. The change and
   the derived output, nothing else, move the exit code.

The gate command has no option to load a later version: that is task-0049. Until then this is the
one place a gate run after a change is shown.
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


def gate(env: dict, *args: str) -> tuple[int, str]:
    p = subprocess.run([sys.executable, "gate_cli.py", "--scenario", SCENARIO, *args], cwd=HARNESS, env=env,
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def stage2_into_store(out: Path) -> str:
    """S6, stages 1 and 2, into the store; returns the derived output's id."""
    sys.path.insert(0, str(HARNESS))
    import gate_cli
    import run
    from gate import resolve
    from load import pristine_values
    from store import open_store
    from subject import SUBJECT
    cfg2 = SUBJECT.scenario(SCENARIO)["stage2"]
    derived = cfg2.get("derived", {})
    code = SUBJECT.record_dir / derived.get("from_scenario", SCENARIO) / derived.get("file", "run1_G.py")
    if not code.exists():
        sys.exit(f"FAIL: no derived input at {code}")
    st = open_store(instance=SUBJECT.id)
    try:
        gate_cli._load(st, SCENARIO)
        g1 = resolve(st, "codegen")
        ids = [a["id"] for v in g1["keys"].values() for a in v["assertions"]]
        s2, g2, _ = run.stage2(SCENARIO, cfg2, pristine_values(), st, code.read_text(encoding="utf-8"), ids)
    finally:
        st.close()
    print(f"{SCENARIO} stage 2 in the store ({st.name}): stage 1 {g1['verdict']}; invalidated "
          f"{sorted(x['key'] for x in s2['D3_stale']['invalidated'])}; before re-verification "
          f"{s2['gate_before_reverification']['verdict']}, after {g2['verdict']}; derived {s2['suspect_derived']}")
    if g2["verdict"] != "PROCEED" or not g2["suspect_derived"]:
        sys.exit("FAIL: the store is not in doc-0011's state (PROCEED with a suspect derived output)")
    return derived.get("id", f"derived:{SCENARIO}")


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if os.environ.get("KG_STORE", "neo4j") == "rdflib":
        ttl = out / "s6-stage2.ttl"
        ttl.unlink(missing_ok=True)
        os.environ["KG_RDFLIB_FILE"] = str(ttl)
    env = dict(os.environ)
    did = stage2_into_store(out)

    report = out / "gate-s6-after-change.json"
    code, text = gate(env, "--no-load", "-f", "json", "-o", str(report))
    if code != 1:
        sys.exit(f"FAIL: the gate after S6's change exited {code}, want 1:\n{text}")
    rep = json.loads(report.read_text(encoding="utf-8"))
    sys.path.insert(0, str(HARNESS))
    import schema_check
    errs = schema_check.validate(rep, schema_check.load("gate-report"))
    if errs:
        sys.exit(f"FAIL: the report does not match its schema: {errs[:5]}")
    blockers = [f for f in rep["findings"] if f["kind"] == "suspect_derived" and f["severity"] == "blocker"]
    stale = [f for f in rep["findings"] if f["kind"] == "stale"]
    if rep["schema_version"] != 2 or rep["verdict"] != "PROCEED" or [f["ref"] for f in blockers] != [did] or not stale:
        sys.exit(f"FAIL: want PROCEED, a blocker on {did} and the stale statements as findings:\n{json.dumps(rep, indent=1)}")
    print(f"exit {code}: gate_cli.py --scenario {SCENARIO} --no-load, after the change: {rep['verdict']}, "
          f"blocker {did} (used {', '.join(blockers[0]['related'])}); stale {[(f['ref'], f['severity']) for f in stale]}")
    _, txt = gate(env, "--no-load")
    print("    " + "\n    ".join(txt.strip().splitlines()))

    code, text = gate(env)
    if code != 0:
        sys.exit(f"FAIL: S6's stage 1 exited {code}, want 0:\n{text}")
    print(f"exit {code}: gate_cli.py --scenario {SCENARIO}, stage 1: {text.strip().splitlines()[0]}")
    print("the gate after S6's change no longer exits 0 while a derived output it names is suspect")


if __name__ == "__main__":
    main()
