"""Task-0007: the gate as a command. The findings, the threshold, the ratchet and the report's
schema are checked here on every scenario of the CargoQuote record, rebuilt from its run files;
the command against a live store (rdflib in harness.yml, Neo4j in the stack job) runs in CI."""
from __future__ import annotations

import io
import json
import sys
import tempfile
from contextlib import redirect_stderr
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(Path(__file__).resolve().parent)]
import gate  # noqa: E402
import gate_cli  # noqa: E402
import schema_check  # noqa: E402
import subject  # noqa: E402
from _subject_pin import CARGO_QUOTE  # noqa: E402

JEF = subject.Subject(ROOT / "subjects" / "jef_data_load")

SCHEMA = schema_check.load("gate-report")
BLOCK = {"absent", "declared_gap", "disputed", "invalidated"}


def _record(sc: str, subj=CARGO_QUOTE) -> dict:
    rel = subj.scenario(sc).get("deterministic_record") or sc
    return json.loads((subj.record_dir / rel / "deterministic.json").read_text(encoding="utf-8"))


def _res(det: dict) -> dict:
    """The gate's result as the record's run file holds it (D6_gate plus gate_keys)."""
    g = det["D6_gate"]
    return {**g, "keys": {k: {"level": v["level"], "flags": v["flags"]} for k, v in det["gate_keys"].items()}}


def _report(res: dict, threshold: str = "blocker", baseline: dict | None = None) -> dict:
    return gate_cli.report(res, subject="cargo_quote", scenario="S", task="codegen", store="rdflib", loaded=True,
                           block_levels=BLOCK, threshold=threshold, baseline=baseline)


def test_the_ladder_and_the_level_order_are_the_gates():
    assert gate_cli.LEVELS == gate.ORDER
    assert gate_cli.SEVERITIES == ["blocker", "critical", "major", "minor", "info"]


def test_every_record_scenario_gives_a_valid_report_and_the_contracts_exit_codes():
    seen = set()
    for sc in CARGO_QUOTE.order:
        det = _record(sc)
        res = _res(det)
        rep = _report(res)
        assert schema_check.validate(rep, SCHEMA) == [], (sc, schema_check.validate(rep, SCHEMA)[:3])
        assert rep["exit_code"] == (1 if res["verdict"] == "BLOCKED" else 0), sc
        blockers = [f for f in rep["findings"] if f["severity"] == "blocker"]
        assert bool(blockers) == (res["verdict"] == "BLOCKED"), sc
        majors = {f["key"] for f in rep["findings"] if f["severity"] == "major"}
        assert majors == set(res["below_verified"]) - set(res["blocked_keys"]), sc
        if res["verdict"] == "QUALIFIED":
            assert _report(res, "major")["exit_code"] == (1 if majors else 0)
            assert _report(res, "minor")["exit_code"] == 1
        # the record is the baseline: the same result is never a regression, whatever the verdict
        base = gate_cli.compare(res, gate_cli.baseline_of(det), "record")
        assert base == {"source": "record", "verdict": res["verdict"], "regression": False, "worse_verdict": False,
                        "regressed_keys": [], "new_suspect": []}
        assert _report(res, baseline=base)["exit_code"] == 0
        seen.add(res["verdict"])
    assert seen == {"PROCEED", "QUALIFIED", "BLOCKED"}


def test_a_worse_verdict_or_a_lower_key_level_is_a_regression():
    s1, s2 = _res(_record("S1")), _res(_record("S2"))
    b = gate_cli.compare(s2, gate_cli.baseline_of(_record("S1")), "record")
    assert b["regression"] and b["worse_verdict"]
    assert {r["key"] for r in b["regressed_keys"]} == {"QuoteAPI|on_screening_outage", "response|hold_presence", "response|statuses"}
    assert _report(s2, baseline=b)["exit_code"] == 1
    assert not gate_cli.compare(s1, gate_cli.baseline_of(_record("S2")), "record")["regression"], "better is not a regression"
    # same verdict, one key lower: still a regression (the ratchet holds keys, not only the verdict)
    lower = json.loads(json.dumps(s1))
    k = next(iter(lower["keys"]))
    lower["keys"][k]["level"] = "verified"
    base = {"verdict": "PROCEED", "levels": {k: "approved"}}
    assert gate_cli.compare(lower, base, "f")["regressed_keys"] == [{"key": k, "level": "verified", "baseline_level": "approved"}]
    # a report of this command is a baseline too
    rep = _report(s1)
    assert gate_cli.baseline_of(rep) == {"verdict": "PROCEED", "levels": rep["levels"], "suspect": []}
    # a version-1 report still reads as a baseline: it named no derived output, so none was suspect
    v1 = {**rep, "schema_version": 1, "stale": 0, "suspect_derived": 0}
    assert gate_cli.baseline_of(v1) == {"verdict": "PROCEED", "levels": rep["levels"], "suspect": []}


def test_a_task_blocked_by_its_share_of_unverified_keys_says_so_as_a_blocker():
    res = _res(_record("S7"))
    assert res["verdict"] == "BLOCKED" and not res["blocked_keys"]
    rep = _report(res)
    whole = [f for f in rep["findings"] if f["key"] is None]
    assert len(whole) == 1 and whole[0]["severity"] == "blocker" and rep["exit_code"] == 1


def test_the_schema_checker_refuses_what_it_cannot_check_and_catches_a_bad_report():
    try:
        schema_check.validate({}, {"type": "object", "pattern": "x"})
        raise AssertionError("an unsupported keyword passed")
    except ValueError:
        pass
    rep = _report(_res(_record("S1")))
    bad = {**rep, "verdict": "MAYBE", "exit_code": 2, "extra": 1}
    del bad["why"]
    errs = " | ".join(schema_check.validate(bad, SCHEMA))
    assert "MAYBE" in errs and "missing 'why'" in errs and "unexpected 'extra'" in errs and "$.exit_code" in errs, errs


def test_what_the_gate_cannot_do_exits_2():
    from subject import SUBJECT   # the process's subject (KG_SUBJECT): the command reads that one
    first = SUBJECT.order[0]
    for argv in (["--scenario", "nope"], ["--task", "nope"], ["--scenario", first, "--task", "nope"],
                 ["--scenario", first, "--baseline", str(ROOT / "no-such-baseline.json")]):
        err = io.StringIO()
        with redirect_stderr(err):
            assert gate_cli.main(argv) == 2, argv
        assert err.getvalue().startswith("gate: cannot run: "), err.getvalue()
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "b.json"
        p.write_text("{}", encoding="utf-8")
        err = io.StringIO()
        with redirect_stderr(err):
            assert gate_cli.main(["--scenario", first, "--baseline", str(p)]) == 2
        assert "neither a gate report nor a deterministic.json" in err.getvalue()


def _scored_s6() -> dict:
    return json.loads((CARGO_QUOTE.record_dir / "S6" / "deterministic.json").read_text(encoding="utf-8"))


def _stage2(gate_res: dict, stage1: dict) -> dict:
    """S6's stage-2 gate as the record holds it. The record keeps no per-key levels after stage 1, so
    the keys take stage 1's, with the blocked ones at invalidated: a key at verified or better and
    unflagged gives no finding at either level, so the findings are the record's own."""
    keys = {k: {"level": v["level"], "flags": v["flags"]} for k, v in stage1["gate_keys"].items()}
    for k in gate_res["blocked_keys"]:
        keys[k] = {"level": "invalidated", "flags": []}
    return {**gate_res, "keys": keys}


def test_after_s6s_change_a_suspect_derived_output_fails_the_gate_whatever_the_verdict():
    """task-0048: doc-0011 point 3 measured PROCEED after S6's re-verification with derived:S1:G:run1
    still suspect, and exit 0, since stale and suspect were counts. They are findings now. The scored
    record's S6 registered S1's governed code as derived; the deterministic record (d3check) did not."""
    det = _scored_s6()
    s2 = det["stage2"]
    after = _stage2(s2["gate_after_reverification"], det)
    assert after["verdict"] == "PROCEED" and after["suspect_derived"], "the record's measurement this task answers"
    rep = _report(after)
    assert schema_check.validate(rep, SCHEMA) == [], schema_check.validate(rep, SCHEMA)[:3]
    assert rep["schema_version"] == 2 and rep["verdict"] == "PROCEED" and rep["exit_code"] == 1
    sus = [f for f in rep["findings"] if f["kind"] == "suspect_derived"]
    assert [(f["severity"], f["ref"]) for f in sus] == [("blocker", "derived:S1:G:run1")]
    assert set(sus[0]["related"]) == {"A:dt:P2|threshold@v1", "A:dt:P2|surcharge@v1", "A:dt:P3|order@v1"}
    assert rep["suspect_derived"] == ["derived:S1:G:run1"]
    # the three invalidated statements are each replaced by an approved successor: info, the record of the change
    stale = [f for f in rep["findings"] if f["kind"] == "stale"]
    assert {f["ref"] for f in stale} == set(rep["stale"]) == {x["id"] for x in s2["gate_after_reverification"]["stale"]}
    assert all(f["severity"] == "info" and f["level"] == "invalidated" and f["related"] for f in stale)
    assert rep["counts"]["info"] == 3 and rep["counts"]["blocker"] == 1
    # the ratchet: stage 1 (the record's D6_gate) held nothing suspect, so the derived output is a regression
    base = gate_cli.compare(after, gate_cli.baseline_of(det), "record")
    assert base["regression"] and base["new_suspect"] == ["derived:S1:G:run1"] and not base["worse_verdict"]
    assert _report(after, baseline=base)["exit_code"] == 1
    # with the derived output's review recorded (no longer suspect), the gate passes and the stale stay info
    clean = _report({**after, "suspect_derived": []})
    assert clean["exit_code"] == 0 and _report({**after, "suspect_derived": []}, "info")["exit_code"] == 1


def test_before_re_verification_the_stale_statements_on_the_blocked_keys_are_major():
    det = _scored_s6()
    before = _stage2(det["stage2"]["gate_before_reverification"], det)
    rep = _report(before)
    assert schema_check.validate(rep, SCHEMA) == [], schema_check.validate(rep, SCHEMA)[:3]
    assert rep["verdict"] == "BLOCKED" and rep["exit_code"] == 1
    sev = {f["ref"]: f["severity"] for f in rep["findings"] if f["kind"] == "stale"}
    assert sev, "S6 stage 2 invalidates statements on required keys"
    for x in det["stage2"]["gate_before_reverification"]["stale"]:
        settled = [t for t in x["successors"] if t["id"] and t["status"] in gate_cli.SETTLED]
        assert sev[x["id"]] == ("info" if settled else "major"), x


def test_every_jef_record_scenario_gives_a_valid_report():
    assert JEF.order
    for sc in JEF.order:
        rep = _report(_res(_record(sc, JEF)))
        assert schema_check.validate(rep, SCHEMA) == [], (sc, schema_check.validate(rep, SCHEMA)[:3])
        assert all(f["kind"] in ("key", "task") for f in rep["findings"]), sc


def test_a_later_version_is_asked_for_coherently_or_the_gate_cannot_run():
    """task-0049: --stage 2 needs a [scenario.stage2]; --reverify is a step of it; --no-load reads,
    so it cannot also load a change. Each refusal is exit 2, before any store is opened. On the
    process's subject (KG_SUBJECT): the J-F subject has no scenario with a later version, so only
    the refusals that need none run there."""
    from subject import SUBJECT
    first = SUBJECT.order[0]
    plain = next((sc for sc in SUBJECT.order if not SUBJECT.scenario(sc).get("stage2")), None)
    changed = next((sc for sc in SUBJECT.order if SUBJECT.scenario(sc).get("stage2")), None)
    cases = [(["--scenario", first, "--reverify"], "add --stage 2")]
    if plain:
        cases.append((["--scenario", plain, "--stage", "2"], "no later version"))
    if changed:
        cases.append((["--scenario", changed, "--stage", "2", "--no-load"], "drop one"))
    for argv, why in cases:
        err = io.StringIO()
        with redirect_stderr(err):
            assert gate_cli.main(argv) == 2, argv
        assert why in err.getvalue(), err.getvalue()


def test_the_report_names_the_version_and_the_change_and_a_report_without_them_still_validates():
    rep = _report(_res(_record("S1")))
    assert rep["version"] is None and rep["change"] is None
    del rep["version"], rep["change"]
    assert schema_check.validate(rep, SCHEMA) == []   # additive within version 2
    s2 = _scored_s6()["stage2"]
    change = {"artefact": "contract/decision_table.md", "version": "v2",
              "invalidated": sorted(x["id"] for x in s2["D3_stale"]["invalidated"]),
              "reverified": False, "reverified_statements": [], "derived": "derived:S1:G:run1"}
    rep = gate_cli.report(_stage2(s2["gate_before_reverification"], _scored_s6()), subject="cargo_quote", scenario="S6",
                          task="codegen", store="rdflib", loaded=True, block_levels=BLOCK, threshold="blocker",
                          baseline=None, version="v2", change=change)
    assert schema_check.validate(rep, SCHEMA) == [], schema_check.validate(rep, SCHEMA)[:3]
    assert rep["verdict"] == "BLOCKED" and rep["exit_code"] == 1 and len(rep["change"]["invalidated"]) == 4
    assert "v2 of contract/decision_table.md: 4 statement(s) invalidated" in gate_cli.render(rep)
    assert schema_check.validate({**rep, "change": {**change, "extra": 1}}, SCHEMA)
