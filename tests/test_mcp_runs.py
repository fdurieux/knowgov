"""Task-0133 (decision-0008): knowgov-runs, a second stdio MCP server that starts and polls a
scenario run through the page's run API. On a stub page: the modes the operator allows, n fixed at
1, the page's refusal passed through, the token sent and never echoed, the annotations. The reader
stays a reader and the shipped allowlist admits it only; the reader reads a run's new load on its
next call (rdflib, where the pinned libraries are installed). The stack job runs it for real."""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import urllib.error
from pathlib import Path

from tests._skip import need_rdflib  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(Path(__file__).resolve().parent)]
import mcp_runs  # noqa: E402
import mcp_server  # noqa: E402

TOKEN = "page-token-0133-not-real"


class _Resp:
    def __init__(self, status, body):
        self.status, self._body = status, json.dumps(body).encode()

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class StubPage:
    """The page's run API: records every request; one run at a time, as the Runner's lock."""

    def __init__(self, run_text="", execution=None, worker="absent"):
        self.requests, self.current, self.run_text, self.worker = [], None, run_text, worker
        self.execution = {"ok": True, "why": None} if execution is None else execution   # "absent": the page omits it

    def __call__(self, req, timeout=None):
        body = json.loads(req.data) if req.data else None
        self.requests.append({"method": req.get_method(), "url": req.full_url, "headers": dict(req.header_items()), "body": body})
        path = req.full_url.split("8080", 1)[1]
        if req.get_method() == "POST" and path.startswith("/api/run"):
            if self.current and self.current["status"] == "running":
                raise urllib.error.HTTPError(req.full_url, 409, "Conflict", {}, io.BytesIO(
                    json.dumps({"error": "a run is already in progress; the store is one database"}).encode()))
            self.current = {"id": "2026-11-04-2300", "subject": body["subject"], "scenario": body["scenario"], "mode": body["mode"],
                            "n": body["n"], "by": body["by"], "status": "running", "started": "2026-11-04T23:00:00+00:00",
                            "elapsed_s": 0, "source": f"demo-runs/{body['subject']}/2026-11-04-2300", "cmd": "python run.py ...",
                            "log_text": self.run_text, "row": None, "model": None, "effort": None, "as_of": body.get("as_of")}
            return _Resp(202, self.current)
        if path.startswith("/api/run?"):
            return _Resp(200, self.current or {"status": "idle"})
        if path.startswith("/api/scenarios"):
            extra = {} if self.execution == "absent" else {"execution": self.execution}
            if self.worker != "absent":
                extra["worker"] = self.worker
            return _Resp(200, {**extra, "scenarios": [{"id": "S1"}, {"id": "S2"}], "arms_enabled": True, "deterministic_enabled": True,
                               "model_rows": [{"id": "openai-gpt", "label": "x", "provider": "openai", "host": "api.openai.com",
                                               "model": "m", "efforts": ["low"], "key_var": "OPENAI_API_KEY", "key_set": True,
                                               "available": True, "why": "", "price": 3}],
                               "record_model": "m", "record_effort": "", "writes": {"token_required": True, "refused": None},
                               "run": self.current})
        if path.startswith("/api/runs"):
            return _Resp(200, {"runs": [], "current": self.current})
        raise AssertionError(path)


class _Env:
    def __init__(self, **kw):
        self.kw = kw

    def __enter__(self):
        self.old = {k: os.environ.get(k) for k in self.kw}
        for k, v in self.kw.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)

    def __exit__(self, *exc):
        for k, v in self.old.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)


def _server(stub, token=TOKEN):
    return mcp_runs.make_server(mcp_runs.Page("http://localhost:8080", token=token, opener=stub))


def _call(srv, name, args=None):
    return srv.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": args or {}}})["result"]


def test_only_the_modes_the_operator_allows_start_and_deterministic_is_the_default():
    stub = StubPage()
    with _Env(KG_MCP_RUN_MODES=None):
        srv = _server(stub)
        r = _call(srv, "start_run", {"scenario": "S1", "mode": "arms"})
        assert r["isError"] and "not allowed here" in r["content"][0]["text"] and stub.requests == [], "refused before the page is asked"
        assert not _call(srv, "start_run", {"scenario": "S1", "mode": "deterministic"})["isError"]
    with _Env(KG_MCP_RUN_MODES=""):
        assert mcp_runs.allowed_modes() == [] and _call(_server(StubPage()), "start_run", {"scenario": "S1", "mode": "deterministic"})["isError"]
    with _Env(KG_MCP_RUN_MODES="arms, deterministic, bogus"):
        assert mcp_runs.allowed_modes() == ["deterministic", "arms"]
        opts = _call(_server(StubPage()), "run_options")["structuredContent"]
        assert opts["allowed_modes"] == ["deterministic", "arms"] and opts["arms_enabled"]
        assert not any("price" in r for r in opts["model_rows"]), "the rows as the page lists them, no more"
    with _Env(KG_MCP_RUN_MODES="deterministic"):
        assert _call(_server(StubPage()), "run_options")["structuredContent"]["arms_enabled"] is False, "arms on the page, not allowed here"


def test_run_options_says_whether_an_arms_run_would_start_not_only_whether_a_key_is_set():
    """task-0168: the page's execution passed through, and arms_ready when a key, the operator's modes and
    execution all hold; arms_enabled and arms_on_page as before."""
    no_worker = {"ok": False, "why": "refused: the worker has not attested its confinement (/jobs/attest.json: FileNotFoundError)"}
    with _Env(KG_MCP_RUN_MODES="deterministic,arms"):
        ok = _call(_server(StubPage()), "run_options")["structuredContent"]
        assert ok["execution"] == {"ok": True, "why": None} and ok["arms_ready"] and ok["arms_enabled"], ok
        refused = _call(_server(StubPage(execution=no_worker)), "run_options")["structuredContent"]
        assert refused["execution"] == no_worker and refused["arms_ready"] is False, refused
        assert refused["arms_enabled"] and refused["arms_on_page"], "the key count is unchanged, for compatibility"
        old = _call(_server(StubPage(execution="absent")), "run_options")["structuredContent"]
        assert old["execution"]["ok"] is False and "task-0167" in old["execution"]["why"] and not old["arms_ready"], old
    with _Env(KG_MCP_RUN_MODES="deterministic"):
        assert _call(_server(StubPage()), "run_options")["structuredContent"]["arms_ready"] is False, "not allowed here"
    table = {t["name"]: t for t in mcp_runs.tools_table()}
    assert "arms_ready" in table["run_options"]["description"] and "execution" in table["run_options"]["description"]
    assert "arms_ready" in mcp_runs.INSTRUCTIONS


def test_n_is_always_one_and_the_run_is_marked_by_mcp():
    stub = StubPage()
    with _Env(KG_MCP_RUN_MODES="deterministic,arms"):
        srv = _server(stub)
        # task-0200 (M5): n is not in the schema, so it is refused (-32602), never silently set to 1; re-pinned
        e = srv.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                        "params": {"name": "start_run", "arguments": {"scenario": "S2", "mode": "arms", "n": 5, "row": "openai-gpt"}}})
        assert e["error"]["code"] == -32602 and "'n'" in e["error"]["message"], e
        assert stub.requests == [], "a refused call reaches nothing"
        r = _call(srv, "start_run", {"scenario": "S2", "mode": "arms", "row": "openai-gpt"})
    assert not r["isError"], r
    (post,) = [x for x in stub.requests if x["method"] == "POST"]
    assert post["body"]["n"] == 1 and post["body"]["by"] == "mcp" and post["body"]["row"] == "openai-gpt", post["body"]
    assert "n" not in mcp_runs.tools_table()[1]["inputSchema"]["properties"]
    with _Env(KG_MCP_RUN_MODES=None):
        r = _call(_server(StubPage()), "start_run", {"scenario": "S1", "mode": "deterministic", "row": "openai-gpt"})
        assert r["isError"] and "calls no model" in r["content"][0]["text"]
        assert _call(_server(StubPage()), "start_run", {"scenario": "S1", "mode": "deterministic", "as_of": "next week"})["isError"]


def test_a_second_start_is_refused_with_the_pages_message():
    stub = StubPage()
    with _Env(KG_MCP_RUN_MODES=None):
        srv = _server(stub)
        first = _call(srv, "start_run", {"scenario": "S1", "mode": "deterministic"})
        second = _call(srv, "start_run", {"scenario": "S2", "mode": "deterministic"})
    assert not first["isError"] and first["structuredContent"]["id"] == "2026-11-04-2300"
    assert second["isError"] and "(409)" in second["content"][0]["text"]
    assert "a run is already in progress; the store is one database" in second["content"][0]["text"]


def test_the_token_is_sent_and_never_echoed():
    stub = StubPage(run_text=f"a log that happens to hold {TOKEN}\n")
    with _Env(KG_MCP_RUN_MODES=None):
        srv = _server(stub)
        replies = [_call(srv, "run_options"), _call(srv, "start_run", {"scenario": "S1", "mode": "deterministic"}),
                   _call(srv, "run_status"), _call(srv, "run_status", {"run": "2026-11-04-2300"})]
    assert all(x["headers"].get("Authorization") == f"Bearer {TOKEN}" for x in stub.requests), stub.requests
    assert not any("Origin" in x["headers"] for x in stub.requests), "the page refuses another origin; none is sent"
    for r in replies:
        assert TOKEN not in json.dumps(r), r
    assert "<token>" in replies[2]["structuredContent"]["log_tail"]

    def down(req, timeout=None):
        raise urllib.error.URLError(f"refused at {TOKEN}")
    r = _call(_server(down), "run_options")
    assert r["isError"] and TOKEN not in r["content"][0]["text"] and "did not answer" in r["content"][0]["text"]
    no_token = StubPage()
    _call(_server(no_token, token=""), "run_options")
    assert "Authorization" not in no_token.requests[0]["headers"]


def test_the_annotations_say_what_each_tool_does():
    with _Env(KG_MCP_RUN_MODES=None):
        table = {t["name"]: t for t in mcp_runs.tools_table()}
        srv = _server(StubPage())
        listed = srv.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})["result"]["tools"]
        info = srv.handle({"jsonrpc": "2.0", "id": 2, "method": "initialize", "params": {}})["result"]
    assert [t["name"] for t in listed] == ["run_options", "start_run", "run_status"]
    s = table["start_run"]["annotations"]
    assert s["readOnlyHint"] is False and s["destructiveHint"] is True and s["idempotentHint"] is False and s["openWorldHint"] is False
    assert table["run_options"]["annotations"] == mcp_server.READ_ONLY and table["run_status"]["annotations"] == mcp_server.READ_ONLY
    with _Env(KG_MCP_RUN_MODES="deterministic,arms"):
        assert {t["name"]: t for t in mcp_runs.tools_table()}["start_run"]["annotations"]["openWorldHint"] is True, "a model call leaves the machine"
    assert info["serverInfo"]["name"] == "knowgov-runs" and "wipes and reloads the one store" in info["instructions"]
    assert mcp_runs.main(["--http"]) == 2, "stdio only"


def test_run_status_reports_the_end_and_points_at_the_reader():
    stub = StubPage(run_text="line\n" * 2000)
    with _Env(KG_MCP_RUN_MODES=None):
        srv = _server(stub)
        assert _call(srv, "run_status")["structuredContent"]["status"] == "idle"
        _call(srv, "start_run", {"scenario": "S1", "mode": "deterministic"})
        running = _call(srv, "run_status")["structuredContent"]
        assert running["status"] == "running" and len(running["log_tail"]) == mcp_runs.LOG_TAIL and "next" not in running
        stub.current.update(status="done", exit_code=0, finished="2026-11-04T23:00:05+00:00", elapsed_s=5)
        done = _call(srv, "run_status", {"run": "2026-11-04-2300"})["structuredContent"]
    assert (done["status"], done["exit_code"], done["by"]) == ("done", 0, "mcp") and done["source"].endswith("/2026-11-04-2300")
    assert "scenario_runs" in done["next"] and "gate_verdict" in done["next"] and "cmd" not in done


def test_the_reader_stays_a_reader_and_the_allowlist_admits_it_only():
    srv = mcp_server.Server(mcp_server.Tools(opener=lambda: None))
    names = [t["name"] for t in srv.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})["result"]["tools"]]
    assert not set(names) & {"run_options", "start_run", "run_status"} and all(
        t["annotations"]["readOnlyHint"] is True for t in mcp_server.TOOLS)
    assert mcp_server.INSTRUCTIONS.endswith("This server only reads.") and mcp_server.SERVER["name"] == "knowgov"
    allow = json.loads((ROOT / "instance" / "ci" / "claude" / "managed-mcp-allowlist.json").read_text(encoding="utf-8"))
    assert allow["allowedMcpServers"] == [{"serverName": "knowgov"}], "the shipped allowlist admits the reader only"
    assert "import mcp_runs" not in (ROOT / "harness" / "mcp_server.py").read_text(encoding="utf-8")
    assert "subprocess" not in (ROOT / "harness" / "mcp_runs.py").read_text(encoding="utf-8"), "it starts no process of its own"


def test_the_reader_reads_a_runs_new_load_on_its_next_call():
    """doc-0016 F6: the reader opens the store per call (task-0097 has not cached a handle), so a gate
    call after an agent's run reads the new load; a run.json recording the run's end changes nothing."""
    RdflibStore = need_rdflib().RdflibStore   # the tests job has no rdflib; the rdflib job runs it
    from subject import SUBJECT
    first, second = SUBJECT.order[0], SUBJECT.order[-1]
    with tempfile.TemporaryDirectory() as td, _Env(KG_TODAY="2026-11-04"):
        path = str(Path(td) / "store.ttl")

        def load(sc):
            st = RdflibStore(path=path)
            st.wipe()
            st.create_node("agent:t", "Agent", {})
            st.create_activity(f"act:extract:{sc}:v1", "extract", "2026-11-04T23:00:00+00:00", "t", "", "agent:t",
                               subject=SUBJECT.id, scenario=sc)   # as a load records it (task-0195)
            st.commit()
            st.close()
        load(first)
        tools = mcp_server.Tools(opener=lambda: mcp_server.open_read_only(lambda **kw: RdflibStore(path=path, **kw)), runs=Path(td))
        assert tools.store_status({})["scenario"] == first
        load(second)   # the agent's run, through the page
        run = Path(td) / SUBJECT.id / "2026-11-04-2300"
        run.mkdir(parents=True)
        (run / "run.json").write_text(json.dumps({"version": 2, "status": "done", "scenario": second, "by": "mcp"}), encoding="utf-8")
        got = tools.store_status({})
        assert got["scenario"] == second and got["loaded_at"] == "2026-11-04T23:00:00+00:00", got
        assert Path(path).read_text(encoding="utf-8").count(f"act:extract:{second}") >= 1


def test_run_options_passes_the_workers_place_through():
    """task-0169: the page's worker (execution.placement()) as it reports it; a page without it reads not attested."""
    aws = {"backend": "worker", "attested": True, "why": None,
           "host": {"system": "Linux", "kernel": "7.0.0-1014-aws", "machine": "x86_64", "engine": "docker"},
           "cloud": {"name": "AWS", "basis": "read from the kernel release's -aws suffix, not checked"}}
    with _Env(KG_MCP_RUN_MODES="deterministic,arms"):
        got = _call(_server(StubPage(worker=aws)), "run_options")["structuredContent"]["worker"]
        assert got == aws, got
        old = _call(_server(StubPage()), "run_options")["structuredContent"]["worker"]
        assert old["attested"] is False and old["host"] is None and "task-0169" in old["why"], old
    assert "worker" in {t["name"]: t for t in mcp_runs.tools_table()}["run_options"]["description"]
