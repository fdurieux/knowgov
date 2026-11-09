"""Task-0281 (decision-0033 choice 7(a)): every MCP call's arguments are held to the tool's inputSchema before
dispatch, on both servers, both transports and both protocol eras. A type, enum, pattern, minimum, minItems or
required violation is -32602 naming the property; arguments that are not an object are refused; a default
applies only when the argument is absent. The page's POST /api/run refuses a body key outside its fields."""
from __future__ import annotations

import json
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "demo" / "app")]
import mcp_runs  # noqa: E402
import mcp_server  # noqa: E402
import schema_check  # noqa: E402
from tests.test_http_limits import _page, _post as _raw_post, _send  # noqa: E402
from tests.test_mcp_server import DAY, _Day, _meta, _server  # noqa: E402


def _servers():
    reader, _ = _server()
    return {"knowgov": reader, "knowgov-runs": mcp_runs.make_server(mcp_runs.Page(url="http://127.0.0.1:9", token=None))}


def _call(s, name, args, modern=False, omit=False):
    params = {"name": name} if omit else {"name": name, "arguments": args}
    if modern:
        params["_meta"] = _meta()
    with _Day():
        return s.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": params})


def _wrong_type(spec: dict):
    """A value no type the property admits accepts."""
    types = spec["type"] if isinstance(spec["type"], list) else [spec["type"]]
    return next(v for v in (1.5, "x", [], {}, True) if not any(schema_check._type_ok(v, t) for t in types))


def test_schema_check_reads_pattern_and_min_items_as_ecma_does():
    s = {"type": "object", "properties": {"n": {"type": "string", "pattern": r"^[A-Z]+-\d{4,}$"},
                                          "k": {"type": "array", "minItems": 1}}}
    assert schema_check.validate({"n": "CAP-0001", "k": ["a"]}, s) == []
    assert schema_check.validate({"n": "CAP-0001\n"}, s) and schema_check.validate({"n": "cap-1"}, s)   # ECMA's $ ends the string
    assert schema_check.validate({"k": []}, s) == ["$.k: 0 item(s), fewer than 1"]


def test_every_propertys_wrong_type_is_minus_32602_naming_it_on_both_servers_and_both_eras():
    """AC1, AC3: for every tool of both servers and every property it declares, a value of a type the
    property does not admit is -32602 whose message names the property; nothing is dispatched."""
    for sname, s in _servers().items():
        n = 0
        for tool in s.table:
            for prop, spec in (tool["inputSchema"].get("properties") or {}).items():
                if "type" not in spec:
                    continue
                for modern in (False, True):
                    r = _call(s, tool["name"], {prop: _wrong_type(spec)}, modern=modern)
                    assert "error" in r and r["error"]["code"] == -32602, (sname, tool["name"], prop, modern, r)
                    assert f"{prop}:" in r["error"]["message"], (sname, tool["name"], prop, r["error"]["message"])
                n += 1
        assert n > (20 if sname == "knowgov" else 3), (sname, n)


def test_enum_pattern_minimum_min_items_and_required_are_minus_32602_naming_the_property():
    """AC1: each keyword the tools use, one violation each, on the server that declares it."""
    reader, runs = _servers().values()
    cases = [(reader, "gate_verdict", {"fail_on": "fatal"}, "fail_on"), (reader, "gate_verdict", {"baseline": "file"}, "baseline"),
             (reader, "gate_verdict", {"keys": []}, "keys"), (reader, "evidence_bundle", {"keys": []}, "keys"),
             (reader, "register_impact", {"node": "CAP-1"}, "node"), (reader, "register_impact", {"node": "CAP-0001", "walk": ""}, "walk"),
             (reader, "register_impact", {}, "node"), (reader, "register_nodes", {"limit": 0}, "limit"),
             (reader, "register_nodes", {"offset": -1}, "offset"), (reader, "register_nodes", {"owner": "org-1"}, "owner"),
             (reader, "scenario_runs", {"limit": 0}, "limit"), (reader, "three_valued_answer", {}, "key"),
             (reader, "scenario_result", {"scenario": "S1"}, "source"), (runs, "start_run", {"scenario": "S1", "mode": "fast"}, "mode"),
             (runs, "start_run", {"mode": "deterministic"}, "scenario")]
    for s, name, args, prop in cases:
        for modern in (False, True):
            r = _call(s, name, args, modern=modern)
            assert r.get("error", {}).get("code") == -32602 and prop in r["error"]["message"], (name, args, modern, r)


def test_arguments_that_are_not_an_object_are_refused_and_absent_or_null_are_none():
    """AC1: [] and "" are refused, no longer read as {}; absent or null arguments are no arguments."""
    for sname, s in _servers().items():
        name = "store_status" if sname == "knowgov" else "run_options"
        for bad in ([], "", 0, ["scenario"]):
            r = _call(s, name, bad)
            assert r["error"]["code"] == -32602 and "object" in r["error"]["message"], (sname, bad, r)
        for ok in ({"omit": True}, {"args": None}, {"args": {}}):
            r = _call(s, name, ok.get("args"), omit=ok.get("omit", False))
            assert "result" in r, (sname, ok, r)


def test_a_default_applies_only_when_the_argument_is_absent():
    """AC2: gate_verdict with scenario "" is refused, never answered for the held scenario; with none, it
    answers for it; task "" is a class the subject does not declare, never codegen; as_of "" is no date."""
    s, _ = _server()
    held = _call(s, "gate_verdict", {"as_of": DAY})["result"]
    assert held["isError"] is False, held
    for args, said in (({"scenario": "", "as_of": DAY}, "not ''"), ({"task": "", "as_of": DAY}, "no task ''"),
                       ({"as_of": ""}, "as_of")):
        r = _call(s, "gate_verdict", args)["result"]
        assert r["isError"] is True and said in r["content"][0]["text"], (args, r)
    r = _call(s, "evidence_bundle", {"task": "", "as_of": DAY})["result"]
    assert r["isError"] is True and "no task ''" in r["content"][0]["text"], r
    src = (ROOT / "harness" / "mcp_server.py").read_text(encoding="utf-8")
    for coerced in ('args.get("task") or', 'args.get("walk") or', 'args.get("fail_on") or', 'args.get("baseline") or',
                    'params.get("arguments") or', "if scenario and scenario"):
        assert coerced not in src, coerced


def test_over_http_a_schema_violation_is_minus_32602_on_both_servers():
    """AC3: the same answer over Streamable HTTP, in the handshake era and the revision."""
    for sname, s in _servers().items():
        httpd = mcp_server.serve_http(s, "127.0.0.1", 0, None)
        httpd.RequestHandlerClass.log_message = lambda self, *a: None
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        port = httpd.server_address[1]
        name, args = ("register_impact", {"node": 5}) if sname == "knowgov" else ("start_run", {"scenario": 5, "mode": "deterministic"})
        prop = "node" if sname == "knowgov" else "scenario"
        try:
            for modern in (False, True):
                params = {"name": name, "arguments": args, **({"_meta": _meta()} if modern else {})}
                body = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": params}).encode()
                extra = (b"MCP-Protocol-Version: 2026-07-28\r\nMcp-Method: tools/call\r\nMcp-Name: " + name.encode() + b"\r\n") if modern else b""
                got, data = _send(port, _raw_post(port, "/mcp", body, extra=extra))
                assert b"-32602" in data and prop.encode() in data, (sname, modern, got, data[-300:])
        finally:
            httpd.shutdown()
            httpd.server_close()


def test_the_pages_run_body_refuses_a_key_outside_its_fields_naming_it():
    """AC4: as-of (for as_of), or any key outside RUN_FIELDS, is 400 naming it; nothing starts. The set is
    run_request's own and the demo README's."""
    import server
    assert server.RUN_FIELDS == ("scenario", "mode", "n", "row", "effort", "as_of", "by", "subject")
    for bad, key in (({"scenario": "S1", "mode": "deterministic", "as-of": "2027-01-01"}, "as-of"), ({"scenario": "S1", "x": 1}, "x")):
        try:
            server.run_request(bad)
        except ValueError as e:
            assert repr(key) in str(e), e
        else:
            raise AssertionError(f"{bad} accepted")
    assert server.run_request({k: "S1" for k in ("scenario", "mode")})["n"] == 1
    readme = (ROOT / "demo" / "README.md").read_text(encoding="utf-8")
    assert all(f"`{k}`" in readme.split("A run's body takes", 1)[1].split("\n\n", 1)[0] for k in server.RUN_FIELDS)
    with _page() as (httpd, calls, log):
        port = httpd.server_address[1]
        body = json.dumps({"scenario": "S1", "mode": "deterministic", "as-of": "2027-01-01"}).encode()
        got, data = _send(port, _raw_post(port, "/api/run", body))
        assert got == 400 and b"as-of" in data, (got, data[-200:])
        assert calls["start"] == 0


def test_the_changelog_rewords_m5():
    log = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").split("\n## ", 2)[1]
    contract = log.split("### Contract changes", 1)[1].split("### Changes", 1)[0]
    assert "task-0281" in contract and "M5" in contract and "outside a tool's input schema" in contract
