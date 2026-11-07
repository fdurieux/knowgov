"""Task-0141.03 (H1): the request's authority and the browser's origin, each checked on its own, on
genuine HTTP requests to both servers, the operation behind each route counted so a refusal is seen
to reach nothing (HTTP-01..HTTP-08 of the review's plan). Header-policy tests: they do not claim to
reproduce a full browser DNS-rebinding exploit, only that a request naming a foreign authority, or
coming from a foreign origin, is refused before anything runs."""
from __future__ import annotations

import contextlib
import http.client
import json
import os
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "demo" / "app")]
import http_boundary as hb  # noqa: E402

PAGE_ENV = ("KG_BIND", "KG_PAGE_LISTEN", "KG_PAGE_TOKEN", "KG_PAGE_AUTHORITIES", "KG_PAGE_ORIGINS", "KG_PUBLIC_PORT",
            "KG_DEMO_HOST", "KG_BROWSER_URL", "KG_STORE")
MCP_ENV = ("KG_MCP_AUTHORITIES", "KG_MCP_ORIGINS")
SECRET = "h1-test-token-not-a-credential"


@contextlib.contextmanager
def _env(names, **kw):
    keep = {k: os.environ.get(k) for k in names}
    for k in names:
        os.environ.pop(k, None)
    os.environ.update({k: v for k, v in kw.items() if v is not None})
    try:
        yield
    finally:
        for k, v in keep.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _raw(port: int, method: str, path: str, headers: list[tuple[str, str]], body: bytes | None = None):
    """One request with exactly the headers given (Host included, repeated if listed twice)."""
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        c.putrequest(method, path, skip_host=True, skip_accept_encoding=True)
        for k, v in headers:
            c.putheader(k, v)
        if body is not None:
            c.putheader("Content-Type", "application/json")
            c.putheader("Content-Length", str(len(body)))
        c.endheaders(body)
        r = c.getresponse()
        return r.status, r.read().decode("utf-8", "replace"), dict(r.getheaders())
    finally:
        c.close()


@contextlib.contextmanager
def _page(**env):
    """The page on a loopback ephemeral port, its run and its runs listing counted, its log kept."""
    import server
    log, calls = [], {"start": 0, "list_runs": 0}

    class Quiet(server.Handler):
        def log_message(self, fmt, *args):
            log.append(fmt % args)

    class Runner:
        current = None

        def start(self, *a, **k):
            calls["start"] += 1
            return {"status": "started"}

        def describe(self):
            return None

    def list_runs():
        calls["list_runs"] += 1
        return []
    keep = server.RUNNER, server.list_runs
    with _env(PAGE_ENV, **env):
        server.RUNNER, server.list_runs = Runner(), list_runs
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), Quiet)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        try:
            yield httpd.server_address[1], calls, log
        finally:
            httpd.shutdown()
            httpd.server_close()
            server.RUNNER, server.list_runs = keep


class _CountingServer:
    def __init__(self):
        self.calls = 0

    def handle_http(self, text, headers):
        self.calls += 1
        return 200, {"jsonrpc": "2.0", "id": 1, "result": {}}


@contextlib.contextmanager
def _mcp(token=None, **env):
    import mcp_server
    with _env(MCP_ENV, **env):
        stub = _CountingServer()
        httpd = mcp_server.serve_http(stub, "127.0.0.1", 0, token)
        log = []
        httpd.RequestHandlerClass.log_message = lambda self, fmt, *a: log.append(fmt % a)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        try:
            yield httpd.server_address[1], stub, log
        finally:
            httpd.shutdown()
            httpd.server_close()


RUN = json.dumps({"scenario": "S1", "mode": "deterministic"}).encode()
INIT = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}).encode()


def test_http_01_a_foreign_host_with_a_matching_foreign_origin_changes_nothing():
    """The reviewed guard compared Origin with the request's own Host, so a rebound name sending both
    as its own passed; now the Host is checked against what the server answers for."""
    with _page() as (port, calls, _):
        for method, path, body in (("POST", "/api/run", RUN), ("GET", "/api/runs", None)):
            code, text, _ = _raw(port, method, path, [("Host", f"evil.example:{port}"), ("Origin", f"http://evil.example:{port}")], body)
            assert code == 421, (method, path, code, text)
        assert calls == {"start": 0, "list_runs": 0}, calls
    with _mcp() as (port, stub, _):
        code, _, _ = _raw(port, "POST", "/mcp", [("Host", f"evil.example:{port}"), ("Origin", f"http://evil.example:{port}")], INIT)
        assert code == 421 and stub.calls == 0


def test_http_02_host_and_origin_are_each_checked_on_their_own():
    with _page() as (port, calls, _):
        own = f"127.0.0.1:{port}"
        assert _raw(port, "POST", "/api/run", [("Host", own), ("Origin", "http://evil.example")], RUN)[0] == 403
        assert _raw(port, "POST", "/api/run", [("Host", f"evil.example:{port}"), ("Origin", f"http://{own}")], RUN)[0] == 421
        assert calls["start"] == 0
        assert _raw(port, "POST", "/api/run", [("Host", own), ("Origin", f"http://{own}")], RUN)[0] == 202 and calls["start"] == 1
    with _mcp() as (port, stub, _):
        own = f"127.0.0.1:{port}"
        assert _raw(port, "POST", "/mcp", [("Host", own), ("Origin", "http://evil.example")], INIT)[0] == 403
        assert _raw(port, "POST", "/mcp", [("Host", f"evil.example:{port}"), ("Origin", f"http://{own}")], INIT)[0] == 421
        assert stub.calls == 0


def test_http_03_scheme_port_opaque_malformed_duplicate_and_deceptive_values_are_refused():
    with _page() as (port, calls, _):
        own = f"localhost:{port}"
        cases = [
            ([("Host", own), ("Origin", f"https://{own}")], 403),            # scheme
            ([("Host", own), ("Origin", f"http://localhost:{port + 1}")], 403),   # another port on this machine
            ([("Host", own), ("Origin", "null")], 403),                        # opaque
            ([("Host", own), ("Origin", f"http://{own}/path")], 403),
            ([("Host", f"localhost:{port + 1}")], 421),
            ([("Host", f"localhost.evil.example:{port}")], 421),               # deceptive suffix
            ([("Host", f"user@localhost:{port}")], 400),                       # userinfo
            ([("Host", f"localhost:{port}, evil.example")], 400),              # a list
            ([("Host", f"[::1:{port}")], 400),                                 # malformed IPv6
            ([("Host", own), ("Host", f"evil.example:{port}")], 400),          # duplicate
            ([], 400),                                                         # absent
        ]
        for headers, want in cases:
            for method, path, body in (("POST", "/api/run", RUN), ("GET", "/api/runs", None)):
                got = _raw(port, method, path, headers, body)[0]
                assert got == want, (headers, method, got, want)
        assert calls == {"start": 0, "list_runs": 0}, calls


def test_http_04_loopback_names_and_a_configured_proxy_identity_and_nothing_wider():
    with _page() as (port, calls, _):
        for host in (f"localhost:{port}", f"127.0.0.1:{port}", f"[::1]:{port}", f"LOCALHOST:{port}"):
            assert _raw(port, "GET", "/api/runs", [("Host", host)])[0] == 200, host
        assert calls["list_runs"] == 4
    proxy = dict(KG_PAGE_AUTHORITIES="kg.example.org:443", KG_PAGE_ORIGINS="https://kg.example.org")
    with _page(**proxy) as (port, calls, _):
        ok = [("Host", "kg.example.org:443"), ("Origin", "https://kg.example.org")]
        assert _raw(port, "POST", "/api/run", ok, RUN)[0] == 202 and calls["start"] == 1
        for bad in ([("Host", "kg.example.org:8443")], [("Host", "a.kg.example.org:443")], [("Host", "kg.example.org")],
                    [("Host", "kg.example.org:443"), ("Origin", "http://kg.example.org")],
                    [("Host", "kg.example.org:443"), ("Origin", "https://a.kg.example.org")]):
            assert _raw(port, "POST", "/api/run", bad, RUN)[0] in (403, 421), bad
        assert calls["start"] == 1
    with _page(KG_PUBLIC_PORT="18080", KG_DEMO_HOST="demo.test") as (port, calls, _):   # compose's published port and host
        for host in ("localhost:18080", "demo.test:18080", f"localhost:{port}"):
            assert _raw(port, "GET", "/api/runs", [("Host", host)])[0] == 200, host
        assert _raw(port, "GET", "/api/runs", [("Host", "demo.test:8080")])[0] == 421


def test_http_05_the_token_and_the_authority_are_independent_and_the_token_never_echoed():
    with _page(KG_PAGE_TOKEN=SECRET) as (port, calls, log):
        own = f"127.0.0.1:{port}"
        for auth in (None, "Bearer wrong", SECRET):
            headers = [("Host", own)] + ([("Authorization", auth)] if auth else [])
            code, text, _ = _raw(port, "POST", "/api/run", headers, RUN)
            assert code == 401 and SECRET not in text, (auth, code)
        assert calls["start"] == 0
        assert _raw(port, "POST", "/api/run", [("Host", own), ("Authorization", f"Bearer {SECRET}")], RUN)[0] == 202
        code, text, _ = _raw(port, "POST", "/api/run", [("Host", f"evil.example:{port}"), ("Authorization", f"Bearer {SECRET}")], RUN)
        assert code == 421 and SECRET not in text and calls["start"] == 1
        assert not any(SECRET in line for line in log), "the token reached the log"
    with _mcp(token=SECRET) as (port, stub, log):
        own = f"127.0.0.1:{port}"
        assert _raw(port, "POST", "/mcp", [("Host", own)], INIT)[0] == 401
        assert _raw(port, "POST", "/mcp", [("Host", own), ("Authorization", f"Bearer {SECRET}")], INIT)[0] == 200
        code, text, _ = _raw(port, "POST", "/mcp", [("Host", f"evil.example:{port}"), ("Authorization", f"Bearer {SECRET}")], INIT)
        assert code == 421 and SECRET not in text and stub.calls == 1
        assert not any(SECRET in line for line in log)


def test_http_06_forwarded_headers_never_stand_in_for_the_host():
    spoof = [("X-Forwarded-Host", "kg.example.org"), ("Forwarded", "host=kg.example.org;proto=https"), ("X-Forwarded-Proto", "https")]
    with _page() as (port, calls, _):   # direct: a foreign Host is refused whatever the forwarded headers claim
        assert _raw(port, "POST", "/api/run", [("Host", f"evil.example:{port}")] + spoof, RUN)[0] == 421
        assert _raw(port, "POST", "/api/run", [("Host", f"127.0.0.1:{port}"), ("X-Forwarded-Host", "evil.example")], RUN)[0] == 202
    with _page(KG_PAGE_AUTHORITIES="kg.example.org:443", KG_PAGE_ORIGINS="https://kg.example.org") as (port, calls, _):
        # behind the configured proxy: the proxy's Host counts, a forwarded claim alone does not
        assert _raw(port, "POST", "/api/run", [("Host", f"evil.example:{port}")] + spoof, RUN)[0] == 421
        assert _raw(port, "POST", "/api/run", [("Host", "kg.example.org:443"), ("X-Forwarded-Host", "evil.example")], RUN)[0] == 202
        assert calls["start"] == 1
    with _mcp() as (port, stub, _):
        assert _raw(port, "POST", "/mcp", [("Host", f"evil.example:{port}")] + spoof, INIT)[0] == 421 and stub.calls == 0


def test_http_07_every_route_family_of_both_servers_is_behind_the_boundary():
    import server
    src = (ROOT / "demo" / "app" / "server.py").read_text(encoding="utf-8")
    for verb in ("do_GET", "do_POST", "do_OPTIONS"):
        body = src.split(f"def {verb}(self)", 1)[1].split("\n    def ", 1)[0]
        first = [ln.strip() for ln in body.splitlines() if ln.strip() and not ln.strip().startswith(("#", '"""', "cache", "\"\"\""))]
        assert any("self._boundary()" in ln for ln in first[:3]), (verb, first[:3])   # among the first things each does
    with _page() as (port, calls, _):
        for method, path in (("GET", "/health"), ("GET", "/"), ("GET", "/api/subjects"), ("OPTIONS", "/api/register/impact/X/guide/rows"),
                             ("POST", "/api/register/project")):
            assert _raw(port, method, path, [("Host", f"evil.example:{port}")], b"{}" if method == "POST" else None)[0] == 421, path
    with _mcp() as (port, stub, _):
        for method in ("GET", "DELETE", "POST"):
            assert _raw(port, method, "/mcp", [("Host", f"evil.example:{port}")], INIT if method == "POST" else None)[0] == 421
        assert stub.calls == 0
    assert server.page_policy(8080).describe()["authorities"]


def test_http_08_the_browser_guide_and_a_non_browser_client_keep_working():
    import register_view
    start = register_view.impact_default()
    with _page(KG_BROWSER_URL="http://localhost:7474") as (port, calls, _):
        own = f"localhost:{port}"
        path = f"/api/register/impact/{start}/guide/rows"
        code, _, hdrs = _raw(port, "OPTIONS", path, [("Host", own), ("Origin", "http://localhost:7474"),
                                                     ("Access-Control-Request-Method", "GET")])
        assert code == 204 and hdrs.get("Access-Control-Allow-Origin") == "*", code
        code, text, _ = _raw(port, "GET", path, [("Host", own), ("Origin", "http://localhost:7474")])
        assert code == 200 and "runnable" in text
        assert _raw(port, "GET", path, [("Host", own), ("Origin", "http://evil.example")])[0] == 403
        assert _raw(port, "POST", "/api/run", [("Host", own), ("Origin", "http://localhost:7474")], RUN)[0] == 403, \
            "the Browser's origin reads guides only"
        assert _raw(port, "GET", "/api/runs", [("Host", own)])[0] == 200   # a client that sends no Origin
    with _mcp() as (port, stub, _):
        assert _raw(port, "POST", "/mcp", [("Host", f"127.0.0.1:{port}")], INIT)[0] == 200 and stub.calls == 1


def test_the_policy_is_built_from_configuration_and_never_names_a_wildcard():
    p = hb.build("0.0.0.0", [8080, 18080])
    assert ("0.0.0.0", 8080) not in p.authorities and ("localhost", 18080) in p.authorities
    p = hb.build("192.0.2.7", [8765], authorities="mcp.example.org:443", origins="https://mcp.example.org")
    assert p.authorities == {("192.0.2.7", 8765), ("mcp.example.org", 443)}
    assert ("https", "mcp.example.org", 443) in p.origins and ("http", "192.0.2.7", 8765) in p.origins
    for bad in ("*", "evil.example:0", "a b", "http://x"):
        try:
            hb.build("127.0.0.1", [1], authorities=bad)
        except hb.BadAuthority:
            continue
        raise AssertionError(f"{bad!r} accepted as an authority")


def _smuggle(port: int, method: str, path: str, outer: list[tuple[str, str]], inner: bytes) -> list[bytes]:
    """A refused request whose body is a second complete request, on one keep-alive socket; every HTTP
    status line the server writes back before it closes (task-0196, doc-0030 M3)."""
    import socket
    head = f"{method} {path} HTTP/1.1\r\n" + "".join(f"{k}: {v}\r\n" for k, v in outer)
    head += f"Connection: keep-alive\r\nContent-Type: application/json\r\nContent-Length: {len(inner)}\r\n\r\n"
    s = socket.create_connection(("127.0.0.1", port), timeout=10)
    try:
        s.sendall(head.encode() + inner)
        got = b""
        while True:
            try:
                chunk = s.recv(65536)
            except (ConnectionResetError, TimeoutError, socket.timeout):
                break
            if not chunk:
                break
            got += chunk
    finally:
        s.close()
    import re   # a second response follows the first's body directly, with no line break between them
    return re.findall(rb"HTTP/1\.[01] \d{3}", got)


def test_m3_a_refusal_closes_the_connection_so_its_body_never_runs_as_a_second_request():
    """doc-0030 M3: the reader answered a refusal (404, 421, 403, 401) without reading the body or closing,
    so on keep-alive the body ran as a request of its own with a forged Host (probe: 421, then a 200
    tools/call). Every refusal now goes through http_boundary's refuse, shared with the page."""
    with _mcp(token=SECRET) as (port, stub, _):
        good = [("Host", f"127.0.0.1:{port}"), ("Authorization", f"Bearer {SECRET}")]
        inner_body = INIT
        inner = (f"POST /mcp HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nAuthorization: Bearer {SECRET}\r\n"
                 f"Content-Type: application/json\r\nContent-Length: {len(inner_body)}\r\n\r\n").encode() + inner_body
        for outer, path, want in ((
                [("Host", f"evil.example:{port}"), ("Authorization", f"Bearer {SECRET}")], "/mcp", b"421"),
                ([("Host", f"127.0.0.1:{port}"), ("Origin", "http://evil.example"), ("Authorization", f"Bearer {SECRET}")], "/mcp", b"403"),
                ([("Host", f"127.0.0.1:{port}")], "/mcp", b"401"),
                (good, "/elsewhere", b"404")):
            lines = _smuggle(port, "POST", path, outer, inner)
            assert len(lines) == 1 and want in lines[0], (path, outer, lines)
        assert stub.calls == 0, "the smuggled request reached the server"
        # the same socket's second request is still answered when the first is admitted: keep-alive works
        lines = _smuggle(port, "POST", "/mcp", good, INIT + b"")
        assert lines and b"200" in lines[0] and stub.calls == 1, lines
    with _page() as (port, calls, _):
        inner = f"GET /api/runs HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\n\r\n".encode()
        lines = _smuggle(port, "GET", "/api/runs", [("Host", f"evil.example:{port}")], inner)
        assert len(lines) == 1 and b"421" in lines[0], lines
        lines = _smuggle(port, "POST", "/api/run", [("Host", f"evil.example:{port}")], inner)
        assert len(lines) == 1 and b"421" in lines[0], lines
        assert calls == {"start": 0, "list_runs": 0}, calls
