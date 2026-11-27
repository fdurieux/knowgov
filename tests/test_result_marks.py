"""task-0365: a result the MCP reader cut says so, in _meta and first in content; an uncut one carries no mark.

register_nodes past its limit and scenario_runs past its limit are the reader's two cuts; an answer refused over
KG_MCP_MAX_RESPONSE names its size and the narrower call. The mark is computed from the tool's own answer, so the
same over both eras here (the stateless era's own _meta stamp kept beside it) and over HTTP and on Neo4j in
tools/check_mcp_server.py. Files only: register_nodes reads the vendored register, no store is opened."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(Path(__file__).resolve().parent)]
import mcp_server  # noqa: E402
import result_marks  # noqa: E402
import schema_check  # noqa: E402
from test_mcp_server import _call, _server  # noqa: E402

META = result_marks.META_CLIPPED
MODERN = {"io.modelcontextprotocol/protocolVersion": "2026-07-28", "io.modelcontextprotocol/clientCapabilities": {},
          "io.modelcontextprotocol/clientInfo": {"name": "t", "version": "1"}}


def _meta_ok(result: dict) -> dict:
    errors = schema_check.validate(result.get("_meta") or {}, schema_check.load("result-meta"))
    assert errors == [], errors
    return result.get("_meta") or {}


def test_register_nodes_past_its_limit_is_marked_partial_in_meta_and_first_in_content():
    s, _ = _server()
    r = _call(s, "register_nodes", {"limit": 2})["result"]
    m = _meta_ok(r)[META]
    data = r["structuredContent"]
    assert m == {"partial": True, "what": "nodes", "returned": 2, "total": data["total"], "narrower": m["narrower"]} and data["total"] > 2
    assert "offset 2" in m["narrower"] and "filter" in m["narrower"]
    assert r["content"][0]["text"] == result_marks.words(m) and r["content"][0]["text"].startswith(f"partial: 2 of {data['total']} nodes")
    assert json.loads(r["content"][1]["text"]) == data   # the answer itself, after the mark


def test_an_uncut_result_carries_no_mark_and_its_content_is_as_before():
    s, _ = _server()
    total = _call(s, "register_nodes", {"limit": 1})["result"]["structuredContent"]["total"]
    for args in ({"limit": total}, {"limit": 1000}, {"node": "CAP-0002"}):
        r = _call(s, "register_nodes", args)["result"]
        assert "_meta" not in r and len(r["content"]) == 1 and json.loads(r["content"][0]["text"]) == r["structuredContent"], args


def test_the_mark_is_the_same_in_the_stateless_era_beside_its_own_stamp():
    s, _ = _server()
    old = _call(s, "register_nodes", {"limit": 2})["result"]
    new = s.handle({"jsonrpc": "2.0", "id": 9, "method": "tools/call",
                    "params": {"name": "register_nodes", "arguments": {"limit": 2}, "_meta": MODERN}})["result"]
    meta = _meta_ok(new)
    assert meta[META] == old["_meta"][META] and mcp_server.META_SERVER in meta
    assert new["content"] == old["content"] and new["structuredContent"] == old["structuredContent"]
    uncut = s.handle({"jsonrpc": "2.0", "id": 10, "method": "tools/call",
                      "params": {"name": "register_nodes", "arguments": {"node": "CAP-0002"}, "_meta": MODERN}})["result"]
    assert META not in uncut["_meta"] and mcp_server.META_SERVER in uncut["_meta"]


def test_scenario_runs_cut_by_its_limit_is_marked_and_uncut_is_not():
    data = {"scenarios": [{"scenario": "S1", "runs": [{}], "runs_total": 3}, {"scenario": "S2", "runs": [], "runs_total": 0}]}
    m = result_marks.clipped("scenario_runs", {"limit": 1}, data)
    assert m == {"partial": True, "what": "runs", "returned": 1, "total": 3, "narrower": m["narrower"]} and "S1" in m["narrower"]
    assert result_marks.clipped("scenario_runs", {}, {"scenarios": [{"scenario": "S1", "runs": [{}], "runs_total": 1}]}) is None
    assert result_marks.clipped("gate_verdict", {}, {"findings": []}) is None   # a tool that never cuts carries none


def test_an_answer_over_the_cap_names_its_size_and_the_narrower_call():
    os.environ["KG_MCP_MAX_RESPONSE"] = "4096"
    try:
        s, _ = _server()
    finally:
        os.environ.pop("KG_MCP_MAX_RESPONSE", None)
    r = _call(s, "register_nodes", {"limit": 1000})["result"]
    m = _meta_ok(r)[META]
    assert r["isError"] is True and "structuredContent" not in r and "KG_MCP_MAX_RESPONSE" in r["content"][0]["text"]
    assert m["what"] == "bytes" and m["returned"] == 0 and m["total"] > 4096 and m["narrower"] == result_marks.NARROWER["register_nodes"]
    assert m["narrower"] in r["content"][0]["text"]
    assert "summary true" in result_marks.NARROWER["gate_verdict"] and "filter" in result_marks.NARROWER["gate_verdict"]


def test_every_narrower_call_names_a_tool_the_reader_serves_and_an_argument_it_takes():
    tools = {t["name"]: set(t["inputSchema"]["properties"]) for t in mcp_server.TOOLS}
    for name, text in result_marks.NARROWER.items():
        assert name in tools, name
        first = text.split(" ", 1)[0]
        assert first in tools, (name, first)
    assert {"summary", "filter"} <= tools["gate_verdict"] and {"keys", "verbatim"} <= tools["evidence_bundle"]
    assert {"offset", "limit"} <= tools["register_nodes"]


def _budget_server(budget: str):
    os.environ["KG_MCP_CLIENT_BUDGET"] = budget
    try:
        return _server()[0]
    finally:
        os.environ.pop("KG_MCP_CLIENT_BUDGET", None)


def test_an_answer_over_the_client_budget_is_whole_and_marked_large_before_it():
    """decision-0048: nothing is cut; the mark names its size, the budget, what it holds and the narrower call, in _meta and
    as a text item before the answer, which stays the last text item, unchanged."""
    s = _budget_server("1000")
    r = _call(s, "register_nodes", {"limit": 1000})["result"]
    meta = _meta_ok(r)
    big = meta[result_marks.META_LARGE]
    data = r["structuredContent"]
    assert META not in meta and big["partial"] is False and big["budget"] == 1000
    assert big["chars"] == len(r["content"][-1]["text"]) > 1000 and big["count"] == {"what": "nodes", "n": data["total"]}
    assert json.loads(r["content"][-1]["text"]) == data and len(r["content"]) == 2
    assert r["content"][0]["text"].startswith(f"large: this answer is {big['chars']} characters") and big["narrower"] in r["content"][0]["text"]
    both = _call(s, "register_nodes", {"limit": 2})["result"]   # small: clipped only
    assert set(both["_meta"]) == {META}
    under = _call(_server()[0], "register_nodes", {"limit": 1000})["result"]   # the default budget: neither mark
    assert "_meta" not in under and len(under["content"]) == 1


def test_a_clipped_answer_over_the_budget_carries_both_marks_each_before_the_answer():
    s = _budget_server("1000")
    total = _call(s, "register_nodes", {"limit": 1})["result"]["structuredContent"]["total"]
    r = _call(s, "register_nodes", {"limit": total - 1})["result"]
    assert set(_meta_ok(r)) == {META, result_marks.META_LARGE} and len(r["content"]) == 3
    assert r["content"][0]["text"].startswith("partial: ") and r["content"][1]["text"].startswith("large: ")
    assert json.loads(r["content"][2]["text"]) == r["structuredContent"]


def test_the_budget_is_a_bounded_setting_refused_at_start_outside_its_bounds():
    import settings
    assert settings.NUMBERS["KG_MCP_CLIENT_BUDGET"] == (int, 1000, 1 << 30, 100_000, True)
    assert "KG_MCP_CLIENT_BUDGET" in mcp_server.MCP_SETTINGS
    import subprocess
    for bad in ("999", "abc", str((1 << 30) + 1)):
        p = subprocess.run([sys.executable, str(ROOT / "harness" / "mcp_server.py")], input="", capture_output=True, text=True,
                           timeout=60, env={**os.environ, "KG_MCP_CLIENT_BUDGET": bad})
        assert p.returncode == 2 and "KG_MCP_CLIENT_BUDGET" in p.stderr, (bad, p.returncode, p.stderr[-300:])
    row = next(ln for ln in (ROOT / "instance" / "README.md").read_text(encoding="utf-8").splitlines() if ln.startswith("| `KG_MCP_CLIENT_BUDGET` |"))
    assert row.endswith("| `100000` | yes |") and "common MCP clients" in row
