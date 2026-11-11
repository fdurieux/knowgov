"""The gate report names the subject's configuration (task-0335, decision-0039 §3.2, doc-0038 §3.2's repros).

Each repro edits one configuration file in a temporary copy of the CargoQuote subject and runs the gate on S1 with
``--baseline`` against the pristine copy's report, as of the same date, on the store ``--store`` names (``KG_STORE``'s
values; ``neo4j`` the stack job's, ``rdflib`` in memory):
- (a) ``register_map.toml``'s ``response|*`` rows reduced to one node each, as of 2027-02-07: QUALIFIED becomes PROCEED;
- (b) ``verifications = false`` for S1 in ``scenarios.toml``: PROCEED becomes BLOCKED;
- (c) ``[rules] vague_words = []`` in ``subject.toml``.
Before task-0335 every one left each identity field equal and ``baseline.differs`` empty. Now each must move
``configuration``, the edited file's digest alone, and ``baseline.differs`` and the stderr lines name ``configuration``
and nothing else. The pristine report must name a digest for each configuration file the subject has.
Exit 0 when every repro holds, 1 when one does not, 2 when the gate cannot run."""
from __future__ import annotations

import argparse
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
sys.path.insert(0, str(HARNESS))

SHA = re.compile(r"[0-9a-f]{64}")
CONFIG = ("subject.toml", "scenarios.toml", "register_map.toml", "plants.toml", "queries.toml")


def reduce_response_rows(root: Path) -> str:
    p = root / "register_map.toml"
    text = p.read_text(encoding="utf-8")
    old = 'nodes = ["APP-0002", "JRN-0004", "JRN-0003", "ENT-0003"]'
    assert text.count(old) == 4, "the response|* rows as vendored"
    p.write_text(text.replace(old, 'nodes = ["APP-0002"]'), encoding="utf-8")
    return "register_map.toml"


def no_verifications(root: Path) -> str:
    p = root / "scenarios.toml"
    text = p.read_text(encoding="utf-8")
    head, sep, rest = text.partition('id = "S1"')
    assert sep and "verifications = true" in rest, "S1 verifies"
    p.write_text(head + sep + rest.replace("verifications = true", "verifications = false", 1), encoding="utf-8")
    return "scenarios.toml"


def no_vague_words(root: Path) -> str:
    p = root / "subject.toml"
    text = p.read_text(encoding="utf-8")
    line = re.search(r"(?m)^vague_words = \[.*\]$", text)
    assert line, "[rules] vague_words"
    p.write_text(text[:line.start()] + "vague_words = []" + text[line.end():], encoding="utf-8")
    return "subject.toml"


# (name, edit, as_of, the verdict before, the verdict after; None: not asserted)
REPROS = (("a: register_map.toml response rows reduced", reduce_response_rows, "2027-02-07", "QUALIFIED", "PROCEED"),
          ("b: scenarios.toml verifications = false", no_verifications, "record", "PROCEED", "BLOCKED"),
          ("c: subject.toml [rules] vague_words = []", no_vague_words, "record", None, None))


def env_for(store: str, root: Path) -> dict:
    import cadence
    env = cadence.pin_record({**os.environ}, None)   # the record's day, the wall clock refused (task-0075)
    env.update(KG_STORE=store, KG_SUBJECT=str(root), KG_SUBJECTS=str(root.parent), PYTHONDONTWRITEBYTECODE="1")
    env.pop("KG_RDFLIB_FILE", None)
    env.setdefault("KG_REGISTER", str(ROOT / "demo" / "register"))   # the copy lies outside the checkout (task-0334)
    return env


class CannotRun(Exception):
    pass


def gate(store: str, root: Path, as_of: str, *args: str) -> tuple[dict, str]:
    p = subprocess.run([sys.executable, str(HARNESS / "gate_cli.py"), "--scenario", "S1", "-f", "json", "--as-of", as_of, *args],
                       capture_output=True, text=True, env=env_for(store, root), timeout=900)
    if p.returncode not in (0, 1):
        raise CannotRun(f"gate_cli exit {p.returncode}: {p.stderr.strip()[-600:]}")
    return json.loads(p.stdout), p.stderr


def named(rep: dict, root: Path) -> list[str]:
    """What the pristine report misses: a configuration file the subject has, with no digest."""
    conf = rep.get("configuration")
    if not isinstance(conf, dict):
        return [f"configuration is {conf!r}, not a map of files"]
    out = [f"{f}: no digest" for f in CONFIG if (root / f).exists() and not SHA.fullmatch(str(conf.get(f)))]
    return out + [f"{f}: {v!r} is no sha256" for f, v in conf.items() if not SHA.fullmatch(str(v))]


def repro(store: str, td: Path, name: str, edit, as_of: str, before: str | None, after: str | None) -> list[str]:
    import gate_cli
    root = td / name[0] / "cargo_quote"
    shutil.copytree(CQ, root, ignore=shutil.ignore_patterns("__pycache__"))
    base, _ = gate(store, root, as_of)
    fails = [f"{name}: pristine {m}" for m in named(base, root)]
    if before and base["verdict"] != before:
        fails.append(f"{name}: pristine verdict {base['verdict']}, not {before}")
    bfile = td / f"{name[0]}-baseline.json"
    bfile.write_text(json.dumps(base), encoding="utf-8")
    edited = edit(root)
    rep, err = gate(store, root, as_of, "--baseline", str(bfile))
    differs = rep["baseline"].get("differs")
    if after and rep["verdict"] != after:
        fails.append(f"{name}: verdict {rep['verdict']}, not {after}")
    if differs != ["configuration"]:
        fails.append(f"{name}: baseline.differs {differs}, not ['configuration']")
    if " configuration differs: " not in err:
        fails.append(f"{name}: stderr names no configuration")
    was, now = base.get("configuration") or {}, rep.get("configuration") or {}
    moved = sorted(f for f in set(was) | set(now) if was.get(f) != now.get(f))
    if moved != [edited]:
        fails.append(f"{name}: configuration moved on {moved}, not [{edited!r}]")
    same = [f for f in gate_cli.IDENTITY_FIELDS if f != "configuration" and base.get(f) != rep.get(f)]
    if same:
        fails.append(f"{name}: identity fields besides configuration moved: {same}")
    print(f"{store}: {name}: {base['verdict']} -> {rep['verdict']}, differs {differs}, moved {moved}")
    return fails


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--store", default=os.environ.get("KG_STORE", "neo4j"), help="the store kind (default: KG_STORE, else neo4j)")
    args = ap.parse_args(argv)
    fails: list[str] = []
    with tempfile.TemporaryDirectory() as td:
        try:
            for r in REPROS:
                fails += repro(args.store, Path(td), *r)
        except CannotRun as e:
            print(f"check_configuration: {e}", file=sys.stderr)
            return 2
    for f in fails:
        print(f"FAIL {f}")
    print(f"{args.store}: {len(REPROS)} repro(s): " + ("each moves configuration alone and differs names it" if not fails else f"{len(fails)} failure(s)"))
    return 1 if fails else 0


if __name__ == "__main__":
    import _outcomes   # task-0159: the outcome recorded when KG_OUTCOMES names a file
    sys.exit(_outcomes.run(main))
