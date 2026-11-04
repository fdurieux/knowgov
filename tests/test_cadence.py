"""Task-0068, decision-0005: a review falls due after the review months of the kind its key concerns.
The cadence is read from the register, the load dates every review verification, and the gate reads
currency as of a date: a lapse lowers the key to validated and is a finding; an execution
verification never lapses by date; a person's later approval renews it; the record is read as of
its pinned date, so it never moves by the clock. Standard library only: a fake store stands in for
the adapters, whose own proof is the comparator and the gate command in harness.yml and demo.yml."""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(Path(__file__).resolve().parent), str(ROOT / "demo" / "tools")]
import cadence  # noqa: E402
import gate  # noqa: E402
import gate_cli  # noqa: E402
import review  # noqa: E402
import schema_check  # noqa: E402
import subject  # noqa: E402
from _subject_pin import CARGO_QUOTE  # noqa: E402

JEF = subject.Subject(ROOT / "subjects" / "jef_data_load")
BLOCK = {"absent", "declared_gap", "disputed", "invalidated"}
D = dt.date.fromisoformat


class Store:
    """The port's gate reads and the two verification operations, over a dict of statements."""

    def __init__(self, rows: dict[str, list[dict]]):
        self.rows = rows

    def key_evidence(self, key, live):
        out = []
        for r in self.rows.get(key, []):
            if r["status"] in live:
                out.append({"value": "1", "text": "", "basis": "extracted", "artefact": "a.md", "agent": None,
                            "fragments": [], "gaps": [], "approvals": [], **json.loads(json.dumps(r))})
        return out

    def declared_gaps_for_key(self, key):
        return []

    def conflict_gaps(self):
        return []

    def stale_on_keys(self, keys):
        return []

    def suspect_derived(self):
        return []

    def review_verifications(self):
        return [{"id": v["id"], "key": k, "at": v["at"]} for k, rs in self.rows.items() for r in rs
                for v in r["verifications"] if v["method"] == "review" and v.get("valid_until") is None]

    def set_valid_until(self, dates):
        for rs in self.rows.values():
            for r in rs:
                for v in r["verifications"]:
                    if v["id"] in dates:
                        v["valid_until"] = dates[v["id"]]


def _row(key, method="review", at="2026-08-06", status="approved", approvals=()):
    vid = f"ver:{'review' if method == 'review' else 'exec:s'}:A:{key}"
    return {"id": f"A:{key}", "status": status, "approvals": list(approvals),
            "verifications": [{"id": vid, "method": method, "scope": "", "at": at, "valid_until": None}]}


def _spec(keys, share=0.25):
    return {"keys": list(keys), "block_levels": BLOCK, "max_unverified_share": share}


def test_the_cadence_is_the_registers_and_a_product_key_reviews_at_six_months():
    by_key, default = cadence.cadence(CARGO_QUOTE)
    assert default == 12 and set(by_key) == {r["key"] for r in CARGO_QUOTE.register_map()["row"]}
    assert set(by_key.values()) == {12}, "every CargoQuote row names capabilities, processes, applications, entities"
    jef, _ = cadence.cadence(JEF)
    product = [r["key"] for r in JEF.register_map()["row"] if any(n.startswith("PRD-") for n in r["nodes"])]
    assert len(product) == 21 and all(jef[k] == 6 for k in product), "decision-0005: 21 of J-F's keys concern a product"
    assert cadence.months_for("no|such key", CARGO_QUOTE) == 12, "a key with no row takes default_months"
    with tempfile.TemporaryDirectory() as t:   # the register is read, never copied: a new cadence is followed
        reg = Path(t)
        (reg / "metamodel").mkdir()
        (reg / "metamodel" / "lifecycle.toml").write_text("[review]\ndefault_months = 3\n", encoding="utf-8")
        (reg / "metamodel" / "types.toml").write_text("", encoding="utf-8")
        assert cadence.cadence(CARGO_QUOTE, reg) == ({k: 3 for k in by_key}, 3)


def test_the_load_dates_every_review_and_leaves_execution_undated():
    st = Store({"S-review|max": [_row("S-review|max")], "P1|formula": [_row("P1|formula", "execution", "2026-10-30T11:39:46+00:00")]})
    assert cadence.date_reviews(st) == 1   # twelve months under either subject: a CargoQuote row, or no J-F row
    assert st.rows["S-review|max"][0]["verifications"][0]["valid_until"] == "2027-08-06"
    assert st.rows["P1|formula"][0]["verifications"][0]["valid_until"] is None
    assert cadence.date_reviews(st) == 0, "a dated review is not dated again"
    assert cadence.due("2026-10-30T11:39:46+00:00", "S-review|max", CARGO_QUOTE) == "2027-10-30"
    assert cadence.due("2026-08-31", "x|y", JEF) == "2027-08-31" and cadence.due("v2", "x|y") is None


def test_a_review_lapses_the_day_after_its_due_date_and_execution_never_does():
    rev = dict(_row("k|rev"), verifications=[dict(_row("k|rev")["verifications"][0], valid_until="2027-08-06")])
    exe = _row("k|exe", "execution")
    for row, on, gone in ((rev, "2027-08-06", False), (rev, "2027-08-07", True), (exe, "2040-01-01", False)):
        got = cadence.lapse(json.loads(json.dumps(row)), row["id"][2:], D(on), CARGO_QUOTE)
        assert bool(got) == gone, (row["id"], on, got)
    got = cadence.lapse(rev, "k|rev", D("2027-08-07"), CARGO_QUOTE)
    assert got == {"id": "A:k|rev", "key": "k|rev", "from": "approved", "valid_until": "2027-08-06", "verifications": ["ver:review:A:k|rev"]}
    both = dict(rev, verifications=rev["verifications"] + exe["verifications"])
    assert cadence.lapse(both, "k|rev", D("2030-01-01"), CARGO_QUOTE) is None, "an execution verification keeps it current"
    tag = dict(rev, verifications=[dict(rev["verifications"][0], valid_until="v2")])
    assert cadence.lapse(tag, "k|rev", D("2030-01-01"), CARGO_QUOTE) is None, "a source change's tag is R-STALE's, not a date"
    assert cadence.lapse(dict(rev, status="validated"), "k|rev", D("2030-01-01"), CARGO_QUOTE) is None
    assert cadence.lapse(dict(rev, basis="elicited"), "k|rev", D("2030-01-01"), CARGO_QUOTE) is None, "a person's answer lapses by decision-0002"


def test_a_persons_later_approval_renews_a_lapsed_review_and_the_loads_own_approval_does_not():
    base = dict(_row("k|rev"), verifications=[dict(_row("k|rev")["verifications"][0], valid_until="2027-08-06")])
    own = dict(base, approvals=[{"id": "appr:A:k|rev", "at": "2027-09-01", "record": "r"}])
    assert cadence.lapse(own, "k|rev", D("2027-09-02"), CARGO_QUOTE), "the load's approval rests on the review"
    ruled = dict(base, approvals=[{"id": "appr:review:2027-09-01-employee-1:A:k|rev", "at": "2027-09-01", "record": "r"}])
    assert cadence.lapse(ruled, "k|rev", D("2027-09-02"), CARGO_QUOTE) is None
    assert cadence.lapse(ruled, "k|rev", D("2028-09-01"), CARGO_QUOTE) is None
    assert cadence.lapse(ruled, "k|rev", D("2028-09-02"), CARGO_QUOTE)["valid_until"] == "2028-09-01"


def test_a_lapse_lowers_the_key_and_the_gate_report_names_it_as_a_major_finding():
    keys = ["k|a", "k|b", "k|c", "k|d"]
    rows = {k: [_row(k, "execution")] for k in keys[:3]}
    rows["k|d"] = [_row("k|d")]
    st = Store(rows)
    st.set_valid_until({"ver:review:A:k|d": "2027-08-06"})
    before = gate.resolve_spec(st, "codegen", _spec(keys), "2027-08-06")
    assert before["verdict"] == "PROCEED" and before["lapsed"] == [] and before["as_of"] == "2027-08-06"
    after = gate.resolve_spec(st, "codegen", _spec(keys), "2027-08-07")
    assert after["keys"]["k|d"]["level"] == "validated" and after["below_verified"] == ["k|d"]
    assert after["verdict"] == "QUALIFIED", "1 of 4 is at the 25 % bar, not above it"
    assert [x["id"] for x in after["lapsed"]] == ["A:k|d"] and after["keys"]["k|d"]["assertions"][0]["lapsed"]["from"] == "approved"
    assert "REVIEW LAPSED" in "\n".join(gate.render_key("k|d", after["keys"]["k|d"]))
    assert "REVIEW LAPSED as of 2027-08-07" in gate.render_bundle(after, "P") and "REVIEW LAPSED" in gate.render_index(after, "P")
    base = gate_cli.compare(after, {"verdict": "PROCEED", "levels": {k: "approved" for k in keys}, "suspect": []}, "record")
    rep = gate_cli.report(after, subject="s", scenario="S1", task="codegen", store="rdflib", loaded=True,
                          block_levels=BLOCK, threshold="blocker", baseline=base)
    assert schema_check.validate(rep, schema_check.load("gate-report")) == []
    [f] = [f for f in rep["findings"] if f["kind"] == "lapsed"]
    assert f["severity"] == "major" and f["ref"] == "A:k|d" and f["related"] == ["ver:review:A:k|d"] and "2027-08-06" in f["message"]
    assert rep["lapsed"] == ["A:k|d"] and rep["as_of"] == "2027-08-07"
    assert base["regression"] and base["regressed_keys"] == [{"key": "k|d", "level": "validated", "baseline_level": "approved"}]
    assert "lapsed" in gate_cli.render(rep) and "(as of 2027-08-07)" in gate_cli.render(rep)


def test_a_replacement_whose_review_lapsed_still_replaced_the_invalidated_statement():
    old = {"id": "A:k@v1", "status": "invalidated", "verifications": [{"id": "ver:exec:s:A:k@v1", "method": "execution", "scope": "", "at": "x", "valid_until": "v2"}]}
    new = dict(_row("k"), id="A:k@v2", verifications=[{"id": "ver:review:v2:A:k@v2", "method": "review", "scope": "", "at": "2026-10-30", "valid_until": "2027-10-30"}])
    res = gate.resolve_spec(Store({"k": [old, new]}), "codegen", _spec(["k"], 1.0), "2027-10-31")
    assert res["keys"]["k"]["level"] == "validated", "S6's re-verification lapses on the same rule; the change stays history"


def test_the_record_is_read_as_of_its_pinned_date_and_the_command_as_of_today():
    assert str(cadence.record_date(CARGO_QUOTE)) == "2026-10-30" and str(cadence.record_date(JEF)) == "2026-10-24"
    assert cadence.as_of("record", CARGO_QUOTE) == D("2026-10-30") and cadence.as_of("2027-08-07") == D("2027-08-07")
    old = {k: os.environ.pop(k, None) for k in ("KG_TODAY", "KG_CLOCK")}
    try:
        os.environ["KG_TODAY"] = "2027-01-15"   # today is KG_TODAY when a run pins it (task-0075)
        assert cadence.as_of(None) == cadence.as_of("today") == cadence.today() == D("2027-01-15")
        os.environ["KG_CLOCK"] = "pinned"
        assert cadence.as_of("record", CARGO_QUOTE) == D("2026-10-30"), "record never reads the clock"
        del os.environ["KG_TODAY"]
        try:
            cadence.as_of("today")
            raise AssertionError("KG_CLOCK=pinned with no KG_TODAY reads the wall clock")
        except review.WallClock:
            pass
        assert cadence.as_of("record", CARGO_QUOTE) == D("2026-10-30")
        del os.environ["KG_CLOCK"]
        assert cadence.today() == dt.date.today(), "unpinned, today is the wall clock"
    finally:
        for k, v in old.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v
    for bad in ("2027-13-01", "tomorrow", "2027-08-07T00:00"):
        try:
            cadence.as_of(bad)
            raise AssertionError(bad)
        except ValueError:
            pass
    st = Store({"k": [dict(_row("k"), verifications=[dict(_row("k")["verifications"][0], valid_until="2027-08-06")])]})
    assert gate.resolve_spec(st, "codegen", _spec(["k"]))["as_of"] == str(cadence.as_of("record")), "the gate's default is the record's date"
    import io
    from contextlib import redirect_stderr, redirect_stdout
    err = io.StringIO()
    with redirect_stderr(err), redirect_stdout(io.StringIO()):   # refused before any store is opened
        assert gate_cli.main(["--as-of", "2027-02-30"]) == 2
    assert "--as-of" in err.getvalue(), err.getvalue()


def test_cargo_quotes_review_only_keys_fall_due_on_2027_08_06():
    """The S1 case: the ten review-only keys of the kit's verification map, reviewed 2026-08-06, are
    current to 2027-08-06 and lapsed on 2027-08-07 (harness.yml shows the gate BLOCKED that day)."""
    review = CARGO_QUOTE.verification["review"]["at"]
    keys = CARGO_QUOTE.verification_map()["review"]["keys"]
    assert len(keys) == 10 and {cadence.due(review, k, CARGO_QUOTE) for k in keys} == {"2027-08-06"}
    assert 10 / len(CARGO_QUOTE.tasks["codegen"]["keys"]) > CARGO_QUOTE.tasks["codegen"]["max_unverified_share"]


def test_the_comparator_holds_a_run_to_the_record_date():
    import compare_deterministic as cd
    rec = json.loads((CARGO_QUOTE.record_dir / "S1" / "deterministic.json").read_text(encoding="utf-8"))
    assert "as_of" not in rec, "the record predates the date; the comparator adds it from the subject"
    with tempfile.TemporaryDirectory() as t:
        run, record = Path(t) / "run", Path(t) / "rec"
        for d in (run / "S1", record / "S1"):
            d.mkdir(parents=True)
        (record / "S1" / "deterministic.json").write_text(json.dumps(rec), encoding="utf-8")
        pinned = cd.PINNED
        for on, want in ((pinned, 0), ("2027-08-07", 1 if pinned else 0)):
            (run / "S1" / "deterministic.json").write_text(json.dumps({**rec, "as_of": on}), encoding="utf-8")
            n, lines = cd.compare(run, record, ["S1"])
            assert n == want, (on, lines)
