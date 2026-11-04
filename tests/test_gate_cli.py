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


def test_after_s6s_re_verification_each_stale_statement_names_what_supersedes_it():
    """task-0071 (doc-0013 P5): superseded is a reading of an invalidated statement with a verified or
    approved successor, never a stored status. The report and the bundle name ``superseded_by``; the
    record's after-re-verification successors are what they name."""
    import gate
    det = _scored_s6()
    after = _stage2(det["stage2"]["gate_after_reverification"], det)
    rep = _report(after)
    want = {x["id"]: sorted({t["id"] for t in x["successors"] if t["id"] and t["status"] in ("verified", "approved")})
            for x in det["stage2"]["gate_after_reverification"]["stale"]}
    assert rep["superseded_by"] == want and len(want) == 3 and all(want.values())
    assert rep["superseded_by"]["A:dt:P3|order@v1"] == ["A:dt:P3|order#1@v1", "A:dt:P3|order@v2"]
    assert schema_check.validate(rep, SCHEMA) == []
    bare = {**after, "keys": {}}   # the record keeps no per-key assertions; the stale section is what is asked
    bundle = gate.render_bundle(bare, "POLICY")
    for sid, ids in want.items():
        assert f"[{sid}]" in bundle and f"superseded_by: {', '.join(ids)}" in bundle, sid
    assert all(f"{sid} superseded_by" in gate.render_index(bare, "POLICY") for sid in want)
    # a successor merely proposed or validated supersedes nothing: the statement still blocks its key
    weak = {**bare, "stale": [{**x, "successors": [{**t, "status": "proposed"} for t in x["successors"]]} for x in after["stale"]]}
    assert _report(weak)["superseded_by"] == {}
    assert "superseded_by: none: it still blocks its key" in gate.render_bundle(weak, "POLICY")
    # a report from before task-0071 still validates: the field is additive
    old = {k: v for k, v in rep.items() if k != "superseded_by"}
    assert schema_check.validate(old, SCHEMA) == []


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


def test_key_stale_and_lapsed_findings_name_the_owner_unit_and_the_questionnaire_route():
    """Task-0102 (doc-0014 C7): S2's blocking findings name their key's owner unit from the subject's
    register_map.toml and the owner's questionnaire; the report validates with the fields and without
    (the version-2 report as first published), and the other kinds carry neither."""
    import capture
    owners = capture.finding_owners(CARGO_QUOTE)
    assert owners["QuoteAPI|on_screening_outage"] == {"unit": "ORG-0002", "name": "Architecture stewardship (stand-in)"}
    res = _res(_record("S2"))
    rep = gate_cli.report(res, subject="cargo_quote", scenario="S2", task="codegen", store="rdflib", loaded=True,
                          block_levels=BLOCK, threshold="blocker", baseline=None, owners=owners)
    assert schema_check.validate(rep, SCHEMA) == []
    blockers = [f for f in rep["findings"] if f["severity"] == "blocker"]
    assert blockers and all(f["kind"] == "key" for f in blockers)
    for f in blockers:
        assert f["owner"] == owners[f["key"]]["unit"] == "ORG-0002", f
        assert f["route"].startswith("python harness/capture.py questionnaire --scenario S2 --task codegen --out DIR"), f
        assert "questionnaire-cargo_quote-S2-ORG-0002.toml" in f["route"] and "ingest" in f["route"], f
    assert all(("owner" in f) == (f["kind"] in gate_cli.OWNED) for f in rep["findings"])
    assert "[owner ORG-0002]" in gate_cli.render(rep)
    # without owners: version 2 as first published, which the schema still validates
    old = _report(res)
    assert not any("owner" in f or "route" in f for f in old["findings"]) and schema_check.validate(old, SCHEMA) == []
    # a key no row maps names no unit, and the route its unassigned questionnaire
    rep = gate_cli.report(res, subject="cargo_quote", scenario="S2", task="codegen", store="rdflib", loaded=True,
                          block_levels=BLOCK, threshold="blocker", baseline=None, owners={})
    f = next(f for f in rep["findings"] if f["kind"] == "key")
    assert f["owner"] is None and "questionnaire-cargo_quote-S2-unassigned.toml" in f["route"]
    assert schema_check.validate(rep, SCHEMA) == []
    bad = json.loads(json.dumps(rep))
    bad["findings"][0]["owner"] = 7
    assert schema_check.validate(bad, SCHEMA), "a non-string owner passed"


def test_stale_and_lapsed_findings_name_the_owner_too():
    res = {"verdict": "PROCEED", "why": "w", "keys": {}, "blocked_keys": [], "below_verified": [], "flagged": [],
           "stale": [{"id": "a1", "key": "k|p", "invalidated_by": "act:x", "successors": [], "verifications": []}],
           "lapsed": [{"id": "a2", "key": "k|q", "from": "verified", "valid_until": "2026-01-01", "verifications": ["v1"]}],
           "suspect_derived": [{"id": "d1", "kind": "code", "used_invalidated": ["a1"]}], "as_of": "2026-11-04"}
    fs = gate_cli.findings(res, BLOCK, {"k|p": {"unit": "U-1", "name": ""}, "k|q": {"unit": None, "name": ""}}, lambda u, k: f"to {u}")
    by = {f["kind"]: f for f in fs}
    assert by["stale"]["owner"] == "U-1" and by["stale"]["route"] == "to U-1"
    assert by["lapsed"]["owner"] is None and by["lapsed"]["route"] == "to None"
    assert "owner" not in by["suspect_derived"] and "route" not in by["suspect_derived"]


def test_an_agent_chosen_key_set_routes_to_the_questionnaire_of_its_task_class():
    """The MCP server's ``keys`` report (task-0102): the route names the class the keys were resolved
    under, never ``--task keys``, which capture.py refuses; a key outside that class has no route."""
    res = _res(_record("S2"))
    owners = {k: {"unit": "ORG-0002", "name": ""} for k in res["keys"]}
    some = sorted(res["blocked_keys"])[:1]
    rep = gate_cli.report(res, subject="cargo_quote", scenario="S2", task="keys", store="rdflib", loaded=False,
                          block_levels=BLOCK, threshold="blocker", baseline=None, owners=owners,
                          route_task="codegen", route_keys=set(some))
    routed = {f["key"]: f["route"] for f in rep["findings"] if f["kind"] == "key"}
    assert routed[some[0]] and "--task codegen" in routed[some[0]] and "--task keys" not in routed[some[0]]
    assert all(r is None for k, r in routed.items() if k not in some)
    assert schema_check.validate(rep, SCHEMA) == []


def test_a_declared_gaps_finding_names_the_unit_that_closes_it_from_its_declaration():
    """Task-0110 (decision-0002 point 3): S2's OD-1 finding names ORG-0002 as answering and ORG-0004
    as closing, the unit the declaration's text names (compliance), not a constant: another text names
    another unit, a text naming none falls to the key's owners, and one naming no unit of the register
    gives null. The report validates with ``closer`` and without it, and no other finding carries it."""
    import capture
    rules = CARGO_QUOTE.rules
    key = "QuoteAPI|on_screening_outage"
    od1 = {"id": rules["declared_gap_id"], "text": rules["declared_gap_text"].format(req="REQ-06")}
    closers = capture.gap_closers(CARGO_QUOTE, {key: [od1]})
    assert closers == {key: {"unit": "ORG-0004", "name": "Compliance (stand-in)", "gap": "gap:declared:OD-1"}}
    other = lambda text: capture.gap_closers(CARGO_QUOTE, {key: [{"id": "g", "text": text}]})[key]["unit"]  # noqa: E731
    assert other("REQ-06 is open (owner: Architecture stewardship)") == "ORG-0002"
    assert other("REQ-06 is open (owner: ORG-0001)") == "ORG-0001"
    of_key = capture.owners_of(CARGO_QUOTE, capture.register_nodes(capture.register_root()))[key]
    assert other("REQ-06 is open") == (of_key[0] if len(of_key) == 1 else None), of_key
    assert other("REQ-06 is open (owner: treasury)") is None
    assert capture.gap_closers(CARGO_QUOTE, {key: []}) == {}

    res = _res(_record("S2"))
    rep = gate_cli.report(res, subject="cargo_quote", scenario="S2", task="codegen", store="rdflib", loaded=True,
                          block_levels=BLOCK, threshold="blocker", baseline=None,
                          owners=capture.finding_owners(CARGO_QUOTE), closers=closers)
    assert schema_check.validate(rep, SCHEMA) == []
    f = next(f for f in rep["findings"] if f["key"] == key)
    assert f["owner"] == "ORG-0002" and f["closer"] == "ORG-0004", f
    assert "ORG-0002 answers" in f["route"] and f["route"].endswith(capture.closing_route("gap:declared:OD-1", "ORG-0004")), f
    assert [x for x in rep["findings"] if "closer" in x] == [f]
    assert "[owner ORG-0002; closed by ORG-0004]" in gate_cli.render(rep)
    # without closers: task-0102's report, which the schema still validates
    old = gate_cli.report(res, subject="cargo_quote", scenario="S2", task="codegen", store="rdflib", loaded=True,
                          block_levels=BLOCK, threshold="blocker", baseline=None, owners=capture.finding_owners(CARGO_QUOTE))
    assert not any("closer" in x for x in old["findings"]) and schema_check.validate(old, SCHEMA) == []
    bad = json.loads(json.dumps(rep))
    next(x for x in bad["findings"] if "closer" in x)["closer"] = 4
    assert schema_check.validate(bad, SCHEMA), "a non-string closer passed"
