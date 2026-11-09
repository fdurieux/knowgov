"""One clock (task-0198, doc-0030 F4: H3, G4, G10, M8; decision-0005 points 3 and 5): for one ``--as-of`` the
gate's report is the same whatever the day the store is loaded on (``KG_TODAY``), and every lapse is decided
against that date. On the store ``KG_STORE`` names, the example instance built under OUT_DIR:

    python tools/check_one_clock.py OUT_DIR

S2' (the review walkthrough's: the rule decided, written nowhere), employee-1's three answers, the documents'
status lists rejected and the answers approved by review files on ON:

- H3: ``--as-of ON`` reads PROCEED under KG_TODAY ON and under KG_TODAY six months on, byte for byte the same
  report; ``--as-of LAPSED`` (the day after six months from the answers) reads the person's statements
  ``proposed``, each a ``lapsed`` finding, QUALIFIED, again the same under both days.
- M8: the MCP reader's ``three_valued_answer``, its session as of LAPSED, marks those statements lapsed.

S2, a document statement with no verification (``A:spec:response|statuses@v1``, validated) approved by a review file:

- G4: it reads approved as of ON and lapses the day after ON plus its key's months, a ``lapsed`` finding.
- G10: as of the day before ON the approval is not counted: it reads validated, the finding says why.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tools")]
import check_review_walkthrough as w  # noqa: E402  (its instance, answers and reviews: one fixture, two checks)
import dates  # noqa: E402  (task-0262: one strict YYYY-MM-DD parse)
import review  # noqa: E402

ON, LAPSED = w.ON, w.LAPSED
LATER = LAPSED   # a second load day, six months on


def gate(env: dict, as_of: str, scenario: str = "S2") -> dict:
    p = subprocess.run([sys.executable, "gate_cli.py", "--scenario", scenario, "--as-of", as_of, "-f", "json"],
                       cwd=w.HARNESS, env=env, capture_output=True, text=True)
    if p.returncode == 2:
        sys.exit(f"FAIL: gate_cli --as-of {as_of} could not run:\n{p.stderr}")
    return json.loads(p.stdout)


def same_under_both_days(env: dict, as_of: str, errs: list[str]) -> dict:
    a, b = gate(review.pinned(env, ON), as_of), gate(review.pinned(env, LATER), as_of)
    if a != b:
        diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
        errs.append(f"--as-of {as_of}: the report differs between KG_TODAY {ON} and {LATER} on {diff}")
    return a


def main(out: Path) -> int:
    errs: list[str] = []
    out.mkdir(parents=True, exist_ok=True)

    print("== S2': a person's approvals, decided against --as-of only (H3)")
    env = w.instance(out, "s2-decided", decided=True)
    d = out / "s2-decided"
    cap = w.answer(env, d)
    docs = [("A:oas:response|statuses@v1", "rejected"), ("A:spec:response|statuses@v1", "rejected")]
    w.expect(env, 0, "3 ruling(s)", "capture.py", "review", str(w.write_review(d / "r-3.toml", "employee-3", "S2", [*docs, (f"{cap}:2@capture", "approved")])))
    w.expect(env, 0, "2 ruling(s)", "capture.py", "review", str(w.write_review(d / "r-2.toml", "employee-2", "S2", [(f"{cap}:{i}@capture", "approved") for i in (1, 3)])))
    now = same_under_both_days(env, ON, errs)
    if now["verdict"] != "PROCEED" or now["lapsed"]:
        errs.append(f"--as-of {ON}: want PROCEED with nothing lapsed, got {now['verdict']} {now['lapsed']}")
    late = same_under_both_days(env, LAPSED, errs)
    mine = sorted(f"{cap}:{i}@capture" for i in (1, 2, 3))
    found = sorted(f["ref"] for f in late["findings"] if f["kind"] == "lapsed" and f["ref"] in mine)
    if late["verdict"] != "QUALIFIED" or found != mine or any(f["level"] != "proposed" for f in late["findings"] if f["ref"] in mine):
        errs.append(f"--as-of {LAPSED}: want QUALIFIED with the three answers lapsed to proposed, got {late['verdict']}, {found}")
    print(f"    as of {ON}: {now['verdict']} under KG_TODAY {ON} and {LATER}; as of {LAPSED}: {late['verdict']}, {len(found)} answer(s) lapsed")

    print("== M8: three_valued_answer as of the session's date")
    store = d / "store.ttl"
    p = subprocess.run([sys.executable, "gate_cli.py", "--scenario", "S2", "--as-of", ON, "--publish"], cwd=w.HARNESS,
                       env={**review.pinned(env, ON), "KG_STORE": "rdflib", "KG_RDFLIB_FILE": str(store)}, capture_output=True, text=True)
    if p.returncode == 2:
        errs.append(f"the load for three_valued_answer could not run: {p.stderr[-400:]}")
    else:
        probe = ("import json, sys; sys.path.insert(0, '.'); import mcp_server; "
                 f"a = mcp_server.Tools(as_of='{LAPSED}').three_valued_answer({{'key': {w.OUT!r}, 'scenario': 'S2'}}); print(json.dumps(a))")
        q = subprocess.run([sys.executable, "-c", probe], cwd=w.HARNESS, capture_output=True, text=True,
                           env={**review.pinned(env, ON), "KG_STORE": "rdflib", "KG_RDFLIB_FILE": str(store)})
        ans = json.loads(q.stdout) if q.returncode == 0 else {}
        marked = [s["id"] for s in ans.get("statements", []) if s.get("lapsed") and s["status"] == "proposed"]
        if ans.get("as_of") != LAPSED or f"{cap}:1@capture" not in marked:
            errs.append(f"three_valued_answer as of {LAPSED} does not mark the person's statement lapsed: {ans.get('as_of')} {marked} {q.stderr[-300:]}")
        print(f"    three_valued_answer({w.OUT}) as of {ans.get('as_of')}: lapsed {marked}")

    print("== S2: a review-file approval of a document statement with no verification (G4), and one dated after the as-of (G10)")
    env = w.instance(out, "s2", decided=False)
    d = out / "s2"
    target = "A:spec:response|statuses@v1"
    w.expect(env, 0, "1 ruling(s)", "capture.py", "review", str(w.write_review(d / "r-approve.toml", "employee-3", "S2", [(target, "approved")])))
    sys.path.insert(0, str(w.HARNESS))
    os.environ.update(KG_SUBJECT=env["KG_SUBJECT"], KG_REGISTER=env["KG_REGISTER"])
    import cadence
    months = cadence.months_for("response|statuses")
    due = review.add_months(dates.parse(ON), months)
    level = lambda r: r["levels"].get("response|statuses")   # noqa: E731
    on_due = same_under_both_days(env, due.isoformat(), errs)
    after = same_under_both_days(env, (due + dt.timedelta(days=1)).isoformat(), errs)
    if any(f["ref"] == target for f in on_due["findings"] if f["kind"] == "lapsed"):
        errs.append(f"G4: {target} reads lapsed on its due day {due}")
    g4 = [f for f in after["findings"] if f["kind"] == "lapsed" and f["ref"] == target]
    if not g4 or g4[0]["level"] != "validated":
        errs.append(f"G4: {target}, approved on {ON} with no verification, does not lapse the day after {due}: {g4}")
    before = same_under_both_days(env, (dates.parse(ON) - dt.timedelta(days=1)).isoformat(), errs)
    g10 = [f for f in before["findings"] if f["kind"] == "lapsed" and f["ref"] == target]
    if not g10 or g10[0]["level"] != "validated" or "after the as-of date" not in g10[0]["message"]:
        errs.append(f"G10: as of the day before {ON} the approval dated {ON} is counted: {g10}")
    print(f"    {target}: approved on {ON}, {months} months; as of {due} {level(on_due)}, the day after lapsed ({len(g4)}); "
          f"the day before {ON} not counted ({len(g10)})")

    for e in errs:
        print("FAIL", e)
    print("one clock: " + ("every check holds" if not errs else f"{len(errs)} failure(s)"))
    return 1 if errs else 0


if __name__ == "__main__":
    import _outcomes   # task-0159: the outcome recorded when KG_OUTCOMES names a file
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(_outcomes.run(lambda: main(Path(sys.argv[1]).resolve())))
