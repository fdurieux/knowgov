"""Task-0056: the gate and the three-valued answer behind a read-only MCP server. Standard library
only: the protocol, the tools and their annotations, the read-only view of the store, the bind and
token rules and the Origin check run here on a stub store. The same scenario through the server and
through gate_cli.py --no-load on a live store (rdflib in harness.yml, Neo4j in the stack job) is
tools/check_mcp_server.py's."""
from __future__ import annotations

import ast
import io
import json
import os
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness")]
import gate_cli  # noqa: E402
import mcp_server  # noqa: E402
from tasks import TASKS  # noqa: E402

PORT = ROOT / "harness" / "store.py"
DAY = "2026-11-04"   # the day the stub's gate reads as of (task-0075): the tests pin it, never the wall clock
SERVER = ROOT / "harness" / "mcp_server.py"


def _row(aid, key, value, status="verified", basis="extracted"):
    return {"id": aid, "value": value, "text": f"{key} is {value}", "basis": basis, "status": status,
            "artefact": "docs/pricing.md", "agent": "extractor", "fragments": [{"locator": "L3", "text": "...", "artefact": "docs/pricing.md"}],
            "verifications": [], "approvals": [], "gaps": []}


class Stub:
    """A store holding S1 with a verified value on every codegen key but one, which is absent."""
    name = "rdflib"

    def __init__(self, scenario="S1", writes=None):
        self.scenario, self.path, self.closed_with = scenario, "store.ttl", None
        keys = TASKS["codegen"]["keys"]
        self.rows = {k: [_row(f"x{i}", k, "42")] for i, k in enumerate(keys[1:])}
        self.rows["S-review|notified"] = [_row("xn", "S-review|notified", "NONE")]
        self.writes = writes if writes is not None else []

    def extraction_activities(self):
        return [f"act:extract:{self.scenario}:v1"] if self.scenario else []

    def key_evidence(self, key, live):
        return [r for r in self.rows.get(key, []) if r["status"] in live]

    def assertions_on_key(self, key, statuses):
        return [{k: r[k] for k in ("id", "value", "status", "basis")} for r in self.rows.get(key, []) if r["status"] in statuses]

    def declared_gaps_for_key(self, key):
        return []

    def conflict_gaps(self):
        return []

    def stale_on_keys(self, keys):
        return []

    def suspect_derived(self):
        return []

    def census(self):
        return {"nodes": 1}

    def wipe(self):
        self.writes.append("wipe")

    def close(self):
        self.closed_with = self.path


def _server(stub=None):
    stub = stub or Stub()
    return mcp_server.Server(mcp_server.Tools(opener=lambda: mcp_server.ReadOnlyStore(stub))), stub


class _Day:
    """KG_TODAY at DAY for the block, as it was after (task-0075; the runner sets KG_CLOCK=pinned)."""
    def __enter__(self):
        self.old = os.environ.get("KG_TODAY")
        os.environ["KG_TODAY"] = DAY

    def __exit__(self, *exc):
        if self.old is None:
            os.environ.pop("KG_TODAY", None)
        else:
            os.environ["KG_TODAY"] = self.old


def _call(server, name, args=None, id_=1):
    with _Day():
        return server.handle({"jsonrpc": "2.0", "id": id_, "method": "tools/call", "params": {"name": name, "arguments": args or {}}})


def _port_methods() -> set[str]:
    tree = ast.parse(PORT.read_text(encoding="utf-8"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Store")
    return {n.name for n in cls.body if isinstance(n, ast.FunctionDef) and not n.name.startswith("__")}


def test_initialize_negotiates_a_version_and_offers_tools_only():
    s, _ = _server()
    r = s.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}})["result"]
    assert r["protocolVersion"] == "2025-06-18" and r["serverInfo"]["name"] == "knowgov"
    assert set(r["capabilities"]) == {"tools"}
    r = s.handle({"jsonrpc": "2.0", "id": 2, "method": "initialize", "params": {"protocolVersion": "1999-01-01"}})["result"]
    assert r["protocolVersion"] == mcp_server.PROTOCOL_VERSIONS[0]
    assert s.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None
    assert s.handle({"jsonrpc": "2.0", "id": 3, "method": "ping"})["result"] == {}
    assert s.handle({"jsonrpc": "2.0", "id": 4, "method": "resources/list"})["error"]["code"] == -32601
    assert s.handle_text("{not json")["error"]["code"] == -32700
    assert s.handle({"id": 5, "method": "ping"})["error"]["code"] == -32600


def test_four_tools_every_one_marked_read_only():
    s, _ = _server()
    tools = s.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})["result"]["tools"]
    assert [t["name"] for t in tools] == ["store_status", "gate_verdict", "three_valued_answer", "evidence_bundle"]
    for t in tools:
        a = t["annotations"]
        assert a["readOnlyHint"] is True and a["destructiveHint"] is False and a["openWorldHint"] is False, t["name"]
        assert t["inputSchema"]["type"] == "object" and t["inputSchema"]["additionalProperties"] is False, t["name"]
        assert callable(getattr(mcp_server.Tools, t["name"]))
    assert _call(s, "load_scenario")["error"]["code"] == -32602


def test_the_store_view_lets_through_reads_of_the_port_and_nothing_else():
    port = _port_methods()
    assert mcp_server.READS <= port, sorted(mcp_server.READS - port)
    writes = []
    view = mcp_server.ReadOnlyStore(Stub(writes=writes))
    for name in sorted(port - mcp_server.READS):
        try:
            getattr(view, name)
        except PermissionError:
            continue
        raise AssertionError(f"{name} reached the store through the read-only view")
    assert writes == []
    # nothing in the server names a store write, nor opens a store other than through the view
    src = SERVER.read_text(encoding="utf-8")
    for name in port - mcp_server.READS - {"close", "name"}:
        assert f".{name}(" not in src, name


def test_an_rdflib_file_is_read_and_never_written_back():
    stub = Stub()
    mcp_server.ReadOnlyStore(stub).release()
    assert stub.closed_with is None, "close() with a path would serialise the graph over the file"


def test_gate_verdict_is_the_commands_report_for_the_same_store():
    s, stub = _server()
    got = _call(s, "gate_verdict", {"scenario": "S1"})["result"]
    assert got["isError"] is False
    spec = TASKS["codegen"]
    with _Day():
        want = gate_cli.evaluate(stub, subject=got["structuredContent"]["subject"], scenario="S1", task="codegen", spec=spec,
                                 threshold="blocker", baseline=None, loaded=False, version="v1")
    assert want["as_of"] == DAY
    assert got["structuredContent"] == want
    assert json.loads(got["content"][0]["text"]) == want
    assert want["verdict"] == "BLOCKED" and want["exit_code"] == 1   # the first codegen key is absent
    assert [f["key"] for f in want["findings"] if f["severity"] == "blocker"] == [spec["keys"][0]]


def test_a_key_set_of_the_agents_own_resolves_through_the_same_gate():
    s, _ = _server()
    keys = TASKS["codegen"]["keys"][1:3]
    rep = _call(s, "gate_verdict", {"keys": keys})["result"]["structuredContent"]
    assert rep["task"] == "keys" and rep["keys"]["total"] == 2 and rep["verdict"] == "PROCEED" and rep["exit_code"] == 0
    rep = _call(s, "gate_verdict", {"keys": [TASKS["codegen"]["keys"][0]]})["result"]["structuredContent"]
    assert rep["verdict"] == "BLOCKED"
    for bad in ({"keys": []}, {"keys": [""]}, {"keys": "P2|surcharge"}, {"task": "nope"}, {"fail_on": "panic"},
                {"baseline": "/etc/passwd"}, {"keys": keys, "baseline": "record"}):
        r = _call(s, "gate_verdict", bad)["result"]
        assert r["isError"] is True, bad


def test_the_scenario_must_be_the_one_the_store_holds_and_nothing_is_ever_loaded():
    s, stub = _server(Stub(scenario="S1"))
    r = _call(s, "gate_verdict", {"scenario": "S2"})["result"]
    assert r["isError"] and "holds S1" in r["content"][0]["text"]
    s, stub = _server(Stub(scenario=None))
    r = _call(s, "gate_verdict", {})["result"]
    assert r["isError"] and "no scenario" in r["content"][0]["text"]
    assert _call(s, "store_status")["result"]["structuredContent"]["scenario"] is None
    assert stub.writes == []


def test_the_three_valued_answer_carries_each_statements_provenance():
    s, _ = _server()
    r = _call(s, "three_valued_answer", {"key": "S-review|notified"})["result"]["structuredContent"]
    assert r["answer"] == "documented_absent"
    (st,) = r["statements"]
    assert st["artefact"] == "docs/pricing.md" and st["fragments"] and st["agent"] == "extractor" and "verifications" in st
    r = _call(s, "three_valued_answer", {"key": TASKS["codegen"]["keys"][1]})["result"]["structuredContent"]
    assert r["answer"] == "asserted" and r["statements"][0]["value"] == "42"
    r = _call(s, "three_valued_answer", {"key": "QuoteAPI|never_said"})["result"]["structuredContent"]
    assert r["answer"] == "unknown" and r["statements"] == [] and "not a documented absence" in r["why"]
    assert _call(s, "three_valued_answer", {})["result"]["isError"]


def test_the_evidence_bundle_is_the_text_the_governed_arm_reads():
    """Task-0080: render_bundle over the gate's result, with the policy and the task's verbatim
    documents from the scenario's kit, as harness/run.py's arm_runs builds it."""
    import arms
    from gate import render_bundle, resolve_spec
    from kitio import kit_for, verbatim_documents
    from subject import SUBJECT
    first = SUBJECT.order[0]   # a scenario of whichever subject runs the suite: the kit is read
    s, stub = _server(Stub(scenario=first))
    got = _call(s, "evidence_bundle", {"scenario": first})["result"]
    assert got["isError"] is False
    b = got["structuredContent"]
    res = resolve_spec(stub, "codegen", TASKS["codegen"], "record")
    verbatim = verbatim_documents(kit_for(first, 1), "task_codegen")
    assert b["bundle"] == render_bundle(res, arms.policy(), verbatim)
    assert b["verdict"] == res["verdict"] == "BLOCKED" and b["as_of"] == res["as_of"] and b["version"] == "v1"
    assert b["verbatim"] == sorted(verbatim)
    assert b["assertion_ids"] == sorted({a["id"] for v in res["keys"].values() for a in v["assertions"]})
    keys = TASKS["codegen"]["keys"][1:3]
    sub = _call(s, "evidence_bundle", {"keys": keys, "verbatim": False})["result"]["structuredContent"]
    assert sub["task"] == "keys" and sub["verbatim"] == [] and sub["verdict"] == "PROCEED"
    assert sub["bundle"] == render_bundle(resolve_spec(stub, "keys", dict(TASKS["codegen"], keys=keys), "record"), arms.policy())
    for bad in ({"keys": []}, {"task": "nope"}, {"verbatim": "yes"}, {"as_of": "soon"}, {"scenario": "not-held"}):
        assert _call(s, "evidence_bundle", bad)["result"]["isError"] is True, bad
    assert stub.writes == []


def test_stdio_is_one_json_message_a_line():
    s, _ = _server()
    inp = io.StringIO("\n".join(json.dumps(m) for m in [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25"}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "store_status", "arguments": {}}}]) + "\n")
    out = io.StringIO()
    mcp_server.serve_stdio(s, inp, out)
    lines = out.getvalue().splitlines()
    assert [json.loads(x)["id"] for x in lines] == [1, 2]
    assert json.loads(lines[1])["result"]["structuredContent"]["scenario"] == "S1"


def test_it_binds_localhost_unless_told_and_a_wider_bind_needs_a_token():
    assert mcp_server.DEFAULT_HOST == "127.0.0.1"
    for host in ("127.0.0.1", "localhost", "::1", "[::1]"):
        assert mcp_server.bind_check(host, None) is None, host
    for host in ("0.0.0.0", "192.168.1.10", "example.org"):
        assert mcp_server.bind_check(host, None), host
        assert mcp_server.bind_check(host, "s3cret") is None, host
    assert mcp_server.main(["--http", "--host", "0.0.0.0"]) == 2
    assert mcp_server.origin_allowed(None) and mcp_server.origin_allowed("http://localhost:6274")
    assert not mcp_server.origin_allowed("https://evil.example")


def _post(url, body, headers=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, (json.loads(r.read() or b"null"))
    except urllib.error.HTTPError as e:
        return e.code, None


def _serve(token=None):
    s, _ = _server()
    httpd = mcp_server.serve_http(s, "127.0.0.1", 0, token)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}"


def test_http_answers_on_mcp_refuses_a_foreign_origin_and_pushes_nothing():
    httpd, base = _serve()
    day = _Day()
    day.__enter__()
    try:
        init = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25"}}
        code, body = _post(base + "/mcp", init)
        assert code == 200 and body["result"]["serverInfo"]["name"] == "knowgov"
        assert _post(base + "/mcp", {"jsonrpc": "2.0", "method": "notifications/initialized"})[0] == 202
        code, body = _post(base + "/mcp", {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "gate_verdict", "arguments": {}}})
        assert code == 200 and body["result"]["structuredContent"]["verdict"] == "BLOCKED"
        assert _post(base + "/mcp", init, {"Origin": "https://evil.example"})[0] == 403
        assert _post(base + "/other", init)[0] == 404
        try:
            urllib.request.urlopen(base + "/mcp", timeout=10)
            raise AssertionError("GET must not open a stream")
        except urllib.error.HTTPError as e:
            assert e.code == 405
    finally:
        httpd.shutdown()
        httpd.server_close()
        day.__exit__()


def test_http_with_a_token_refuses_a_request_without_it():
    httpd, base = _serve(token="s3cret")
    try:
        ping = {"jsonrpc": "2.0", "id": 1, "method": "ping"}
        assert _post(base + "/mcp", ping)[0] == 401
        assert _post(base + "/mcp", ping, {"Authorization": "Bearer wrong"})[0] == 401
        assert _post(base + "/mcp", ping, {"Authorization": "Bearer s3cret"}) == (200, {"jsonrpc": "2.0", "id": 1, "result": {}})
    finally:
        httpd.shutdown()
        httpd.server_close()


# Task-0079: the stateless revision (2026-07-28) beside the handshake.

MODERN = "2026-07-28"


def _meta(version=MODERN, caps=True):
    m = {mcp_server.META_VERSION: version, "io.modelcontextprotocol/clientInfo": {"name": "t", "version": "1"}}
    if caps:
        m[mcp_server.META_CAPABILITIES] = {}
    return m


def _modern(method, id_=1, version=MODERN, caps=True, **params):
    return {"jsonrpc": "2.0", "id": id_, "method": method, "params": {**params, "_meta": _meta(version, caps)}}


def test_server_discover_answers_per_the_revision_without_a_handshake():
    s, _ = _server()
    r = s.handle(_modern("server/discover"))["result"]
    assert r["resultType"] == "complete" and r["supportedVersions"][0] == MODERN
    assert set(mcp_server.PROTOCOL_VERSIONS) <= set(r["supportedVersions"]), "the handshake era is still served"
    assert r["capabilities"] == {"tools": {"listChanged": False}} and r["instructions"] == mcp_server.INSTRUCTIONS
    assert r["_meta"][mcp_server.META_SERVER]["name"] == "knowgov"
    assert isinstance(r["ttlMs"], int) and r["ttlMs"] >= 0 and r["cacheScope"] in ("public", "private")
    tl = s.handle(_modern("tools/list", 2))["result"]
    assert [t["name"] for t in tl["tools"]][0] == "store_status" and tl["resultType"] == "complete" and "ttlMs" in tl
    with _Day():
        call = s.handle(_modern("tools/call", 3, name="store_status", arguments={}))["result"]
    assert call["structuredContent"]["scenario"] == "S1" and call["resultType"] == "complete" and "ttlMs" not in call
    assert call["_meta"][mcp_server.META_SERVER]["name"] == "knowgov"


def test_a_modern_request_is_refused_on_its_version_or_its_missing_meta():
    s, _ = _server()
    e = s.handle(_modern("server/discover", version="1900-01-01"))["error"]
    assert e["code"] == -32022 and e["data"] == {"supported": mcp_server.SUPPORTED_VERSIONS, "requested": "1900-01-01"}
    assert s.handle(_modern("tools/list", caps=False))["error"]["code"] == -32602
    assert s.handle(_modern("ping"))["error"]["code"] == -32601, "ping is not a method of the stateless era"
    bare = {"jsonrpc": "2.0", "id": 9, "method": "server/discover"}
    assert s.handle(bare)["error"]["code"] == -32602   # no _meta: malformed, and a dual-era client falls back


def test_the_handshake_is_unchanged_for_an_older_client():
    s, _ = _server()
    r = s.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25"}})["result"]
    assert r["protocolVersion"] == "2025-11-25" and "resultType" not in r
    tl = s.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]
    assert "resultType" not in tl and "ttlMs" not in tl and "_meta" not in tl


def _post_raw(url, body, headers):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream", **headers})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"null")


def test_http_serves_the_revision_and_checks_its_headers_against_the_body():
    httpd, base = _serve()
    url = base + "/mcp"
    hd = {"MCP-Protocol-Version": MODERN, "Mcp-Method": "server/discover"}
    day = _Day()
    day.__enter__()
    try:
        code, body = _post_raw(url, _modern("server/discover"), hd)
        assert code == 200 and body["result"]["supportedVersions"][0] == MODERN
        call = _modern("tools/call", 2, name="gate_verdict", arguments={})
        code, body = _post_raw(url, call, {"MCP-Protocol-Version": MODERN, "Mcp-Method": "tools/call", "Mcp-Name": "gate_verdict"})
        assert code == 200 and body["result"]["structuredContent"]["verdict"] == "BLOCKED"
        import base64
        enc = "=?base64?" + base64.b64encode(b"gate_verdict").decode() + "?="
        assert _post_raw(url, call, {"MCP-Protocol-Version": MODERN, "Mcp-Method": "tools/call", "Mcp-Name": enc})[0] == 200
        for bad in ({"Mcp-Method": "server/discover"}, {"MCP-Protocol-Version": "2025-11-25", "Mcp-Method": "server/discover"},
                    {"MCP-Protocol-Version": MODERN, "Mcp-Method": "tools/list"}):
            code, body = _post_raw(url, _modern("server/discover"), bad)
            assert code == 400 and body["error"]["code"] == -32020, bad
        code, body = _post_raw(url, call, {"MCP-Protocol-Version": MODERN, "Mcp-Method": "tools/call", "Mcp-Name": "three_valued_answer"})
        assert code == 400 and body["error"]["code"] == -32020
        old = _modern("server/discover", version="1900-01-01")
        code, body = _post_raw(url, old, {"MCP-Protocol-Version": "1900-01-01", "Mcp-Method": "server/discover"})
        assert code == 400 and body["error"]["code"] == -32022
        code, body = _post_raw(url, _modern("ping"), {"MCP-Protocol-Version": MODERN, "Mcp-Method": "ping"})
        assert code == 404 and body["error"]["code"] == -32601
        # the handshake era on the same endpoint, as before: errors stay in a 200
        code, body = _post_raw(url, {"jsonrpc": "2.0", "id": 5, "method": "resources/list"}, {})
        assert code == 200 and body["error"]["code"] == -32601
    finally:
        day.__exit__()
        httpd.shutdown()
        httpd.server_close()


def test_a_tool_that_raises_is_an_error_result_not_a_dropped_connection():
    s, _ = _server()
    s.tools.store_status = lambda args: (_ for _ in ()).throw(RuntimeError("boom"))
    r = s.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "store_status", "arguments": {}}})["result"]
    assert r["isError"] is True and "RuntimeError: boom" in r["content"][0]["text"]
