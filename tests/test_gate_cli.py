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
from _subject_pin import CARGO_QUOTE  # noqa: E402

SCHEMA = schema_check.load("gate-report")
BLOCK = {"absent", "declared_gap", "disputed", "invalidated"}


def _record(sc: str) -> dict:
    rel = CARGO_QUOTE.scenario(sc).get("deterministic_record") or sc
    return json.loads((CARGO_QUOTE.record_dir / rel / "deterministic.json").read_text(encoding="utf-8"))


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
        assert base == {"source": "record", "verdict": res["verdict"], "regression": False, "worse_verdict": False, "regressed_keys": []}
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
    assert gate_cli.baseline_of(rep) == {"verdict": "PROCEED", "levels": rep["levels"]}


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
