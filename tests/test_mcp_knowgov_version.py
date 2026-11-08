"""task-0231: the MCP servers name the knowgov they run (task-0227's identity, harness/build_identity.py): the reader's
store_status and knowgov-runs' run_options carry {version, commit, describe}, the page's /api/subjects
shape, read once at start, each null when unknown; both servers' serverInfo.version is knowgov's VERSION,
in the handshake reply and in the stateless era's _meta stamp. The output schemas hold the field."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(Path(__file__).resolve().parent)]
import build_identity  # noqa: E402
import mcp_runs  # noqa: E402
import mcp_server  # noqa: E402
import schema_check  # noqa: E402
import test_mcp_runs as runs_t  # noqa: E402
import test_mcp_server as reader_t  # noqa: E402

VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def test_store_status_names_the_knowgov_it_runs():
    got = reader_t._call(reader_t._server()[0], "store_status")["result"]["structuredContent"]
    assert got["knowgov"] == build_identity.identity(ROOT), got.get("knowgov")
    assert set(got["knowgov"]) == {"version", "commit", "describe"} and got["knowgov"]["version"] == VERSION
    assert not schema_check.validate(got, schema_check.load("store-status")), "the schema holds the field"
    bad = dict(got, knowgov={"version": VERSION})
    assert schema_check.validate(bad, schema_check.load("store-status")), "all three parts, each a string or null"


def test_knowgov_runs_run_options_names_it_too():
    with runs_t._Env(KG_MCP_RUN_MODES="deterministic"):
        got = runs_t._call(runs_t._server(runs_t.StubPage()), "run_options")["structuredContent"]
    assert got["knowgov"] == build_identity.identity(ROOT), got.get("knowgov")
    assert not schema_check.validate(got, schema_check.load("run-options"))


def test_server_info_version_is_knowgov_version_in_both_eras():
    for info in (mcp_server.SERVER, mcp_runs.SERVER):
        assert info["version"] == VERSION, info
    s = reader_t._server()[0]
    init = s.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                     "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}}})
    assert init["result"]["serverInfo"]["version"] == VERSION, init["result"]["serverInfo"]
    modern = s.handle({"jsonrpc": "2.0", "id": 2, "method": "server/discover",
                       "params": {"_meta": {mcp_server.META_VERSION: "2026-07-28", mcp_server.META_CAPABILITIES: {},
                                            "io.modelcontextprotocol/clientInfo": {"name": "t", "version": "1"}}}})
    assert modern["result"]["_meta"][mcp_server.META_SERVER]["version"] == VERSION, json.dumps(modern)[:400]


def test_read_once_at_start():
    for src in ("mcp_server.py", "mcp_runs.py"):
        text = (ROOT / "harness" / src).read_text(encoding="utf-8")
        assert text.count("build_identity.identity(") <= 1, src
    assert "build_identity.identity(" in (ROOT / "harness" / "mcp_server.py").read_text(encoding="utf-8")
