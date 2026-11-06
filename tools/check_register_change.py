"""A register change invalidates (task-0122), by exit code, on each store kind named.

    python tools/check_register_change.py OUT_DIR [--stores neo4j,rdflib]

Builds the fixture register change under OUT_DIR from the vendored register, never editing it
(``tools/register_fixture.py``: CAP-0001 deprecated by a fixture decision, its children moved,
REL-06001 withdrawn), then runs ``harness/gate_cli.py --scenario S1 --as-of record`` with
``KG_REGISTER`` on the fixture and ``--register-previous`` on the vendored register, once per store:

1. the change: exit 1; the report's ``register_change`` names CAP-0001 and REL-06001, each with the
   fixture's decision record as reason. CAP-0001's children were moved, not withdrawn, so it lands
   nothing; REL-06001 lands the eight DT-V keys and their 15 statements. Every one is a stale finding
   naming that reason, and ``derived:S1:G:run1``, the record's S1 output, is a suspect blocker;
2. a register update with no state change: nothing withdrawn, nothing invalidated, and the report
   equal to the gate's without the flag, ``register_change`` aside: exit 0, the record's PROCEED.

Every report is valid against the schema, and with more than one store kind each run's report must
equal across them, the store's name aside (both adapters agree). Exit 0 when every check holds.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "harness"
VENDORED = ROOT / "demo" / "register"
sys.path[:0] = [str(HARNESS), str(ROOT / "tools")]
import cadence  # noqa: E402
import register_fixture  # noqa: E402
import schema_check  # noqa: E402

SCENARIO = "S1"
DERIVED = "derived:S1:G:run1"
# The fixture moves every child of CAP-0001 under CAP-0006, so they were moved, not withdrawn, and the
# deprecation lands nothing (the maintainer, 2026-11-04); REL-06001 lands the eight DT-V rows, and on
# S1 their 15 statements, measured equal on Neo4j and rdflib.
KEYS = {"shipper_id|present", "weight_kg|min", "weight_kg|max", "distance_km|min", "distance_km|max",
        "declared_value|min", "declared_value|max", "invalid_request|behaviour"}
STATEMENTS = 15


def gate(out: Path, name: str, store: str, register: Path | None, *args: str) -> dict:
    report = out / f"gate-{name}-{store}.json"
    env = cadence.pin_record({**os.environ, "KG_STORE": store, **({"KG_REGISTER": str(register)} if register else {})})
    p = subprocess.run([sys.executable, "gate_cli.py", "--scenario", SCENARIO, "--as-of", "record", *args, "-f", "json", "-o", str(report)],
                       cwd=HARNESS, capture_output=True, text=True, env=env)
    if p.returncode not in (0, 1) or not report.exists():
        sys.exit(f"FAIL: {store} gate_cli.py {' '.join(args)} could not run (exit {p.returncode}):\n{p.stdout}{p.stderr}")
    rep = json.loads(report.read_text(encoding="utf-8"))
    errs = schema_check.validate(rep, schema_check.load("gate-report"))
    if errs:
        sys.exit(f"FAIL: {store} {name}: the report does not match its schema: {errs[:3]}")
    if rep["exit_code"] != p.returncode:
        sys.exit(f"FAIL: {store} {name}: exit {p.returncode}, the report says {rep['exit_code']}")
    return rep


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("out", type=Path)
    ap.add_argument("--stores", default=os.environ.get("KG_STORE") or "rdflib", help="comma-separated store kinds (default: KG_STORE, else rdflib)")
    a = ap.parse_args(argv)
    out = a.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    changed, same = out / "register-changed", out / "register-same"
    for d, make in ((changed, register_fixture.changed), (same, register_fixture.same)):
        if not d.exists():
            make(d)
    failures: list[str] = []
    runs: dict[str, dict[str, dict]] = {}
    for store in [s.strip() for s in a.stores.split(",") if s.strip()]:
        ch = gate(out, "changed", store, changed, "--register-previous", str(VENDORED))
        sm = gate(out, "same", store, same, "--register-previous", str(VENDORED))
        plain = gate(out, "plain", store, None)
        runs[store] = {"changed": ch, "same": sm, "plain": plain}
        rc = ch.get("register_change") or {}
        nodes = {n["id"]: n for n in rc.get("nodes", [])}
        links = {ln["id"]: ln for ln in rc.get("links", [])}
        reason = f"the register at {register_fixture.TAG}: {register_fixture.DECISION}"
        stale = [f for f in ch["findings"] if f["kind"] == "stale"]
        if ch["exit_code"] != 1 or ch["verdict"] != "BLOCKED":
            failures.append(f"{store} changed: exit {ch['exit_code']}, {ch['verdict']}; want exit 1, BLOCKED")
        if set(nodes) != {"CAP-0001"} or nodes["CAP-0001"]["to"] != "deprecated" or set(links) != {"REL-06001"}:
            failures.append(f"{store} changed: withdrew nodes {sorted(nodes)} and links {sorted(links)}; want CAP-0001 and REL-06001")
        if any(x["reason"] != reason for x in [*nodes.values(), *links.values()]):
            failures.append(f"{store} changed: a reason is not the fixture's decision record ({reason})")
        if {k["key"] for k in rc.get("keys", [])} != KEYS or any(k["causes"] != ["REL-06001"] for k in rc.get("keys", [])):
            failures.append(f"{store} changed: keys {sorted(k['key'] for k in rc.get('keys', []))}; want the DT-V rows, each through REL-06001 alone")
        if len(rc.get("invalidated") or []) != STATEMENTS:
            failures.append(f"{store} changed: {len(rc.get('invalidated') or [])} statements invalidated; want {STATEMENTS}")
        if not rc.get("invalidated") or sorted(rc["invalidated"]) != sorted(ch["stale"]):
            failures.append(f"{store} changed: {len(rc.get('invalidated') or [])} invalidated, {len(ch['stale'])} stale on the task's keys")
        if not stale or any(reason not in f["message"] or not f.get("owner") for f in stale):
            failures.append(f"{store} changed: every stale finding names the decision and its key's owner")
        if {f["key"] for f in stale} != {k["key"] for k in rc.get("keys", [])}:
            failures.append(f"{store} changed: the stale findings' keys are not the keys resting on the change")
        if rc.get("derived") != DERIVED or ch["suspect_derived"] != [DERIVED] or not any(
                f["kind"] == "suspect_derived" and f["severity"] == "blocker" and f["ref"] == DERIVED for f in ch["findings"]):
            failures.append(f"{store} changed: {DERIVED} is not registered and reported suspect, a blocker")
        src = sm.pop("register_change", None) or {}
        if src.get("nodes") or src.get("links") or src.get("keys") or src.get("invalidated") or src.get("derived"):
            failures.append(f"{store} same: a register update with no state change invalidated something: {src}")
        if sm != plain or plain["exit_code"] != 0 or plain["verdict"] != "PROCEED":
            failures.append(f"{store} same: the report differs from the gate's without the flag, or the record's PROCEED moved")
        print(f"{store}: changed exit {ch['exit_code']} {ch['verdict']}, {len(rc.get('keys', []))} keys, {len(rc.get('invalidated', []))} statements "
              f"invalidated, {len(stale)} stale findings, {ch['suspect_derived']} suspect; same exit {plain['exit_code']} {plain['verdict']}, nothing invalidated")
    kinds = list(runs)
    for other in kinds[1:]:
        for name in ("changed", "same", "plain"):
            x, y = (dict(runs[k][name], store=None) for k in (kinds[0], other))
            if x != y:
                diff = sorted(f for f in set(x) | set(y) if x.get(f) != y.get(f))
                failures.append(f"{name}: {kinds[0]} and {other} disagree on {diff}")
    for f in failures:
        print("FAIL " + f, file=sys.stderr)
    print("register change: " + ("every check holds" + (f", {' and '.join(kinds)} agree" if len(kinds) > 1 else "") if not failures else f"{len(failures)} failure(s)"))
    return 1 if failures else 0


if __name__ == "__main__":
    import _outcomes   # task-0159: the outcome recorded when KG_OUTCOMES names a file
    sys.exit(_outcomes.run(main))
