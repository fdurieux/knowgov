"""task-0171: a model row's key is checked before the Arms drop-down offers the row, by the endpoint's
model listing, so no token is spent. Stand-in responses only: a stand-in probe for the verdicts, the
cache and the page; with the openai library installed, the real client against a loopback stand-in
of the listing. No paid call, no real key."""
from __future__ import annotations

import ast
import contextlib
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "demo" / "app")]
import key_check  # noqa: E402
from tests._skip import skip  # noqa: E402

FAKE = "sk-fake-0171-not-a-key-ABCDEFGH"   # never a real key; it must appear in no output
KEYS = ("OPENAI_API_KEY", "GEMINI_API_KEY", "LITELLM_MASTER_KEY", "KG_MODEL_API_KEY", "KG_MODEL_BASE_URL",
        "KG_MODEL_API_KEY_VAR", "KG_ARMS_MODEL", "KG_ARMS_EFFORT", "KG_MODELS", "KG_KEY_CHECK")


@contextlib.contextmanager
def _env(**kw):
    keep = {k: os.environ.get(k) for k in set(KEYS) | set(kw)}
    for k in keep:
        os.environ.pop(k, None)
    os.environ.update({k: v for k, v in kw.items() if v is not None})
    try:
        yield
    finally:
        for k, v in keep.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)


class Stand:
    """A stand-in probe: the verdict per base URL, counting the calls; it sees the key, keeps none."""

    def __init__(self, by_base: dict):
        self.by_base, self.calls = by_base, []

    def __call__(self, base_url, key):
        self.calls.append(base_url)
        return dict(self.by_base[base_url])


OK = {"state": "accepted", "status": 200, "models": ["gpt-5.5", "gpt-5.1", "models/gemini-3.8-flash", "claude-sonnet-5-5"]}


def _checker(by_base):
    c = key_check.Checker(Stand(by_base))
    c.enabled = True
    return c


def test_each_verdict_with_its_status_and_reason():
    by = {"https://a/v1": OK, "https://r/v1": {"state": "refused", "status": 401, "models": None},
          "https://u/v1": {"state": "unreachable", "status": None, "models": None},
          "https://n/v1": {"state": "unchecked", "status": 404, "models": None},
          "https://o/v1": {"state": "unchecked", "status": 200, "models": ["openai/gpt-5.5"], "open": True}}
    c = _checker(by)
    with _env(OPENAI_API_KEY=FAKE):
        c.ensure([(b, "OPENAI_API_KEY") for b in by])
        a = c.verdict("https://a/v1", "OPENAI_API_KEY", "gpt-5.5")
        assert a["state"] == "accepted" and a["status"] == 200 and a["model_listed"] is True and a["scope"] == "key", a
        assert a["checked_at"] and a["checked_at"].endswith("Z")
        assert c.verdict("https://a/v1", "OPENAI_API_KEY", "gemini-3.8-flash")["model_listed"] is True, "Google's models/ prefix"
        assert c.verdict("https://a/v1", "OPENAI_API_KEY", "gpt-9")["model_listed"] is False
        r = c.verdict("https://r/v1", "OPENAI_API_KEY", "m")
        assert r["state"] == "refused" and r["status"] == 401 and "OPENAI_API_KEY" in r["why"] and "HTTP 401" in r["why"], r
        assert c.verdict("https://u/v1", "OPENAI_API_KEY")["state"] == "unreachable"
        n = c.verdict("https://n/v1", "OPENAI_API_KEY")
        assert n["state"] == "unchecked" and n["status"] == 404 and n["model_listed"] is None, n
        o = c.verdict("https://o/v1", "OPENAI_API_KEY", "gpt-5.5")   # task-0188: a listing open without a key
        assert o["state"] == "unchecked" and o["status"] == 200 and o["model_listed"] is True, o
        assert o["why"] == "the endpoint lists its models without a key, so the listing says nothing of the key in OPENAI_API_KEY", o["why"]
        assert set(o) == set(a), ("no new field in the page's answer", set(o) ^ set(a))
    with _env():
        assert c.verdict("https://a/v1", "OPENAI_API_KEY")["why"] == "set OPENAI_API_KEY", "no key, nothing known"


def test_once_per_endpoint_and_key_by_a_fingerprint_and_rechecked_on_demand():
    stand = Stand({"https://a/v1": OK, "https://b/v1": OK})
    c = key_check.Checker(stand)
    with _env(OPENAI_API_KEY=FAKE, KG_MODEL_API_KEY=FAKE):
        c.ensure([("https://a/v1", "OPENAI_API_KEY")])
        assert stand.calls == [], "nothing is sent before the page enables the checker"
        c.enabled = True
        # two rows on one endpoint and key (the record's and gpt-5.5's): one request; another endpoint, its own
        c.ensure([("https://a/v1", "OPENAI_API_KEY"), ("https://a/v1", "KG_MODEL_API_KEY"), ("https://b/v1", "OPENAI_API_KEY")])
        c.ensure([("https://a/v1", "OPENAI_API_KEY")])
        assert sorted(stand.calls) == ["https://a/v1", "https://b/v1"], stand.calls
        c.ensure([("https://a/v1", "OPENAI_API_KEY")], recheck=True)
        assert stand.calls.count("https://a/v1") == 2, "re-checkable"
        os.environ["OPENAI_API_KEY"] = FAKE + "-changed"
        assert c.verdict("https://a/v1", "OPENAI_API_KEY")["state"] == "unchecked", "another key, another check"
        c.ensure([("https://a/v1", "OPENAI_API_KEY")])
        assert stand.calls.count("https://a/v1") == 3
        with _env(KG_KEY_CHECK="off", OPENAI_API_KEY=FAKE):
            c.ensure([("https://a/v1", "OPENAI_API_KEY")], recheck=True)
            v = c.verdict("https://a/v1", "OPENAI_API_KEY")
            assert stand.calls.count("https://a/v1") == 3 and v["state"] == "unchecked" and "KG_KEY_CHECK" in v["why"], v
    fp = key_check.fingerprint("https://a/v1", FAKE)
    assert FAKE not in fp and FAKE[-8:] not in fp and len(fp) == 24
    import hashlib
    assert fp not in (hashlib.sha256(FAKE.encode()).hexdigest()[:24], hashlib.sha256(("https://a/v1\0" + FAKE).encode()).hexdigest()[:24]), \
        "keyed by a secret of this process, not a plain digest anyone could recompute"
    assert all(FAKE not in json.dumps(v) for v in c._done.values()) and all(FAKE not in str(k) for k in c._done)


def test_a_refused_row_is_unavailable_and_a_run_on_it_refused_before_anything_runs():
    import models
    import server
    import execution
    stand = Stand({"https://api.openai.com/v1": {"state": "refused", "status": 401, "models": None},
                   "https://generativelanguage.googleapis.com/v1beta/openai/": OK, "http://litellm:4000/v1": OK})
    keep_checker, keep_refusal = key_check.CHECKER, execution.refusal
    key_check.CHECKER = key_check.Checker(stand)
    key_check.CHECKER.enabled = True
    execution.refusal = lambda *a, **kw: None   # a contained worker, as the stack has it: the key is what refuses here
    try:
        import page_subject
        from subject import Subject
        # the subject named, whatever the process's KG_SUBJECT (tests.yml runs the suite again on J-F):
        # CargoQuote has S1, an oracle and a record row on OpenAI's endpoint
        with _env(OPENAI_API_KEY=FAKE, GEMINI_API_KEY=FAKE, LITELLM_MASTER_KEY=FAKE), \
                page_subject.using(Subject(ROOT / "subjects" / "cargo_quote")):
            rows = {r["id"]: r for r in server.model_rows()}
            gpt = rows["openai-gpt-5.5"]
            assert not gpt["available"] and gpt["key_set"] and gpt["key_check"]["state"] == "refused", gpt
            assert "HTTP 401" in gpt["why"] and "OPENAI_API_KEY" in gpt["why"], gpt["why"]
            assert not rows["record"]["available"], "the record's row shares the endpoint and the key"
            assert rows["google-gemini-3.8-flash"]["available"] and rows["google-gemini-3.8-flash"]["key_check"]["state"] == "accepted"
            claude = rows["anthropic-claude-sonnet-5-5"]
            assert claude["available"] and claude["key_check"]["scope"] == "gateway", claude
            assert claude["key_check"]["why"] == "gateway key accepted, upstream unchecked", claude["key_check"]
            assert stand.calls.count("https://api.openai.com/v1") == 1, "the record's row and both OpenAI rows: one check"
            assert FAKE not in json.dumps(list(rows.values())), "no key in what the page receives"
            n_before = len(list((server.RUNS_DIR).glob("*/*"))) if server.RUNS_DIR.exists() else 0
            runner = server.Runner()
            try:
                runner.start("S1", "arms", 1, row="openai-gpt-5.5", effort="")
                raise AssertionError("a run on a refused key started")
            except ValueError as e:
                assert "HTTP 401" in str(e) and "OPENAI_API_KEY" in str(e) and FAKE not in str(e), e
            finally:
                runner.join()   # nothing started; joined all the same, as every test that starts a run
            n_after = len(list((server.RUNS_DIR).glob("*/*"))) if server.RUNS_DIR.exists() else 0
            assert n_after == n_before, "refused before a run folder exists"
            try:
                models.resolve("openai-gpt-5.5", "", "", "", "reply", check=server._key_verdict)
                raise AssertionError("resolve let a refused row through")
            except ValueError as e:
                assert "is not available" in str(e)
            assert server.arms_enabled(), "the other rows are still usable"
    finally:
        key_check.CHECKER, execution.refusal = keep_checker, keep_refusal


def test_without_the_checker_started_every_row_reads_unchecked_and_nothing_changes():
    import server
    assert key_check.CHECKER.enabled is False, "importing the page sends nothing; main() enables it"
    import page_subject
    from subject import Subject
    with _env(OPENAI_API_KEY=FAKE), page_subject.using(Subject(ROOT / "subjects" / "cargo_quote")):
        rows = server.model_rows()
    gpt = next(r for r in rows if r["id"] == "openai-gpt-5.5")
    assert gpt["available"] and gpt["key_check"]["state"] == "unchecked" and gpt["why"] == "", gpt
    src = (ROOT / "demo" / "app" / "server.py").read_text(encoding="utf-8")
    main = src.split("def main()", 1)[1].split("\ndef ", 1)[0]
    assert "key_check.CHECKER.enabled = True" in main and "check_keys(wait=0)" in main
    post = src.split("    def _post(self", 1)[1].split("\n    def ", 1)[0]
    assert '["api", "models", "check"]' in post, "the re-check is a POST, behind the write guard every POST passes"


def test_the_gateway_row_is_declared_and_the_mcp_run_options_pass_the_verdict_through():
    import models
    table = {r["id"]: r for r in models.load_table()}
    assert table["anthropic-claude-sonnet-5-5"]["gateway"] is True
    assert not any(r["gateway"] for i, r in table.items() if i != "anthropic-claude-sonnet-5-5")
    import mcp_runs
    assert "key_check" in mcp_runs.tools_table()[0]["description"]
    src = (ROOT / "harness" / "mcp_runs.py").read_text(encoding="utf-8")
    assert '"available", "why", "key_check")' in src
    page = (ROOT / "demo" / "app" / "index.html").read_text(encoding="utf-8")
    assert "gateway key accepted, upstream unchecked" in page and "/api/models/check" in page


def test_the_check_is_the_model_clients_listing_and_nothing_else():
    """The only outbound call key_check.py makes is the model client's models.list(), to the row's own
    base URL; no completion, no chat, no /health; nothing printed or logged."""
    tree = ast.parse((ROOT / "harness" / "key_check.py").read_text(encoding="utf-8"))
    attrs = {f"{n.value.attr}.{n.attr}" for n in ast.walk(tree)
             if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Attribute)}
    assert "models.list" in attrs and not any(a.split(".")[0] in ("chat", "completions", "responses", "embeddings") for a in attrs), attrs
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert not names & {"print", "logging", "logger", "write_text", "open"}, names & {"print", "logging", "logger", "write_text", "open"}
    imports = {a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module == "openai" for a in n.names}
    assert "OpenAI" in imports
    call = next(n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "OpenAI")
    assert {k.arg for k in call.keywords} == {"api_key", "base_url", "max_retries", "timeout"}
    assert any(k.arg == "max_retries" and getattr(k.value, "value", None) == 0 for k in call.keywords), "no retry"
    assert "/health" not in (ROOT / "harness" / "key_check.py").read_text(encoding="utf-8").replace('``/health``', '')


class _Listing(BaseHTTPRequestHandler):
    """A stand-in of an endpoint's GET /v1/models, a body quoting the key the way OpenAI's 401 does, so
    the test sees that no provider message leaves the check. ``status`` answers every bearer, as an
    open listing does (OpenRouter's, Ollama's) or a broken one; with ``keyed`` set, the listing answers
    200 to that bearer only and ``status`` to any other, as Mistral's does (task-0188)."""
    status = 200
    keyed: str | None = None
    ids = ("gpt-5.5",)
    seen: list = []

    def do_GET(self):  # noqa: N802
        type(self).seen.append({"path": self.path, "auth": self.headers.get("Authorization") or ""})
        auth = self.headers.get("Authorization") or ""
        status = 200 if type(self).keyed and auth == "Bearer " + type(self).keyed else type(self).status
        if status == 200:
            body = {"object": "list", "data": [{"id": i, "object": "model", "created": 0, "owned_by": "x"} for i in type(self).ids]}
        else:
            body = {"error": {"message": f"Incorrect API key provided: {auth[7:14]}...{auth[-4:]}", "type": "invalid_request_error"}}
        raw = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):  # noqa: N802
        type(self).seen.append({"path": self.path, "post": True})
        self.send_response(500)
        self.end_headers()

    def log_message(self, *a):
        pass


def test_no_key_and_no_provider_message_leaves_the_check():
    """The real model client against a loopback stand-in of the listing (task-0171, task-0188). The listing
    is read first with NO_KEY. A Mistral-shaped listing, which refuses it, is then read with the key:
    accepted for the key, refused (401, 403) for another; a 404 to both reads unchecked. An OpenRouter- or
    Ollama-shaped listing, which answers any bearer, reads unchecked after the first request, the key never
    sent. A closed port is unreachable. The key appears in no verdict, nor does the provider's message."""
    try:
        import openai  # noqa: F401
    except ModuleNotFoundError:
        skip("openai", "the openai library is not installed; the probe is the model client's own listing")
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Listing)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    base = f"http://127.0.0.1:{httpd.server_address[1]}/v1"
    first = {"path": "/v1/models", "auth": "Bearer " + key_check.NO_KEY}
    keyed = {"path": "/v1/models", "auth": "Bearer " + FAKE}
    try:
        # Mistral-shaped: no key refused, the key accepted, another key refused; then a refusal or no listing at all
        for keyed_to, status, key, state, want in ((FAKE, 401, FAKE, "accepted", 200), (FAKE, 401, "sk-another-0188-WXYZ", "refused", 401),
                                                     (None, 403, FAKE, "refused", 403), (None, 404, FAKE, "unchecked", 404)):
            _Listing.keyed, _Listing.status, _Listing.ids, _Listing.seen = keyed_to, status, ("mistral-medium-3-5",), []
            got = key_check.probe(base, key)
            assert got["state"] == state and got["status"] == want and "open" not in got, (status, key[-4:], got)
            assert _Listing.seen == [first, {"path": "/v1/models", "auth": "Bearer " + key}], _Listing.seen
            assert FAKE not in json.dumps(got) and FAKE[-4:] not in json.dumps(got) and "Incorrect" not in json.dumps(got), got
            if state == "accepted":
                assert got["models"] == ["mistral-medium-3-5"]
        # OpenRouter- and Ollama-shaped: any bearer listed, so the listing says nothing of the key, which is never sent
        for ids in (("openai/gpt-5.5", "mistralai/mistral-large-4-0"), ("qwen3.5:2b", "ministral-3:3b")):
            _Listing.keyed, _Listing.status, _Listing.ids, _Listing.seen = None, 200, ids, []
            got = key_check.probe(base, FAKE)
            assert got == {"state": "unchecked", "status": 200, "models": list(ids), "open": True}, got
            assert _Listing.seen == [first] and keyed not in _Listing.seen, _Listing.seen
    finally:
        _Listing.keyed, _Listing.status, _Listing.ids = None, 200, ("gpt-5.5",)
        httpd.shutdown()
        httpd.server_close()
    got = key_check.probe(base, FAKE)   # the port is closed now
    assert got == {"state": "unreachable", "status": None, "models": None}, got
