"""Task-0286 (G9-17; the bounded re-probe of task-0258, group 1 at 9861953): ``gate_cli --baseline FILE`` given a
deterministic.json holds it to the run, as task-0258 holds a report.

Probed: CargoQuote S2 exited 0 against S5's record, and against S2's record under ``--task design`` though the record
is codegen's; J-F's D5 record read as a CargoQuote baseline exited 1, a "regression" against J-F's keys; a stage-1
record was read at stage 2. And, fix-only, a version-3 report whose ``levels`` held a value the gate's ladder lacks
passed the schema and exited 2 as "the store did not answer: ValueError". Now each is refused, exit 2, before the store,
naming the file and what differs; the record's own file for the same run reads as before. Stdlib."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(Path(__file__).resolve().parent)]
import gate_cli  # noqa: E402
import test_baseline_identity as tbi  # noqa: E402

CQ = ROOT / "subjects" / "cargo_quote" / "vendor" / "kg_experiment" / "results"
JF = ROOT / "subjects" / "jef_data_load" / "record"


class Subject(tbi.Subject):
    record_dir = CQ


def _refused(path, *want, scenario="S2", task="codegen", stage=1) -> str:
    args = (str(path), Subject(), scenario, task) + ((stage,) if stage != 1 else ())
    try:
        gate_cli._baseline(*args)
    except gate_cli.CannotRun as e:
        msg = str(e)
        assert "did not answer" not in msg and str(path) in msg, msg
        assert all(w in msg for w in want), (want, msg)
        return msg
    raise AssertionError(f"accepted: {path} for {scenario} {task} stage {stage}")


def test_another_scenarios_record_is_refused():
    _refused(CQ / "S5" / "deterministic.json", "scenario 'S5'", "'S2'")


def test_another_subjects_record_is_refused_as_outside_this_subjects_record():
    _refused(JF / "D5" / "deterministic.json", "outside this subject's record")


def test_a_record_read_under_another_task_or_stage_is_refused():
    _refused(CQ / "S2" / "deterministic.json", "task 'codegen'", "'design'", task="design")
    _refused(CQ / "S2" / "deterministic.json", "stage 1", "is 2", stage=2)


def test_a_copy_outside_the_record_tree_is_refused_naming_it():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "deterministic.json"
        p.write_text((CQ / "S2" / "deterministic.json").read_text(encoding="utf-8"), encoding="utf-8")
        _refused(p, "outside this subject's record")


def test_the_records_own_file_for_the_same_run_reads_as_the_record():
    base, source = gate_cli._baseline(str(CQ / "S2" / "deterministic.json"), Subject(), "S2", "codegen")
    assert base == gate_cli._baseline("record", Subject(), "S2", "codegen")[0] and source.endswith("deterministic.json")
    s6 = gate_cli._baseline(str(CQ / "d3check" / "S6" / "deterministic.json"), Subject(), "S6", "codegen")
    assert s6[0]["verdict"] in gate_cli.VERDICTS   # a scenario whose record sits under another folder


def test_a_report_level_off_the_ladder_is_named_never_the_store():
    bad = tbi._report()
    bad["levels"] = {"shipper_id|present": "bogus"}
    msg = tbi._refused(bad, "$.levels.shipper_id|present", "'bogus'", "not a level of the gate")
    assert "did not answer" not in msg


def test_the_changelog_names_it_under_contract_changes():
    log = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").split("\n## ", 2)[1]
    assert "task-0286" in log.split("### Contract changes", 1)[1].split("### Changes", 1)[0]
