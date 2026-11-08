"""Pre-load findings as routed gaps (task-0216, decision-0018 point 5), on the store KG_STORE names (rdflib persisted
to a file under OUT_DIR), the public example instance built under OUT_DIR:

    python tools/check_lint_gaps.py OUT_DIR

The example instance's sequence diagram gains a participant nothing uses, a defect pumllint reports (SEQ002,
minor) that leaves the diagram's statements as they were. Then:

1. A gap and a finding. With the pre-load report at the instance's root, S1's load keeps the finding as a lint
   gap, and the gate reports it, kind ``lint``, naming the document's owner and route (``capture.routing`` over
   the keys behind it). Every key's level and the verdict equal those of the same instance unplanted: a lint
   gap never lowers a key's level.
2. The baseline. A report made with ``--baseline`` holds the finding: the gap is kept, ``held``, and its finding
   is info, not raised.
3. A resolution. A review by the owner, under a handle with the role ``closes``, resolves it as a choice: the
   finding is info and names who, when and the record. A review by a handle without the role is refused whole,
   and the gate says so.
4. A slip. The diagram mended, a re-lint with ``--previous`` at the same tool versions shows the finding gone, a
   slip; the load holds no lint gap, and the review's resolution, with nothing left to resolve, is info.
5. The Turtle round trip keeps every lint gap, on this store's adapter.

Exit 0 when all hold, 1 on a failure. The store is the one ``KG_STORE`` names; the stack job runs it on Neo4j.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "harness"
sys.path[:0] = [str(HARNESS), str(ROOT / "tools")]
import cadence  # noqa: E402
import example_instance  # noqa: E402

DIAGRAM = Path("artefacts") / "plantuml-models" / "quote_flow.puml"
ON = "2026-11-03"   # the reviews' day: on or after the handles' issue (2026-11-02)


def run(env: dict, *args: str, cwd: Path = HARNESS) -> tuple[int, str, str]:
    p = subprocess.run([sys.executable, *args], cwd=cwd, env=env, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def gate(env: dict) -> dict:
    code, so, se = run(env, "gate_cli.py", "--as-of", "record", "-f", "json", "--scenario", "S1", "--publish")
    if code == 2:
        sys.exit(f"FAIL: gate_cli could not run:\n{se[-1500:]}")
    return json.loads(so)


def lint_check(inst: Path, out: Path, *extra: str) -> dict:
    code, so, se = run(dict(os.environ), str(ROOT / "tools" / "preload_check.py"), str(inst), "-o", str(out), *extra, cwd=ROOT)
    if code == 2:
        sys.exit(f"FAIL: preload_check could not run:\n{se[-1500:]}")
    return json.loads(out.read_text(encoding="utf-8"))


def probe(env: dict, code: str) -> object:
    p = subprocess.run([sys.executable, "-c", "import json, sys; sys.path.insert(0, '.')\n" + code], cwd=HARNESS, env=env,
                       capture_output=True, text=True)
    if p.returncode:
        sys.exit(f"FAIL: probe could not run:\n{p.stderr[-1500:]}")
    return json.loads(p.stdout.strip().splitlines()[-1])


def instance(out: Path, name: str, plant: bool) -> tuple[Path, dict]:
    inst = example_instance.build(out / name)
    if plant:
        d = inst / DIAGRAM
        d.write_text(d.read_text(encoding="utf-8").replace("@enduml", "participant Idle\n@enduml", 1), encoding="utf-8")
    env = cadence.pin_record(dict(os.environ, KG_SUBJECT=str(inst / "subjects" / "cargo_quote"), KG_REGISTER=str(inst / "register"),
                                    KG_RDFLIB_FILE=str(out / name / "store.ttl"), PYTHONDONTWRITEBYTECODE="1"))
    return inst, env


def lints(rep: dict, rule: str | None = None) -> list[dict]:
    """The lint findings, or those of one rule (the example's own documents have findings of their own, task-0217)."""
    return [f for f in rep["findings"] if f["kind"] == "lint" and rule in (None, f["lint"]["rule"])]


def review(inst: Path, name: str, by: str, gap: dict, resolution: str) -> None:
    d = inst / "subjects" / "cargo_quote" / "captures" / "reviews"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{ON}-{name}.toml").write_text(
        f'[review]\nby = "{by}"\non = {ON}\nrecord = "decisions/lint-{gap["rule"]}.md"\nscenario = "S1"\n\n'
        f'[[resolves]]\ngap = {json.dumps(gap["id"])}\nresolution = "{resolution}"\nsha256 = {json.dumps(gap["sha256"])}\n'
        f'note = "the participant is the diagram\'s, kept for the next release"\n', encoding="utf-8")


def main(out: Path) -> int:
    errs: list[str] = []
    if out.exists() and any(out.iterdir()):
        sys.exit(f"FAIL: {out} is not empty")
    out.mkdir(parents=True)

    print("== 1: the planted SEQ002 is a lint gap and a finding with its owner and route; no level moves")
    plain_inst, plain_env = instance(out, "plain", plant=False)
    lint_check(plain_inst, plain_inst / "preload-report.json")
    plain = gate(plain_env)
    inst, env = instance(out, "lint", plant=True)
    first = lint_check(inst, out / "first.json")
    shutil.copy(out / "first.json", inst / "preload-report.json")
    rep = gate(env)
    gaps = probe(env, "import store\nwith store.open_store(access='read') as st:\n    print(json.dumps(st.lint_gaps()))")
    found = [f for f in lints(rep) if f["lint"]["rule"] == "SEQ002"]
    if not gaps or not found or found[0]["severity"] != "minor" or not found[0].get("route") or "questionnaire" not in found[0]["route"]:
        errs.append(f"1: want a lint gap and a minor lint finding with its route: gaps {len(gaps)}, findings {[(f['severity'], f.get('route')) for f in found]}")
    if rep["levels"] != plain["levels"] or rep["verdict"] != plain["verdict"] or lints(plain, "SEQ002"):
        errs.append(f"1: a lint gap moved a level or the verdict: {rep['verdict']} vs {plain['verdict']}, "
                    f"{ {k: (v, plain['levels'].get(k)) for k, v in rep['levels'].items() if v != plain['levels'].get(k)} }")
    gap = next((g for g in gaps if g["rule"] == "SEQ002"), None)
    print(f"    {len(gaps)} lint gap(s); SEQ002 {found[0]['severity'] if found else None} behind {len(found[0]['related']) if found else 0} key(s), "
          f"owner {found[0].get('owner') if found else None}; verdict {rep['verdict']} as unplanted, every level equal")

    print("== 2: --baseline holds the finding: the gap kept, held, its finding info")
    lint_check(inst, out / "held.json", "--baseline", str(out / "first.json"))
    shutil.copy(out / "held.json", inst / "preload-report.json")
    held = [f for f in lints(gate(env)) if f["lint"]["rule"] == "SEQ002"]
    if not held or held[0]["severity"] != "info" or not held[0]["lint"]["held"]:
        errs.append(f"2: want the baseline's finding held at info: {[(f['severity'], f['lint']['held']) for f in held]}")
    print(f"    held {held[0]['lint']['held'] if held else None}, {held[0]['severity'] if held else None}")

    print("== 3: the owner resolves it as a choice; a handle without closes is refused")
    shutil.copy(out / "first.json", inst / "preload-report.json")
    if gap is None:
        sys.exit("FAIL: no SEQ002 gap to resolve")
    review(inst, "employee-3", "employee-3", gap, "choice")    # ORG-0001, closes
    review(inst, "employee-1", "employee-1", gap, "open")      # ORG-0002, gives only
    rep = gate(env)
    done = [f for f in lints(rep) if f["lint"]["rule"] == "SEQ002"]
    refused = [f for f in rep["findings"] if f["kind"] == "act" and f["act"]["why"] == "refused" and "employee-1" in f["act"]["review"]]
    if not done or done[0]["severity"] != "info" or done[0]["lint"]["resolution"] != "choice" or done[0]["lint"]["resolved_by"] != "employee-3":
        errs.append(f"3: want SEQ002 resolved as a choice by employee-3 at info: {[(f['severity'], f['lint']) for f in done]}")
    if not refused:
        errs.append("3: the review by employee-1, who lacks closes, was not refused")
    print(f"    {done[0]['severity'] if done else None}: resolved {done[0]['lint']['resolution'] if done else None} by "
          f"{done[0]['lint']['resolved_by'] if done else None}; employee-1's review refused: {bool(refused)}")

    print("== 4: the diagram mended, the re-lint's delta shows a slip; no lint gap left")
    d = inst / DIAGRAM
    d.write_text(d.read_text(encoding="utf-8").replace("participant Idle\n", "", 1), encoding="utf-8")
    again = lint_check(inst, out / "again.json", "--previous", str(out / "first.json"))
    delta = again.get("delta") or {}
    gone = [g for g in delta.get("gone", []) if g["rule"] == "SEQ002"]
    if not delta.get("comparable") or not gone or not gone[0]["slip"] or delta.get("new"):
        errs.append(f"4: want a comparable delta with SEQ002 gone as a slip: {json.dumps(delta)[:400]}")
    shutil.copy(out / "again.json", inst / "preload-report.json")
    rep = gate(env)
    left = probe(env, "import store\nwith store.open_store(access='read') as st:\n    print(json.dumps(st.lint_gaps()))")
    stale = [f for f in rep["findings"] if f["kind"] == "act" and f["act"]["act"] == "resolve"]
    if [g for g in left if g["rule"] == "SEQ002"] or lints(rep, "SEQ002") or not stale or stale[0]["severity"] != "info":
        errs.append(f"4: want no SEQ002 gap or finding, and the resolution's act at info: gaps {len(left)}, "
                    f"lint {len(lints(rep, 'SEQ002'))}, acts {[(f['severity'], f['act']['why']) for f in stale]}")
    print(f"    delta comparable {delta.get('comparable')}: gone {[(g['rule'], g['slip']) for g in gone]}, kept {delta.get('kept')}; "
          f"SEQ002 gaps now {len([g for g in left if g['rule'] == 'SEQ002'])}; the resolution's act {stale[0]['severity'] if stale else None} ({stale[0]['act']['why'] if stale else None})")

    print("== 5: the Turtle round trip keeps every lint gap")
    shutil.copy(out / "first.json", inst / "preload-report.json")
    d.write_text(d.read_text(encoding="utf-8").replace("@enduml", "participant Idle\n@enduml", 1), encoding="utf-8")
    gate(env)
    trip = probe(env, "import store\nfrom store_rdflib import RdflibStore\n"
                      "with store.open_store(access='read') as st:\n    a = st.lint_gaps(); ttl = st.export_turtle()\n"
                      "b = RdflibStore(path='')\nb.import_turtle(ttl)\nprint(json.dumps([a, b.lint_gaps()]))")
    if not trip[0] or trip[0] != trip[1]:
        errs.append(f"5: the round trip changed the lint gaps: {len(trip[0])} -> {len(trip[1])}")
    print(f"    {len(trip[0])} lint gap(s) equal after the round trip")

    for e in errs:
        print(f"FAIL {e}")
    store = os.environ.get("KG_STORE") or "neo4j"
    print(f"lint gaps on {store}: " + ("every check holds" if not errs else f"{len(errs)} failure(s)"))
    return 1 if errs else 0


if __name__ == "__main__":
    import _outcomes   # task-0159: the outcome recorded when KG_OUTCOMES names a file
    if len(sys.argv) != 2:
        sys.exit("usage: python tools/check_lint_gaps.py OUT_DIR")
    sys.exit(_outcomes.run(lambda: main(Path(sys.argv[1]).resolve())))
