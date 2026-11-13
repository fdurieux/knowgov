"""knowgov-trace on the example instance, S6 as acceptance (task-0051; doc-0011 point 3), on the
store KG_STORE names (CI: rdflib, persisted to a file under OUT_DIR so each command reads what the
last one left).

    python tools/check_trace_walkthrough.py OUT_DIR

1. Build the example instance under OUT_DIR; load S6's stage 1 (``gate_cli.py --scenario S6 --publish``,
   published since trace reads the store, decision-0017).
2. ``trace.py register`` the reference code, as a merge would after the build: exit 0, one entry
   in the ledger, APP-0001 from code_map.toml.
   The entry records the date it read, the record's day (task-0093).
3. ``trace.py check``: unchanged, PROCEED, exit 0.
   ``trace.py register --as-of`` a day after 2027-08-07, the date CargoQuote's reviews lapse by, into
   a second ledger: the entry and the report name that day, and ``check --as-of`` the same day reads
   the gate on it with its lapses (task-0093).
   Two hand-written files under a new code-map row (task-0124): one registered with ``--keys`` on
   P2|surcharge, a key the change will invalidate, one ``--cited`` on the key its Java header names,
   shipper_id|present, which the change leaves alone; an unknown key is refused (exit 2).
4. The decision table's change (``gate_cli.py --scenario S6 --stage 2 --publish``): a reload, so the store loses
   the registration; the ledger keeps it.
5. ``trace.py check``: the registered build is suspect, built from statements the change invalidated,
   a blocker naming APP-0001; exit 1. The hand-written file on P2|surcharge is suspect as the built one
   is, on that key's invalidated statement; the one on shipper_id|present is not.
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
HAND = "hand/tariff_rules.py"            # hand-written, registered with --keys (task-0124)
HAND_JAVA = "hand/Screening.java"        # hand-written, its Java header cited, registered with --cited
CHANGED_KEY = "P2|surcharge"             # S6's change invalidates its statement
KEPT_KEY = "shipper_id|present"          # S6's change leaves it alone
LAPSE_DAY = "2027-09-01"   # after 2027-08-07, the day S6's reviews lapse by (decision-0005)


def findings(rep: dict) -> list[dict]:
    """The report's findings but the read rule's info notes (decision-0019, task-0221: a subject whose [verification]
    lists no Version attests per load, and the gate says so at info until the subject lists them)."""
    return [f for f in rep["findings"] if not (f["kind"] == "gate:attestation" and f["severity"] == "info")]


def run(env: dict, *args: str) -> tuple[int, str]:
    p = subprocess.run([sys.executable, *args], cwd=HARNESS, env=env, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def trace(env: dict, out: Path, name: str, *args: str, ledger: str = "ledger.json") -> tuple[int, dict]:
    report = out / f"trace-{name}.json"
    code, text = run(env, "trace.py", *args, "--instance", str(out / "inst"), "--ledger", str(out / ledger), "-o", str(report))
    if code not in (0, 1) or not report.exists():
        sys.exit(f"FAIL: trace.py {' '.join(args)} could not run (exit {code}):\n{text}")
    rep = json.loads(report.read_text(encoding="utf-8"))
    errs = schema_check.validate(rep, schema_check.load("trace-report"))
    if errs:
        sys.exit(f"FAIL: trace {name}: the report does not match its schema: {errs[:5]}")
    print(f"exit {code}: trace.py {' '.join(args)}\n    " + "\n    ".join(text.strip().splitlines()))
    return code, rep


def check_answers(rep: dict) -> None:
    """task-0304 (decision-0035 B2): a finding that rests on keys names their owner and route, as the gate's do, and
    the gate block names what the gate decided on (task_profile, register, knowgov), as gate-report v3 does."""
    gate = rep.get("gate") or {}
    if not (isinstance(gate.get("task_profile"), str) and len(gate["task_profile"]) == 64
            and {"tag", "commit", "why"} <= set(gate.get("register") or {}) and {"version", "commit", "describe"} <= set(gate.get("knowgov") or {})):
        sys.exit(f"FAIL: the trace's gate block names no task_profile, register or knowgov:\n{json.dumps(gate, indent=1)}")
    keyed = [f for f in rep["findings"] if f["kind"] in ("suspect", "drift", "missing") or f["kind"] == "gate:key"]
    if not keyed or any("owner" not in f or "route" not in f or not f["owner"] or not f["route"] for f in keyed):
        sys.exit(f"FAIL: a finding that rests on keys names no owner or route:\n{json.dumps(keyed, indent=1)}")
    print(f"    every finding on keys names its owner ({', '.join(sorted({f['owner'] for f in keyed}))}) and route; "
          f"the gate block names task_profile {gate['task_profile'][:12]}, register {gate['register'].get('tag')} and knowgov")


def check_code_path(env: dict, out: Path) -> None:
    """task-0303 (decision-0035 B1): code_path's ledger leg on this ledger names the entry's statement ids and keys,
    sorted, and its state, so file -> keys -> key_nodes holds; whether it is suspect is the store's, unchecked here."""
    p = subprocess.run([sys.executable, "upward.py", "code", "--instance", str(out / "inst"), "--ledger", str(out / "ledger.json"), CODE],
                       cwd=HARNESS, env=env, capture_output=True, text=True)
    led = next(e for e in json.loads((out / "ledger.json").read_text(encoding="utf-8"))["entries"] if e["path"] == CODE)
    entry = json.loads(p.stdout)["ledger"]["entry"] if p.returncode == 0 else None
    want_keys = sorted({u["key"] for u in led.get("used") or [] if u.get("key")} | set(led.get("keys") or []))
    if (entry is None or entry["assertions"] != sorted(led["assertions"]) or entry["keys"] != want_keys or not want_keys
            or entry["state"] not in ("current", "drift") or entry["suspect"]["status"] != "unchecked"):
        sys.exit(f"FAIL: code_path {CODE}'s ledger leg is not the ledger's ids and keys, sorted (exit {p.returncode}):\n{p.stdout[-2000:]}{p.stderr}")
    print(f"    code_path {CODE}: {len(entry['assertions'])} statement id(s) and {len(entry['keys'])} key(s), sorted; state {entry['state']}")


def main() -> None:
    import _outcomes
    if not _outcomes.one_dir_arg():   # task-0314 B-X7: --help is not an output directory
        sys.exit(__doc__)
    out = Path(sys.argv[1]).resolve()
    if out.exists() and any(out.iterdir()):
        sys.exit(f"FAIL: {out} is not empty")
    out.mkdir(parents=True, exist_ok=True)
    inst = example_instance.build(out / "inst")
    env = cadence.pin_record(dict(os.environ, KG_SUBJECT=str(inst / "subjects" / "cargo_quote"), KG_REGISTER=str(inst / "register"),
                                    KG_RDFLIB_FILE=str(out / "store.ttl"),
                                    PYTHONDONTWRITEBYTECODE="1"))   # the record's day, the wall clock refused (task-0075)
    code, text = run(env, "gate_cli.py", "--scenario", "S6", "--publish")   # trace reads this load (decision-0017)
    if code != 0:
        sys.exit(f"FAIL: S6 stage 1 exited {code}, want 0:\n{text}")

    code, rep = trace(env, out, "register", "register", "--commit", "c0ffee1", "--file", CODE)
    [e] = json.loads((out / "ledger.json").read_text(encoding="utf-8"))["entries"]
    if code != 0 or e["app"] != APP or e["id"] != f"derived:code@c0ffee1:{CODE}" or not e["assertions"] \
            or e.get("as_of") != env["KG_TODAY"] or rep["registered"][0].get("as_of") != env["KG_TODAY"]:
        sys.exit(f"FAIL: register: want exit 0 and one {APP} entry as of {env['KG_TODAY']}:\n{json.dumps(rep, indent=1)}")

    code, rep = trace(env, out, "stage1", "check")
    if code != 0 or rep["gate"]["verdict"] != "PROCEED" or [r["state"] for r in rep["registered"]] != ["unchanged"] or findings(rep):
        sys.exit(f"FAIL: check at stage 1: want exit 0, PROCEED, unchanged, no finding:\n{json.dumps(rep, indent=1)}")

    # a registration while rehearsing a later date reads the gate on that date and says so (task-0093)
    code, rep = trace(env, out, "register-lapsed", "register", "--commit", "c0ffee1", "--file", CODE, "--as-of", LAPSE_DAY,
                      ledger="ledger-lapsed.json")
    [f] = json.loads((out / "ledger-lapsed.json").read_text(encoding="utf-8"))["entries"]
    if code != 0 or f.get("as_of") != LAPSE_DAY or rep["registered"][0].get("as_of") != LAPSE_DAY or not f["assertions"]:
        sys.exit(f"FAIL: register --as-of {LAPSE_DAY}: want exit 0 and the entry as of it:\n{json.dumps(rep, indent=1)}")
    code, rep = trace(env, out, "check-lapsed", "check", "--as-of", LAPSE_DAY, "--fail-on", "major", ledger="ledger-lapsed.json")
    lapsed = [g for g in rep["findings"] if g["kind"] == "gate:lapsed"]
    if code != 1 or rep["gate"].get("as_of") != LAPSE_DAY or rep["gate"]["verdict"] != "BLOCKED" or not lapsed \
            or rep["registered"][0].get("as_of") != LAPSE_DAY:
        sys.exit(f"FAIL: check --as-of {LAPSE_DAY}: want exit 1, BLOCKED as of it with gate:lapsed findings:\n{json.dumps(rep, indent=1)}")
    print(f"    registered and checked as of {LAPSE_DAY}: gate {rep['gate']['verdict']}, {len(lapsed)} gate:lapsed finding(s)")

    # hand-written code rests on the keys it cites (task-0124)
    cm = out / "inst" / "code_map.toml"
    cm.write_text(cm.read_text(encoding="utf-8").replace('include = ["**/*.py"]', 'include = ["**/*.py", "**/*.java"]')
                  + '\n[[map]]\nglob = "hand/**"\napp = "APP-0001"\nnote = "hand-written: it cites the keys it rests on"\n', encoding="utf-8")
    code_root = out / "inst" / json.loads((out / "trace-register.json").read_text(encoding="utf-8"))["code_root"]
    (code_root / "hand").mkdir()
    (code_root / HAND).write_text(f"# knowgov-keys: {CHANGED_KEY}\nP2_SURCHARGE = 316.00\n", encoding="utf-8")
    (code_root / HAND_JAVA).write_text(f"package quote;\n\n// knowgov-keys: {KEPT_KEY}\nclass Screening {{}}\n", encoding="utf-8")
    code, text = run(env, "trace.py", "register", "--commit", "c0ffee2", "--file", HAND, "--keys", "P2|nonesuch",
                     "--instance", str(out / "inst"), "--ledger", str(out / "ledger.json"))
    if code != 2 or "unknown key(s) P2|nonesuch" not in text:
        sys.exit(f"FAIL: register --keys with an unknown key: want exit 2 naming it, got {code}:\n{text}")
    code, rep = trace(env, out, "register-keys", "register", "--commit", "c0ffee2", "--file", HAND, "--keys", CHANGED_KEY)
    if code != 0 or [(r["path"], r.get("keys")) for r in rep["registered"]] != [(HAND, [CHANGED_KEY])] or not rep["registered"][0]["used"]:
        sys.exit(f"FAIL: register --keys {CHANGED_KEY}: want exit 0 and {HAND} on the key:\n{json.dumps(rep, indent=1)}")
    code, rep = trace(env, out, "register-cited", "register", "--commit", "c0ffee2", "--file", HAND_JAVA, "--cited")
    if code != 0 or [(r["path"], r.get("keys")) for r in rep["registered"]] != [(HAND_JAVA, [KEPT_KEY])]:
        sys.exit(f"FAIL: register --cited: want exit 0 and {HAND_JAVA} on {KEPT_KEY}:\n{json.dumps(rep, indent=1)}")
    code, rep = trace(env, out, "stage1-hand", "check")
    if code != 0 or [r["state"] for r in rep["registered"]] != ["unchanged"] * 3 or findings(rep):
        sys.exit(f"FAIL: check at stage 1 with the hand-written files: want exit 0, three unchanged, no finding:\n{json.dumps(rep, indent=1)}")

    code, text = run(env, "gate_cli.py", "--scenario", "S6", "--stage", "2", "--publish")
    if code != 1:
        sys.exit(f"FAIL: S6 stage 2 exited {code}, want 1:\n{text}")

    code, rep = trace(env, out, "stage2", "check")
    sus = {f["path"]: f for f in rep["findings"] if f["kind"] == "suspect"}
    rows = {r["path"]: r for r in rep["registered"]}
    if code != 1 or sorted(sus) != sorted([CODE, HAND]) or any(f["severity"] != "blocker" or f["app"] != APP or APP not in f["message"]
                                                              or not f["related"] or rows[p]["used_invalidated"] != f["related"]
                                                              for p, f in sus.items()):
        sys.exit(f"FAIL: check after the change: want exit 1 and suspect blockers naming {APP} on {CODE} and {HAND}, "
                 f"none on {HAND_JAVA}:\n{json.dumps(rep, indent=1)}")
    if CHANGED_KEY not in sus[HAND]["message"] or rows[HAND_JAVA]["used_invalidated"]:
        sys.exit(f"FAIL: check after the change: want {HAND} suspect on {CHANGED_KEY}, {HAND_JAVA} clean:\n{json.dumps(rep, indent=1)}")
    print(f"    {HAND} (--keys {CHANGED_KEY}) suspect on {', '.join(sus[HAND]['related'])}; {HAND_JAVA} (--cited {KEPT_KEY}) not")
    check_answers(rep)
    check_code_path(env, out)

    root = inst / rep["code_root"]
    (root / CODE).write_text((root / CODE).read_text(encoding="utf-8") + "\n# an edit after the registration\n", encoding="utf-8")
    (root / "notify.py").write_text("# new code no row maps\n", encoding="utf-8")
    (root / "NOTES.txt").write_text("not code\n", encoding="utf-8")
    code, rep = trace(env, out, "changed", "check", "--changed", CODE, "--changed", "notify.py", "--changed", "NOTES.txt", "--fail-on", "major")
    kinds = sorted((f["kind"], f["severity"], f["path"]) for f in rep["findings"] if not f["kind"].startswith("gate:"))
    if code != 1 or kinds != [("drift", "minor", CODE), ("suspect", "blocker", HAND), ("suspect", "blocker", CODE), ("unmapped", "major", "notify.py")]:
        sys.exit(f"FAIL: check --changed: want drift, suspect and unmapped, nothing on NOTES.txt:\n{json.dumps(rep, indent=1)}")
    print(f"knowgov-trace: a registered build of {APP} and a hand-written file citing {CHANGED_KEY} turn suspect after S6's change, "
          "and check exits 1 naming them")


if __name__ == "__main__":
    import _outcomes   # task-0314 R5
    _outcomes.help_exit(__doc__)
    import _outcomes   # task-0159: the outcome recorded when KG_OUTCOMES names a file
    sys.exit(_outcomes.run(main))
