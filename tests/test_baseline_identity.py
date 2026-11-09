"""Task-0258 (G9-17; decision-0032's validation pass, group 1 C2 and F4, group 3 CB4 and F9): ``gate_cli --baseline
FILE`` keeps the flag's own promise, "an earlier report of this command (at stage 2, a stage-2 report)".

Probed on main 2a8bbeb: a BLOCKED run exited 0 against another subject's report, another task class's, a hand-written
``{"tool": "knowgov gate", "verdict": "BLOCKED"}`` and a stage-1 report read at stage 2; ``schema_version`` 99 was
read; a malformed field (verdict "FOO", a bad level, ``levels`` a list) exited 2 as "the store did not answer:
ValueError"; a baseline without ``levels`` never tripped the key ratchet. Now a report baseline is refused, exit 2,
naming the file and what differs, before any store is opened; versions 1 to 3 read as before, each against the
schema of its own version; ``--baseline record`` and a deterministic.json read as before; and the MCP reader's
``gate_verdict`` serves no report baseline at all. Stdlib: every refusal happens before the store."""
from __future__ import annotations

import contextlib
import copy
import io
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(Path(__file__).resolve().parent)]
import gate_cli  # noqa: E402
import schema_check  # noqa: E402

KEY = "S-review|notified"
CHANGE = {"artefact": "contract/decision_table.md", "version": "v2", "invalidated": [], "reverified": False,
          "reverified_statements": [], "derived": None}


def _report(subject="cargo_quote", scenario="S2", task="codegen", change=None, verdict="BLOCKED", level="approved") -> dict:
    res = {"verdict": verdict, "why": "probe", "keys": {KEY: {"level": level, "flags": [], "assertions": []}},
           "below_verified": [], "flagged": [], "blocked_keys": [KEY] if verdict == "BLOCKED" else []}
    r = gate_cli.report(res, subject=subject, scenario=scenario, task=task, store="rdflib", loaded=True, block_levels=set(),
                        threshold="blocker", baseline=None, change=change)
    return json.loads(json.dumps(r))


def _v2(r: dict) -> dict:
    out = {k: v for k, v in r.items() if k not in ("task_profile", "register", "knowgov")}
    return {**out, "schema_version": 2}


def _v1(r: dict) -> dict:
    out = {k: v for k, v in _v2(r).items() if k not in ("as_of", "lapsed", "superseded_by", "version", "change")}
    return {**out, "schema_version": 1, "stale": len(r["stale"]), "suspect_derived": len(r["suspect_derived"])}


class Subject:
    id = "cargo_quote"
    record_dir = ROOT / "subjects" / "cargo_quote" / "vendor" / "kg_experiment" / "results"

    def scenario(self, s):
        return {}


def _read(data, scenario="S2", task="codegen", stage=1, subject=Subject()):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "base.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        args = (str(p), subject, scenario, task) + ((stage,) if stage != 1 else ())   # stage 1 as the call reads it before
        return gate_cli._baseline(*args)


def _refused(data, *want, **run) -> str:
    try:
        _read(data, **run)
    except gate_cli.CannotRun as e:
        msg = str(e)
        assert "--baseline" in msg and "did not answer" not in msg, msg
        assert all(w in msg for w in want), (want, msg)
        return msg
    raise AssertionError(f"accepted: {json.dumps(data)[:200]}")


def test_the_reports_of_each_version_validate_against_their_own_schema():
    r = _report()
    for data, name in ((r, "gate-report"), (_v2(r), "gate-report-v2"), (_v1(r), "gate-report-v1")):
        assert schema_check.validate(data, schema_check.load(name)) == [], name
        base, source = _read(data)   # versions 1 to 3 read as before
        assert base["verdict"] == "BLOCKED" and base["levels"] == {KEY: "approved"} and source.endswith("base.json")
    assert gate_cli.REPORT_SCHEMAS == {1: "gate-report-v1", 2: "gate-report-v2", 3: "gate-report"}


def test_another_subject_scenario_task_or_stage_is_refused_naming_the_field_and_both_values():
    _refused(_report(subject="minimal", scenario="S0"), "subject 'minimal'", "'cargo_quote'")   # group 1 C2
    _refused(_report(scenario="S1"), "scenario 'S1'", "'S2'")
    _refused(_report(task="design"), "task 'design'", "'codegen'")                              # S2's design report
    _refused(_report(), "stage 1", "is 2", stage=2)                                              # group 3 CB4
    _refused(_report(change=CHANGE), "stage 2", "is 1", stage=1)
    assert _read(_report(change=CHANGE), stage=2)[0]["verdict"] == "BLOCKED"                    # a stage-2 report at stage 2


def test_a_newer_schema_version_is_refused_under_decision_0023():
    _refused({**_report(), "schema_version": 99}, "schema_version = 99", "version 3 and earlier", "decision-0023")   # F9
    _refused({**_report(), "schema_version": 0}, "schema_version 0")
    _refused({**_report(), "schema_version": True}, "schema_version True")
    _refused({k: v for k, v in _report().items() if k != "schema_version"}, "schema_version None")


def test_a_malformed_report_names_the_file_and_its_first_error_never_the_store():
    _refused({"tool": "knowgov gate", "verdict": "BLOCKED", "schema_version": 3}, "not a valid version-3 gate report")   # F4
    for field, value in (("verdict", "FOO"), ("levels", [KEY]), ("levels", {KEY: 7})):
        bad = copy.deepcopy(_report())
        bad[field] = value
        msg = _refused(bad, "not a valid version-3 gate report", f"$.{field}")
        assert "base.json" in msg
    _refused({k: v for k, v in _report().items() if k != "levels"}, "levels")   # a baseline without levels: refused


def test_the_record_and_a_deterministic_json_read_as_before():
    base, source = gate_cli._baseline("record", Subject(), "S1", "codegen")
    assert source == "record" and base["verdict"] in gate_cli.VERDICTS
    own = gate_cli._baseline(str(Subject.record_dir / "S1" / "deterministic.json"), Subject(), "S1", "codegen")
    assert own[0] == base   # the record's own file, named by its path, reads as the record (task-0286 holds it to the run)


def test_gate_cli_refuses_another_scenarios_report_before_the_store():
    from subject import SUBJECT
    if len(SUBJECT.order) < 2:
        return
    first, second = SUBJECT.order[:2]
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "base.json"
        p.write_text(json.dumps(_report(subject=SUBJECT.id, scenario=first)), encoding="utf-8")
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            assert gate_cli.main(["--scenario", second, "--baseline", str(p), "--as-of", "2026-11-08"]) == 2
        assert f"scenario {first!r}" in err.getvalue() and "did not answer" not in err.getvalue(), err.getvalue()


def test_the_mcp_reader_serves_no_report_baseline():
    src = (ROOT / "harness" / "mcp_server.py").read_text(encoding="utf-8")
    assert '"baseline": {"type": "string", "enum": ["none", "record"]' in src
    assert 'raise ToolError("baseline must be none or record; a file path is not served")' in src


def test_the_changelog_names_it_under_contract_changes():
    log = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").split("\n## ", 2)[1]
    assert "task-0258" in log.split("### Contract changes", 1)[1].split("### Changes", 1)[0]
