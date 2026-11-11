"""A person's act binds to content (task-0199, doc-0030 F2: H5, I4, I9; doc-0032 §6 items 7 and 8), on the store
KG_STORE names, the public example instance built under OUT_DIR:

    python tools/check_act_binding.py OUT_DIR

Every gate runs ``--as-of`` ON with KG_TODAY ON and the clock pinned (task-0075).

- Binding: employee-3 (closes, ORG-0001) approves ``A:dt:S-accept|max@v1`` (41) on S1 through ``capture.py
  review``; the file records the statement's key, value and content digest.
- Item 8, a reordered table: DT-S's rows swapped; the ruling still lands on the same statement and the gate
  lists no act.
- H5, an edit after the ruling: the accept row reads ``risk_index <= 40``; the ruling is not applied to what the
  id now carries, and the gate lists an ``act`` finding (major) naming the file, employee-3, 41 and its digest
  to 40 and its digest, the owner ORG-0001 and the owner's route.
- A vanished statement: a hand-written file with one ruling on a statement no longer extracted and one on an
  unchanged statement: the second applies, the first is an ``act`` finding; the file is not refused whole.
- The read rule: a file from before 0.9.0 (no key, value or digest) is applied by id, an ``act`` finding at info.
- Item 8, renumbered answers (S2'): employee-1's answers ruled on as in the review walkthrough, then the
  capture's first answer moved last, so every answer has another id: the approvals follow their content (PROCEED, no
  act), and none lands on the answer that now carries the old id.
- task-0302 (decision-0032 C2-1): employee-2 approves employee-1's answer on ``response|hold_presence``, its capture
  is deleted and employee-3 gives the identical answer: a captured answer's digest is the empty text's, yet the
  approval does not move to another person's answer (not approved, a major ``gone`` act naming the vanished id);
  employee-1 giving it again on another day carries it (the same giver repairs).
- task-0308: ``ops`` ingests twice the same day, so its second file has ``ops-2``'s first stem; the approval of that id,
  its files deleted and ``ops-2`` giving the value, is not carried (not approved: a review recording ``ops`` as its
  giver a ``gone`` act, one written before without a giver a major ``ambiguous`` act).
- task-0320 (decision-0038 G1, G2): with ``ops`` and ``ops-2`` issued, ``ops-2``'s answers are ruled on as employee-1's
  are in the review walkthrough, the review recording ``ops-2`` from the capture's content: the dispute is settled and
  the gate PROCEEDs.
- Item 7 at stage 2 (S6): employee-3 approves P2's surcharge (316.00); ``--stage 2`` re-extracts the tariff
  change: the ruling is not moved onto the successor (341.00) and is an ``act`` finding naming both.
- I4: employee-3 approving the model's statement on S5 is refused (rejecting it is not).
- I9: a subject whose ``[verification] authored`` names no ``at`` is refused by check_subject, and the load
  applies it to nothing.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tools")]
import review  # noqa: E402
import check_review_walkthrough as w  # noqa: E402  (its instance, answers and review files: one fixture)
import review  # noqa: E402

ON = w.ON
KEY, AID = "S-accept|max", "A:dt:S-accept|max@v1"
P2, P2_AID = "P2|surcharge", "A:dt:P2|surcharge@v1"
TABLE = "artefacts/decision-tables/decision_table.md"
ACCEPT = "| accept | `risk_index <= 41` | quote issued | yes | yes (quote document) | `quoted` |"
REVIEW = "| review | `42 <= risk_index <= 66` | held for manual review | **no** | **no** | `review_hold` |"


def fresh(out: Path, name: str, decided: bool) -> dict:
    """A new example instance under ``out``; its commands' env with today ON and the wall clock refused (task-0075)."""
    return review.pinned(w.instance(out, name, decided), ON)


def _gate(env: dict, *args: str) -> dict:
    p = subprocess.run([sys.executable, "gate_cli.py", "--as-of", ON, "-f", "json", *args], cwd=w.HARNESS, env=env,
                       capture_output=True, text=True)
    if p.returncode == 2:
        sys.exit(f"FAIL: gate_cli {' '.join(args)} could not run:\n{p.stderr[-2000:]}")
    return json.loads(p.stdout)


def gate(env: dict, scenario: str, *extra: str) -> dict:
    """The gate on a private load; on the store KG_STORE names too, published and read back with ``--no-load``,
    so the acts are the store's own read (``act_findings``) on that adapter, and both reports must agree."""
    private = _gate(env, "--scenario", scenario, *extra)
    if os.environ.get("KG_STORE"):
        _gate(env, "--scenario", scenario, *extra, "--publish")
        held = _gate(env, "--scenario", scenario, "--no-load")
        if held["findings"] != private["findings"]:
            sys.exit(f"FAIL: {scenario} {' '.join(extra)}: the published store's findings differ from the private load's:\n"
                     f"{json.dumps([f for f in held['findings'] if f not in private['findings']], indent=1)[:2000]}")
    return private


def acts(rep: dict) -> list[dict]:
    return [f for f in rep["findings"] if f["kind"] == "act"]


def approvals(env: dict, scenario: str, key: str) -> dict[str, list[str]]:
    """statement id -> the ids of the approvals a person's review made of it, on a private load of ``scenario``."""
    probe = ("import json, sys; sys.path.insert(0, '.'); import gate_cli, store, gate; "
             "st = store.scratch_store(); st.__enter__(); "
             f"gate_cli._load(st, {scenario!r}); "
             f"print(json.dumps({{r['id']: [a['id'] for a in r['approvals'] if a['id'].startswith('appr:review:')] "
             f"for r in st.key_evidence({key!r}, gate.LIVE)}}))")
    p = subprocess.run([sys.executable, "-c", probe], cwd=w.HARNESS, env=env, capture_output=True, text=True)
    if p.returncode:
        sys.exit(f"FAIL: the approvals probe could not run:\n{p.stderr[-2000:]}")
    return json.loads(p.stdout.strip().splitlines()[-1])


def edit(root: Path, rel: str, old: str, new: str) -> None:
    p = root / rel
    s = p.read_text(encoding="utf-8")
    assert old in s, f"{rel}: {old!r}"
    p.write_text(s.replace(old, new, 1), encoding="utf-8")


def written(out: str) -> dict:
    m = re.search(r"into (\S+\.toml)", out)
    return tomllib.loads(Path(m.group(1)).read_text(encoding="utf-8"))


def giver_cases(out: Path) -> list[str]:
    """task-0302 (decision-0032 C2-1): employee-2 approves employee-1's answer, its capture is deleted, and the same
    value is given again by employee-3 (the approval must not follow) or by employee-1 (it must)."""
    errs: list[str] = []
    print("== task-0302: an approved answer's capture deleted, then another person's identical answer (S2')")
    hold = "response|hold_presence"
    for who, on, repairs in (("employee-3", ON, False), ("employee-1", ON, True)):
        env = fresh(out, f"giver-{who}", decided=True)
        d = out / f"giver-{who}"
        cap = w.answer(env, d)
        capdir = d / "subjects" / "cargo_quote" / "captures"
        capfile = next(capdir.glob("*.toml"))
        n = 1 + [a["key"] for a in tomllib.loads(capfile.read_text(encoding="utf-8"))["answer"]].index(hold)
        ruled = f"{cap}:{n}@capture"
        w.expect(env, 0, "1 ruling(s)", "capture.py", "review", str(w.write_review(d / "r.toml", "employee-2", "S2", [(ruled, "approved")])))
        capfile.unlink()   # the approved answer's capture gone; an identical answer given again, by another person or the same
        again = w.answer(env, d, handle=who, on=on, want={hold: "held_unscreened only"})
        got = {k: v for k, v in approvals(env, "S2", hold).items() if v}
        gone = [f for f in acts(gate(env, "S2")) if f["ref"] == ruled and f["act"]["why"] == "gone"]
        if repairs and (not any(k.startswith(again) for k in got) or gone):
            errs.append(f"task-0302: the same giver's re-ingested answer should carry the approval; got {got}, acts {gone}")
        if not repairs and (got or len(gone) != 1 or gone[0]["severity"] != "major"):
            errs.append(f"task-0302: {who}'s identical answer inherited employee-1's approval: approved {got}, gone acts {gone}")
        print(f"    {who} again on {on}: approved on {sorted(got) or 'nothing'}; "
              f"{gone[0]['severity'] + ' act: ' + gone[0]['message'] if gone else 'no gone act'}")
    return errs


def forged_cases(out: Path) -> list[str]:
    """task-0321 H1: the recorded giver is checked at the load. employee-2's approval of employee-1's answer records
    ``employee-1``; the capture deleted and employee-3 giving the same value, the file edited to name employee-3 as
    giver is an act finding (the key not approved), where the honest file is the ``gone`` act."""
    errs: list[str] = []
    print("== task-0321: a review's recorded giver edited to the person whose identical answer remains (S2')")
    hold = "response|hold_presence"
    env = fresh(out, "giver-forged", decided=True)
    d = out / "giver-forged"
    cap = w.answer(env, d)
    capdir = d / "subjects" / "cargo_quote" / "captures"
    capfile = next(capdir.glob("*.toml"))
    n = 1 + [a["key"] for a in tomllib.loads(capfile.read_text(encoding="utf-8"))["answer"]].index(hold)
    ruled = f"{cap}:{n}@capture"
    got = w.expect(env, 0, "1 ruling(s)", "capture.py", "review", str(w.write_review(d / "r.toml", "employee-2", "S2", [(ruled, "approved")])))
    saved = Path(re.search(r"into (\S+\.toml)", got).group(1))
    capfile.unlink()
    w.answer(env, d, handle="employee-3", want={hold: "held_unscreened only"})
    honest = [f for f in acts(gate(env, "S2")) if f["ref"] == ruled]
    saved.write_text(saved.read_text(encoding="utf-8").replace('giver = "employee-1"', 'giver = "employee-3"'), encoding="utf-8")
    held = {k: v for k, v in approvals(env, "S2", hold).items() if v}
    forged = [f for f in acts(gate(env, "S2")) if f["ref"] == ruled]
    if held or len(honest) != 1 or len(forged) != 1 or forged[0]["severity"] != "major" or not all(
            g in forged[0]["message"] for g in ("employee-3", "employee-1")):
        errs.append(f"task-0321: a forged giver should be a major act naming both givers and approve nothing: approved {held}, honest {honest}, forged {forged}")
    print(f"    approved on {sorted(held) or 'nothing'}; {forged[0]['severity'] + ' act: ' + forged[0]['message'] if forged else 'no act'}")
    return errs


def _ops(d: Path) -> None:
    """Issue ``ops`` and ``ops-2`` (gives) in the instance's register: a handle and its ``-<n>`` neighbour."""
    hp = d / "register" / "people" / "handles.toml"
    hp.write_text(hp.read_text(encoding="utf-8") + "".join(
        f'\n[[handle]]\nhandle = "{h}"\nunit = "ORG-0002"\nroles = ["gives"]\nissued = 2026-11-02\n' for h in ("ops", "ops-2")), encoding="utf-8")


def same_day_cases(out: Path) -> list[str]:
    """task-0322 J1: the legacy review (no giver) and employee-2's re-ruling the same day, which ``capture.py review``
    saves as ``<on>-<by>-2.toml``, a name that sorts before ``<on>-<by>.toml``: the re-ruling is still the later, so the
    ambiguous act is settled at info and the key reads approved."""
    errs: list[str] = []
    print("== task-0322: a same-day re-ruling settles the legacy ambiguous act (ops, ops-2)")
    hold = "response|hold_presence"
    env = fresh(out, "giver-same-day", decided=True)
    d = out / "giver-same-day"
    _ops(d)
    want = {hold: "held_unscreened only"}
    w.answer(env, d, handle="ops", want=want)
    w.answer(env, d, handle="ops", want=want)
    capdir = d / "subjects" / "cargo_quote" / "captures"
    second = next(capdir.glob("*-ops-2.toml"))
    n = 1 + [a["key"] for a in tomllib.loads(second.read_text(encoding="utf-8"))["answer"]].index(hold)
    ruled = f"A:cap:{second.stem}:{n}@capture"
    got = w.expect(env, 0, "1 ruling(s)", "capture.py", "review", str(w.write_review(d / "r.toml", "employee-2", "S2", [(ruled, "approved")])))
    saved = Path(re.search(r"into (\S+\.toml)", got).group(1))
    saved.write_text(re.sub(r'(?m)^giver = .*\n', "", saved.read_text(encoding="utf-8")), encoding="utf-8")   # a review from before the giver
    for f in capdir.glob("*-ops*.toml"):
        f.unlink()
    w.answer(env, d, handle="ops-2", want=want)
    before = [f for f in acts(gate(env, "S2")) if f["ref"] == ruled and f["act"]["why"] == "ambiguous"]
    w.expect(env, 0, "1 ruling(s)", "capture.py", "review", str(w.write_review(d / "r2.toml", "employee-2", "S2", [(ruled, "approved")])))
    second_review = sorted((capdir / "reviews").glob("*-employee-2-2.toml"))
    after = [f for f in acts(gate(env, "S2")) if f["ref"] == ruled and f["act"]["why"] == "ambiguous"]
    held = {k: v for k, v in approvals(env, "S2", hold).items() if v}
    if not second_review or len(before) != 1 or before[0]["severity"] != "major" or len(after) != 1 or after[0]["severity"] != "info" or not held:
        errs.append(f"task-0322: a same-day re-ruling should settle the legacy act at info: before {before}, after {after}, approved {held}")
    print(f"    approved on {sorted(held) or 'nothing'}; {after[0]['severity'] + ': ' + after[0]['message'][-90:] if after else 'no act'}")
    return errs


def x_n_cases(out: Path) -> list[str]:
    """task-0320 (decision-0038 G1, G2): with ``ops`` and ``ops-2`` both issued, ``ops-2``'s answers have the stem
    ``ops``'s second file of the day would have. The review records the giver from the capture's own content, so
    ``ops-2``'s answers are approved and the dispute its statuses answer raises is settled, as employee-1's are in the
    review walkthrough: PROCEED."""
    errs: list[str] = []
    print("== task-0320: X and X-n issued; X-n's answer approved and its dispute settled (S2')")
    env = fresh(out, "giver-x-n", decided=True)
    d = out / "giver-x-n"
    _ops(d)
    cap = w.answer(env, d, handle="ops-2")
    docs = [("A:oas:response|statuses@v1", "rejected"), ("A:spec:response|statuses@v1", "rejected")]
    got = w.expect(env, 0, "3 ruling(s)", "capture.py", "review",
                   str(w.write_review(d / "r-3.toml", "employee-3", "S2", [*docs, (f"{cap}:2@capture", "approved")])))
    givers = [r.get("giver") for r in written(got)["ruling"] if r["assertion"].startswith("A:cap:")]
    if givers != ["ops-2"]:
        errs.append(f"task-0320: the review should record ops-2, read from the capture's content, as the giver: {givers}")
    w.expect(env, 0, "2 ruling(s)", "capture.py", "review",
             str(w.write_review(d / "r-2.toml", "employee-2", "S2", [(f"{cap}:{i}@capture", "approved") for i in (1, 3)])))
    rep = gate(env, "S2", "--fail-on", "major")
    held = {k: v for k, v in approvals(env, "S2", "response|statuses").items() if v}
    if rep["verdict"] != "PROCEED" or acts(rep) or f"{cap}:2@capture" not in held:
        errs.append(f"task-0320: ops-2's answers ruled on should PROCEED with no act: {rep['verdict']}, acts {acts(rep)}, approved {held}")
    print(f"    {cap}: {rep['verdict']}, statuses approved on {sorted(held)}, {len(acts(rep))} act(s)")
    return errs


def stem_cases(out: Path) -> list[str]:
    """task-0308 (the re-check of task-0302): ``ops`` ingests twice the same day, so its second file shares a stem with
    ``ops-2``'s first. employee-2 approves ``…-ops-2:n``; since task-0320 the command records ``ops``, read from that
    file's content, as its giver. A file without the giver, saved before, keeps the stem's rule. Both files are deleted
    and ``ops-2`` gives the value again: neither approval passes to ``ops-2`` (not approved; the recorded giver's ruling
    a ``gone`` act, the file without one a major ``ambiguous`` act)."""
    errs: list[str] = []
    print("== task-0308: a capture stem that reads as two givers (ops, second file / ops-2, first file)")
    hold = "response|hold_presence"
    env = fresh(out, "giver-stem", decided=True)
    d = out / "giver-stem"
    _ops(d)
    want = {hold: "held_unscreened only"}
    first = w.answer(env, d, handle="ops", want=want)
    w.answer(env, d, handle="ops", want=want)
    capdir = d / "subjects" / "cargo_quote" / "captures"
    second = next(f for f in capdir.glob("*-ops-2.toml"))
    n = 1 + [a["key"] for a in tomllib.loads(second.read_text(encoding="utf-8"))["answer"]].index(hold)
    ruled = f"A:cap:{second.stem}:{n}@capture"
    rdir = capdir / "reviews"
    got = w.expect(env, 0, "1 ruling(s)", "capture.py", "review", str(w.write_review(d / "r.toml", "employee-2", "S2", [(ruled, "approved")])))
    if [r.get("giver") for r in written(got)["ruling"]] != ["ops"]:   # task-0320: the content's giver, never the stem's
        errs.append(f"task-0320: the review of {ruled} should record ops, its file's own from: {written(got)['ruling']}")
    # the file a reviewer had saved before task-0320: it carries key, value and sha256 and no giver, as the load reads it
    rdir.mkdir(parents=True, exist_ok=True)
    (rdir / "2026-11-05-employee-2.toml").write_text(review.review_toml(
        {"by": "employee-2", "on": dt.date(2026, 11, 5), "record": "minutes/2026-11-03-outage-rule.md", "scenario": "S2", "closes": [],
         "rulings": [{"assertion": ruled, "key": hold, "value": "held_unscreened only", "sha256": review.content_digest([]),
                      "outcome": "approved"}]}), encoding="utf-8")
    for f in capdir.glob("*-ops*.toml"):
        f.unlink()
    again = w.answer(env, d, handle="ops-2", want=want)
    got = {k: v for k, v in approvals(env, "S2", hold).items() if v}
    mine = [f for f in acts(gate(env, "S2")) if f["ref"] == ruled]
    found = [f for f in mine if f["act"]["why"] == "ambiguous"]
    gone = [f for f in mine if f["act"]["why"] in ("gone", "changed")]
    if got or len(found) != 1 or found[0]["severity"] != "major" or len(gone) != 1:
        errs.append(f"task-0308: ops-2's answer inherited the approval of {ruled}: approved {got}, ambiguous acts {found}, gone acts {gone}")
    print(f"    {first} twice, then {again}: approved on {sorted(got) or 'nothing'}; "
          f"{found[0]['severity'] + ' ambiguous act' if found else 'no ambiguous act'}, {len(gone)} gone act(s) for the giver's ruling")
    # task-0321 H2: a later review (6 November) rules on ops-2's answer, the same id and content, binding by the giver it records
    (rdir / "2026-11-06-employee-3.toml").write_text(review.review_toml(
        {"by": "employee-3", "on": dt.date(2026, 11, 6), "record": "minutes/2026-11-03-outage-rule.md", "scenario": "S2", "closes": [],
         "rulings": [{"assertion": ruled, "key": hold, "value": "held_unscreened only", "sha256": review.content_digest([]),
                      "outcome": "approved", "giver": "ops-2"}]}), encoding="utf-8")
    settled = [f for f in acts(gate(env, "S2")) if f["ref"] == ruled and f["act"]["why"] == "ambiguous"]
    held = {k: v for k, v in approvals(env, "S2", hold).items() if v}
    if len(settled) != 1 or settled[0]["severity"] != "info" or "2026-11-06-employee-3" not in settled[0]["message"] or not held:
        errs.append(f"task-0321: the ambiguous act should read info naming the review that settled it, the key approved: {settled}, approved {held}")
    print(f"    settled by a later review: approved on {sorted(held) or 'nothing'}; "
          f"{settled[0]['severity'] + ': ' + settled[0]['message'][-80:] if settled else 'no ambiguous act'}")
    return errs


def _opposed_case(out: Path, hold: str, name: str, a: str, oa: str, b: str, ob: str, clash: bool, later: str | None = None) -> list[str]:
    """One pair of same-day rulings (reviewer ``a`` then ``b``), written, loaded and read by the gate; with ``later``, a
    ruling of that outcome by employee-3 on 8 November (task-0331: the remedy, or a rejection, after the pair)."""
    env = fresh(out, f"opposed-{name}", decided=True)
    d = out / f"opposed-{name}"
    hp = d / "register" / "people" / "handles.toml"
    hp.write_text(hp.read_text(encoding="utf-8") + '\n[[handle]]\nhandle = "boss"\nunit = "ORG-0002"\nroles = ["gives", "approves"]\nissued = 2026-11-02\n',
                  encoding="utf-8")
    cap = w.answer(env, d)
    capdir = d / "subjects" / "cargo_quote" / "captures"
    ruled = f"{cap}:{1 + [x['key'] for x in tomllib.loads(next(capdir.glob('*.toml')).read_text(encoding='utf-8'))['answer']].index(hold)}@capture"
    saved = None
    for who, outcome in ((a, oa), (b, ob)):
        saved = written(w.expect(env, 0, "1 ruling(s)", "capture.py", "review", str(w.write_review(d / f"r-{who}.toml", who, "S2", [(ruled, outcome)]))))
    if later:
        (capdir / "reviews" / "2026-11-08-employee-3.toml").write_text(review.review_toml(
            {"by": "employee-3", "on": dt.date(2026, 11, 8), "record": "minutes/2026-11-03-outage-rule.md", "scenario": "S2", "closes": [],
             "rulings": [{**saved["ruling"][0], "outcome": later}]}), encoding="utf-8")
    live = approvals(env, "S2", hold)   # every live statement of the key: a rejected one is absent, a proposed one is here
    got = {k: v for k, v in live.items() if v}
    mine = [f for f in acts(gate(env, "S2")) if f["ref"] == ruled and f["act"]["why"] == "ambiguous"]
    named = len(mine) == 2 and all(all(x in f["message"] for x in (f"{ON}-{a}", f"{ON}-{b}")) and "several statements" not in f["message"]
                                   and "capture.py review" in f.get("route", "") for f in mine)
    sev = {"approved": "info", "rejected": "major", None: "major"}[later]
    if not clash:
        ok = not mine and ruled in got
    elif later == "approved":
        ok = named and {f["severity"] for f in mine} == {"info"} and all("settled by" in f["message"] for f in mine) and ruled in got
    else:
        ok = (named and {f["severity"] for f in mine} == {sev} and not got and (later is None or ruled not in live)
              and (later is None or all("ruled by" in f["message"] for f in mine)) and (later is not None or ruled in live)
              and {f["act"]["by"] for f in mine} == {a, b})
    print(f"    {name} ({a} {oa}, {b} {ob}{', then ' + later if later else ''}): approved on {sorted(got) or 'nothing'}; "
          f"{mine[0]['severity'] + ': ' + mine[0]['message'][-110:] if mine else 'no act'}")
    return [] if ok else [f"task-0328/0331 {name}: acts {mine}, approved {got}, live {sorted(live)}"]


def opposed_cases(out: Path) -> list[str]:
    """task-0328, task-0331: employee-2 and ``boss`` rule on employee-1's answer the same day, one approving and one not.
    Neither ruling applies, whichever file comes first: a major act per file, each naming both files and routed to
    ``capture.py review``, the statement unapproved and still live; two rulings that agree keep their approval. A later
    day's approval settles both acts at info (the key approved by it), a later rejection leaves them major."""
    errs: list[str] = []
    print("== task-0328, task-0331: opposing rulings of one answer on one day by two reviewers (S2')")
    hold = "response|hold_presence"
    cases = (("approve-last", "boss", "rejected", "employee-2", "approved", True), ("approve-first", "boss", "approved", "employee-2", "rejected", True),
             ("referred", "boss", "referred", "employee-2", "approved", True), ("agree", "boss", "approved", "employee-2", "approved", False),
             ("settled", "boss", "rejected", "employee-2", "approved", True, "approved"),
             ("ruled-again", "boss", "rejected", "employee-2", "approved", True, "rejected"))
    for case in cases:
        errs += _opposed_case(out, hold, *case)
    return errs


def main(out: Path) -> int:
    errs: list[str] = []
    out.mkdir(parents=True, exist_ok=True)
    if os.environ.get("KG_STORE") == "rdflib":   # the published store a --no-load reads back: a file, as the stack's is a server
        os.environ.setdefault("KG_RDFLIB_FILE", str(out / "store.ttl"))

    print("== S1: a ruling records what it ruled on")
    env = fresh(out, "s1", decided=False)
    d = out / "s1"
    reviews = d / "subjects" / "cargo_quote" / "captures" / "reviews"
    got = w.expect(env, 0, "1 ruling(s)", "capture.py", "review", str(w.write_review(d / "r.toml", "employee-3", "S1", [(AID, "approved")])))
    ru = written(got)["ruling"][0]
    if (ru.get("key"), ru.get("value"), len(str(ru.get("sha256", "")))) != (KEY, "41", 64):
        errs.append(f"the review file records {ru}: want key {KEY}, value 41 and a sha256")
    held = approvals(env, "S1", KEY)
    if not held.get(AID):
        errs.append(f"the ruling is not applied to {AID}: {held}")
    if acts(gate(env, "S1")):
        errs.append(f"S1 with a bound ruling lists an act: {acts(gate(env, 'S1'))}")

    print("== item 8: DT-S's rows reordered, the same content: the ruling stays on its statement")
    edit(d, TABLE, f"{ACCEPT}\n{REVIEW}", f"{REVIEW}\n{ACCEPT}")
    rep, held = gate(env, "S1"), approvals(env, "S1", KEY)
    if acts(rep) or not held.get(AID):
        errs.append(f"a reordered table moved or dropped the ruling: acts {acts(rep)}, approvals {held}")
    print(f"    acts {len(acts(rep))}; {AID} approved by {held.get(AID)}")

    print("== H5: the accept row edited after the ruling (41 -> 40): not applied, and the gate says so")
    edit(d, TABLE, "`risk_index <= 41`", "`risk_index <= 40`")
    rep, held = gate(env, "S1"), approvals(env, "S1", KEY)
    a = [f for f in acts(rep) if f["ref"] == AID]
    want = a and a[0]["severity"] == "major" and a[0]["act"]["why"] == "changed" and a[0]["act"]["by"] == "employee-3" \
        and a[0]["act"]["from"] == {"value": "41", "sha256": ru.get("sha256")} and [t["value"] for t in a[0]["act"]["to"]] == ["40"] \
        and a[0].get("owner") == "ORG-0001" and a[0].get("route") and "'41'" in a[0]["message"] and "'40'" in a[0]["message"]
    if not want:
        errs.append(f"H5: want one major act finding naming employee-3, 41 to 40, ORG-0001 and its route; got {a}")
    if any(held.values()):
        errs.append(f"H5: the ruling on 41 still approves what the store holds now: {held}")
    print(f"    {a[0]['message'] if a else 'no act finding'} [owner {a[0].get('owner') if a else None}]")

    print("== a vanished statement: the rest of the file applies")
    p2 = approvals(env, "S1", P2)
    rest = written(w.expect(env, 0, "1 ruling(s)", "capture.py", "review", str(w.write_review(d / "r2.toml", "employee-3", "S1", [(P2_AID, "approved")]))))
    hand = reviews / f"{ON}-employee-3-hand.toml"
    gone = {"assertion": "A:dt:S-accept|ceiling@v1", "key": "S-accept|ceiling", "value": "41", "sha256": ru.get("sha256", "0" * 64), "outcome": "approved"}
    hand.write_text(f'[review]\nby = "employee-3"\non = {ON}\nrecord = "minutes/x.md"\nscenario = "S1"\n'
                    + "".join("\n[[ruling]]\n" + "".join(f"{k} = {json.dumps(v)}\n" for k, v in r.items())
                              for r in (gone, {**rest["ruling"][0], "outcome": "approved"})), encoding="utf-8")
    for f in sorted(reviews.glob("*.toml")):   # only the hand file rules on P2 from here
        if f != hand and "P2|surcharge" in f.read_text(encoding="utf-8"):
            f.unlink()
    rep, p2 = gate(env, "S1"), approvals(env, "S1", P2)
    g = [f for f in acts(rep) if f["ref"] == gone["assertion"]]
    if not g or g[0]["act"]["why"] != "gone" or g[0]["severity"] != "major" or not any(f"review:{hand.stem}" in x for x in p2.get(P2_AID, [])):
        errs.append(f"a vanished statement: want a major 'gone' act and the file's other ruling applied; got {g}, approvals {p2}")
    print(f"    {g[0]['message'] if g else 'no act finding'}; {P2_AID} approved by {p2.get(P2_AID)}")

    print("== the read rule: a file from before 0.9.0, bound by id")
    old = reviews / f"{ON}-employee-3-old.toml"
    old.write_text(f'[review]\nby = "employee-3"\non = {ON}\nrecord = "minutes/x.md"\nscenario = "S1"\n\n'
                   f'[[ruling]]\nassertion = "A:dt:S-review|min@v1"\noutcome = "approved"\n', encoding="utf-8")
    rep = gate(env, "S1")
    u = [f for f in acts(rep) if f["act"]["why"] == "unbound"]
    if len(u) != 1 or u[0]["severity"] != "info" or not approvals(env, "S1", "S-review|min").get("A:dt:S-review|min@v1"):
        errs.append(f"the read rule: want one info act, the ruling applied by id; got {u}")
    print(f"    {u[0]['severity'] if u else '-'}: {u[0]['message'] if u else 'no act finding'}")

    print("== item 8: employee-1's answers renumbered (S2'); the approvals follow their content")
    env = fresh(out, "s2-decided", decided=True)
    d = out / "s2-decided"
    cap = w.answer(env, d)
    docs = [("A:oas:response|statuses@v1", "rejected"), ("A:spec:response|statuses@v1", "rejected")]
    w.expect(env, 0, "3 ruling(s)", "capture.py", "review", str(w.write_review(d / "r-3.toml", "employee-3", "S2", [*docs, (f"{cap}:2@capture", "approved")])))
    w.expect(env, 0, "2 ruling(s)", "capture.py", "review", str(w.write_review(d / "r-2.toml", "employee-2", "S2", [(f"{cap}:{i}@capture", "approved") for i in (1, 3)])))
    before = gate(env, "S2")
    capfile = next((d / "subjects" / "cargo_quote" / "captures").glob("*.toml"))
    text = capfile.read_text(encoding="utf-8")
    head, *items = text.split("[[answer]]")
    items = [i if i.endswith("\n") else i + "\n" for i in items]
    capfile.write_text("[[answer]]".join([head, *items[1:], items[0]]), encoding="utf-8")   # answer 1 last: every answer renumbered
    after = gate(env, "S2")
    moved = {k: v for k, v in approvals(env, "S2", w.OUT).items() if v}
    if before["verdict"] != "PROCEED" or after["verdict"] != "PROCEED" or acts(after) or after["levels"] != before["levels"]:
        errs.append(f"renumbered answers: want PROCEED twice, the same levels and no act; got {before['verdict']} then "
                    f"{after['verdict']}, acts {acts(after)}, levels {sorted(set(after['levels'].items()) ^ set(before['levels'].items()))}")
    if f"{cap}:1@capture" in moved:
        errs.append(f"renumbered answers: the approval of answer 1 stayed on its id, which now carries another answer: {moved}")
    print(f"    {before['verdict']} -> {after['verdict']}; {w.OUT} approved on {sorted(moved)}")

    errs += giver_cases(out)
    errs += forged_cases(out)
    errs += stem_cases(out)
    errs += same_day_cases(out)
    errs += x_n_cases(out)
    errs += opposed_cases(out)

    print("== item 7 at stage 2 (S6): a ruling on P2's surcharge, then the tariff change")
    env = fresh(out, "s6", decided=False)
    d = out / "s6"
    w.expect(env, 0, "1 ruling(s)", "capture.py", "review", str(w.write_review(d / "r.toml", "employee-3", "S6", [(P2_AID, "approved")])))
    one, two = gate(env, "S6"), gate(env, "S6", "--stage", "2")
    a = [f for f in acts(two) if f["ref"] == P2_AID]
    if acts(one) or not a or a[0]["act"]["why"] != "changed" or [t["value"] for t in a[0]["act"]["to"]] != ["341.00"]:
        errs.append(f"stage 2: want no act at stage 1 and a changed act 316.00 -> 341.00 after; got {acts(one)} then {a}")
    print(f"    stage 1: {len(acts(one))} act(s); stage 2: {a[0]['message'] if a else 'no act finding'}")

    print("== I4: a model's statement is never approved by a ruling (S5)")
    env = fresh(out, "s5", decided=False)
    d = out / "s5"
    llm = "A:llm:QuoteAPI|on_screening_outage@v1"
    code, said = w.run(env, "capture.py", "review", str(w.write_review(d / "r-yes.toml", "employee-3", "S5", [(llm, "approved")])))
    if code != 1 or "never approve it" not in said:
        errs.append(f"I4: employee-3's approval of the model's statement is not refused as such: exit {code}, {said.strip()[-300:]}")
    print(f"    approving it: exit {code}; {next((x for x in said.splitlines() if 'never approve' in x), 'accepted').strip()[:160]}")
    code, said = w.run(env, "capture.py", "review", str(w.write_review(d / "r-no.toml", "employee-3", "S5", [(llm, "rejected")])))
    if "never approve it" in said:
        errs.append(f"I4: a rejection of the model's statement is refused as an approval: {said[-400:]}")

    print("== I9: an undated attestation is refused, and applied to nothing")
    env = fresh(out, "i9", decided=False)
    d = out / "i9"
    edit(d, "subjects/cargo_quote/subject.toml", 'authored = { at = "2026-10-30", ', "authored = { ")
    c = subprocess.run([sys.executable, str(ROOT / "tools" / "check_subject.py"), str(d / "subjects" / "cargo_quote"), "--json",
                        "--register", env["KG_REGISTER"]], env=env, capture_output=True, text=True)
    rep_c = json.loads(c.stdout) if c.stdout.strip().startswith("{") else {}
    rules = [x.get("rule") for x in rep_c.get("findings", []) if x.get("level") == "error"]
    if c.returncode == 0 or "attestation" not in rules:
        errs.append(f"I9: check_subject accepts an undated [verification] authored: exit {c.returncode}, errors {rules} {c.stderr[-300:]}")
    p = subprocess.run([sys.executable, "gate_cli.py", "--scenario", "S1", "--as-of", ON], cwd=w.HARNESS, env=env, capture_output=True, text=True)
    if "attestation not applied: authored" not in p.stderr:
        errs.append(f"I9: the load does not say it set the undated attestation aside: {p.stderr[-400:]}")
    print(f"    check_subject exit {c.returncode} ({', '.join(sorted(set(r for r in rules if r)))}); the load: "
          f"{next((x for x in p.stderr.splitlines() if 'attestation not applied' in x), 'silent')}")

    for e in errs:
        print("FAIL", e)
    print(f"acts bound to content ({'on ' + os.environ['KG_STORE'] if os.environ.get('KG_STORE') else 'private loads'}): " + ("every check holds" if not errs else f"{len(errs)} failure(s)"))
    return 1 if errs else 0


if __name__ == "__main__":
    import _outcomes   # task-0159: the outcome recorded when KG_OUTCOMES names a file
    if len(sys.argv) != 2 or sys.argv[1].startswith("-"):   # task-0308 R3: --help is not an output folder
        print(__doc__)
        sys.exit(0 if sys.argv[1:] in (["-h"], ["--help"]) else 2)
    sys.exit(_outcomes.run(lambda: main(Path(sys.argv[1]).resolve())))
