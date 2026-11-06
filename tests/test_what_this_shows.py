"""task-0170: the plain-English box's "What this shows" comes from the source's own outcome. The record,
and a run whose every arm outcome the record also had, end with the record's sentence. A run whose
model calls failed, or whose code did not reproduce the record's, says so plainly and never the record's
sentence. A deterministic run (no arm) and a replay (the record) are unchanged."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "demo" / "app"), str(Path(__file__).resolve().parent)]
import views  # noqa: E402
from _subject_pin import on_cargo_quote  # noqa: E402

RESULTS = ROOT / "subjects" / "cargo_quote" / "vendor" / "kg_experiment" / "results"
NO_RUNS = ROOT / "nonexistent-demo-runs"
FAILED = "Error code: 401 - {'error': {'message': 'Incorrect API key provided', 'code': 'invalid_api_key'}}"


def _run_folder(td: str, stamp: str, sc: str, arms: bool = True) -> Path:
    """A demo run folder of ``sc`` copied from the record: its deterministic.json, and its arm runs when asked."""
    d = Path(td) / "demo-runs" / stamp / sc
    d.mkdir(parents=True)
    shutil.copy(RESULTS / sc / "deterministic.json", d / "deterministic.json")
    if arms:
        for p in sorted((RESULTS / sc).glob("run1_*")):
            shutil.copy(p, d / p.name)
    return d


def _fail_calls(d: Path) -> None:
    """Each arm run as harness/run.py records a model call that failed: no answer, no code, no grade."""
    for p in d.glob("run*_?.json"):
        r = json.loads(p.read_text(encoding="utf-8"))
        r.update({"api_error": FAILED, "M1_decision": None, "M2_code": False, "M4_suite": {"ran": False, "passed": 0, "total": 11, "per_scenario": {}},
                  "M4_targets": {}, "M3_flagged": {"flagged": False, "hits": []}, "usage": {"prompt_tokens": 0, "completion_tokens": 0, "attempts": 4}})
        p.write_text(json.dumps(r), encoding="utf-8")
        p.with_suffix(".py").unlink(missing_ok=True)


@on_cargo_quote
def test_the_record_and_a_reproducing_run_end_with_the_records_sentence():
    plain = views._ps().scenarios["S1"]["plain"]
    rec = views.build("S1", "record", NO_RUNS)
    assert views.reproduces_record(rec) and "What this shows: " + plain in rec["narrative"], rec["narrative"][-3:]
    with tempfile.TemporaryDirectory() as td:
        _run_folder(td, "2026-11-06-1300", "S1")
        v = views.build("S1", "demo-runs/2026-11-06-1300", Path(td) / "demo-runs")
        assert views.reproduces_record(v) and "What this shows: " + plain in v["narrative"], v["narrative"]


@on_cargo_quote
def test_a_run_whose_calls_failed_says_so_and_never_the_records_sentence():
    plain = views._ps().scenarios["S1"]["plain"]
    with tempfile.TemporaryDirectory() as td:
        _fail_calls(_run_folder(td, "2026-11-06-1301", "S1"))
        v = views.build("S1", "demo-runs/2026-11-06-1301", Path(td) / "demo-runs")
        text = " ".join(v["narrative"])
        assert not views.reproduces_record(v) and plain not in text and "both arms wrote working code" not in text, text
        assert "What this run shows: the arms' calls to the model failed, so no code was graded." in text, text
        assert "First error: Error code: 401" in text and "The record's conclusion does not apply to this run." in text, text


@on_cargo_quote
def test_a_run_with_one_arm_failed_and_code_that_did_not_pass_says_what_happened():
    with tempfile.TemporaryDirectory() as td:
        d = _run_folder(td, "2026-11-06-1302", "S1")
        for p in d.glob("run*_B.json"):   # arm B's call failed
            p.unlink()
        shutil.copy(RESULTS / "S1" / "run1_G.json", d / "run1_B.json")
        b = json.loads((d / "run1_B.json").read_text(encoding="utf-8"))
        b.update({"arm": "B", "api_error": FAILED, "M1_decision": None, "M2_code": False,
                                "M4_suite": {"ran": False, "passed": 0, "total": 11, "per_scenario": {}}, "M4_targets": {}})
        (d / "run1_B.json").write_text(json.dumps(b), encoding="utf-8")
        g = json.loads((d / "run1_G.json").read_text(encoding="utf-8"))   # arm G's code passed 9 of 11
        g["M4_suite"] = {**g["M4_suite"], "ran": True, "passed": 9, "total": 11}
        (d / "run1_G.json").write_text(json.dumps(g), encoding="utf-8")
        v = views.build("S1", "demo-runs/2026-11-06-1302", Path(td) / "demo-runs")
        text = " ".join(v["narrative"])
        assert "What this run shows: its arms did not reproduce the record's outcome." in text, text
        assert "Arm B's calls to the model failed, so none of its code was graded." in text, text
        assert "Arm G's code failed some of the oracle's scenarios in 1 of 1 runs." in text, text
        assert views._ps().scenarios["S1"]["plain"] not in text


@on_cargo_quote
def test_a_deterministic_run_and_the_replay_are_unchanged():
    with tempfile.TemporaryDirectory() as td:
        _run_folder(td, "2026-11-06-1303", "S1", arms=False)
        v = views.build("S1", "demo-runs/2026-11-06-1303", Path(td) / "demo-runs")
        text = " ".join(v["narrative"])
        assert "This source holds the store's half only." in text and "What this" not in text, text
    for sc in views.ORDER:   # every scenario's replay keeps its record sentence
        v = views.build(sc, views.default_source(sc), NO_RUNS)
        if v["arms"]["G"]["summary"]["n"] or v["arms"]["B"]["summary"]["n"]:
            assert "What this shows: " + views._ps().scenarios[sc]["plain"] in v["narrative"], sc


@on_cargo_quote
def test_the_new_sentences_keep_to_the_glossary_and_the_length_limit():
    """The sentences the box now builds are held as every generated sentence is (tests/test_demo.py)."""
    import re
    with tempfile.TemporaryDirectory() as td:
        _fail_calls(_run_folder(td, "2026-11-06-1304", "S1"))
        v = views.build("S1", "demo-runs/2026-11-06-1304", Path(td) / "demo-runs")
    for item in v["text_registry"]:
        if item["kind"] != "controlled":
            continue
        for s in re.split(r"(?<=[.!?])\s+", item["text"]):
            assert len(s.split()) <= 20, s
            assert not [f for f in views.FORBIDDEN if re.search(r"\b" + re.escape(f) + r"\b", s.lower())], s
