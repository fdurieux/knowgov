"""A person's statement against the documents' (task-0038, doc-0007 F3), on the store KG_STORE
names: CI runs it on rdflib (harness.yml) and on Neo4j (the stack job).

    python tools/check_capture_pairing.py OUT_DIR

It builds the public example instance into OUT_DIR, loads S2 as the gate command does, then adds
one capture by employee-1 with two answers and loads S2 again:

- response|statuses: a list with held_unscreened, which the contract's and the spec's (both
  validated, corroborating each other) lack. Each pair raises a conflict gap naming the person's
  statement and the document's; the three statements are disputed and the gate BLOCKED on the key.
- quote_api|technology: "Python 3.12, FastAPI", as the C4 model says (proposed, one document).
  The two are recorded as corroborating, and neither rises: both stay proposed.

Nothing else moves: every other assertion keeps its status, and no other gap appears.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUSES = "error: store_unavailable|held_unscreened|quoted|refused_screening|rejected: invalid_request|review_hold"
TECH = "Python 3.12, FastAPI"
STEM = "2026-11-02-ORG-0002-employee-1"
CAPTURE = f"""# A capture (task-0009), written here as harness/capture.py ingest would write it.
[capture]
from = "employee-1"
on = 2026-11-02
record = "minutes/2026-11-02-employee-1.md"
owner = "ORG-0002"

[[answer]]
key = "response|statuses"
value = "{STATUSES}"
note = ""

[[answer]]
key = "quote_api|technology"
value = "{TECH}"
note = ""
"""
CAP_STATUSES, CAP_TECH = f"A:cap:{STEM}:1@capture", f"A:cap:{STEM}:2@capture"
DOCS = ["A:oas:response|statuses@v1", "A:spec:response|statuses@v1"]
C4 = "A:c4:quote_api|technology@v1"


def facts() -> dict:
    """S2 loaded as the gate command loads it: statuses, conflict gaps with what they concern,
    the agreeing pairs of a person and a document, the gate's level on the statuses key."""
    sys.path.insert(0, str(ROOT / "harness"))
    import gate_cli
    from gate import resolve
    from rules import compatible, pairs
    from store import open_store
    st = open_store(access="write")   # loads S2, published once the reads below are made (task-0141.02)
    try:
        gate_cli._load(st, "S2")
        status = {x["id"]: x["status"] for x in st.assertion_rows()}
        gaps = [{"id": g["id"], "text": g["text"], "concerns": sorted(c["id"] for c in g["concerns"] if c["id"])}
                for g in st.gaps_with_concerns() if g["kind"] == "conflict"]
        agree = sorted(sorted([p["a"], p["b"]]) for p, person in pairs(st)
                       if person and compatible(p["va"], p["vb"], p["pred"]) == "equal")
        level = resolve(st, "codegen")["keys"]["response|statuses"]["level"]
        st.commit()
        return {"store": st.name, "status": status, "conflicts": gaps, "agree": agree, "level": level}
    finally:
        st.close()


def load(env: dict) -> dict:
    p = subprocess.run([sys.executable, __file__, "--facts"], env=env, capture_output=True, text=True)
    if p.returncode:
        sys.exit(f"FAIL: loading S2:\n{p.stdout}{p.stderr}")
    return json.loads(p.stdout)


def main(out: Path) -> int:
    root = out / "instance"
    subprocess.run([sys.executable, str(ROOT / "tools" / "example_instance.py"), str(root)], check=True, capture_output=True)
    sys.path.insert(0, str(ROOT / "harness"))
    import cadence
    env = cadence.pin_record(dict(os.environ, KG_SUBJECT=str(root / "subjects" / "cargo_quote"), KG_REGISTER=str(root / "register"),
                                  PYTHONDONTWRITEBYTECODE="1"))   # the record's day, the wall clock refused (task-0075)
    before = load(env)
    capdir = root / "subjects" / "cargo_quote" / "captures"
    capdir.mkdir(parents=True, exist_ok=True)
    (capdir / f"{STEM}.toml").write_text(CAPTURE, encoding="utf-8")
    after = load(env)
    print(f"store {after['store']}; S2 before the capture: statuses {before['level']}, "
          f"{', '.join(f'{d} {before['status'][d]}' for d in DOCS)}; {C4} {before['status'][C4]}")

    errs = []
    mine = [g for g in after["conflicts"] if CAP_STATUSES in g["concerns"]]
    for d in DOCS:
        hit = [g for g in mine if d in g["concerns"]]
        if len(hit) != 1:
            errs.append(f"want one conflict gap naming {CAP_STATUSES} and {d}, got {hit}")
        else:
            print(f"conflict {hit[0]['id']}\n    {hit[0]['text']}")
    for x in [CAP_STATUSES, *DOCS]:
        if after["status"].get(x) != "disputed":
            errs.append(f"{x} is {after['status'].get(x)}, want disputed")
    if after["level"] != "disputed":
        errs.append(f"response|statuses reads {after['level']} at the gate, want disputed")
    if after["agree"] != [sorted([CAP_TECH, C4])]:
        errs.append(f"want {CAP_TECH} and {C4} recorded as agreeing, got {after['agree']}")
    else:
        print(f"agree {CAP_TECH} ~ {C4}: {after['status'][CAP_TECH]}, {after['status'][C4]}")
    if after["status"].get(CAP_TECH) != "proposed" or after["status"].get(C4) != before["status"][C4] or before["status"][C4] != "proposed":
        errs.append(f"agreement raised a status: {CAP_TECH} {after['status'].get(CAP_TECH)}, {C4} {before['status'][C4]} -> {after['status'].get(C4)}")
    moved = {x: (s, after["status"].get(x)) for x, s in before["status"].items() if x not in DOCS and after["status"].get(x) != s}
    if moved:
        errs.append(f"other assertions moved: {moved}")
    others = [g for g in after["conflicts"] if CAP_STATUSES not in g["concerns"] and CAP_TECH not in g["concerns"]]
    if sorted(g["id"] for g in others) != sorted(g["id"] for g in before["conflicts"]):
        errs.append(f"the documents' own conflicts changed: {before['conflicts']} -> {others}")
    if errs:
        sys.exit("FAIL:\n  " + "\n  ".join(errs))
    print("OK: a person contradicting two documents raises a conflict gap with each, all three disputed; "
          "a person agreeing with one corroborates it, both still proposed")
    return 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--facts"]:
        print(json.dumps(facts()))
        sys.exit(0)
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(Path(sys.argv[1]).resolve()))
