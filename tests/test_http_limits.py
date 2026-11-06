"""Task-0141.04 (H2): bounded HTTP input, connections and admitted work, on a disposable loopback page
and MCP server with small injected limits (LIMIT-01..LIMIT-07 of the review's plan). Raw sockets, so a
test sends exactly the framing it means; every wait is bounded, and a deadline is measured on the
monotonic clock against the injected limit plus a tolerance."""
from __future__ import annotations

import contextlib
import json
import os
import socket
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "demo" / "app")]
import http_boundary as hb  # noqa: E402

SMALL = hb.Limits(max_body=1024, read_timeout=1.5, idle_timeout=1.0, max_connections=3)
TOLERANCE = 2.0   # seconds over a deadline a busy runner may take to close


def _wait(cond, timeout=10.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if cond():
            return True
        time.sleep(0.02)
    return cond()


@contextlib.contextmanager
def _env(**kw):
    keep = {k: os.environ.get(k) for k in kw}
    os.environ.update({k: v for k, v in kw.items() if v is not None})
    for k, v in kw.items():
        if v is None:
            os.environ.pop(k, None)
    try:
        yield
    finally:
        for k, v in keep.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)


class Counting(hb.BoundedServer):
    """The bounded server, counting every connection it has taken from the listen backlog, admitted
    or refused, so a test can wait until the server has seen what it sent: ``active() == 0`` is also
    true before a connection is accepted at all (the race that made LIMIT-06 flaky under load)."""

    def __init__(self, *a, **k):
        self.accepted = 0
        self._count = threading.Lock()
        super().__init__(*a, **k)

    def process_request(self, request, client_address):
        with self._count:
            self.accepted += 1
        super().process_request(request, client_address)


@contextlib.contextmanager
def _page(limits=SMALL, start=None):
    import server
    calls, log = {"start": 0}, []

    class Quiet(server.Handler):
        def log_message(self, fmt, *args):
            log.append(fmt % args)

    class Runner:
        current = None

        def start(self, scenario, mode, n, **k):
            calls["start"] += 1
            if start:
                return start(scenario, mode, n)
            return {"status": "started", "n": n}

        def describe(self):
            return None
    keep = server.RUNNER
    with _env(KG_BIND=None, KG_PAGE_LISTEN=None, KG_PAGE_TOKEN=None, KG_PAGE_AUTHORITIES=None, KG_PAGE_ORIGINS=None,
              KG_PUBLIC_PORT=None, KG_DEMO_HOST=None, KG_PAGE_MAX_RUNS=None):
        server.RUNNER = Runner()
        httpd = Counting(("127.0.0.1", 0), Quiet, limits)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        try:
            yield httpd, calls, log
        finally:
            httpd.shutdown()
            httpd.server_close()
            server.RUNNER = keep


@contextlib.contextmanager
def _mcp(limits=SMALL):
    import mcp_server
    calls = []

    class Stub:
        def handle_http(self, text, headers):
            calls.append(text)
            try:
                json.loads(text)
            except ValueError:
                return 400, {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
            return 200, {"jsonrpc": "2.0", "id": 1, "result": {}}
    with _env(KG_MCP_AUTHORITIES=None, KG_MCP_ORIGINS=None, KG_MCP_MAX_BODY=str(limits.max_body),
              KG_MCP_READ_TIMEOUT=str(limits.read_timeout), KG_MCP_IDLE_TIMEOUT=str(limits.idle_timeout),
              KG_MCP_MAX_CONNECTIONS=str(limits.max_connections)):
        httpd = mcp_server.serve_http(Stub(), "127.0.0.1", 0, None)
        httpd.RequestHandlerClass.log_message = lambda self, *a: None
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        try:
            yield httpd, calls
        finally:
            httpd.shutdown()
            httpd.server_close()


def _send(port: int, raw: bytes, *, read=True, timeout=10.0) -> tuple[int | None, bytes]:
    s = socket.create_connection(("127.0.0.1", port), timeout=timeout)
    try:
        s.sendall(raw)
        if not read:
            return None, b""
        data = b""
        while True:
            try:
                chunk = s.recv(65536)
            except (ConnectionResetError, socket.timeout):
                break
            if not chunk:
                break
            data += chunk
        status = int(data.split(b" ", 2)[1]) if data.startswith(b"HTTP/") else None
        return status, data
    finally:
        s.close()


def _post(port: int, path: str, body: bytes, extra: bytes = b"", length: bytes | None = None) -> bytes:
    cl = b"Content-Length: " + (length if length is not None else str(len(body)).encode()) + b"\r\n"
    return (b"POST " + path.encode() + b" HTTP/1.1\r\nHost: 127.0.0.1:" + str(port).encode() + b"\r\n"
            b"Content-Type: application/json\r\nConnection: close\r\n" + cl + extra + b"\r\n" + body)


def test_limit_01_framing_is_checked_before_a_byte_of_the_body_is_read():
    with _page() as (httpd, calls, _):
        port = httpd.server_address[1]
        for length, extra, want in ((b"-1", b"", 400), (b"abc", b"", 400), (b"1e3", b"", 400), (b"5", b"Content-Length: 6\r\n", 400),
                                    (str(10 ** 9).encode(), b"", 413), (b"2000", b"", 413)):
            t0 = time.monotonic()
            got, _ = _send(port, _post(port, "/api/run", b"{}", extra, length))
            assert got == want and time.monotonic() - t0 < TOLERANCE, (length, extra, got)
        raw = (b"POST /api/run HTTP/1.1\r\nHost: 127.0.0.1:" + str(port).encode() + b"\r\nTransfer-Encoding: chunked\r\n"
               b"Connection: close\r\n\r\n2\r\n{}\r\n0\r\n\r\n")
        assert _send(port, raw)[0] == 411
        assert _send(port, _post(port, "/api/run", b"{}", b"Content-Encoding: gzip\r\n"))[0] == 415
        assert _send(port, _post(port, "/api/run", b"{}").replace(b"application/json", b"text/plain"))[0] == 415
        assert calls["start"] == 0
    with _mcp() as (httpd, calls):
        port = httpd.server_address[1]
        for length, want in ((b"-1", 400), (b"x", 400), (str(10 ** 9).encode(), 413)):
            assert _send(port, _post(port, "/mcp", b"{}", b"", length))[0] == want, length
        no_length = b"POST /mcp HTTP/1.1\r\nHost: 127.0.0.1:" + str(port).encode() + b"\r\nConnection: close\r\n\r\n"
        assert _send(port, no_length)[0] == 411
        assert calls == []


def test_limit_02_a_body_that_is_not_a_json_object_is_a_controlled_400():
    with _page() as (httpd, calls, log):
        port = httpd.server_address[1]
        for body in (b"null", b"[]", b"3", b'"x"', b"\xff\xfe{}", b"{not json", b'{"scenario": 5}', b'{"subject": 7}',
                     b'{"scenario": "S1", "mode": "deterministic", "row": 1}'):
            got, data = _send(port, _post(port, "/api/run", body))
            assert got == 400 and b"Traceback" not in data, (body, got, data[-200:])
        assert calls["start"] == 0 and not any("Traceback" in x for x in log)
    with _mcp() as (httpd, calls):
        port = httpd.server_address[1]
        got, data = _send(port, _post(port, "/mcp", b"{not json"))
        assert got == 400 and b"-32700" in data, data   # JSON-RPC's own parse error, the protocol's answer


def test_limit_03_n_is_an_integer_from_1_to_the_maximum_and_never_coerced():
    with _page() as (httpd, calls, _):
        port = httpd.server_address[1]
        for n in (0, -1, True, 2.5, "3", 6, 10 ** 6, None):
            body = json.dumps({"scenario": "S1", "mode": "deterministic", "n": n}).encode()
            got, data = _send(port, _post(port, "/api/run", body))
            assert got == 400 and b"n must be an integer from 1 to 5" in data, (n, got, data[-200:])
        assert calls["start"] == 0
        got, data = _send(port, _post(port, "/api/run", json.dumps({"scenario": "S1", "mode": "deterministic", "n": 5}).encode()))
        assert got == 202 and b'"n": 5' in data and calls["start"] == 1
        with _env(KG_PAGE_MAX_RUNS="2"):
            body = json.dumps({"scenario": "S1", "mode": "deterministic", "n": 3}).encode()
            assert _send(port, _post(port, "/api/run", body))[0] == 400


def test_limit_04_a_body_that_never_completes_or_trickles_is_cut_at_the_absolute_deadline():
    with _page() as (httpd, calls, _):
        port = httpd.server_address[1]
        head = _post(port, "/api/run", b"", length=b"100")   # announces 100 bytes
        s = socket.create_connection(("127.0.0.1", port), timeout=10)
        t0 = time.monotonic()
        s.sendall(head + b'{"sce')
        data = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
        s.close()
        took = time.monotonic() - t0
        assert took < SMALL.read_timeout + TOLERANCE, took
        s = socket.create_connection(("127.0.0.1", port), timeout=10)
        t0 = time.monotonic()
        s.sendall(b"POST /api/run HTTP/1.1\r\nHost: 127.0.0.1:" + str(port).encode() + b"\r\n")
        closed = False
        for _ in range(40):   # one header byte every 0.2 s, inside the idle timeout, never finishing
            try:
                s.sendall(b"X")
                s.settimeout(0.2)
                if s.recv(1) == b"":
                    closed = True
                    break
            except socket.timeout:
                continue
            except OSError:
                closed = True
                break
        took = time.monotonic() - t0
        s.close()
        assert closed and took < SMALL.read_timeout + TOLERANCE, (closed, took)
        assert calls["start"] == 0
        assert _wait(lambda: httpd.active() == 0), httpd.active()


def test_limit_05_connections_over_capacity_get_503_without_a_thread_and_recover():
    with _page() as (httpd, calls, _):
        port = httpd.server_address[1]
        before = threading.active_count()
        held = [socket.create_connection(("127.0.0.1", port), timeout=10) for _ in range(SMALL.max_connections)]
        for s in held:
            s.sendall(b"GET /health HTTP/1.1\r\n")   # admitted, and holding its slot until the deadline or close
        assert _wait(lambda: httpd.active() == SMALL.max_connections), httpd.active()
        for _ in range(5):
            got, data = _send(port, b"GET /health HTTP/1.1\r\nHost: 127.0.0.1:" + str(port).encode() + b"\r\nConnection: close\r\n\r\n")
            assert got == 503 and b"Retry-After" in data, (got, data)
        # an admitted connection runs its handler and its arrival deadline's timer: two threads, never more, whatever the 503s
        assert threading.active_count() <= before + 2 * SMALL.max_connections, (before, threading.active_count())
        for s in held:
            s.close()
        assert _wait(lambda: httpd.active() == 0), httpd.active()
        got, _ = _send(port, b"GET /health HTTP/1.1\r\nHost: 127.0.0.1:" + str(port).encode() + b"\r\nConnection: close\r\n\r\n")
        assert got == 200


def test_limit_06_a_disconnect_or_a_failing_operation_leaks_nothing():
    def boom(*a):
        raise RuntimeError("a run is already in progress")
    with _page(start=boom) as (httpd, calls, log):
        port = httpd.server_address[1]
        sent = SMALL.max_connections + 2
        for _ in range(sent):   # each leaves mid-body; a leaked slot would fill the server
            _send(port, _post(port, "/api/run", b'{"sc', length=b"40"), read=False)
        # every one taken from the backlog first: before that, active() is 0 with nothing yet served
        assert _wait(lambda: httpd.accepted >= sent, SMALL.read_timeout + TOLERANCE + 5), (httpd.accepted, sent)
        assert _wait(lambda: httpd.active() == 0, SMALL.read_timeout + TOLERANCE + 5), httpd.active()
        got, data = _send(port, _post(port, "/api/run", json.dumps({"scenario": "S1", "mode": "deterministic"}).encode()))
        assert got == 409 and b"Traceback" not in data and calls["start"] == 1
        assert not any("Traceback" in x for x in log)
        assert _wait(lambda: httpd.active() == 0), httpd.active()


def test_limit_07_the_ordinary_requests_answer_as_before():
    import register_view
    with _page() as (httpd, calls, _):
        port = httpd.server_address[1]
        got, data = _send(port, _post(port, "/api/run", json.dumps({"scenario": "S1", "mode": "deterministic", "n": 1}).encode()))
        assert got == 202 and calls["start"] == 1
        got, _ = _send(port, b"GET /api/subjects HTTP/1.1\r\nHost: 127.0.0.1:" + str(port).encode() + b"\r\nConnection: close\r\n\r\n")
        assert got == 200
        guide = f"/api/register/impact/{register_view.impact_default()}/guide/rows".encode()
        with _env(KG_STORE=None):
            got, data = _send(port, b"GET " + guide + b" HTTP/1.1\r\nHost: 127.0.0.1:" + str(port).encode()
                              + b"\r\nOrigin: http://localhost:7474\r\nConnection: close\r\n\r\n")
        assert got == 200 and b"runnable" in data
    with _mcp() as (httpd, calls):
        port = httpd.server_address[1]
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}).encode()
        assert _send(port, _post(port, "/mcp", body))[0] == 200 and len(calls) == 1


def test_the_limits_are_finite_configurable_and_refuse_nonsense():
    import mcp_server
    import server
    assert server.page_limits() == hb.Limits(65536, 10.0, 5.0, 32)
    assert mcp_server.mcp_limits().max_body == 4 << 20
    with _env(KG_PAGE_MAX_BODY="0"):
        try:
            server.page_limits()
        except ValueError as e:
            assert "KG_PAGE_MAX_BODY" in str(e)
        else:
            raise AssertionError("a zero limit accepted")
    with _env(KG_MCP_READ_TIMEOUT="soon"):
        try:
            mcp_server.mcp_limits()
        except ValueError as e:
            assert "KG_MCP_READ_TIMEOUT" in str(e)
        else:
            raise AssertionError("a non-number accepted")


def test_limit_04_a_request_cut_at_its_deadline_is_never_dispatched():
    """Found under load: headers cut by the deadline's shutdown parsed as a request without a body and
    started a run. A request the deadline cut is refused, never handed to its route."""
    with _page() as (httpd, calls, _):
        port = httpd.server_address[1]
        for head in (b"POST /api/run HTTP/1.1\r\nHost: 127.0.0.1:" + str(port).encode() + b"\r\nContent-Type: application/json\r\n",
                     b"POST /api/run HTTP/1.1\r\nHost: 127.0.0.1:" + str(port).encode() + b"\r\nContent-Length: 50\r\n\r\n{}"):
            s = socket.create_connection(("127.0.0.1", port), timeout=10)
            s.sendall(head)   # no blank line, or a body short of its length: the deadline cuts it
            data = b""
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                data += chunk
            s.close()
            assert b" 202 " not in data and calls["start"] == 0, (head[-30:], data[:80], calls)
