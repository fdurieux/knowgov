"""Task-0199, doc-0030 F2 (H5, I4, I9) and doc-0032 §6 items 7 and 8: a person's act binds to what it ruled on.
tools/check_act_binding.py holds it end to end on the example instance; it runs here on rdflib, and in CI on
rdflib (harness.yml) and on Neo4j (demo.yml's stack job). The unit tests below need no store."""
from __future__ import annotations

import ast
import datetime as dt
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tools"), str(Path(__file__).resolve().parent)]
from _skip import need_rdflib  # noqa: E402
import review  # noqa: E402

TOOL = "tools/check_act_binding.py"
KEY = "S-accept|max"


class Store:
    """What review.bind reads: assertion_brief and key_evidence, over rows with fragments."""

    def __init__(self, rows):
        self.rows = rows

    def assertion_brief(self, aid):
        r = next((x for x in self.rows if x["id"] == aid), None)
        return None if r is None else {k: r[k] for k in ("id", "key", "value", "basis", "status")} | {"agent": "harness"}

    def key_evidence(self, key, live):
        return [x for x in self.rows if x["key"] == key and x["status"] in live]


def _row(aid, value, text, key=KEY, status="verified"):
    return {"id": aid, "key": key, "value": value, "basis": "extracted", "status": status, "fragments": [{"text": text, "locator": "row 1"}]}


ROW = "| accept | `risk_index <= 41` | quote issued |"


def _ruling(aid="A:dt:S-accept|max@v1", value="41", text=ROW):
    return {"assertion": aid, "key": KEY, "value": value, "sha256": review.content_digest([{"text": text}]), "outcome": "approved"}


def test_a_ruling_binds_to_its_statement_while_it_holds_its_content():
    b, how = review.bind(Store([_row("A:dt:S-accept|max@v1", "41", ROW)]), _ruling())
    assert b["id"] == "A:dt:S-accept|max@v1" and how["why"] == "content" and b["sha256"] == _ruling()["sha256"]


def test_an_edit_under_the_same_id_is_changed_and_names_what_the_store_holds():
    b, how = review.bind(Store([_row("A:dt:S-accept|max@v1", "40", ROW.replace("41", "40"))]), _ruling())
    assert b is None and how["why"] == "changed" and [t["value"] for t in how["to"]] == ["40"], how


def test_a_successor_with_other_content_is_changed_never_bound():
    st = Store([_row("A:dt:S-accept|max@v1", "41", ROW, status="invalidated"), _row("A:dt:S-accept|max@v2", "40", ROW.replace("41", "40"))])
    b, how = review.bind(st, _ruling())
    assert b is None and how["why"] == "changed" and [t["id"] for t in how["to"]] == ["A:dt:S-accept|max@v2"], how


def test_the_same_content_under_another_id_is_repaired_and_another_content_under_the_old_id_is_not_ruled():
    """Item 8: a renumbering puts the statement ruled on at another id, and another statement at its old one."""
    st = Store([_row("A:x:2", "41", ROW), _row("A:x:1", "17", "other", key="S-review|min")])
    b, how = review.bind(st, _ruling(aid="A:x:1"))
    assert b["id"] == "A:x:2" and how["why"] == "repaired", (b, how)


def test_a_vanished_statement_is_gone_and_two_holders_of_one_content_are_ambiguous():
    assert review.bind(Store([]), _ruling())[1]["why"] == "gone"
    st = Store([_row("A:x:2", "41", ROW), _row("A:x:3", "41", ROW)])
    assert review.bind(st, _ruling(aid="A:x:1")) == (None, {"why": "ambiguous", "to": []})


def test_the_read_rule_binds_a_file_from_before_by_id():
    b, how = review.bind(Store([_row("A:dt:S-accept|max@v1", "40", ROW)]), {"assertion": "A:dt:S-accept|max@v1", "outcome": "approved"})
    assert b["id"] == "A:dt:S-accept|max@v1" and how["why"] == "unbound"


def test_the_written_file_carries_the_content_it_was_checked_on():
    import tomllib
    norm = {"by": "employee-3", "on": dt.date(2026, 11, 3), "record": "m.md", "scenario": "S1", "closes": [],
            "rulings": [{"assertion": "A:dt:S-accept|max@v1", "key": KEY, "value": "41", "sha256": "ab" * 32, "outcome": "approved", "note": ""}]}
    ru = tomllib.loads(review.review_toml(norm))["ruling"][0]
    assert (ru["key"], ru["value"], ru["sha256"]) == (KEY, "41", "ab" * 32)


def test_a_lapse_with_no_date_at_all_is_unreachable_and_says_why():
    """The F4 edge: min() of nothing. Every person's act now carries its date, so it is an assertion, not a crash."""
    import cadence
    row = {"id": "A:x@v1", "status": "approved", "basis": "extracted", "verifications": [],
           "approvals": [{"id": f"{cadence.RULING}r:A:x@v1", "at": None}]}
    try:
        cadence.lapse(row, KEY, dt.date(2026, 11, 3))
    except AssertionError as e:
        assert "task-0199" in str(e), e
    else:
        raise AssertionError("an undated approval read as if it had a date")


def test_the_load_never_dates_an_attestation_by_its_own_day_nor_defaults_its_attester():
    src = (ROOT / "harness" / "load.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "load_verifications")
    body = ast.get_source_segment(src, fn)
    assert '.get("at", ts)' not in body and 'HUMAN["id"]' not in body and "ATTESTER" in body, "I9"
    change = (ROOT / "harness" / "change.py").read_text(encoding="utf-8")
    assert 'cfg2.get("at", "")' not in change and "attestation(" in change


def test_the_act_port_is_a_read_on_both_adapters_and_in_the_mcp_view():
    import store
    assert "act_findings" in store.READS and "record_act_finding" not in store.READS
    for name in ("store_rdflib.py", "store_neo4j.py"):
        src = (ROOT / "harness" / name).read_text(encoding="utf-8")
        assert "def record_act_finding(self" in src and "def act_findings(self" in src, name
    assert '"act_findings"' in (ROOT / "harness" / "mcp_server.py").read_text(encoding="utf-8")


def test_the_check_holds_on_rdflib():
    need_rdflib()
    with tempfile.TemporaryDirectory() as td:
        env = {**os.environ, "KG_STORE": "rdflib", "PYTHONDONTWRITEBYTECODE": "1"}
        env.pop("KG_RDFLIB_FILE", None)
        p = subprocess.run([sys.executable, str(ROOT / TOOL), str(Path(td) / "out")], env=env, cwd=ROOT,
                           capture_output=True, text=True, timeout=1500)
        assert p.returncode == 0 and "every check holds" in p.stdout, p.stdout[-3000:] + p.stderr[-1500:]


def test_ci_runs_it_on_both_stores():
    assert f"KG_STORE=rdflib python {TOOL} runs/act-binding" in (ROOT / ".github" / "workflows" / "harness.yml").read_text(encoding="utf-8")
    assert f"python {TOOL} runs/act-binding" in (ROOT / ".github" / "workflows" / "demo.yml").read_text(encoding="utf-8")


def _check(rulings, rows, strict):
    reg = ROOT / "demo" / "register"
    doc = {"review": {"by": "employee-3", "on": "2026-11-03", "record": "m.md"}, "ruling": rulings}
    return review.check(doc, Store(rows), handles=review.issued_handles(reg), owners={KEY: ["ORG-0001"]},
                        units=review.organisation_units(reg), captures={}, now=dt.date(2026, 11, 3),
                        compatible=lambda a, b, _p="": "equal" if a == b else "conflict", strict=strict)


def test_i4_a_model_statement_is_rejected_or_referred_never_approved():
    llm = [{**_row("A:llm:x@v1", "41", ROW), "basis": "inferred", "status": "proposed"}]
    for outcome, refused in (("approved", True), ("rejected", False), ("referred", False)):
        errs, _ = _check([{"assertion": "A:llm:x@v1", "outcome": outcome}], llm, strict=True)
        assert any("never approve it" in e for e in errs) is refused, (outcome, errs)


def test_a_load_sets_aside_the_act_that_no_longer_binds_and_applies_the_rest():
    rows = [_row("A:dt:S-accept|max@v1", "40", ROW.replace("41", "40")), _row("A:dt:S-accept|max@v9", "7", "seven")]
    keep = {"assertion": "A:dt:S-accept|max@v9", "key": KEY, "value": "7", "sha256": review.content_digest([{"text": "seven"}]),
            "outcome": "approved"}
    errs, rv = _check([_ruling(), keep], rows, strict=False)
    assert not errs and [r["statement"] for r in rv["rulings"]] == ["A:dt:S-accept|max@v9"], (errs, rv["rulings"])
    assert [(x["n"], x["why"], x["value"]) for x in rv["skipped"]] == [(1, "changed", "41")], rv["skipped"]
    errs, _ = _check([_ruling(), keep], rows, strict=True)   # the day it is written, the same file is refused
    assert any("no longer holds what the ruling records" in e for e in errs), errs


def _answer(stem, n, handle, value="held_unscreened only", key="response|hold_presence"):
    """A captured answer as the store holds it: no fragments (its digest is the empty text's) and its giver."""
    return {"id": f"A:cap:{stem}:{n}@capture", "key": key, "value": value, "basis": "elicited", "status": "approved",
            "fragments": [], "agent": handle}


def _answer_ruling(aid, value="held_unscreened only", key="response|hold_presence"):
    return {"assertion": aid, "key": key, "value": value, "sha256": review.content_digest([]), "outcome": "approved"}


def test_a_vanished_answer_is_never_repaired_by_another_persons_identical_answer():
    """task-0302 (decision-0032 C2-1): a captured answer's digest is the empty text's, so another person's identical
    answer held the ruling's content and won as "repaired" once the ruled answer's capture was deleted."""
    ruled = "A:cap:2026-11-05-ORG-0002-employee-1:1@capture"
    assert review.content_digest([]).startswith("e3b0c442")
    st = Store([_answer("2026-11-06-ORG-0002-employee-3", 1, "employee-3")])
    b, how = review.bind(st, _answer_ruling(ruled))
    assert b is None and how["why"] == "gone", (b, how)
    # nor through a handle that ends where the ruled one does, nor a file renamed by a second capture the same day
    for stem, handle in (("2026-11-06-ORG-0002-x-employee-1", "x-employee-1"), ("2026-11-06-ORG-0002-employee-1-2", "employee-1-2")):
        assert review.bind(Store([_answer(stem, 1, handle)]), _answer_ruling(ruled))[0] is None, stem
    assert review.bind(Store([_answer("2026-11-06-ORG-0002-employee-1", 1, "employee-1")]),
                       _answer_ruling("A:cap:2026-11-05-ORG-0002-employee-1-2:1@capture"))[0] is None


def test_the_same_givers_answer_given_again_still_repairs():
    """The reverse: the same person's identical answer, captured again under another id, carries the ruling."""
    ruled = "A:cap:2026-11-05-ORG-0002-employee-1:1@capture"
    st = Store([_answer("2026-11-06-ORG-0002-employee-1", 2, "employee-1"), _answer("2026-11-06-ORG-0002-employee-3", 1, "employee-3")])
    b, how = review.bind(st, _answer_ruling(ruled))
    assert b["id"] == "A:cap:2026-11-06-ORG-0002-employee-1:2@capture" and how["why"] == "repaired", (b, how)
    assert review.bind(Store([_answer("2026-11-05-ORG-0002-employee-1", 1, "employee-1")]), _answer_ruling(ruled))[1]["why"] == "content"


HANDLES = {h: {"unit": "ORG-0002", "roles": set(), "issued": None, "withdrawn": None} for h in ("ops", "ops-2", "employee-1", "employee-2")}


def test_a_stem_that_reads_as_two_givers_names_none_task_0308():
    """R1: ``ops``'s second file the day and ``ops-2``'s first have one stem; the approval of the first must not pass
    to ``ops-2``'s later identical answer, and the gate reads it ambiguous."""
    ruled = "A:cap:2026-11-05-ORG-0002-ops-2:1@capture"
    st = Store([_answer("2026-11-07-ORG-0002-ops-2", 1, "ops-2")])
    b, how = review.bind(st, _answer_ruling(ruled), HANDLES)
    assert b is None and how["why"] == "ambiguous", (b, how)
    # the same id again (either person's file may carry it) proves nothing; no holder at all reads gone
    assert review.bind(Store([_answer("2026-11-05-ORG-0002-ops-2", 1, "ops-2")]), _answer_ruling(ruled), HANDLES)[1]["why"] == "ambiguous"
    assert review.bind(Store([]), _answer_ruling(ruled), HANDLES)[1]["why"] == "gone"


def test_a_digit_ending_handle_with_one_reading_still_binds_task_0308():
    ruled = "A:cap:2026-11-05-ORG-0002-employee-1:1@capture"
    st = Store([_answer("2026-11-07-ORG-0002-employee-1", 1, "employee-1")])
    b, how = review.bind(st, _answer_ruling(ruled), HANDLES)
    assert b is not None and how["why"] == "repaired", (b, how)


def _gone_act():
    return {"review": "r.toml", "act": "ruling", "n": 1, "by": "employee-2", "on": "2026-11-03", "outcome": "approved",
            "statement": "A:cap:2026-11-05-ORG-0002-employee-1:1@capture", "key": "response|hold_presence", "from_value": "x",
            "from_sha256": "e3b0c442" + "0" * 56, "to": [], "reasons": [], "why": "gone"}


def test_the_gone_message_says_only_another_persons_identical_answer_may_remain_task_0308():
    """R2: the message does not claim that no answer of the key is extracted when another person's identical one is."""
    import gate_cli
    msg = gate_cli.act_finding(_gone_act())["message"]
    assert "no statement of it is extracted any more" in msg, msg
    assert "if only another person's identical answer remains, this ruling does not cover it" in msg, msg


def _run_check(*args):
    with tempfile.TemporaryDirectory() as d:
        p = subprocess.run([sys.executable, str(ROOT / "tools" / "check_act_binding.py"), *args], cwd=d, capture_output=True, text=True)
        return p, sorted(os.listdir(d))


def test_the_check_tool_prints_usage_on_help_and_refuses_a_stray_option_task_0308():
    """R3: an argument starting with ``-`` was taken as the output folder (``./--help/`` was created)."""
    p, left = _run_check("--help")
    assert p.returncode == 0 and "check_act_binding.py OUT_DIR" in p.stdout and left == [], (p.returncode, p.stderr, left)
    p, left = _run_check("-x")
    assert p.returncode == 2 and left == [], (p.returncode, p.stderr, left)


def _ops_check(aid, rows, ruling=None):
    doc = {"review": {"by": "employee-2", "on": "2026-11-05", "record": "m.md"}, "ruling": [ruling or _answer_ruling(aid)]}
    return review.check(doc, Store(rows), handles=HANDLES, owners={"response|hold_presence": ["ORG-0002"]},
                        units={}, captures={}, now=dt.date(2026, 11, 5),
                        compatible=lambda a, b, _p="": "equal" if a == b else "conflict", strict=True)


def test_a_review_of_an_ambiguous_stem_is_refused_at_write_time_task_0310():
    """Write time refuses what load time reports ambiguous: nothing binds, so nothing is saved (key-less input too)."""
    aid = "A:cap:2026-11-05-ORG-0002-ops-2:1@capture"
    rows = [_answer("2026-11-05-ORG-0002-ops-2", 1, "ops-2")]
    errs, rv = _ops_check(aid, rows)
    msg = " ".join(errs)
    assert "ops-2" in msg and "ops's second" in msg and "decision-0038" in msg and "no capture file holds" in msg, errs
    assert rv["rulings"] == [], rv
    errs, rv = _ops_check(aid, rows, {"assertion": aid, "outcome": "approved"})   # the reviewer's input: no key, value, sha256
    assert any("two givers" in e for e in errs) and rv["rulings"] == [], (errs, rv)


def test_a_single_reading_stem_is_still_accepted_at_write_time_task_0310():
    aid = "A:cap:2026-11-05-ORG-0002-employee-1:1@capture"
    errs, rv = _ops_check(aid, [_answer("2026-11-05-ORG-0002-employee-1", 1, "employee-1")])
    assert not any("two givers" in e for e in errs) and [r["statement"] for r in rv["rulings"]] == [aid], (errs, rv)


def _load_check(aid, giver, captures, rows=None):
    """A load (not strict) of one ruling that records ``giver``."""
    ru = {**_answer_ruling(aid), "giver": giver}
    doc = {"review": {"by": "employee-2", "on": "2026-11-05", "record": "m.md"}, "ruling": [ru]}
    return review.check(doc, Store(rows if rows is not None else []), handles=HANDLES, owners={"response|hold_presence": ["ORG-0002"]},
                        units={}, captures=captures, now=dt.date(2026, 11, 5),
                        compatible=lambda a, b, _p="": "equal" if a == b else "conflict", strict=False)[1]


def test_a_recorded_giver_the_load_cannot_confirm_is_an_act_task_0321():
    """H1: the capture gone, the identical answer of employee-3 remains; a file edited to name employee-3 binds nothing
    and reads as a changed act naming both givers. Check on both the present and the vanished capture."""
    aid = "A:cap:2026-11-05-ORG-0002-employee-1:1@capture"
    rows = [_answer("2026-11-06-ORG-0002-employee-3", 1, "employee-3")]
    rv = _load_check(aid, "employee-3", {}, rows)
    assert rv["rulings"] == [] and [x["why"] for x in rv["skipped"]] == ["changed"], rv
    msg = rv["skipped"][0]["reasons"][0]
    assert "employee-3" in msg and "employee-1" in msg, msg
    rv = _load_check(aid, "employee-3", {aid: {"from": "employee-1"}}, [_answer("2026-11-05-ORG-0002-employee-1", 1, "employee-1")])
    assert rv["rulings"] == [] and "employee-1" in rv["skipped"][0]["reasons"][0], rv


def test_honest_givers_bind_as_before_task_0321():
    one = "A:cap:2026-11-05-ORG-0002-employee-1:1@capture"
    held = [_answer("2026-11-05-ORG-0002-employee-1", 1, "employee-1")]
    assert _load_check(one, "employee-1", {one: {"from": "employee-1"}}, held)["skipped"] == []   # capture present
    again = [_answer("2026-11-06-ORG-0002-employee-1", 1, "employee-1")]
    rv = _load_check(one, "employee-1", {}, again)   # vanished, single reading, the same giver again
    assert rv["skipped"] == [] and len(rv["rulings"]) == 1, rv
    amb = "A:cap:2026-11-05-ORG-0002-ops-2:1@capture"
    for giver in ("ops", "ops-2"):   # an ambiguous stem: either reading is honest
        rv = _load_check(amb, giver, {}, [_answer("2026-11-05-ORG-0002-ops-2", 1, giver)])
        assert rv["skipped"] == [] and len(rv["rulings"]) == 1, (giver, rv)
    assert _load_check(amb, "employee-1", {}, [])["skipped"][0]["why"] == "changed"


def _ambiguous_act(reasons):
    return {**_gone_act(), "why": "ambiguous", "reasons": reasons}


def test_an_ambiguous_act_settled_by_a_later_review_reads_info_task_0321():
    """H2: settled, info and naming the review; unsettled, major as before."""
    import gate_cli
    f = gate_cli.act_finding(_ambiguous_act(["settled by captures/reviews/2026-11-06-employee-3.toml"]))
    assert f["severity"] == "info" and "2026-11-06-employee-3" in f["message"], f
    assert gate_cli.act_finding(_ambiguous_act([]))["severity"] == "major"


def test_a_second_review_the_same_day_orders_after_the_first_task_0322():
    """J1: ``-`` sorts before ``.``, so ``<on>-<by>-2.toml`` sorted before ``<on>-<by>.toml`` by name."""
    docs = {n: {"review": {"by": "employee-2", "on": "2026-11-06"}} for n in ("2026-11-06-employee-2", "2026-11-06-employee-2-2", "2026-11-06-employee-2-10")}
    assert sorted(docs)[0] != "2026-11-06-employee-2" or sorted(docs)[1] != "2026-11-06-employee-2-2"   # by name it is not this order
    by_key = sorted(docs, key=lambda n: review.order_key(Path(n + ".toml"), docs[n]))
    assert by_key == ["2026-11-06-employee-2", "2026-11-06-employee-2-2", "2026-11-06-employee-2-10"], by_key
    other_day = {"review": {"by": "employee-2", "on": "2026-11-07"}}
    assert review.order_key(Path("2026-11-06-employee-2-2.toml"), docs["2026-11-06-employee-2"]) < review.order_key(Path("x.toml"), other_day)


def _pending(statement="A:cap:2026-11-05-ORG-0002-ops-2:1@capture"):
    return {"statement": statement, "key": "response|hold_presence", "from_value": "held_unscreened only", "from_sha256": review.content_digest([])}


def _bound(rel, id_, giver, outcome="approved", at=("2026-11-06", "employee-3", 0, "x")):
    return {"at": at, "rel": rel, "id": id_, "key": "response|hold_presence", "value": "held_unscreened only",
            "sha256": review.content_digest([]), "giver": giver, "outcome": outcome}


def test_only_a_ruling_of_the_same_statement_settles_an_ambiguous_act_task_0322():
    """J2: another person's identical answer, approved later, supersedes the act for the key; it does not settle it."""
    at = ("2026-11-05", "employee-2", 0, "a")
    same = _bound("r-same.toml", "A:cap:2026-11-05-ORG-0002-ops-2:1@capture", "ops-2")
    assert review.settling(_pending(), at, [same], HANDLES) == "settled by r-same.toml"
    other = _bound("r-other.toml", "A:cap:2026-11-07-ORG-0002-employee-1:1@capture", "employee-1")
    why = review.settling(_pending(), at, [other], HANDLES)
    assert why == "superseded for the key by r-other.toml; the answer it named stays unruled", why
    rejected = _bound("r-rej.toml", other["id"], "employee-1", "rejected")
    assert "stays unruled" in review.settling(_pending(), at, [rejected], HANDLES) and "superseded" not in review.settling(_pending(), at, [rejected], HANDLES)
    assert review.settling(_pending(), at, [_bound("r-early.toml", same["id"], "ops-2", at=("2026-11-04", "x", 0, "x"))], HANDLES) is None


def test_the_gate_reads_a_superseded_act_at_info_only_while_the_key_is_approved_task_0322():
    import gate_cli
    f = gate_cli.act_finding(_ambiguous_act(["superseded for the key by r.toml; the answer it named stays unruled"]))
    assert f["severity"] == "info" and "stays unruled" in f["message"], f
    f = gate_cli.act_finding(_ambiguous_act(["the key was ruled by r.toml (rejected); the answer it named stays unruled"]))
    assert f["severity"] == "major" and "stays unruled" in f["message"], f


def test_every_reason_load_writes_is_one_the_gate_recognises_task_0322():
    """The prefixes are one set (review.REASON_PREFIXES): each reason ``_settling`` writes starts with one, and the gate
    reads the info ones at info and the rest at major."""
    import gate_cli
    at = ("2026-11-05", "employee-2", 0, "a")
    other = "A:cap:2026-11-07-ORG-0002-employee-1:1@capture"
    cases = [_bound("r.toml", "A:cap:2026-11-05-ORG-0002-ops-2:1@capture", "ops-2"), _bound("r.toml", other, "employee-1"),
             _bound("r.toml", other, "employee-1", "rejected"), _bound("r.toml", other, "employee-1", "referred")]
    seen = set()
    for b in cases:
        why = review.settling(_pending(), at, [b], HANDLES)
        pre = next((p for p in review.REASON_PREFIXES if why.startswith(p)), None)
        assert pre is not None, why
        seen.add(pre)
        want = "info" if pre in review.INFO_REASONS else "major"
        assert gate_cli.act_finding(_ambiguous_act([why]))["severity"] == want, (why, want)
    assert seen == set(review.REASON_PREFIXES), seen
