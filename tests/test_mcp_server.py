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

from tests._skip import skip  # noqa: E402

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


FIRST = object()   # the Stub's default: the first scenario of whichever subject runs the suite


class Stub:
    """A store holding the subject's first scenario with a verified value on every codegen key but one, which is absent."""
    name = "rdflib"

    def __init__(self, scenario=FIRST, writes=None):
        from subject import SUBJECT
        scenario = SUBJECT.order[0] if scenario is FIRST else scenario   # the server's subject's first; None holds nothing
        self.scenario, self.path, self.closed_with = scenario, "store.ttl", None
        keys = TASKS["codegen"]["keys"]
        self.rows = {k: [_row(f"x{i}", k, "42")] for i, k in enumerate(keys[1:])}
        self.rows["S-review|notified"] = [_row("xn", "S-review|notified", "NONE")]
        self.writes = writes if writes is not None else []

    def extraction_activities(self):
        return [f"act:extract:{self.scenario}:v1"] if self.scenario else []

    def held(self):
        """As a store records it since task-0195: the load's own subject, the one declaring its scenario."""
        if not self.scenario:
            return None
        from subject import SUBJECT
        import subject_ids
        owners = [SUBJECT.id] if self.scenario in SUBJECT.scenarios else subject_ids.declaring(self.scenario)
        return {"subject": owners[0] if owners else "elsewhere", "scenario": self.scenario, "version": "v1",
                "versions": {}, "loaded_at": "2026-11-04T19:45:00+00:00"}

    def extraction_times(self):
        return [{"id": a, "at": "2026-11-04T19:45:00+00:00"} for a in self.extraction_activities()]

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

    def derived_outputs(self):   # task-0327: register_impact reads the statements' keys
        return []

    def census(self):
        return {"nodes": 1}

    def version_digests(self):   # task-0307: the documents' Versions, none in this stand-in
        return []

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


def _refused(server, name, args) -> bool:
    """The call is refused as task-0281 has it: -32602 naming a property when ``args`` break the tool's
    inputSchema (``mcp_server.argument_refusal`` says which), else the tool's own error result. Never both,
    never an answer."""
    tool = next(t for t in server.table if t["name"] == name)
    r = _call(server, name, args)
    if mcp_server.argument_refusal(name, args, tool["inputSchema"]):
        return r.get("error", {}).get("code") == -32602
    return r.get("result", {}).get("isError") is True


def _as_result(r: dict) -> dict:
    """A tools/call response as its result, a refusal before dispatch (-32602, task-0281) read as an error
    result with its message as the text and the code kept as ``protocol_error``."""
    if "error" in r:
        assert r["error"]["code"] == -32602, r
        return {"isError": True, "protocol_error": -32602, "content": [{"type": "text", "text": r["error"]["message"]}]}
    return r["result"]


def _port_methods() -> set[str]:
    tree = ast.parse(PORT.read_text(encoding="utf-8"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Store")
    return {n.name for n in cls.body if isinstance(n, ast.FunctionDef) and not n.name.startswith("__")}


def test_initialize_negotiates_a_version_and_offers_tools_and_prompts_only():
    s, _ = _server()
    r = s.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}})["result"]
    assert r["protocolVersion"] == "2025-06-18" and r["serverInfo"]["name"] == "knowgov"
    assert set(r["capabilities"]) == {"tools", "prompts"}   # prompts: task-0148; never resources
    r = s.handle({"jsonrpc": "2.0", "id": 2, "method": "initialize", "params": {"protocolVersion": "1999-01-01"}})["result"]
    assert r["protocolVersion"] == mcp_server.PROTOCOL_VERSIONS[0]
    assert s.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None
    assert s.handle({"jsonrpc": "2.0", "id": 3, "method": "ping"})["result"] == {}
    assert s.handle({"jsonrpc": "2.0", "id": 4, "method": "resources/list"})["error"]["code"] == -32601
    assert s.handle_text("{not json")["error"]["code"] == -32700
    assert s.handle({"id": 5, "method": "ping"})["error"]["code"] == -32600


def test_every_tool_listed_and_marked_read_only():
    s, _ = _server()
    tools = s.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})["result"]["tools"]
    assert [t["name"] for t in tools] == ["store_status", "gate_verdict", "three_valued_answer", "evidence_bundle", "register_impact",
                                          "proposal_impact", "scenario_runs", "scenario_result", "register_nodes",
                                          "key_nodes", "code_path", "document_links", "subject_check", "held_keys", "derived_outputs", "document_statements",
                                          "list_subjects"]
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


def test_the_server_opens_the_ports_read_handle_which_never_publishes():
    """task-0141.02: the server's store is a read handle (open_store(access="read")) under its own
    narrower view, so releasing it publishes nothing whichever adapter it is; the old workaround,
    clearing an rdflib store's path before close, is gone (tests/test_store_persistence.py, ST-02)."""
    import store
    seen = {}

    def opener(**kw):
        seen.update(kw)
        return Stub()
    view = mcp_server.open_read_only(opener)
    assert seen["access"] == "read" and isinstance(view._inner, store.ReadOnly), seen
    try:
        view._inner.commit()
    except store.StoreReadOnly:
        pass
    else:
        raise AssertionError("a read handle published")
    view.release()
    assert ".path = None" not in SERVER.read_text(encoding="utf-8")


def test_gate_verdict_is_the_commands_report_for_the_same_store():
    s, stub = _server()
    got = _call(s, "gate_verdict", {"scenario": stub.scenario})["result"]
    assert got["isError"] is False
    spec = TASKS["codegen"]
    with _Day():
        want = gate_cli.evaluate(stub, subject=got["structuredContent"]["subject"], scenario=stub.scenario, task="codegen", spec=spec,
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
        assert _refused(s, "gate_verdict", bad), bad


def test_the_scenario_must_be_the_one_the_store_holds_and_nothing_is_ever_loaded():
    from subject import SUBJECT
    first, second = SUBJECT.order[:2]
    s, stub = _server(Stub(scenario=first))
    r = _call(s, "gate_verdict", {"scenario": second})["result"]
    assert r["isError"] and f"holds {first}" in r["content"][0]["text"]
    s, stub = _server(Stub(scenario=None))
    r = _call(s, "gate_verdict", {})["result"]
    assert r["isError"] and "no scenario" in r["content"][0]["text"]
    assert _call(s, "store_status")["result"]["structuredContent"]["scenario"] is None
    assert stub.writes == []


def _foreign_scenario() -> str:
    """A scenario of the other public subject: J-F's C under CargoQuote, CargoQuote's S1 under J-F."""
    from subject import SUBJECT
    foreign = "C" if SUBJECT.id == "cargo_quote" else "S1"
    assert foreign not in SUBJECT.scenarios
    return foreign


def test_a_scenario_of_another_subject_reads_as_none_held_and_every_scenario_tool_refuses_it():
    """task-0126 (doc-0016 F1): one store serves every subject; the server reads its own subject's
    scenarios only, with or without a scenario argument, and never answers on another's graph."""
    from subject import SUBJECT
    foreign = _foreign_scenario()
    s, stub = _server(Stub(scenario=foreign))
    st = _call(s, "store_status")["result"]
    assert not st["isError"]
    assert st["structuredContent"]["scenario"] is None
    assert st["structuredContent"]["held_by_other_subject"] == foreign
    key = TASKS["codegen"]["keys"][-1]
    for name, args in (("gate_verdict", {}), ("three_valued_answer", {"key": key}), ("evidence_bundle", {}),
                       ("register_impact", {"node": "CAP-0001"}),
                       ("proposal_impact", {"proposal": json.loads((ROOT / "tools" / "fixtures" / "proposal_contract_quote.json").read_text(encoding="utf-8"))})):
        for extra in ({}, {"scenario": foreign}, {"scenario": SUBJECT.order[0]}):
            r = _call(s, name, {**args, **extra})["result"]
            assert r["isError"] is True, (name, extra, r)
            text = r["content"][0]["text"]
            assert foreign in text and SUBJECT.id in text and "another subject" in text, (name, extra, text)
    assert stub.writes == []
    own = _call(_server()[0], "store_status")["result"]["structuredContent"]
    assert own["scenario"] == SUBJECT.order[0] and own["held_by_other_subject"] is None


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
    assert _refused(s, "three_valued_answer", {})


def test_the_evidence_bundle_is_the_text_the_governed_arm_reads():
    """Task-0080: render_bundle over the gate's result, with the policy and the task's verbatim
    documents from the scenario's kit, as harness/run.py's arm_runs builds it."""
    import arms
    from gate import render_bundle, resolve_spec
    from kitio import kit_for, verbatim_documents
    from subject import SUBJECT
    first = SUBJECT.order[0]   # a scenario of whichever subject runs the suite: the kit is read
    s, stub = _server(Stub(scenario=first))
    got = _call(s, "evidence_bundle", {"scenario": first, "as_of": "record"})["result"]   # the arms' date, named
    assert got["isError"] is False
    b = got["structuredContent"]
    res = resolve_spec(stub, "codegen", TASKS["codegen"], "record")
    verbatim = verbatim_documents(kit_for(first, 1), "task_codegen")
    assert b["bundle"] == render_bundle(res, arms.policy(), verbatim)
    assert b["verdict"] == res["verdict"] == "BLOCKED" and b["as_of"] == res["as_of"] and b["version"] == "v1"
    assert b["verbatim"] == sorted(verbatim)
    assert b["assertion_ids"] == sorted({a["id"] for v in res["keys"].values() for a in v["assertions"]})
    keys = TASKS["codegen"]["keys"][1:3]
    sub = _call(s, "evidence_bundle", {"keys": keys, "verbatim": False, "as_of": "record"})["result"]["structuredContent"]
    assert sub["task"] == "keys" and sub["verbatim"] == [] and sub["verdict"] == "PROCEED"
    assert sub["bundle"] == render_bundle(resolve_spec(stub, "keys", dict(TASKS["codegen"], keys=keys), "record"), arms.policy())
    for bad in ({"keys": []}, {"task": "nope"}, {"verbatim": "yes"}, {"as_of": "soon"}, {"as_of": 20261104}, {"scenario": "not-held"}):
        assert _refused(s, "evidence_bundle", bad), bad
    assert stub.writes == []


def test_one_session_reads_one_as_of():
    """Task-0100: with no argument, one session's verdict and bundle carry the same date, the one
    store_status reports, read once: a later KG_TODAY (midnight) does not move it. KG_AS_OF names
    another; an argument still wins."""
    import cadence
    from subject import SUBJECT
    first = SUBJECT.order[0]
    s, _ = _server(Stub(scenario=first))
    status = _call(s, "store_status")["result"]["structuredContent"]
    assert (status["as_of"], status["as_of_from"]) == (DAY, "today")
    verdict = _call(s, "gate_verdict", {})["result"]["structuredContent"]
    old = os.environ.get("KG_TODAY")
    os.environ["KG_TODAY"] = "2026-11-05"   # the session runs past midnight
    try:
        bundle = s.tools.evidence_bundle({"verbatim": False})
        again = s.tools.gate_verdict({"as_of": "today"})
    finally:
        os.environ["KG_TODAY"] = old if old is not None else DAY
        if old is None:
            os.environ.pop("KG_TODAY")
    assert verdict["as_of"] == bundle["as_of"] == again["as_of"] == DAY
    rec = cadence.as_of("record").isoformat()
    assert _call(s, "evidence_bundle", {"as_of": "record", "verbatim": False})["result"]["structuredContent"]["as_of"] == rec
    assert _call(s, "gate_verdict", {"as_of": "2027-01-02"})["result"]["structuredContent"]["as_of"] == "2027-01-02"
    old = os.environ.get("KG_AS_OF")
    os.environ["KG_AS_OF"] = "record"
    try:
        s, _ = _server(Stub(scenario=first))
    finally:
        os.environ.pop("KG_AS_OF")
        if old is not None:
            os.environ["KG_AS_OF"] = old
    assert _call(s, "store_status")["result"]["structuredContent"]["as_of"] == rec
    assert _call(s, "gate_verdict", {})["result"]["structuredContent"]["as_of"] == rec
    assert _call(s, "evidence_bundle", {"verbatim": False})["result"]["structuredContent"]["as_of"] == rec
    s = mcp_server.Server(mcp_server.Tools(opener=lambda: mcp_server.ReadOnlyStore(Stub()), as_of="soon"))
    assert _call(s, "gate_verdict", {})["result"]["isError"] is True
    assert mcp_server.main(["--as-of", "soon"]) == 2   # refused at start, before any transport opens


def test_stdio_is_one_json_message_a_line():
    s, _ = _server()
    inp = io.StringIO("\n".join(json.dumps(m) for m in [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25"}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "store_status", "arguments": {}}}]) + "\n")
    out = io.StringIO()
    with _Day():   # store_status reports the session's date (task-0100)
        mcp_server.serve_stdio(s, inp, out)
    lines = out.getvalue().splitlines()
    assert [json.loads(x)["id"] for x in lines] == [1, 2]
    assert json.loads(lines[1])["result"]["structuredContent"]["scenario"] == Stub().scenario


def test_it_binds_localhost_unless_told_and_a_wider_bind_needs_a_token():
    assert mcp_server.DEFAULT_HOST == "127.0.0.1"
    for host in ("127.0.0.1", "localhost", "::1", "[::1]"):
        assert mcp_server.bind_check(host, None) is None, host
    for host in ("0.0.0.0", "192.168.1.10", "example.org"):
        assert mcp_server.bind_check(host, None), host
        assert mcp_server.bind_check(host, "s3cret") is None, host
    assert mcp_server.main(["--http", "--host", "0.0.0.0"]) == 2
    # task-0141.03: the origins are the server's own, never every loopback port; the MCP Inspector's is configured
    import http_boundary as hb
    own = {"Host": "127.0.0.1:8765"}
    assert hb.check(mcp_server.http_policy("127.0.0.1", 8765), own) is None
    assert hb.check(mcp_server.http_policy("127.0.0.1", 8765), {**own, "Origin": "http://localhost:6274"})[0] == 403
    assert hb.check(mcp_server.http_policy("127.0.0.1", 8765), {**own, "Origin": "https://evil.example"})[0] == 403
    keep = os.environ.get("KG_MCP_ORIGINS")
    os.environ["KG_MCP_ORIGINS"] = "http://localhost:6274"
    try:
        assert hb.check(mcp_server.http_policy("127.0.0.1", 8765), {**own, "Origin": "http://localhost:6274"}) is None
    finally:
        os.environ.pop("KG_MCP_ORIGINS") if keep is None else os.environ.__setitem__("KG_MCP_ORIGINS", keep)


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
    assert r["capabilities"] == {"tools": {"listChanged": False}, "prompts": {"listChanged": False}} and r["instructions"] == mcp_server.INSTRUCTIONS
    assert r["_meta"][mcp_server.META_SERVER]["name"] == "knowgov"
    assert isinstance(r["ttlMs"], int) and r["ttlMs"] >= 0 and r["cacheScope"] in ("public", "private")
    tl = s.handle(_modern("tools/list", 2))["result"]
    assert [t["name"] for t in tl["tools"]][0] == "store_status" and tl["resultType"] == "complete" and "ttlMs" in tl
    with _Day():
        call = s.handle(_modern("tools/call", 3, name="store_status", arguments={}))["result"]
    assert call["structuredContent"]["scenario"] == Stub().scenario and call["resultType"] == "complete" and "ttlMs" not in call
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


# ---- register_impact (task-0111): the register's walk, the map rows it lands on, the gate's levels

def _register_view():
    sys.path.insert(0, str(ROOT / "demo" / "app"))
    import register_view
    return register_view


def test_register_impact_walks_as_the_page_does_for_every_node():
    """Edges, what is reached and each reached node's owning unit equal register_view.impact's, for
    every node of the vendored register, on the subject the runner holds; no store needed."""
    import register_impact as ri
    rv = _register_view()
    s = mcp_server.Server(mcp_server.Tools(opener=lambda: (_ for _ in ()).throw(OSError("no store here"))))
    reg = ri.load_tools()["register"].load_register(ri.register_root())
    assert len(reg["nodes"]) > 40
    for nid in sorted(reg["nodes"]):
        page = rv.impact(nid)
        r = _call(s, "register_impact", {"node": nid})["result"]
        assert r["isError"] is False, (nid, r["content"][0]["text"])
        got = r["structuredContent"]
        assert got["edges"] == page["edges"], nid
        ids = sorted(x["id"] for xs in got["reached"].values() for x in xs)
        assert ids == page["reached"]["all"], nid
        assert all(x["id"].startswith(p + "-") for p, xs in got["reached"].items() for x in xs), nid
        assert {x["id"]: x["owning_unit"] for xs in got["reached"].values() for x in xs} == {x: page["owners"][x] for x in ids}, nid
        assert got["node"]["id"] == nid and got["node"]["owning_unit"] == page["owners"][nid]
        assert got["scenario"] is None and got["gate"] is None and "store_unavailable" in got
        assert all(e["live"] in (True, False) for e in got["edges"])
        assert all(k["via"] and k["via"][0] in [nid] + ids for k in got["keys"]), nid


def test_register_impact_lists_a_domains_children_without_walking_them():
    s, _ = _server()
    got = _call(s, "register_impact", {"node": "CAP-0001"})["result"]["structuredContent"]
    assert got["edges"] == [] and got["reached"] == {}
    assert [c["id"] for c in got["children"]] == ["CAP-0002", "CAP-0003", "CAP-0004", "CAP-0005"]
    assert all(c["walked"] is False and c["state"] for c in got["children"])
    assert got["node"]["kind"] == "capability_domain" and got["node"]["parent"] is None
    assert got["register"]["tag"].startswith("v") and len(got["register"]["commit"]) == 40


def test_register_impact_refuses_an_unknown_or_malformed_id():
    s, _ = _server()
    for bad in ({"node": "CAP-9999"}, {"node": "cap-0001"}, {"node": "CAP-01"}, {"node": 7}, {},
                {"node": "CAP-0002", "walk": "ancestors"}):
        assert _refused(s, "register_impact", bad), bad
    assert _call(s, "register_impact", {"node": "CAP-0002", "scenario": "S9"})["result"]["isError"] is True


def test_register_impact_owns_the_finding_kinds_gate_cli_owns():
    """task-0260, doc-0032 group 3 CB1: one definition. register_impact lists, for each landed key, the findings of
    the kinds gate_verdict names the key's owner and route on (key, intended, stale, lapsed and act), so an act
    finding on a key whose ruling no longer binds shows on both; tools/check_owned_findings.py runs it on a store.
    The register-impact schema admits every one of them, and the act object."""
    import register_impact as ri
    import schema_check
    assert ri.OWNED is gate_cli.OWNED and set(ri.OWNED) >= {"key", "intended", "stale", "lapsed", "act"}
    finding = schema_check.load("register-impact")["$defs"]["finding"]
    assert set(ri.OWNED) <= set(finding["properties"]["kind"]["enum"]) and "act" in finding["properties"]
    gate_finding = schema_check.load("gate-report")["$defs"]["finding"]
    assert finding["properties"]["act"] == gate_finding["properties"]["act"], "the act object as the gate report has it"


def test_register_impact_reads_levels_as_gate_verdict_and_writes_nothing():
    """With a scenario held, the landed keys carry the levels gate_verdict gives that key set on the
    same as_of; the store sees reads only."""
    from subject import SUBJECT
    rows = SUBJECT.register_map().get("row") or []
    if not rows:
        skip("register-rows", "the subject's register_map.toml has no rows")
    writes = []
    s, _ = _server(Stub(writes=writes))
    start = rows[0]["nodes"][0]
    got = _call(s, "register_impact", {"node": start, "as_of": DAY})["result"]["structuredContent"]
    assert got["scenario"] == Stub().scenario and got["as_of"] == DAY and got["keys"]
    assert rows[0]["key"] in [k["key"] for k in got["keys"]]
    keys = [k["key"] for k in got["keys"]]
    want = _call(s, "gate_verdict", {"keys": keys, "as_of": DAY})["result"]["structuredContent"]
    assert {k["key"]: k["level"] for k in got["keys"]} == want["levels"]
    assert got["gate"]["verdict"] == want["verdict"] and got["gate"]["exit_code"] == want["exit_code"]
    for k in got["keys"]:
        assert k["findings"] == [f for f in want["findings"] if f["kind"] in gate_cli.OWNED and f["key"] == k["key"]]
        assert k["stale"] == [] and k["suspect"] == [] and k["via"]
    assert writes == []
    held_none = _call(_server(Stub(scenario=None))[0], "register_impact", {"node": start})["result"]["structuredContent"]
    assert held_none["scenario"] is None and all("level" not in k for k in held_none["keys"])



# ---- register_impact with children (task-0118): the register's decision 0014 descent, off by default

# per subject: (start, walk) -> how many register-map keys land with children, of them how many flagged
# withdrawn (task-0120: a row naming only a withdrawn descendant); none land without
CHILDREN_LANDS = {"cargo_quote": {("CAP-0001", "dependants"): (32, 1), ("CAP-0001", "realisers"): (36, 0)},
                  "jef_data_load": {("CAP-0006", "dependants"): (30, 0), ("CAP-0006", "realisers"): (80, 0),
                                    ("ENT-0006", "dependants"): (154, 0)}}


def test_register_impact_children_off_by_default_and_equal_to_the_registers_walk_on_every_node():
    """children false (or absent) is task-0111's answer; children true is impact.walk_children's edges and
    reached set, every descendant listed with its state, walked when approved, withdrawn otherwise."""
    import register_impact as ri
    s = mcp_server.Server(mcp_server.Tools(opener=lambda: (_ for _ in ()).throw(OSError("no store here"))))
    T = ri.load_tools()
    reg = T["register"].load_register(ri.register_root())
    with_desc = 0
    for nid in sorted(reg["nodes"]):
        for which in ("dependants", "realisers"):
            plain = _call(s, "register_impact", {"node": nid, "walk": which})["result"]["structuredContent"]
            off = _call(s, "register_impact", {"node": nid, "walk": which, "children": False})["result"]["structuredContent"]
            on = _call(s, "register_impact", {"node": nid, "walk": which, "children": True})["result"]["structuredContent"]
            assert plain == off and plain["children_walked"] is False and on["children_walked"] is True, (nid, which)
            assert all(c["walked"] is False and "not_followed" not in c for c in plain["children"])
            want = T["impact"].walk_children(reg, nid, T["impact"].WALKS[which])
            assert on["edges"] == want["edges"], (nid, which)
            assert sorted(x["id"] for xs in on["reached"].values() for x in xs) == sorted(want["reached"]), (nid, which)
            assert [(c["id"], c["state"], c["walked"], c["not_followed"]) for c in on["children"]] == \
                [(d["id"], d["state"], d["live"], not d["live"]) for d in want["descendants"]], (nid, which)
            assert all(c["walked"] == (c["state"] == "approved") and reg["nodes"][c["parent"]] for c in on["children"])
            assert [c["id"] for c in on["children"] if c["parent"] == nid] == [c["id"] for c in plain["children"]]
            if not on["children"]:   # the same walk; the register's walk_children leaves the start out of what is reached
                # where a cycle leads back to it (thirteen nodes on the dependants walk), as the plain walk does not
                assert on["edges"] == plain["edges"], (nid, which)
                assert sorted(x["id"] for xs in on["reached"].values() for x in xs) == \
                    sorted(x["id"] for xs in plain["reached"].values() for x in xs if x["id"] != nid), (nid, which)
            with_desc += bool(on["children"])
    assert with_desc == 2 * 14   # decision 0014: fourteen nodes have children


def mcp_server_subject() -> str:
    from subject import SUBJECT
    return SUBJECT.id


def test_register_impact_children_reaches_what_cap_0001s_children_reach_and_skips_the_proposed_one():
    s, _ = _server()
    off = _call(s, "register_impact", {"node": "CAP-0001"})["result"]["structuredContent"]
    on = _call(s, "register_impact", {"node": "CAP-0001", "children": True})["result"]["structuredContent"]
    assert off["edges"] == [] and off["reached"] == {}   # task-0111's answer, unchanged
    assert sorted(x["id"] for xs in on["reached"].values() for x in xs) == ["JRN-0001", "PRD-0002", "PROC-0001"]
    assert [(c["id"], c["walked"]) for c in on["children"]] == [("CAP-0002", True), ("CAP-0003", True), ("CAP-0004", True), ("CAP-0005", False)]
    assert next(c for c in on["children"] if c["id"] == "CAP-0005") == {"id": "CAP-0005", "name": on["children"][3]["name"], "state": "proposed",
                                                                         "parent": "CAP-0001", "walked": False, "not_followed": True}
    assert "CAP-0005" not in {e["from"] for e in on["edges"]}   # a withdrawn descendant is not walked from
    assert not {"CAP-0001", "CAP-0002", "CAP-0003", "CAP-0004", "CAP-0005"} & {x["id"] for xs in on["reached"].values() for x in xs}
    live = [k for k in on["keys"] if not k.get("not_followed")]
    assert all("CAP-0005" not in k["via"] for k in live)   # a walked key never comes through the proposed one
    if mcp_server_subject() == "cargo_quote":   # task-0120: the key resting only on CAP-0005, listed last, flagged
        assert len(on["keys"]) == 32 and on["keys"][:31] == live
        last = on["keys"][31]
        assert (last["key"], last["via"], last["not_followed"], last["owner"]) == ("QuoteAPI|on_notification_failure", ["CAP-0005"], True, "ORG-0002")
        assert last["level"]   # listed with its level, as the others are
    for bad in ("yes", 1, None):
        assert _refused(s, "register_impact", {"node": "CAP-0001", "children": bad}), bad


def test_register_impact_children_lands_the_subjects_keys_at_gate_verdicts_levels():
    """On the subject the runner holds: with children, the parents above its slice land the counts
    CHILDREN_LANDS names (CargoQuote's realisers walk from CAP-0001 lands all 36 codegen keys), none
    without, each key at the level gate_verdict gives that key set; the store sees reads only."""
    from subject import SUBJECT
    want_counts = CHILDREN_LANDS[SUBJECT.id]
    writes = []
    s, _ = _server(Stub(writes=writes))
    for (start, which), (n, nflag) in want_counts.items():
        off = _call(s, "register_impact", {"node": start, "walk": which, "as_of": DAY})["result"]["structuredContent"]
        on = _call(s, "register_impact", {"node": start, "walk": which, "children": True, "as_of": DAY})["result"]["structuredContent"]
        flagged = [k for k in on["keys"] if k.get("not_followed")]
        assert off["keys"] == [] and len(on["keys"]) == n and len(flagged) == nflag, (start, which, len(on["keys"]), len(flagged))
        assert on["keys"][n - nflag:] == flagged and all(k["not_followed"] is True for k in flagged)
        walked = {c["id"] for c in on["children"] if c["walked"]}
        withdrawn = {c["id"] for c in on["children"] if c["not_followed"]}
        reached = {x["id"] for xs in on["reached"].values() for x in xs}
        assert all(set(k["via"]) <= {start} | walked | reached for k in on["keys"] if k not in flagged)
        assert all(k["via"] and set(k["via"]) <= withdrawn for k in flagged)
        assert not withdrawn & {e["from"] for e in on["edges"]}   # listed, walked no further
        keys = [k["key"] for k in on["keys"]]
        want = _call(s, "gate_verdict", {"keys": keys, "as_of": DAY})["result"]["structuredContent"]
        assert {k["key"]: k["level"] for k in on["keys"]} == want["levels"] and on["gate"]["verdict"] == want["verdict"]
    if SUBJECT.id == "cargo_quote":
        on = _call(s, "register_impact", {"node": "CAP-0001", "walk": "realisers", "children": True})["result"]["structuredContent"]
        assert sorted(k["key"] for k in on["keys"]) == sorted(TASKS["codegen"]["keys"])
    assert writes == []


# ---- register_impact under a task class (task-0120): gate_verdict --task's block levels, bar and route

def test_register_impact_reads_the_keys_under_the_task_class_named_and_refuses_keys():
    """Each declared class: the landed keys' levels and findings (owner and route included) and the gate
    line equal gate_verdict's for that key set under that class; the default is codegen's; on CargoQuote
    design and codegen answer differently; keys, an undeclared name or a non-string is refused."""
    from subject import SUBJECT
    rows = SUBJECT.register_map().get("row") or []
    if not rows:
        skip("register-rows", "the subject's register_map.toml has no rows")
    s, _ = _server()
    start, which = next(iter(CHILDREN_LANDS[SUBJECT.id]))
    args = {"node": start, "walk": which, "children": True, "as_of": DAY}
    got = {}
    for task in TASKS:
        on = _call(s, "register_impact", {**args, "task": task})["result"]["structuredContent"]
        keys = [k["key"] for k in on["keys"]]
        want = _call(s, "gate_verdict", {"task": task, "keys": keys, "as_of": DAY})["result"]["structuredContent"]
        assert on["gate"]["task"] == task and on["gate"]["verdict"] == want["verdict"] and on["gate"]["why"] == want["why"], task
        assert {k["key"]: k["level"] for k in on["keys"]} == want["levels"], task
        for k in on["keys"]:
            assert k["findings"] == [f for f in want["findings"] if f["kind"] in gate_cli.OWNED and f["key"] == k["key"]], (task, k["key"])
        got[task] = on
    if "codegen" in TASKS:
        assert _call(s, "register_impact", args)["result"]["structuredContent"] == got["codegen"]
    if SUBJECT.id == "cargo_quote":
        strip = lambda r: [(k["key"], k["level"], k["findings"]) for k in r["keys"]]   # noqa: E731
        assert strip(got["design"]) != strip(got["codegen"])
    for bad in ("keys", "nope", 7, ""):
        assert _refused(s, "register_impact", {**args, "task": bad}), bad


# Task-0117: the adopter section of instance/README.md, held to the server and the commands it names.

README = ROOT / "instance" / "README.md"


def _assistant_section() -> str:
    text = README.read_text(encoding="utf-8")
    start = text.index("## Letting an AI assistant ask the gate")
    return text[start:text.index("\n## ", start + 1)]


def _blocks(section: str, lang: str) -> list[str]:
    import re
    return re.findall(rf"```{lang}\n(.*?)```", section, re.S)


def _commands(section: str) -> list[list[str]]:
    """Each command of the section's bash blocks and of the Desktop JSON's command and args, as argv."""
    import re
    import shlex
    out = []
    for block in _blocks(section, "bash"):
        pending = ""
        for line in block.replace("\\\n", " ").splitlines():
            line = line.split("   #")[0].strip()
            if not pending and (not line or line.startswith("#")):
                continue
            pending = f"{pending}\n{line}" if pending else line
            try:
                out.append(shlex.split(pending))       # a quoted argument may span lines
            except ValueError:
                continue
            pending = ""
        assert not pending, pending
    for block in _blocks(section, "json"):
        for entry in json.loads(re.sub(r"^\s{3}", "", block, flags=re.M))["mcpServers"].values():
            out.append([Path(entry["command"]).name, *entry["args"]])
    for inline in re.findall(r"`((?:claude|docker|exec) [^`]+)`", section):   # inline commands too
        out.append(shlex.split(inline if not inline.startswith("exec ") else "docker compose " + inline))
    return out


# Flags of programs this repository does not ship, as their help prints them (claude mcp add on
# Claude Code 2.x, claude remote-control, Docker Compose v2, curl): a flag the section adds must be
# checked against the tool's own --help and added here.
EXTERNAL_FLAGS = {
    "claude mcp add": {"-s", "--scope", "-e", "--env", "-t", "--transport", "-H", "--header"},
    "claude mcp remove": {"-s", "--scope"},
    "claude": set(),
    "docker compose": {"-f", "--file", "-p", "--project-name"},
    "docker compose exec": {"-T", "-e", "--env"},
    "curl": {"-s", "-H", "-d"},
}


def _script_flags(script: str) -> set[str]:
    import re
    import subprocess
    help_text = subprocess.run([sys.executable, str(ROOT / script), "--help"], capture_output=True, text=True,
                               cwd=ROOT, timeout=60).stdout
    return set(re.findall(r"(?<![\w-])(--?[A-Za-z][\w-]*)", help_text))


def test_every_flag_the_assistant_section_names_exists():
    """Every option a command in the section passes is one its program accepts (task-0117 AC3)."""
    import re
    section, seen, scripts = _assistant_section(), set(), {}
    for argv in _commands(section):
        program = None
        for i, tok in enumerate(argv):
            if program is None and re.fullmatch(r"[A-Z_]+=\S*", tok):
                continue                                        # an environment assignment before the program
            if tok == "--" and program and program.startswith("claude"):
                program = None                                  # the command claude starts begins here
                continue
            if program is None or (program.startswith("docker compose") and tok == "exec"):
                if tok in ("python", "python3"):
                    program = argv[i + 1]
                    scripts.setdefault(program, _script_flags(program))
                elif tok == "claude":
                    program = {("mcp", "add"): "claude mcp add", ("mcp", "remove"): "claude mcp remove"}.get(
                        tuple(argv[i + 1:i + 3]), "claude")
                elif tok == "docker":
                    program = "docker compose"
                elif tok == "exec":
                    program = "docker compose exec"
                elif tok in ("curl",):
                    program = tok
                continue
            if program == "docker compose exec" and tok in ("python", "python3"):
                program = argv[i + 1]
                scripts.setdefault(program, _script_flags(program))
                continue
            if tok.startswith("-") and tok != "--":
                allowed = scripts.get(program) or EXTERNAL_FLAGS.get(program)
                assert allowed is not None, f"{program}: a program the guard does not know"
                assert tok in allowed, f"{program} has no option {tok} (instance/README.md)"
                seen.add((program, tok))
    assert ("harness/mcp_server.py", "--http") in seen and ("claude mcp add", "-s") in seen
    assert ("docker compose exec", "-T") in seen and ("harness/mcp_server.py", "--as-of") in seen


def test_the_assistant_section_answers_the_connection_pitfalls():
    """The findings behind task-0117: each pitfall is answered where an adopter reads it."""
    s = _assistant_section()
    for needle in ("is the *path* to the subject's folder", "never the bare `cargo_quote`",
                   "replacing `/path/to/knowgov` with the absolute",
                   "full path to `docker`", "~/Library/Application Support/Claude/claude_desktop_config.json",
                   r"%APPDATA%\Claude\claude_desktop_config.json", "do not replace the file", "Quit Claude Desktop",
                   "~/Library/Logs/Claude/mcp-server-knowgov.log", "some builds show no Developer section",
                   "cannot reach a stack on your computer", "not the server's HTTP port (8765)",
                   "pass `scenario`", "restart the assistant's connection", "-s user", "Remote Control",
                   "Never put the server on a public address", "io.modelcontextprotocol/clientCapabilities", "-32602"):
        assert needle in s, needle


def test_the_readmes_stateless_example_runs_against_the_server():
    """The curl example, as printed, answers over HTTP; without clientCapabilities it is -32602 (task-0117 AC2)."""
    import shlex
    block = next(b for b in _blocks(_assistant_section(), "bash") if "clientCapabilities" in b)
    argv = shlex.split(block.replace("\\\n", " "))
    assert argv[0] == "curl" and argv[2] == "http://127.0.0.1:8765/mcp", argv[:3]
    headers = dict(h.split(": ", 1) for flag, h in zip(argv, argv[1:]) if flag == "-H")
    body = json.loads(argv[argv.index("-d") + 1])
    from subject import SUBJECT
    if body["params"]["arguments"].get("scenario") not in SUBJECT.scenarios:   # the example is CargoQuote's (task-0126)
        body["params"]["arguments"]["scenario"] = Stub().scenario
    httpd, base = _serve()
    day = _Day()
    day.__enter__()
    try:
        code, resp = _post_raw(base + "/mcp", body, headers)
        assert code == 200, resp
        result = resp["result"]
        assert result["isError"] is False and result["resultType"] == "complete"
        assert result["structuredContent"]["verdict"] == "BLOCKED" and result["structuredContent"]["task"] == "codegen"
        bare = json.loads(json.dumps(body))
        del bare["params"]["_meta"][mcp_server.META_CAPABILITIES]
        code, resp = _post_raw(base + "/mcp", bare, headers)
        assert resp["error"]["code"] == -32602, resp
    finally:
        day.__exit__()
        httpd.shutdown()
        httpd.server_close()


# Task-0182: the servers over SSH stdio when the stack runs on another machine (EC2, task-0162).

def _remote_section() -> str:
    s = _assistant_section()
    start = s.index("### The MCP servers when the stack runs on another machine")
    end = s.find("\n### ", start + 1)
    return s[start:] if end < 0 else s[start:end]


def test_the_remote_section_runs_the_local_command_over_ssh():
    """Each client's entry is the local exec command behind `ssh -T <alias>`, for both servers; nothing listens."""
    import re
    s = _remote_section()
    for needle in ("BatchMode yes", "ssh -o BatchMode=no knowgov-ec2 true", "Never set `StrictHostKeyChecking no`",
                   "/usr/bin/ssh", "`claude mcp add` changes Claude Code only", "it never sees what `claude mcp add`", "`127.0.0.1` bind, no port is opened and no token is needed",
                   "`http://localhost:8080`, is the page on the server", "/mcp", "mcp-server-knowgov.log"):
        assert needle in s, needle
    tail = ["docker", "compose", "-f", "knowgov/demo/docker-compose.yml", "exec", "-T", "app", "python"]
    (block,) = _blocks(s, "json")
    servers = json.loads(block)["mcpServers"]
    assert set(servers) == {"knowgov", "knowgov-runs"}
    for name, script in (("knowgov", "harness/mcp_server.py"), ("knowgov-runs", "harness/mcp_runs.py")):
        assert servers[name] == {"command": "/usr/bin/ssh", "args": ["-T", "knowgov-ec2", *tail, script]}, name
        assert f"claude mcp add {name} -s user -- ssh -T knowgov-ec2 {' '.join(tail)} {script}" in s, name
    assert "KG_MCP_TOKEN" not in s and not re.search(r"-L \d", s), "the SSH route needs no token and no tunnel"
    demo = (ROOT / "demo" / "README.md").read_text(encoding="utf-8")
    ec2 = " ".join(demo[demo.index("**The Arms mode on an EC2 instance.**"):].split())
    assert "The MCP servers when the stack runs on another machine" in ec2, "demo/README's EC2 route links it"


def test_the_remote_sections_check_answers_over_stdio():
    """The check's JSON-RPC lines, fed to the server as ssh feeds them, get the greeting and the subjects."""
    import re
    import subprocess
    block = next(b for b in _blocks(_remote_section(), "bash") if "<<'END'" in b)
    lines = re.search(r"<<'END'\n(.*?)\nEND", block, re.S).group(1).splitlines()
    env = {**os.environ, "KG_STORE": "rdflib", "KG_SUBJECT": str(ROOT / "subjects" / "cargo_quote"),
           "KG_SUBJECTS": str(ROOT / "subjects"), "KG_TODAY": DAY}
    env.pop("KG_RDFLIB_FILE", None)
    out = subprocess.run([sys.executable, str(ROOT / "harness" / "mcp_server.py")], input="\n".join(lines) + "\n",
                         capture_output=True, text=True, cwd=ROOT, env=env, timeout=120).stdout.splitlines()
    assert len(out) == 2, out
    greeting, subjects = (json.loads(line) for line in out)
    assert greeting["result"]["serverInfo"]["name"] == "knowgov"
    ids = {s["id"] for s in json.loads(subjects["result"]["content"][0]["text"])["subjects"]}
    assert {"cargo_quote", "jef_data_load"} <= ids, ids
