"""The gate report names the code and suite it compared and the pre-load report it applied (task-0341, decision-0040).

Group A's repros, on the store ``--store`` names (``KG_STORE``'s values; ``neo4j`` the stack job's, ``rdflib`` in memory):
- R3 (task-0338's re-check): in a temporary copy of the CargoQuote subject, the suite's expectations edited
  (``vendor/tools/acceptance/cargo_quote_suite.py``'s ``require_re`` ``"3186"`` to ``"3211"``), then the gate on S1 with
  ``--baseline`` against the pristine copy's report, as of the record's day: PROCEED becomes BLOCKED. Likewise an edit
  to the reference implementation (``[reference] code``).
- Q1 (task-0335's re-check): ``tools/preload_check.py`` on the example instance, then its gate on S1 with
  ``--fail-on minor``, without the report and with it (``KG_PRELOAD_REPORT``): the findings and the exit move.
Before task-0341 every one left each identity field equal and ``baseline.differs`` empty. Now R3 must move ``code``,
the edited file's digest alone, and Q1 ``preload``; ``baseline.differs`` and the stderr lines name that field and
nothing else. Without a report, ``preload`` reads null with ``why``.
Exit 0 when every repro holds, 1 when one does not, 2 when the gate cannot run."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / "harness"
CQ = ROOT / "subjects" / "cargo_quote"
SUITE = "vendor/tools/acceptance/cargo_quote_suite.py"
IMPL = "vendor/stack_experiment/cargo_quote/reference_impl.py"
sys.path[:0] = [str(HARNESS), str(ROOT / "tools")]

SHA = re.compile(r"[0-9a-f]{64}")


def edit_suite(root: Path) -> str:
    p = root / SUITE
    text = p.read_text(encoding="utf-8")
    old = '"require_re": r"3186"'
    assert text.count(old) == 1, "the suite's expectation as vendored"
    p.write_text(text.replace(old, '"require_re": r"3211"'), encoding="utf-8")
    return SUITE


def edit_implementation(root: Path) -> str:
    p = root / IMPL
    p.write_text(p.read_text(encoding="utf-8") + "\n# an edit to the implementation the execution ran\n", encoding="utf-8")
    return IMPL


# (name, edit, the verdict before, the verdict after; None: not asserted)
CODE_REPROS = (("R3: the suite's expectations edited", edit_suite, "PROCEED", "BLOCKED"),
               ("R3b: the reference implementation edited", edit_implementation, "PROCEED", "BLOCKED"))


def env_for(store: str, root: Path, **extra: str) -> dict:
    import cadence
    env = cadence.pin_record({**os.environ}, None)   # the record's day, the wall clock refused (task-0075)
    env.update(KG_STORE=store, KG_SUBJECT=str(root), KG_SUBJECTS=str(root.parent), PYTHONDONTWRITEBYTECODE="1", **extra)
    for k in ("KG_RDFLIB_FILE", "KG_PRELOAD_REPORT"):
        if k not in extra:
            env.pop(k, None)
    env.setdefault("KG_REGISTER", str(ROOT / "demo" / "register"))   # the copy lies outside the checkout (task-0334)
    return env


class CannotRun(Exception):
    pass


def gate(store: str, root: Path, *args: str, **extra: str) -> tuple[dict, str, int]:
    p = subprocess.run([sys.executable, str(HARNESS / "gate_cli.py"), "--scenario", "S1", "-f", "json", "--as-of", "record", *args],
                       capture_output=True, text=True, env=env_for(store, root, **extra), timeout=900)
    if p.returncode not in (0, 1):
        raise CannotRun(f"gate_cli exit {p.returncode}: {p.stderr.strip()[-600:]}")
    return json.loads(p.stdout), p.stderr, p.returncode


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def others(base: dict, rep: dict, field: str) -> list[str]:
    import gate_cli
    return [f for f in gate_cli.IDENTITY_FIELDS if f != field and base.get(f) != rep.get(f)]


def code_repro(store: str, td: Path, name: str, edit, before: str | None, after: str | None) -> list[str]:
    root = td / name.split(":")[0] / "cargo_quote"
    shutil.copytree(CQ, root, ignore=shutil.ignore_patterns("__pycache__"))
    base, _, _ = gate(store, root)
    fails = []
    code = base.get("code")
    if not isinstance(code, dict) or not code or not all(SHA.fullmatch(str(v)) for v in code.values()):
        fails.append(f"{name}: pristine code is {code!r}, not a map of files to digests")
    elif {SUITE, IMPL} - set(code):
        fails.append(f"{name}: pristine code names no digest for {sorted({SUITE, IMPL} - set(code))}")
    if before and base["verdict"] != before:
        fails.append(f"{name}: pristine verdict {base['verdict']}, not {before}")
    bfile = td / f"{name.split(':')[0]}-baseline.json"
    bfile.write_text(json.dumps(base), encoding="utf-8")
    edited = edit(root)
    rep, err, _ = gate(store, root, "--baseline", str(bfile))
    differs = rep["baseline"].get("differs")
    if after and rep["verdict"] != after:
        fails.append(f"{name}: verdict {rep['verdict']}, not {after}")
    if differs != ["code"]:
        fails.append(f"{name}: baseline.differs {differs}, not ['code']")
    if " code differs: " not in err:
        fails.append(f"{name}: stderr names no code")
    was, now = base.get("code") or {}, rep.get("code") or {}
    moved = sorted(f for f in set(was) | set(now) if was.get(f) != now.get(f))
    if moved != [edited] or now.get(edited) != _sha(root / edited):
        fails.append(f"{name}: code moved on {moved}, not [{edited!r}] at its raw digest")
    if others(base, rep, "code"):
        fails.append(f"{name}: identity fields besides code moved: {others(base, rep, 'code')}")
    print(f"{store}: {name}: {base['verdict']} -> {rep['verdict']}, differs {differs}, moved {moved}")
    return fails


def preload_repro(store: str, td: Path) -> list[str]:
    import example_instance
    name = "Q1: the example instance's pre-load report applied"
    inst = example_instance.build(td / "exinst")
    root = inst / "subjects" / "cargo_quote"
    pre = td / "pre.json"
    p = subprocess.run([sys.executable, str(ROOT / "tools" / "preload_check.py"), str(inst), "-o", str(pre)],
                       capture_output=True, text=True, env=env_for(store, root), timeout=900)
    if p.returncode == 2 or not pre.is_file():
        raise CannotRun(f"preload_check exit {p.returncode}: {p.stderr.strip()[-600:]}")
    base, _, exit_without = gate(store, root, "--fail-on", "minor")
    fails = []
    pl = base.get("preload")
    if not (isinstance(pl, dict) and pl.get("path") is None and pl.get("sha256") is None and isinstance(pl.get("why"), str) and pl["why"]):
        fails.append(f"{name}: without a report preload is {pl!r}, not null with why")
    bfile = td / "q1-baseline.json"
    bfile.write_text(json.dumps(base), encoding="utf-8")
    rep, err, exit_with = gate(store, root, "--fail-on", "minor", "--baseline", str(bfile), KG_PRELOAD_REPORT=str(pre))
    differs = rep["baseline"].get("differs")
    if differs != ["preload"]:
        fails.append(f"{name}: baseline.differs {differs}, not ['preload']")
    if " preload differs: " not in err:
        fails.append(f"{name}: stderr names no preload")
    now = rep.get("preload") or {}
    if now.get("sha256") != _sha(pre) or now.get("path") != str(pre) or now.get("why") is not None:
        fails.append(f"{name}: with the report preload is {now!r}, not its path and raw digest")
    if (len(base["findings"]), exit_without) == (len(rep["findings"]), exit_with):
        fails.append(f"{name}: the report moved neither the findings nor the exit: the repro does not hold")
    if others(base, rep, "preload"):
        fails.append(f"{name}: identity fields besides preload moved: {others(base, rep, 'preload')}")
    print(f"{store}: {name}: findings {len(base['findings'])} -> {len(rep['findings'])}, exit {exit_without} -> {exit_with}, "
          f"differs {differs}")
    return fails


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--store", default=os.environ.get("KG_STORE", "neo4j"), help="the store kind (default: KG_STORE, else neo4j)")
    args = ap.parse_args(argv)
    fails: list[str] = []
    with tempfile.TemporaryDirectory() as td:
        try:
            for r in CODE_REPROS:
                fails += code_repro(args.store, Path(td), *r)
            fails += preload_repro(args.store, Path(td))
        except CannotRun as e:
            print(f"check_code_preload: {e}", file=sys.stderr)
            return 2
    for f in fails:
        print(f"FAIL {f}")
    print(f"{args.store}: {len(CODE_REPROS) + 1} repro(s): "
          + ("each moves its field alone and differs names it" if not fails else f"{len(fails)} failure(s)"))
    return 1 if fails else 0


if __name__ == "__main__":
    import _outcomes   # task-0159: the outcome recorded when KG_OUTCOMES names a file
    sys.exit(_outcomes.run(main))
