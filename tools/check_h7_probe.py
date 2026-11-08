"""H7's two mutants as the re-run step's first probe, on jef_data_load (task-0219, decision-0018 point 8,
doc-0032 §5). Pre-registered in ``subjects/jef_data_load/probes/h7/PREREGISTRATION.md``; the results are its
``RESULTS.md``.

    python tools/check_h7_probe.py OUT_DIR

Each mutant is a copy of the subject's public reference rebuild (``[reference] code``, the codex rebuild of
2026-10-24) under OUT_DIR, edited in ``src/jef/data/sync.py`` only. J-F's original is never read. The vendored
files are never edited:

- m1: the leg's bar fetch moves above its corporate-actions refresh;
- m2: the crypto end-guard (a crypto leg's ``end`` capped at the previous UTC day) is removed;
- control: the copy unedited.

Three instruments, on each of the three:

- R-STALE: scenario C loaded into an rdflib store, then each of the subject's five documents re-ingested as a
  later version on it (``change.apply_change``, as stage 2 does), with the mutant as the reference code. The statements
  invalidated are counted; the gate's verdict on C with the mutant as reference code is recorded beside it.
- trace ``drift``: a temporary instance whose ``code_map.toml`` maps the copy's ``src/`` to APP-0005
  (``jef-data``), with a copy of the subject's register to check it against; C published to a file store; ``sync.py`` registered from the control; then each variant's
  ``sync.py`` in its place and ``trace.py check --changed jef/data/sync.py``.
- the suite: ``subjects/jef_data_load/oracle/jef_suite.py`` on the copy, under the J-F pins on CPython 3.12.

Writes OUT_DIR/results.json and prints the table against the pre-registered expectations. Exit 0 when every
cell meets its expectation, 1 naming each that does not. No model call; nothing outside OUT_DIR is written.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUBJECT_ROOT = ROOT / "subjects" / "jef_data_load"
REBUILD = SUBJECT_ROOT / "vendor" / "recreate_experiment" / "rebuilds" / "codex-2026-10-24"
SYNC = Path("src") / "jef" / "data" / "sync.py"
APP = "APP-0005"
SC = "C"

# The two edits, each an exact text the rebuild's sync.py holds once (refused otherwise).
GUARD = "     if leg['asset_type']=='crypto':end=min(x for x in [end,(today-timedelta(days=1)).isoformat()] if x)\n"
FETCH = "     bars=[] if inverted else c.get_eod(leg['symbol'],start,end)\n"
ACTIONS = "     if leg['actions']:\n      state=store.actions_state(root,leg['symbol'])"


def mutate(text: str, name: str) -> str:
    def once(t: str, a: str) -> None:
        if t.count(a) != 1:
            sys.exit(f"FAIL: {name}: the rebuild's sync.py does not hold the edited text once: {a.strip()[:80]!r}")
    if name == "control":
        return text
    if name == "m1":   # the bar fetch above the actions refresh
        once(text, FETCH)
        once(text, ACTIONS)
        text = text.replace(FETCH, "", 1)
        return text.replace(ACTIONS, FETCH + ACTIONS, 1)
    if name == "m2":   # the crypto end-guard removed
        once(text, GUARD)
        return text.replace(GUARD, "", 1)
    raise ValueError(name)


VARIANTS = ("control", "m1", "m2")
# the pre-registered table (PREREGISTRATION.md §8): flags or not, and the suite's at least one failure
EXPECTED = {"control": {"r_stale": False, "drift": False, "suite": False},
            "m1": {"r_stale": False, "drift": True, "suite": True},
            "m2": {"r_stale": False, "drift": True, "suite": True}}


def copies(out: Path) -> dict[str, Path]:
    made = {}
    for v in VARIANTS:
        d = out / "variants" / v
        shutil.copytree(REBUILD, d, ignore=shutil.ignore_patterns("__pycache__"))
        p = d / SYNC
        p.write_text(mutate(p.read_text(encoding="utf-8"), v), encoding="utf-8")
        made[v] = d
    return made


def suite(variant: Path) -> dict:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    p = subprocess.run([sys.executable, str(SUBJECT_ROOT / "oracle" / "jef_suite.py"), str(variant)], capture_output=True,
                       text=True, cwd=ROOT, env=env, timeout=3600)
    lines = p.stdout.strip().splitlines()
    try:
        total = json.loads(lines[-1])
    except (IndexError, json.JSONDecodeError):
        sys.exit(f"FAIL: the suite did not run on {variant.name}:\n{p.stderr[-2000:]}")
    failed = [ln for ln in lines[:-1] if ln.startswith("FAIL")]
    return {"passed": total["passed"], "total": total["total"], "failed_features": failed, "flags": total["passed"] < total["total"]}


def r_stale(variant: Path) -> dict:
    """In a child process, so each variant's reference code binds afresh."""
    code = r"""
import json, os, sys
sys.path[:0] = [os.environ["KG_ROOT"] + "/harness", os.environ["KG_ROOT"] + "/tools"]
import cadence
os.environ.update(cadence.pin_record({}))
from subject import SUBJECT
SUBJECT.reference = {"code": os.environ["KG_MUTANT"]}
import check_stage2_reload as s2
from kitio import kit_for
import gate_cli
from tasks import TASKS
from change import apply_change
from store import open_store
st = open_store("rdflib", access="write", path="")
kit = kit_for("C")
s2.load_fresh(st, "C", kit)
on = cadence.as_of("record").isoformat()
gate = gate_cli.evaluate(st, subject=SUBJECT.id, scenario="C", task="codegen", spec=TASKS["codegen"], threshold="blocker",
                         baseline=None, loaded=True, as_of=on)
inval, reingested = 0, []
for i, key in enumerate([a["key"] for a in SUBJECT.artefacts if a.get("mapper")]):
    ch = apply_change("C", {"artefact": key, "version": f"v{i + 2}"}, st, None, [], kit2=kit, kit1=kit)
    inval += len(ch["D3_stale"]["invalidated"])
    reingested.append(key)
print(json.dumps({"invalidated": inval, "reingested": reingested, "gate": gate["verdict"]}))
st.close()
"""
    env = dict(os.environ, KG_ROOT=str(ROOT), KG_SUBJECT=str(SUBJECT_ROOT), KG_MUTANT=str(variant / "src" / "jef" / "data"),
               PYTHONDONTWRITEBYTECODE="1")
    p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=ROOT, env=env, timeout=3600)
    try:
        r = json.loads(p.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        sys.exit(f"FAIL: R-STALE did not run on {variant.name}:\n{p.stderr[-3000:]}")
    return {**r, "flags": r["invalidated"] > 0}


def trace(out: Path, made: dict[str, Path]) -> dict[str, dict]:
    import cadence
    inst = out / "inst"
    (inst / "code").mkdir(parents=True)
    shutil.copytree(made["control"] / "src", inst / "code", dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(ROOT / "demo" / "register", inst / "register")   # the subject's register (KG_REGISTER's default): APP-0005 is checked against it
    (inst / "code_map.toml").write_text(
        '[code]\nroot = "code"\ninclude = ["**/*.py"]\n\n'
        f'[[map]]\nglob = "jef/**"\napp = "{APP}"\nnote = "the public rebuild of jef-data (task-0219 probe)"\n', encoding="utf-8")
    env = cadence.pin_record(dict(os.environ, KG_SUBJECT=str(SUBJECT_ROOT), KG_STORE="rdflib", KG_RDFLIB_FILE=str(out / "store.ttl"),
                                  PYTHONDONTWRITEBYTECODE="1"))

    def run(*args: str) -> tuple[int, str]:
        p = subprocess.run([sys.executable, *args], capture_output=True, text=True, cwd=ROOT / "harness", env=env, timeout=3600)
        return p.returncode, p.stdout + p.stderr

    code, text = run("gate_cli.py", "--scenario", SC, "--publish", "--as-of", "record")
    if code not in (0, 1):
        sys.exit(f"FAIL: publishing {SC} exited {code}:\n{text[-2000:]}")
    ledger = out / "ledger.json"
    code, text = run("trace.py", "register", "--instance", str(inst), "--commit", "control", "--file", "jef/data/sync.py",
                     "--ledger", str(ledger), "--as-of", "record")
    if code != 0:
        sys.exit(f"FAIL: trace register exited {code}:\n{text[-2000:]}")
    target = inst / "code" / "jef" / "data" / "sync.py"
    res = {}
    for v in VARIANTS:
        shutil.copyfile(made[v] / SYNC, target)
        report = out / f"trace-{v}.json"
        code, text = run("trace.py", "check", "--instance", str(inst), "--ledger", str(ledger), "--changed", "jef/data/sync.py",
                         "--as-of", "record", "-f", "json", "-o", str(report))
        if code not in (0, 1) or not report.exists():
            sys.exit(f"FAIL: trace check on {v} exited {code}:\n{text[-2000:]}")
        rep = json.loads(report.read_text(encoding="utf-8"))
        kinds = sorted({f["kind"] for f in rep["findings"]})
        res[v] = {"exit": code, "kinds": kinds, "flags": "drift" in kinds}
    shutil.copyfile(made["control"] / SYNC, target)
    return res


def main() -> int:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    out = Path(sys.argv[1]).resolve()
    if out.exists() and any(out.iterdir()):
        sys.exit(f"FAIL: {out} is not empty")
    out.mkdir(parents=True, exist_ok=True)
    sys.path[:0] = [str(ROOT / "harness")]
    os.environ["KG_SUBJECT"] = str(SUBJECT_ROOT)
    made = copies(out)
    results = {v: {} for v in VARIANTS}
    tr = trace(out, made)
    for v in VARIANTS:
        results[v]["drift"] = tr[v]
        results[v]["r_stale"] = r_stale(made[v])
        results[v]["suite"] = suite(made[v])
        print(f"{v}: R-STALE {results[v]['r_stale']}; trace {results[v]['drift']}; suite {results[v]['suite']['passed']}/{results[v]['suite']['total']}",
              flush=True)
    (out / "results.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    errs = [f"{v} {i}: {'flagged' if results[v][i]['flags'] else 'not flagged'}, expected {'flagged' if want else 'not flagged'}"
            for v in VARIANTS for i, want in EXPECTED[v].items() if results[v][i]["flags"] != want]
    print("\n| variant | R-STALE | trace drift | the suite |\n|---|---|---|---|")
    for v in VARIANTS:
        r = results[v]
        print(f"| {v} | {r['r_stale']['invalidated']} invalidated, gate {r['r_stale']['gate']} | "
              f"{', '.join(r['drift']['kinds']) or 'no finding'} | {r['suite']['passed']} of {r['suite']['total']} pass |")
    for e in errs:
        print("AGAINST EXPECTATION", e)
    print("the H7 probe: " + ("every cell as pre-registered" if not errs else f"{len(errs)} cell(s) against expectation"))
    return 1 if errs else 0


if __name__ == "__main__":
    import _outcomes   # task-0159: the outcome recorded when KG_OUTCOMES names a file
    sys.exit(_outcomes.run(main))
