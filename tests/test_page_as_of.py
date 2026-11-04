"""Task-0076: the page shows the as-of date its gate read and the reviews that had lapsed by then
(decision-0005, task-0068). A run names its date (``run.py --as-of``, the app's ``as_of``); the gate
box and panel name it, the panel lists each lapsed review with the date it lapsed and its key's
review months; the record reads as of the subject's pinned date. The stack job proves it through
the app on S1 as of 2027-09-01 (demo.yml); here the view is built from a run folder standard-library
only, and its prose is held to the controlled-English limits."""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "demo" / "app"), str(Path(__file__).resolve().parent)]
import cadence  # noqa: E402
import server  # noqa: E402
import views  # noqa: E402
from _subject_pin import CARGO_QUOTE, on_cargo_quote  # noqa: E402

RESULTS = ROOT / "subjects" / "cargo_quote" / "vendor" / "kg_experiment" / "results"
NO_RUNS = ROOT / "nonexistent-demo-runs"
D = dt.date.fromisoformat


def _row(key, at="2026-08-06"):
    return {"id": f"A:{key}", "status": "approved", "approvals": [],
            "verifications": [{"id": f"ver:review:A:{key}", "method": "review", "at": at, "valid_until": cadence.due(at, key, CARGO_QUOTE)}]}


def test_a_lapse_names_the_day_it_lapsed_its_months_and_the_kind_they_come_from():
    got = cadence.lapse(_row("shipper_id|present"), "shipper_id|present", D("2027-09-01"), CARGO_QUOTE)
    assert got["valid_until"] == "2027-08-06" and got["lapsed_on"] == "2027-08-07", got
    # CAP-0004 and the entities beneath are named at twelve months; on a tie the first named kind is shown
    assert got["months"] == 12 and got["kind"] == "business_entity", got
    assert cadence.lapse(_row("shipper_id|present"), "shipper_id|present", D("2027-08-06"), CARGO_QUOTE) is None, "current on its last day"
    # a key on the API's response rests on a step: six months (register decision 0013, v0.2.7)
    assert cadence.kind_for("response|statuses", CARGO_QUOTE) == "step" and cadence.months_for("response|statuses", CARGO_QUOTE) == 6
    got = cadence.lapse(_row("response|statuses"), "response|statuses", D("2027-09-01"), CARGO_QUOTE)
    assert got["valid_until"] == "2027-02-06" and got["lapsed_on"] == "2027-02-07" and got["months"] == 6, got
    # a key whose nodes are of kinds the register names no months for takes the default, and no kind
    assert cadence.kind_for("no|such key", CARGO_QUOTE) is None and cadence.months_for("no|such key", CARGO_QUOTE) == 12


def _lapsed_run(td: Path) -> Path:
    """A demo run folder of S1 as of 2027-09-01: the record's numbers, the gate as the run gives it."""
    j = json.loads((RESULTS / "S1" / "deterministic.json").read_text(encoding="utf-8"))
    keys = ["shipper_id|present", "weight_kg|max", "response|statuses"]
    lapsed = [cadence.lapse(_row(k), k, D("2027-09-01"), CARGO_QUOTE) for k in keys] + [cadence.lapse(dict(_row(keys[0]), id="B"), keys[0], D("2027-09-01"), CARGO_QUOTE)]
    j["as_of"] = "2027-09-01"
    j["D6_gate"].update(verdict="BLOCKED", why="10 of 36 required keys (28%) are below verified; the bar is 25%", lapsed=lapsed)
    d = td / "demo-runs" / "cargo_quote" / "2027-09-01-0000" / "S1"
    d.mkdir(parents=True)
    (d / "deterministic.json").write_text(json.dumps(j), encoding="utf-8")
    return td / "demo-runs"


# (key, lapsed on, months) as of 2027-09-01: twelve months for the entities, six for the step (decision 0013)
LAPSES = {("shipper_id|present", "2027-08-07", "12"), ("weight_kg|max", "2027-08-07", "12"), ("response|statuses", "2027-02-07", "6")}


def _sentences(text):
    return [s for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])", text.strip()) if s]


@on_cargo_quote
def test_the_gate_box_and_panel_name_the_as_of_date_and_list_each_lapsed_review():
    with tempfile.TemporaryDirectory() as td:
        runs = _lapsed_run(Path(td))
        v = views.build("S1", "demo-runs/cargo_quote/2027-09-01-0000", runs)
    assert v["as_of"] == {"date": "2027-09-01", "record_date": "2026-10-30", "from_run": True, "is_record": False}
    gate = next(s for s in v["stages"] if s["id"] == "gate")
    assert gate["lines"][:3] == ["BLOCKED", "as of 2027-09-01", "4 reviews lapsed, on 3 keys"], gate["lines"]
    sec = next(x for x in v["details"]["gate"]["sections"] if x["heading"].startswith("Review currency"))
    assert sec["heading"] == "Review currency: 4 reviews on 3 keys lapsed by 2027-09-01" and "as of 2027-09-01" in sec["text"]
    t = sec["table"]
    assert t["cols"] == ["assertion", "key", "was", "current until", "lapsed on", "review months", "kind"]
    assert len(t["rows"]) == 4 and {(r[1], r[4], r[5]) for r in t["rows"]} == LAPSES, t["rows"]
    assert {r[1]: r[6] for r in t["rows"]} == {"shipper_id|present": "business_entity", "weight_kg|max": "business_entity", "response|statuses": "step"}
    text = " ".join(v["narrative"])
    assert "as of 2027-09-01, not the record date 2026-10-30." in text and "By then 4 reviews on 3 keys had lapsed." in text
    assert "so the record is not its measure" in text, "a run read as of another date is not the record's measure"
    # every generated sentence keeps to the page's controlled English (tests/test_demo.py's rules)
    for item in v["text_registry"]:
        if item["kind"] == "data":
            continue
        for s in _sentences(item["text"]):
            assert len(s.split()) <= {"controlled": 20, "reading": 25}[item["kind"]], s
            assert not [f for f in views.FORBIDDEN if re.search(r"\b" + re.escape(f) + r"\b", s.lower())], s


@on_cargo_quote
def test_the_record_reads_as_of_its_pinned_date_and_names_no_lapse():
    v = views.build("S1", "record", NO_RUNS)
    assert v["as_of"]["date"] == CARGO_QUOTE.record_as_of and v["as_of"]["is_record"] and not v["as_of"]["from_run"]
    assert "as of " + CARGO_QUOTE.record_as_of in next(s for s in v["stages"] if s["id"] == "gate")["lines"]
    assert v["gate"]["lapsed"] == []
    sec = next(x for x in v["details"]["gate"]["sections"] if x["heading"].startswith("Review currency"))
    assert sec["heading"] == "Review currency: no review lapsed" and "table" not in sec
    assert any("the subject's record date." in n for n in v["narrative"])
    for t in ("as-of date", "lapsed"):
        assert t in views.GLOSSARY and f"| {t} |" in (ROOT / "demo" / "GLOSSARY.md").read_text(encoding="utf-8")


def test_a_run_through_the_app_passes_its_date_and_refuses_a_bad_one():
    started = []

    class _Proc:
        def wait(self):
            return 0

    def popen(cmd, cwd=None, stdout=None, stderr=None, env=None):
        started.append(cmd)
        return _Proc()
    keep_popen, keep_runs = server.subprocess.Popen, server.RUNS_DIR
    with tempfile.TemporaryDirectory() as td:
        server.subprocess.Popen, server.RUNS_DIR = popen, Path(td)
        try:
            import page_subject
            with page_subject.using(CARGO_QUOTE):
                rec = server.Runner().start("S1", "deterministic", 1, as_of="2027-09-01")
                assert rec["as_of"] == "2027-09-01" and started[-1][-2:] == ["--as-of", "2027-09-01"], started[-1]
                rec = server.Runner().start("S1", "deterministic", 1)
                assert rec["as_of"] is None and "--as-of" not in started[-1], "no date: the run reads the record date"
                for bad in ("2027-13-01", "2027-9-1", "record; rm -rf /"):
                    try:
                        server.Runner().start("S1", "deterministic", 1, as_of=bad)
                    except ValueError:
                        continue
                    raise AssertionError(f"{bad!r} accepted")
        finally:
            server.subprocess.Popen, server.RUNS_DIR = keep_popen, keep_runs
    page = (ROOT / "demo" / "app" / "index.html").read_text(encoding="utf-8")
    assert 'id="as-of"' in page and "as_of: $('#as-of').value" in page


def test_the_run_reads_its_date_and_the_stack_job_asserts_the_page_on_s1_after_the_lapse():
    run_py = (ROOT / "harness" / "run.py").read_text(encoding="utf-8")
    assert 'ap.add_argument("--as-of", default="record"' in run_py and 'resolve(s, "codegen", as_of)' in run_py
    wf = (ROOT / ".github" / "workflows" / "demo.yml").read_text(encoding="utf-8")
    step = wf.split("task-0076", 1)[1].split("- name:", 1)[0]
    assert '"as_of":"2027-09-01"' in step and 'x["lapsed_on"], x["months"]) == lapse(x["key"])' in step
    assert 'v["as_of"]["date"] == "2027-09-01"' in step and '"as of 2027-09-01" in gate["lines"]' in step


def _lapsed_s6_run(td: Path) -> Path:
    """A demo run folder of S6 as of 2027-09-01: the record's numbers, each stage-2 gate as the run
    gives it (the run on either store lists the same ten keys lapsed in both: seven on 2027-08-07, three on 2027-02-07)."""
    j = json.loads((RESULTS / "S6" / "deterministic.json").read_text(encoding="utf-8"))
    keys = ["shipper_id|present", "weight_kg|max", "response|statuses"]
    lapsed = [cadence.lapse(_row(k), k, D("2027-09-01"), CARGO_QUOTE) for k in keys]
    j["as_of"] = "2027-09-01"
    j["D6_gate"].update(lapsed=lapsed)
    j["stage2"]["gate_before_reverification"].update(lapsed=lapsed)
    j["stage2"]["gate_after_reverification"].update(verdict="BLOCKED", why="10 of 36 required keys (28%) are below verified; the bar is 25%", lapsed=lapsed[:2])
    d = td / "demo-runs" / "cargo_quote" / "2027-09-01-0000" / "S6"
    d.mkdir(parents=True)
    (d / "deterministic.json").write_text(json.dumps(j), encoding="utf-8")
    return td / "demo-runs"


@on_cargo_quote
def test_s6_stage_2_gate_boxes_and_panels_list_the_lapsed_reviews_as_stage_1_does():
    """Task-0086: each stage-2 gate, before and after re-verification, names its as-of date and lists
    its lapsed reviews, in the stage-1 gate's box lines and panel section; its colour is its verdict's."""
    with tempfile.TemporaryDirectory() as td:
        runs = _lapsed_s6_run(Path(td))
        v = views.build("S6", "demo-runs/cargo_quote/2027-09-01-0000", runs)
    boxes = {s["id"]: s for s in v["stage2"]["stages"]}
    assert boxes["gate_before"]["lines"][:3] == ["BLOCKED", "as of 2027-09-01", "3 reviews lapsed, on 3 keys"], boxes["gate_before"]["lines"]
    assert boxes["gate_after"]["lines"][:3] == ["BLOCKED", "as of 2027-09-01", "2 reviews lapsed, on 2 keys"], boxes["gate_after"]["lines"]
    assert boxes["gate_before"]["colour"] == boxes["gate_after"]["colour"] == "bad", "a BLOCKED gate after re-verification is not shown green"
    assert v["stage2"]["gate_after"]["lapsed"] == v["stage2"]["gate_after"]["lapsed"][:2]
    stage1 = next(x for x in v["details"]["gate"]["sections"] if x["heading"].startswith("Review currency"))
    for panel, n, keys in (("gate_before", 3, 3), ("gate_after", 2, 2)):
        sec = next(x for x in v["details"][panel]["sections"] if x["heading"].startswith("Review currency"))
        assert sec["heading"] == f"Review currency: {n} reviews on {keys} keys lapsed by 2027-09-01" and "as of 2027-09-01" in sec["text"], sec
        assert sec["table"]["cols"] == stage1["table"]["cols"] and len(sec["table"]["rows"]) == n
        assert {(r[1], r[4], r[5]) for r in sec["table"]["rows"]} <= LAPSES, sec["table"]["rows"]
    assert "Re-verification renewed none of the 2 lapsed reviews on 2 keys." in " ".join(v["narrative"])
    for item in v["text_registry"]:
        if item["kind"] == "data":
            continue
        for s in _sentences(item["text"]):
            assert len(s.split()) <= {"controlled": 20, "reading": 25}[item["kind"]], s
            assert not [f for f in views.FORBIDDEN if re.search(r"\b" + re.escape(f) + r"\b", s.lower())], s


@on_cargo_quote
def test_the_record_s6_stage_2_gates_name_no_lapse_and_keep_their_colours():
    v = views.build("S6", "record", NO_RUNS)
    boxes = {s["id"]: s for s in v["stage2"]["stages"]}
    assert boxes["gate_before"]["colour"] == "bad" and boxes["gate_after"]["colour"] == "ok"
    assert boxes["gate_after"]["lines"][:2] == ["PROCEED", "as of " + CARGO_QUOTE.record_as_of]
    for panel in ("gate_before", "gate_after"):
        sec = next(x for x in v["details"][panel]["sections"] if x["heading"].startswith("Review currency"))
        assert sec["heading"] == "Review currency: no review lapsed" and "table" not in sec


def test_the_stack_job_asserts_s6_stage_2_gates_after_the_lapse():
    wf = (ROOT / ".github" / "workflows" / "demo.yml").read_text(encoding="utf-8")
    step = wf.split("task-0086", 1)[1].split("- name:", 1)[0]
    assert '"scenario":"S6"' in step and '"as_of":"2027-09-01"' in step
    assert 'for panel in ("gate_before", "gate_after")' in step and '(x["lapsed_on"], x["months"]) == lapse(x["key"])' in step
