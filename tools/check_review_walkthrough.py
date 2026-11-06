"""The review step end to end, by command and exit code (task-0037, decision-0002), on the store
KG_STORE names: CI runs it on rdflib (harness.yml) and on Neo4j (the stack job).

    python tools/check_review_walkthrough.py OUT_DIR

It builds the public example instance into OUT_DIR, then:

S2' (S2 with REQ-06 no longer declared open: the rule decided, written nowhere). BLOCKED, exit 1;
employee-1 answers the three keys; the status list includes held_unscreened, the contract's and
the spec's do not, so the three statements are disputed (task-0038): BLOCKED, exit 1. A review by
employee-1 of its own answers is refused; employee-2 (approves) cannot overrule the documents'
status lists; employee-3 (closes) rejecting them without ruling on employee-1's side is refused
(half-settled); employee-3 rejecting them and approving employee-1's list settles the dispute, and
employee-2 approves the other two answers: PROCEED, exit 0 with --fail-on major. A review written
into the folder by hand is checked again on load and refused. With KG_TODAY past the six months the
approvals lapse, the dispute stays settled and the person's statements read proposed: QUALIFIED.

Its clock is pinned (task-0075): every command runs with KG_TODAY at the day its reviews are written
(ON) and KG_CLOCK=pinned, so the wall clock is never read and the outcome never moves by the calendar;
the lapse step reads six months on from ON.

S2 itself (task-0054): OD-1 names compliance as its owner, the register's ORG-0004 (its decision
0011). BLOCKED, exit 1; a close by employee-3 (closes, but ORG-0001) is refused; employee-1 answers
and the answers are ruled on as in S2' (the dispute settled whole), and the gate is still BLOCKED on the declared gap; employee-4
(closes, ORG-0004) closes OD-1: PROCEED, exit 0 with --fail-on major. Closing supplies no value
(decision-0002): on a fresh instance, employee-4's close before any answer leaves the key absent,
still BLOCKED.

S4: approving the table's side alone is refused (half-settled); employee-3 approving the table and
the spec and rejecting the diagram and the BPMN settles it: PROCEED.

The handles are the synthetic ones the vendored register issues (people/handles.toml). John Doe
is the reader's name for employee-1 only.
"""
from __future__ import annotations

import datetime as dt
import os
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "harness"
sys.path.insert(0, str(HARNESS))
import review  # noqa: E402  (KG_TODAY and KG_CLOCK for every command, task-0075)
OUT = "QuoteAPI|on_screening_outage"
STATUSES = "error: store_unavailable|held_unscreened|quoted|refused_screening|rejected: invalid_request|review_hold"
HELD = "priced=yes;status=held_unscreened;notified=no;hold=true"
REQ06 = 'new = "| REQ-06 | behaviour on a screening outage: NOT YET SPECIFIED (open decision OD-1, owner: compliance) |"'
DECIDED = 'new = "| REQ-06 | behaviour on a screening outage: decided by compliance under OD-1, held by the product owner |"'
ANSWERED_ON = "2026-11-02"   # employee-1's answers
ON = "2026-11-03"            # the reviews, and the walkthrough's today (KG_TODAY)
# the first day the approvals no longer hold: the day after six months from the answers' on (ieam-register decision 0008)
LAPSED = (review.add_months(dt.date.fromisoformat(ANSWERED_ON), review.LAPSE_MONTHS) + dt.timedelta(days=1)).isoformat()


def run(env: dict, *args: str) -> tuple[int, str]:
    p = subprocess.run([sys.executable, *args], cwd=HARNESS, env=env, capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr)


def expect(env: dict, want: int, contains: str, *args: str) -> str:
    code, out = run(env, *args)
    first = out.strip().splitlines()[0] if out.strip() else ""
    if code != want or contains not in out:
        sys.exit(f"FAIL: {' '.join(args)} exited {code} (want {want}), looking for {contains!r}:\n{out}")
    print(f"exit {code}: {' '.join(args[:3])}{' ...' if len(args) > 3 else ''}\n    {first}")
    return out


def instance(out: Path, name: str, decided: bool) -> dict:
    root = out / name
    subprocess.run([sys.executable, str(ROOT / "tools" / "example_instance.py"), str(root)], check=True, capture_output=True)
    if decided:
        p = root / "subjects" / "cargo_quote" / "plants.toml"
        s = p.read_text(encoding="utf-8")
        assert REQ06 in s, "the S2 plant that declares REQ-06 open"
        p.write_text(s.replace(REQ06, DECIDED), encoding="utf-8")
    env = dict(os.environ, KG_SUBJECT=str(root / "subjects" / "cargo_quote"), KG_REGISTER=str(root / "register"),
               PYTHONDONTWRITEBYTECODE="1")
    return review.pinned(env, ON)


def write_review(path: Path, by: str, scenario: str, rulings=(), closes=()) -> Path:
    lines = ["[review]", f'by = "{by}"', f"on = {ON}", 'record = "minutes/2026-11-03-outage-rule.md"', f'scenario = "{scenario}"']
    for aid, outcome in rulings:
        lines += ["", "[[ruling]]", f'assertion = "{aid}"', f'outcome = "{outcome}"']
    for gid in closes:
        lines += ["", "[[closes]]", f'gap = "{gid}"']
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def answer(env: dict, out: Path) -> str:
    """employee-1 answers ORG-0002's S2 questionnaire; returns the capture's stem."""
    qdir = out / "questionnaires"
    expect(env, 0, "Questionnaire for ORG-0002", "capture.py", "questionnaire", "--scenario", "S2", "--out", str(qdir))
    text = (qdir / "questionnaire-cargo_quote-S2-ORG-0002.toml").read_text(encoding="utf-8")
    text = text.replace('from = ""', 'from = "employee-1"', 1).replace('on = ""', f'on = "{ANSWERED_ON}"', 1)
    want = {OUT: HELD, "response|hold_presence": "held_unscreened only", "response|statuses": STATUSES}
    parts = text.split("[[item]]")
    for i, part in enumerate(parts[1:], 1):
        key = tomllib.loads(part)["key"]
        if key in want:
            parts[i] = part.replace('answer = ""', f'answer = "{want[key]}"', 1)
    answered = out / "answered.toml"
    answered.write_text("[[item]]".join(parts), encoding="utf-8")
    expect(env, 0, "captured 3 answer(s)", "capture.py", "ingest", str(answered))
    return f"A:cap:{ANSWERED_ON}-ORG-0002-employee-1"


def main(out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    print("== S2': the rule decided, written nowhere; employee-1 knows it")
    env = instance(out, "s2-decided", decided=True)
    w = out / "s2-decided"
    expect(env, 1, "BLOCKED", "gate_cli.py", "--scenario", "S2")
    cap = answer(env, w)
    expect(env, 1, "response|statuses (disputed)", "gate_cli.py", "--scenario", "S2")
    mine = [(f"{cap}:{i}@capture", "approved") for i in (1, 2, 3)]
    expect(env, 1, "gave this statement and may not rule on it", "capture.py", "review", str(write_review(w / "r-self.toml", "employee-1", "S2", mine)))
    docs = [("A:oas:response|statuses@v1", "rejected"), ("A:spec:response|statuses@v1", "rejected")]
    expect(env, 1, "needs the role closes", "capture.py", "review", str(write_review(w / "r-2-docs.toml", "employee-2", "S2", docs)))
    expect(env, 1, "half-settled", "capture.py", "review", str(write_review(w / "r-3-docs.toml", "employee-3", "S2", docs)))
    statuses = (f"{cap}:2@capture", "approved")   # the person's side of the dispute
    expect(env, 0, "3 ruling(s)", "capture.py", "review", str(write_review(w / "r-3.toml", "employee-3", "S2", [*docs, statuses])))
    rest = [(f"{cap}:{i}@capture", "approved") for i in (1, 3)]
    expect(env, 0, "2 ruling(s)", "capture.py", "review", str(write_review(w / "r-2.toml", "employee-2", "S2", rest)))
    expect(env, 0, "PROCEED", "gate_cli.py", "--scenario", "S2", "--fail-on", "major")
    # a review written straight into the folder, past the command, is checked again on every load
    write_review(w / "subjects" / "cargo_quote" / "captures" / "reviews" / f"{ON}-employee-1.toml", "employee-1", "S2",
                 [(f"{cap}:1@capture", "rejected")])
    expect(env, 0, f"review refused: captures/reviews/{ON}-employee-1.toml", "gate_cli.py", "--scenario", "S2", "--fail-on", "major")
    expect(dict(env, KG_TODAY=LAPSED), 0, "QUALIFIED", "gate_cli.py", "--scenario", "S2")

    print("== S2: OD-1 declared open, owned by compliance (ORG-0004); only its owner closes it")
    env = instance(out, "s2", decided=False)
    w = out / "s2"
    expect(env, 1, "QuoteAPI|on_screening_outage (declared_gap)", "gate_cli.py", "--scenario", "S2")
    expect(env, 1, "the declaration names 'compliance' (ORG-0004) as its owner; employee-3's unit is ORG-0001", "capture.py", "review",
           str(write_review(w / "r-close-3.toml", "employee-3", "S2", closes=["gap:declared:OD-1"])))
    cap = answer(env, w)
    expect(env, 0, "3 ruling(s)", "capture.py", "review", str(write_review(w / "r-3.toml", "employee-3", "S2", [*docs, (f"{cap}:2@capture", "approved")])))
    expect(env, 0, "2 ruling(s)", "capture.py", "review", str(write_review(w / "r-2.toml", "employee-2", "S2", [(f"{cap}:{i}@capture", "approved") for i in (1, 3)])))
    expect(env, 1, "BLOCKED — 1 required key(s) at a blocking level: QuoteAPI|on_screening_outage (declared_gap)",
           "gate_cli.py", "--scenario", "S2", "--fail-on", "major")
    expect(env, 0, "1 gap(s) closed", "capture.py", "review", str(write_review(w / "r-close-4.toml", "employee-4", "S2", closes=["gap:declared:OD-1"])))
    expect(env, 0, "PROCEED", "gate_cli.py", "--scenario", "S2", "--fail-on", "major")

    print("== S2: a close supplies no value; the key is then absent")
    env = instance(out, "s2-close-first", decided=False)
    expect(env, 0, "1 gap(s) closed", "capture.py", "review",
           str(write_review(out / "s2-close-first" / "r-close-4.toml", "employee-4", "S2", closes=["gap:declared:OD-1"])))
    expect(env, 1, "QuoteAPI|on_screening_outage (absent)", "gate_cli.py", "--scenario", "S2")

    print("== S4: two documents against two; a ruling on every side settles it")
    env = instance(out, "s4", decided=False)
    w = out / "s4"
    expect(env, 1, "disputed", "gate_cli.py", "--scenario", "S4")
    expect(env, 1, "half-settled", "capture.py", "review", str(write_review(w / "r-half.toml", "employee-3", "S4", [(f"A:dt:{OUT}@v1", "approved")])))
    expect(env, 1, "disputed", "gate_cli.py", "--scenario", "S4")
    settle = [(f"A:dt:{OUT}@v1", "approved"), (f"A:spec:{OUT}@v1", "approved"), (f"A:seq:{OUT}@v1", "rejected"), (f"A:bpmn:{OUT}@v1", "rejected")]
    expect(env, 0, "4 ruling(s)", "capture.py", "review", str(write_review(w / "r-settle.toml", "employee-3", "S4", settle)))
    rep = expect(env, 0, "PROCEED", "gate_cli.py", "--scenario", "S4", "-f", "json")
    assert '"conflicts": 0' in rep, "the settled conflicts are no longer listed"
    print("OK: S2' BLOCKED -> disputed by a person -> PROCEED, lapses after six months; S2 BLOCKED -> PROCEED by its owner's "
          "close, another unit's refused, a close alone supplies nothing; S4 settled whole")
    return 0


if __name__ == "__main__":
    import _outcomes   # task-0159: the outcome recorded when KG_OUTCOMES names a file
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(_outcomes.run(lambda: main(Path(sys.argv[1]).resolve())))
