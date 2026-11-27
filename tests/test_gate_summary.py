"""task-0364: gate_verdict's summary and filter (harness/gate_summary.py), read from the one gate report.

The summary's counts are the report's own, computed again here from its findings and levels; a filter keeps the
findings matching every field it names and nothing else of the report moves; the default answer is the report
untouched. On a live store, both transports and both stores, tools/check_mcp_server.py holds the same."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness"))
import gate  # noqa: E402
import gate_summary  # noqa: E402
import mcp_server  # noqa: E402
import schema_check  # noqa: E402

SPEC = {"keys": ["a|x", "b|y", "c|z"], "block_levels": {"absent"}, "max_unverified_share": 0.25}


def _f(sev, kind, key=None, level=None, **kw):
    return {"severity": sev, "kind": kind, "key": key, "level": level, "flags": [], "ref": None, "related": [], "message": "m", **kw}


def _report() -> dict:
    fs = [_f("blocker", "key", "a|x", "absent", owner="ORG-1", route="r"), _f("major", "key", "b|y", "proposed", owner="ORG-2", route="r"),
          _f("major", "stale", "b|y", "invalidated", owner="ORG-2", route="r", ref="A:b@v1"), _f("blocker", "task"),
          _f("info", "key", "c|z", "verified", owner=None, route=None)]
    return {"schema_version": 3, "tool": "knowgov gate", "subject": "s", "scenario": "S1", "task": "codegen", "store": "rdflib",
            "loaded": False, "version": "v1", "change": None, "verdict": "BLOCKED", "why": "w", "threshold": "blocker",
            "findings": fs, "counts": {"blocker": 2, "critical": 0, "major": 2, "minor": 0, "info": 1},
            "keys": {"total": 3, "below_verified": 2, "flagged": 0}, "conflicts": 0, "stale": ["A:b@v1"], "superseded_by": {},
            "suspect_derived": [], "as_of": "2026-10-30", "lapsed": [], "levels": {"a|x": "absent", "b|y": "proposed", "c|z": "verified"},
            "baseline": None, "exit_code": 1, "task_profile": None, "register": {"tag": None, "commit": None, "why": "w"},
            "knowgov": {"version": "0.9.1", "commit": None, "describe": None}, "corpus": None, "attestations": None, "captures": None,
            "configuration": None, "code": None, "preload": None}


def test_the_summary_counts_the_report_and_lists_no_finding():
    rep = _report()
    s = gate_summary.summary(rep, SPEC)
    assert schema_check.validate(s, schema_check.load("gate-summary")) == []
    assert "findings" in s and s["findings"] == 5 and not isinstance(s["findings"], list)
    assert s["counts"]["by_severity"] == rep["counts"]
    assert s["counts"]["by_kind"] == {"key": 3, "stale": 1, "task": 1}
    assert s["counts"]["by_level"] == {"absent": 1, "proposed": 1, "verified": 1} and sum(s["counts"]["by_level"].values()) == rep["keys"]["total"]
    assert s["counts"]["by_owner"] == [
        {"owner": "ORG-1", "findings": 1, "keys": 1, "by_severity": {"blocker": 1, "critical": 0, "major": 0, "minor": 0, "info": 0}},
        {"owner": "ORG-2", "findings": 2, "keys": 1, "by_severity": {"blocker": 0, "critical": 0, "major": 2, "minor": 0, "info": 0}},
        {"owner": None, "findings": 2, "keys": 1, "by_severity": {"blocker": 1, "critical": 0, "major": 0, "minor": 0, "info": 1}}]
    assert s["bar"] == {"block_levels": ["absent"], "max_unverified_share": 0.25, "require_approved": False}
    for k in gate_summary.IDENTITY + ("verdict", "why", "exit_code", "as_of", "keys"):
        assert s[k] == rep[k], k
    assert len(json.dumps(s)) < len(json.dumps(rep)) or rep["findings"] == []


def test_a_filter_keeps_only_the_findings_it_names_and_moves_nothing_else():
    rep = _report()
    got = gate_summary.filtered(rep, {"owner": "ORG-2", "kind": "key"})
    assert [f["key"] for f in got["findings"]] == ["b|y"] and got["filter"] == {"owner": "ORG-2", "kind": "key", "matched": 1, "total": 5}
    assert {k: v for k, v in got.items() if k not in ("findings", "filter")} == {k: v for k, v in rep.items() if k != "findings"}
    none = gate_summary.filtered(rep, {"owner": None})   # the owner summary's null row: no single unit, or a kind naming none
    assert [f["kind"] for f in none["findings"]] == ["task", "key"] and none["filter"]["matched"] == 2
    assert schema_check.validate(got, schema_check.load("gate-report")) == []
    for row in gate_summary.summary(rep, SPEC)["counts"]["by_owner"]:   # every row's count is what its filter returns
        assert gate_summary.filtered(rep, {"owner": row["owner"]})["filter"]["matched"] == row["findings"]


def test_the_tool_takes_summary_and_filter_and_names_both_schemas():
    t = next(t for t in mcp_server.TOOLS if t["name"] == "gate_verdict")
    props = t["inputSchema"]["properties"]
    assert props["summary"]["type"] == "boolean" and set(props["filter"]["properties"]) == set(gate_summary.FILTERS)
    assert mcp_server.GATE_LEVELS == gate.ORDER == list(gate_summary.LEVELS)
    kinds = schema_check.load("gate-report")["$defs"]["finding"]["properties"]["kind"]["enum"]
    assert mcp_server.FINDING_KINDS == kinds
    assert mcp_server.output_schema("gate_verdict", {"summary": True}) == "gate-summary"
    assert mcp_server.output_schema("gate_verdict", {}) == mcp_server.output_schema("gate_verdict", {"filter": {"kind": "key"}}) == "gate-report"
    assert "harness/schemas/gate-summary.schema.json" in t["description"] and "summary true" in t["description"]
    schema_check.validate({}, schema_check.load("gate-summary"))   # every keyword in the supported subset
    refuse = lambda a: mcp_server.sent_refusal("gate_verdict", a, t["inputSchema"])
    assert refuse({"filter": {"key": "nonsense"}}) and refuse({"filter": {"colour": "x"}}) and refuse({"summary": "yes"})
    assert refuse({"filter": {"key": "thing​|property"}}) and refuse({"filter": {"kind": "bogus"}})
    assert refuse({"filter": {"owner": None, "severity": "major"}}) is None


def test_the_bar_lists_a_classs_block_levels_in_the_gates_order_whatever_the_set_order():
    """A task class's block levels are a set; the summary lists them worst first, so stdio and HTTP, each its own process
    with its own hash seed, answer byte for byte alike."""
    for levels in ({"invalidated", "absent", "disputed", "declared_gap"}, ["disputed", "declared_gap", "invalidated", "absent"]):
        assert gate_summary.bar({"block_levels": levels})["block_levels"] == ["absent", "declared_gap", "disputed", "invalidated"]


def test_an_empty_filter_or_one_beside_summary_is_refused_and_none_reads_the_report_whole():
    for args, why in (({"filter": {}}, "names none"), ({"summary": True, "filter": {"kind": "key"}}, "name one")):
        try:
            mcp_server.verdict_filter(args)
        except mcp_server.ToolError as e:
            assert why in str(e), e
        else:
            raise AssertionError(args)
    assert mcp_server.verdict_filter({}) is None and mcp_server.verdict_filter({"summary": True}) is None


def test_a_filter_key_is_read_in_nfc():
    got = mcp_server.nfc_keys({"filter": {"key": "Café|price", "kind": "key"}})
    assert got["filter"] == {"key": "Café|price", "kind": "key"}
