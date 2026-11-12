"""A derived output binds to what it was built on (task-0199, doc-0030 F2: H6, R5; doc-0032 §6 item 6), on the
store KG_STORE names (rdflib persisted to a file under OUT_DIR, so each command reads what the last left), the
public example instance built under OUT_DIR:

    python tools/check_ledger_binding.py OUT_DIR

1. S6 published; ``trace.py register`` the reference code: the ledger entry records each statement it used with
   its value and content digest, P2's surcharge at 316.00.
2. ``trace.py check``: unchanged, exit 0.
3. H6: the decision table's P2 surcharge edited 316.00 -> 341.00 and S6 published again, a reload that re-mints
   the same statement id for the new value: ``trace.py check`` reads the build suspect, a blocker naming the
   statement, 316.00 and 341.00, exit 1.
4. R5, one rule: on the store trace left, the gate (``gate_cli.py --no-load``) lists the same output in
   ``suspect_derived`` and the MCP reader's ``derived_outputs`` marks it suspect, with the same statement changed.
5. The read rule: the same check over a ledger whose entry records ids only (written before 0.9.0) reads it by
   status, as before, and says so in an ``unbound`` finding at info.
6. R5 as doc-0030 found it: after S6's stage 2 invalidates P2, ``trace.py check`` registers the output again on
   the reloaded store; trace and the gate read it suspect alike (before, the gate read a flag the re-registration
   left false).
Every trace report is valid against harness/schemas/trace-report.schema.json.
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

CODE = "reference_impl.py"
P2 = "A:dt:P2|surcharge@v1"
TABLE = "artefacts/decision-tables/decision_table.md"
ROW = "add `316.00` (flat)"


def run(env: dict, *args: str) -> tuple[int, str, str]:
    p = subprocess.run([sys.executable, *args], cwd=HARNESS, env=env, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def trace(env: dict, out: Path, name: str, *args: str, ledger: str = "ledger.json") -> tuple[int, dict]:
    report = out / f"trace-{name}.json"
    code, so, se = run(env, "trace.py", *args, "--instance", str(out / "inst"), "--ledger", str(out / ledger), "-o", str(report))
    if code not in (0, 1) or not report.exists():
        sys.exit(f"FAIL: trace.py {' '.join(args)} could not run (exit {code}):\n{so}{se}")
    rep = json.loads(report.read_text(encoding="utf-8"))
    errs = schema_check.validate(rep, schema_check.load("trace-report"))
    if errs:
        sys.exit(f"FAIL: trace {name}: the report does not match its schema: {errs[:5]}")
    print(f"exit {code}: trace.py {' '.join(args)}\n    " + "\n    ".join(so.strip().splitlines()[:6]))
    return code, rep


def publish(env: dict, scenario: str) -> None:
    code, so, se = run(env, "gate_cli.py", "--scenario", scenario, "--publish", "--as-of", "record")
    if code == 2:
        sys.exit(f"FAIL: {scenario} could not be published:\n{se[-1500:]}")


def main(out: Path) -> int:
    errs: list[str] = []
    if out.exists() and any(out.iterdir()):
        sys.exit(f"FAIL: {out} is not empty")
    out.mkdir(parents=True, exist_ok=True)
    inst = example_instance.build(out / "inst")
    env = cadence.pin_record(dict(os.environ, KG_SUBJECT=str(inst / "subjects" / "cargo_quote"), KG_REGISTER=str(inst / "register"),
                                    KG_RDFLIB_FILE=str(out / "store.ttl"),
                                    PYTHONDONTWRITEBYTECODE="1"))   # the record's day, the wall clock refused (task-0075)
    publish(env, "S6")

    print("== 1. the ledger records what the build used")
    code, rep = trace(env, out, "register", "register", "--commit", "c0ffee1", "--file", CODE)
    [e] = json.loads((out / "ledger.json").read_text(encoding="utf-8"))["entries"]
    p2 = next((u for u in e.get("used") or [] if u["id"] == P2), None)
    if code or not p2 or p2["value"] != "316.00" or len(p2.get("sha256", "")) != 64 or len(e["used"]) != len(e["assertions"]):
        errs.append(f"register: want every used statement recorded with its value and digest, {P2} at 316.00; got {e.get('used')}")

    print("== 2. unchanged")
    code, rep = trace(env, out, "check-1", "check")
    if code or [f for f in rep["findings"] if f["kind"] == "suspect"]:
        errs.append(f"check before the edit: want exit 0 and nothing suspect; got {code}, {rep['findings']}")

    print("== 3. H6: P2 edited 316.00 -> 341.00 and reloaded under the same id")
    t = inst / TABLE
    text = t.read_text(encoding="utf-8")
    assert ROW in text, ROW
    t.write_text(text.replace(ROW, "add `341.00` (flat)", 1), encoding="utf-8")
    example_instance.attest(inst, t)   # the edit listed: this measures the ledger, not the attestation (decision-0036)
    publish(env, "S6")
    code, rep = trace(env, out, "check-2", "check")
    sus = [f for f in rep["findings"] if f["kind"] == "suspect" and P2 in f["related"]]
    row = rep["registered"][0] if rep["registered"] else {}
    if code != 1 or not sus or sus[0]["severity"] != "blocker" or "'316.00'" not in sus[0]["message"] or "'341.00'" not in sus[0]["message"] \
            or P2 not in row.get("used_changed", []):
        errs.append(f"H6: want exit 1, a suspect blocker naming {P2}, 316.00 and 341.00; got {code}, {sus}, {row.get('used_changed')}")
    print(f"    {sus[0]['message'] if sus else 'no suspect finding'}")

    print("== 4. R5: the gate and the MCP reader read the same output suspect on the store trace left")
    code, so, se = run(env, "gate_cli.py", "--scenario", "S6", "--no-load", "--as-of", "record", "-f", "json")
    gate = json.loads(so) if so.strip().startswith("{") else {}
    if e["id"] not in (gate.get("suspect_derived") or []):
        errs.append(f"R5: gate_cli --no-load does not list {e['id']} suspect: {gate.get('suspect_derived')} {se[-400:]}")
    probe = ("import json, sys; sys.path.insert(0, '.'); import mcp_server; "
             f"print(json.dumps(mcp_server.Tools(as_of='record').derived_outputs({{'derived': {e['id']!r}}})))")
    code, so, se = run(env, "-c", probe)
    try:
        d = json.loads(so.strip().splitlines()[-1])
        out_ = (d.get("structuredContent") or d)["outputs"][0]
    except (ValueError, KeyError, IndexError):
        out_ = {}
    if not out_.get("suspect") or P2 not in out_.get("used_changed", []):
        errs.append(f"R5: the MCP reader's derived_outputs does not read {e['id']} suspect on {P2}: {out_ or so[-300:]} {se[-300:]}")
    print(f"    gate suspect_derived {gate.get('suspect_derived')}; derived_outputs suspect {out_.get('suspect')}, changed {out_.get('used_changed')}")

    print("== 5. the read rule: a ledger from before 0.9.0, ids only")
    led = json.loads((out / "ledger.json").read_text(encoding="utf-8"))
    for x in led["entries"]:
        x.pop("used", None)
    (out / "ledger-old.json").write_text(json.dumps(led, indent=1) + "\n", encoding="utf-8")
    publish(env, "S6")   # a fresh load: the old ledger's output is registered again from ids alone
    code, rep = trace(env, out, "check-old", "check", ledger="ledger-old.json")
    unb = [f for f in rep["findings"] if f["kind"] == "unbound"]
    if code != 0 or len(unb) != 1 or unb[0]["severity"] != "info":
        errs.append(f"the read rule: want exit 0 (status only, as before) and one info unbound finding; got {code}, {rep['findings']}")

    print("== 6. R5 as found: stage 2 invalidates P2, trace registers the output again on the reloaded store")
    t.write_text(text, encoding="utf-8")   # the table as the kit has it: stage 2's change is the plant's own
    publish(env, "S6")
    code, so, se = run(env, "gate_cli.py", "--scenario", "S6", "--stage", "2", "--publish", "--as-of", "record")
    code, rep = trace(env, out, "check-3", "check")
    code_g, so, se = run(env, "gate_cli.py", "--scenario", "S6", "--no-load", "--as-of", "record", "-f", "json")
    gate = json.loads(so) if so.strip().startswith("{") else {}
    tr = sorted(f["ref"] for f in rep["findings"] if f["kind"] == "suspect")
    if code != 1 or tr != [e["id"]] or (gate.get("suspect_derived") or []).count(e["id"]) != 1:
        errs.append(f"R5: after stage 2, want trace and the gate to read {e['id']} suspect alike; trace {code} {tr}, "
                    f"gate {gate.get('suspect_derived')} {se[-300:]}")
    print(f"    trace suspect {tr}; gate suspect_derived {gate.get('suspect_derived')}")

    for x in errs:
        print("FAIL", x)
    print(f"derived outputs bound to content on {os.environ.get('KG_STORE', 'neo4j')}: "
          + ("every check holds" if not errs else f"{len(errs)} failure(s)"))
    return 1 if errs else 0


if __name__ == "__main__":
    import _outcomes   # task-0159: the outcome recorded when KG_OUTCOMES names a file
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(_outcomes.run(lambda: main(Path(sys.argv[1]).resolve())))
