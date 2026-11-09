"""Task-0272: the servers survive deep nesting and answer JSON-RPC's protocol edge cases.

A request nested past the parser's depth is a parse error (-32700 on both MCP servers and both transports,
400 on the page), never a RecursionError that ends the stdio loop or drops the connection; an id that is
not a string, a whole number or null is -32600; a ``_meta`` protocol version that is not a string is
-32602; invalid UTF-8 in an HTTP body is -32700, never a "replace" decode; the Bearer scheme is compared
without regard to case on both servers and the page; the page's startup line names the store in use; and
``add_artefact``'s ``file`` is confined as ``subject_check`` confines a manifest's paths."""
from __future__ import annotations

import io
import json
import os
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "demo" / "app")]
import http_boundary as hb  # noqa: E402
import mcp_runs  # noqa: E402
import mcp_server  # noqa: E402
import wizard  # noqa: E402
from tests.test_http_limits import _env, _page, _post as _raw_post, _send  # noqa: E402
from tests.test_mcp_server import MODERN, _meta, _server  # noqa: E402

DEEP_LINE = "[" * 200_000 + "\n"            # one stdio line the parser cannot read (AC1)
DEEP_BODY = b"[" * 20_000 + b"]" * 20_000   # 40 KB, under every limit, nested past the parser's depth
INIT = {"jsonrpc": "2.0", "id": 7, "method": "initialize", "params": {"protocolVersion": "2025-11-25"}}


def _servers():
    """Both MCP servers' protocol layers: the reader and knowgov-runs (its page never reached here)."""
    reader, _ = _server()
    return {"knowgov": reader, "knowgov-runs": mcp_runs.make_server(mcp_runs.Page(url="http://127.0.0.1:9", token=None))}


def _stdio(server, lines: list[str]) -> list[dict]:
    out = io.StringIO()
    mcp_server.serve_stdio(server, io.StringIO("".join(lines)), out)
    return [json.loads(x) for x in out.getvalue().splitlines()]


def test_a_200k_level_line_is_a_parse_error_and_the_stdio_loop_answers_the_next_request():
    """AC1 (stdio): -32700 for the deep line, then the next request answered, on both servers."""
    for name, s in _servers().items():
        got = _stdio(s, [DEEP_LINE, json.dumps(INIT) + "\n"])
        assert len(got) == 2, (name, got)
        assert got[0]["error"]["code"] == -32700 and got[0]["id"] is None, (name, got[0])
        assert got[1]["id"] == 7 and got[1]["result"]["serverInfo"]["name"] == name, (name, got[1])
    assert isinstance(hb.parse_json(json.dumps(INIT)), dict)
    for bad in (DEEP_LINE, DEEP_BODY, b"\xff\xfe{}", "{not json"):
        try:
            hb.parse_json(bad)
        except hb.NotJson:
            continue
        raise AssertionError(f"{bad[:12]!r} parsed")


def _serve_http(server, token=None):
    httpd = mcp_server.serve_http(server, "127.0.0.1", 0, token)
    httpd.RequestHandlerClass.log_message = lambda self, *a: None
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def test_a_deep_body_and_invalid_utf8_are_minus_32700_over_http_on_both_servers_and_400_on_the_page():
    """AC1 (HTTP), AC2: a 20k-level body (40 KB) and a body that is not UTF-8 each get a response, 400 with
    -32700, on both MCP servers; the connection serves a request after; the page answers 400, no traceback."""
    for name, s in _servers().items():
        httpd = _serve_http(s)
        port = httpd.server_address[1]
        try:
            for body in (DEEP_BODY, b'{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"x": "\xff"}}'):
                got, data = _send(port, _raw_post(port, "/mcp", body))
                assert got == 400 and b"-32700" in data, (name, body[:20], got, data[-200:])
            got, data = _send(port, _raw_post(port, "/mcp", json.dumps(INIT).encode()))
            assert got == 200 and b'"serverInfo"' in data, (name, data[-200:])
        finally:
            httpd.shutdown()
            httpd.server_close()
    with _page(limits=hb.Limits(max_body=1 << 20, read_timeout=5, idle_timeout=5, max_connections=3)) as (httpd, calls, log):
        port = httpd.server_address[1]
        for body in (DEEP_BODY, b'{"scenario": "\xff"}'):
            got, data = _send(port, _raw_post(port, "/api/run", body))
            assert got == 400 and b"Traceback" not in data, (body[:20], got, data[-200:])
        assert calls["start"] == 0 and not any("Traceback" in x for x in log)


def test_an_id_that_is_not_a_string_a_whole_number_or_null_is_minus_32600_on_both_servers():
    """AC2: [1], {}, 1.5 and true are refused with a null id; a string, a whole number and null still answer."""
    for name, s in _servers().items():
        for bad in ([1], {"a": 1}, 1.5, True):
            r = s.handle({**INIT, "id": bad})
            assert r["error"]["code"] == -32600 and r["id"] is None, (name, bad, r)
            code, r = s.handle_http(json.dumps({**INIT, "id": bad}).encode(), {})
            assert code == 400 and r["error"]["code"] == -32600 and r["id"] is None, (name, bad, code, r)
        for good in ("a", 3, 0):
            assert s.handle({**INIT, "id": good})["id"] == good, (name, good)
        r = s.handle({**INIT, "id": None})   # null stays a JSON-RPC id, as before
        assert r["id"] is None and "result" in r, (name, r)


def test_a_meta_protocol_version_that_is_not_a_string_is_minus_32602_and_never_reads_as_the_handshake_era():
    """AC2: a _meta version of 5, null or a list is -32602 on both servers and over HTTP, never answered as
    a handshake-era request without the revision's checks; a string version still reaches them."""
    for name, s in _servers().items():
        for bad in (5, None, ["2026-07-28"]):
            msg = {"jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": {"_meta": {**_meta(), mcp_server.META_VERSION: bad}}}
            r = s.handle(msg)
            assert r["error"]["code"] == -32602 and r["id"] == 3, (name, bad, r)
            code, r = s.handle_http(json.dumps(msg).encode(), {})
            assert code == 400 and r["error"]["code"] == -32602, (name, bad, code, r)
        ok = {"jsonrpc": "2.0", "id": 4, "method": "server/discover", "params": {"_meta": _meta()}}
        assert s.handle(ok)["result"]["supportedVersions"][0] == MODERN, name


def test_the_bearer_scheme_is_compared_without_regard_to_case_on_both_servers_and_the_page():
    """AC2 (RFC 7235 §2.1): bearer, BEARER and Bearer pass with the right token; a wrong token, another
    scheme or none is 401 everywhere."""
    for h, want in (("Bearer tok", True), ("bearer tok", True), ("BEARER  tok", True), ("Bearer tok2", False),
                    ("Basic tok", False), ("tok", False), ("", False), (None, False)):
        assert hb.bearer_matches(h, "tok") is want, h
    for name, s in _servers().items():
        httpd = _serve_http(s, token="tok")
        port = httpd.server_address[1]
        try:
            for h, want in ((b"bearer tok", 200), (b"BeArEr tok", 200), (b"Bearer nope", 401), (b"Token tok", 401)):
                got, data = _send(port, _raw_post(port, "/mcp", json.dumps(INIT).encode(), extra=b"Authorization: " + h + b"\r\n"))
                assert got == want, (name, h, got, data[-160:])
        finally:
            httpd.shutdown()
            httpd.server_close()
    import server
    with _env(KG_PAGE_TOKEN="tok"):
        assert server.write_guard({"Authorization": "bearer tok"}) is None
        assert server.write_guard({"Authorization": "BEARER tok"}) is None
        assert server.write_guard({"Authorization": "bearer nope"})[0] == 401
        assert server.write_guard({})[0] == 401


def test_the_pages_startup_line_names_the_store_in_use():
    """Under rdflib the startup line names rdflib and its file, never the bolt URL the page does not use."""
    import server
    assert server.store_named({"KG_STORE": "rdflib", "KG_RDFLIB_FILE": "/data/s.ttl"}) == "rdflib /data/s.ttl"
    assert server.store_named({"KG_STORE": "rdflib"}) == "rdflib in memory"
    assert server.store_named({"KG_NEO4J_URI": "bolt://neo4j:7687"}) == "bolt://neo4j:7687"
    assert server.store_named({}) == "bolt://localhost:7687"
    src = (ROOT / "demo" / "app" / "server.py").read_text(encoding="utf-8")
    assert "store {store_named()}" in src and "store {NEO4J_URI}" not in src


def test_add_artefacts_file_refuses_control_characters_dot_dot_and_absolute_paths():
    """AC3: the file token is a relative path inside the instance, as subject_check confines a manifest's:
    NUL and other control characters, a backslash, ~, an absolute path and any .. segment are refused, over
    prompts/get too; an ordinary path still gives the prompt with it."""
    for bad in ("a\x00b", "a\x01b", "ok\x7f", "a\x85b", "/etc/passwd", "../x", "artefacts/../../x", "a/..", "~/x", "a\\b"):
        try:
            wizard.get("add_artefact", {"subject": "cargo_quote", "file": bad})
        except wizard.PromptError as e:
            assert "file" in str(e), (bad, e)
        else:
            raise AssertionError(f"file {bad!r} accepted")
    good = wizard.get("add_artefact", {"subject": "cargo_quote", "file": "artefacts/contracts/quote.md"})
    assert "file `artefacts/contracts/quote.md`" in good["messages"][0]["content"]["text"]
    s, _ = _server()
    r = s.handle({"jsonrpc": "2.0", "id": 9, "method": "prompts/get",
                  "params": {"name": "add_artefact", "arguments": {"subject": "cargo_quote", "file": "../../etc/passwd"}}})
    assert r["error"]["code"] == -32602 and "climbs out" in r["error"]["message"], r


def test_the_changelog_names_it():
    log = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").split("\n## ", 2)[1]
    assert log.startswith("Unreleased") and "task-0272" in log
