"""One definition per concept (task-0201, doc-0030 F5: G3, M4, G8, S4, S2's declared_gaps_for_key), on the store
KG_STORE names (rdflib persisted to a file under OUT_DIR), the public example instance built under OUT_DIR:

    python tools/check_one_definition.py OUT_DIR

- G3, one successor set: S6's stage 2 with DT-V's row V2 removed as well, re-verified. ``weight_kg|max``'s
  decision-table statement is invalidated with no successor of its own, while the contract's still stands
  approved. The gate's level, the stale finding, ``superseded_by`` and the bundle read it alike: not superseded,
  so the key reads invalidated, a major stale finding, no ``superseded_by`` entry, and the bundle's header and
  stale line say the same.
- M4, disputed is live: on S4, ``three_valued_answer`` for ``QuoteAPI|on_screening_outage``, whose statements
  are all disputed, is not unknown. It reads them, and ``disputed`` names them.
- G8, one owner and route: ``response|statuses``'s map row loses its ``owner``, so two units answer for it. Its
  gate finding's route names a questionnaire for each, ``capture.py questionnaire`` writes both, and each holds
  the key.
- S4, one uniqueness rule: registering one derived output id twice is refused, on this store's adapter.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "harness"
sys.path[:0] = [str(HARNESS), str(ROOT / "tools")]
import cadence  # noqa: E402
import example_instance  # noqa: E402

KEY = "weight_kg|max"
DT = f"A:dt:{KEY}@v1"
V2 = "| V2 | `weight_kg` | number, `3 <= weight_kg <= 19400` |\n"
DISPUTED = "QuoteAPI|on_screening_outage"
OWNED = "response|statuses"


def run(env: dict, *args: str) -> tuple[int, str, str]:
    p = subprocess.run([sys.executable, *args], cwd=HARNESS, env=env, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def gate(env: dict, *args: str) -> dict:
    code, so, se = run(env, "gate_cli.py", "--as-of", "record", "-f", "json", *args)
    if code == 2:
        sys.exit(f"FAIL: gate_cli {' '.join(args)} could not run:\n{se[-1500:]}")
    return json.loads(so)


def probe(env: dict, code: str) -> dict:
    p = subprocess.run([sys.executable, "-c", "import json, sys; sys.path.insert(0, '.')\n" + code], cwd=HARNESS, env=env,
                       capture_output=True, text=True)
    if p.returncode:
        sys.exit(f"FAIL: probe could not run:\n{p.stderr[-1500:]}")
    return json.loads(p.stdout.strip().splitlines()[-1])


def instance(out: Path, name: str) -> tuple[Path, dict]:
    inst = example_instance.build(out / name)
    env = cadence.pin_record(dict(os.environ, KG_SUBJECT=str(inst / "subjects" / "cargo_quote"), KG_REGISTER=str(inst / "register"),
                                    KG_RDFLIB_FILE=str(out / name / "store.ttl"), PYTHONDONTWRITEBYTECODE="1"))
    return inst, env   # the record's day, the wall clock refused (task-0075)


def main(out: Path) -> int:
    errs: list[str] = []
    if out.exists() and any(out.iterdir()):
        sys.exit(f"FAIL: {out} is not empty")
    out.mkdir(parents=True)

    print(f"== G3: S6's stage 2 also drops DT-V's V2; {KEY} through the gate, the stale finding, superseded_by and the bundle")
    inst, env = instance(out, "g3")
    plants = inst / "subjects" / "cargo_quote" / "plants.toml"
    plants.write_text(plants.read_text(encoding="utf-8") + '\n[[stage2.S6]]\npath = "contract/decision_table.md"\nop = "replace"\n'
                      f"old = {json.dumps(V2)}\nnew = \"\"\n", encoding="utf-8")
    gate(env, "--scenario", "S6", "--publish")
    rep = gate(env, "--scenario", "S6", "--stage", "2", "--reverify", "--publish")
    level = rep["levels"].get(KEY)
    stale = [f for f in rep["findings"] if f["kind"] == "stale" and f["ref"] == DT]
    bundle = probe(env, "import gate, store\n"
                        "with store.open_store(access='read') as st:\n"
                        "    print(json.dumps(gate.render_bundle(gate.resolve(st, 'codegen', 'record'), 'policy')))")
    header = next((ln for ln in bundle.splitlines() if ln.startswith(f"## {KEY} ")), "")
    line = next((ln for ln in bundle.splitlines() if ln.strip().startswith(f"[{DT}]") and "superseded_by:" in ln), "")
    agree = (stale and stale[0]["severity"] == "major" and DT not in rep["superseded_by"] and level == "invalidated"
             and "level=invalidated" in header and "none: it still blocks its key" in line)
    if not agree:
        errs.append(f"G3: the four readers disagree on {DT}: level {level}, stale {[(f['severity'], f['message'][-60:]) for f in stale]}, "
                    f"superseded_by {rep['superseded_by'].get(DT)}, bundle {header!r} / {line[-60:]!r}")
    print(f"    level {level}; stale {stale[0]['severity'] if stale else None}; superseded_by {rep['superseded_by'].get(DT)}; bundle {header.strip()}")

    print(f"== M4: S4, {DISPUTED} all disputed: three_valued_answer reads them")
    inst, env = instance(out, "m4")
    gate(env, "--scenario", "S4", "--publish")
    ans = probe(env, f"import mcp_server\nprint(json.dumps(mcp_server.Tools(as_of='record').three_valued_answer({{'key': {DISPUTED!r}, 'scenario': 'S4'}})))")
    ids = [s["id"] for s in ans.get("statements", []) if s.get("status") == "disputed"]
    if ans.get("answer") == "unknown" or not ids or sorted(ans.get("disputed") or []) != sorted(ids):
        errs.append(f"M4: three_valued_answer({DISPUTED}) on S4: {ans.get('answer')}, disputed {ans.get('disputed')}, statements {ids}")
    print(f"    answer {ans.get('answer')}; disputed {len(ans.get('disputed') or [])}: {ans.get('why', '')[:90]}")

    print(f"== G8: {OWNED} with two answering units: the route names where the questionnaire is written")
    inst, env = instance(out, "g8")
    rm = inst / "subjects" / "cargo_quote" / "register_map.toml"
    text = rm.read_text(encoding="utf-8")
    text, n = re.subn(rf'(key = "{re.escape(OWNED)}"\n)owner = "[^"]*"\n', r"\1", text)
    assert n == 1, n
    rm.write_text(text, encoding="utf-8")
    rep = gate(env, "--scenario", "S2")
    f = next((f for f in rep["findings"] if f["key"] == OWNED and f["kind"] == "key"), None)
    named = re.findall(r"DIR/(questionnaire-[^ ,]+\.toml)", (f or {}).get("route") or "")
    qdir = out / "g8" / "q"
    code, so, se = run(env, "capture.py", "questionnaire", "--scenario", "S2", "--out", str(qdir))
    written = sorted(p.name for p in qdir.glob("*.toml")) if qdir.is_dir() else []
    holds = [p for p in named if (qdir / p).is_file() and OWNED in [i.get("key") for i in tomllib.loads((qdir / p).read_text(encoding="utf-8")).get("item", [])]]
    if not f or f.get("owner") is not None or len(named) < 2 or holds != named:
        errs.append(f"G8: {OWNED}'s route names {named}, owner {(f or {}).get('owner')!r}; written {written}; holding the key {holds}")
    print(f"    route names {named}; written {written}")

    print("== S4: one derived output id registered twice is refused")
    res = probe(env, "import store\n"
                     "st = store.open_store(access='write'); st.__enter__()\n"
                     "st.register_derived('derived:twice', 'code', 's', [])\n"
                     "try:\n    st.register_derived('derived:twice', 'code', 's', []); print(json.dumps({'refused': False}))\n"
                     "except Exception as e:\n    print(json.dumps({'refused': True, 'why': str(e)[:200]}))")
    if not res.get("refused"):
        errs.append(f"S4: the {os.environ.get('KG_STORE', 'neo4j')} adapter holds one Derived id twice")
    print(f"    refused {res.get('refused')}: {res.get('why', '')[:100]}")

    for x in errs:
        print("FAIL", x)
    print(f"one definition per concept on {os.environ.get('KG_STORE', 'neo4j')}: " + ("every check holds" if not errs else f"{len(errs)} failure(s)"))
    return 1 if errs else 0


if __name__ == "__main__":
    import _outcomes   # task-0314 R5
    _outcomes.help_exit(__doc__)
    import _outcomes   # task-0159: the outcome recorded when KG_OUTCOMES names a file
    if len(sys.argv) != 2 or sys.argv[1].startswith("-"):   # task-0314 B-X7: --help is not an output directory
        sys.exit(__doc__)
    sys.exit(_outcomes.run(lambda: main(Path(sys.argv[1]).resolve())))
