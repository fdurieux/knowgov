"""The gate and the three-valued answer as a read-only MCP server (task-0056).

    python harness/mcp_server.py                      # stdio, for an agent that starts the server itself
    python harness/mcp_server.py --http [--host H] [--port P]   # Streamable HTTP at http://H:P/mcp

The question an agent asks is "may I build on this?". Three tools answer it, all read-only:

    store_status          what the store holds: the subject, the scenario loaded, the tasks and the
                          keys the subject asks the three-valued question of
    gate_verdict          the gate's report for a task, or for a key set of the agent's own, exactly
                          as ``gate_cli.py --no-load -f json`` prints it for the same store
    three_valued_answer   asserted, documented absent or unknown for one key, with each statement's
                          provenance: its source document and fragments, who made it, its
                          verifications, approvals and gaps

The server never loads, wipes or writes: it reads the store the page or a run left (``KG_STORE``;
for rdflib the Turtle file ``KG_RDFLIB_FILE``, read and never written back), through a view that
refuses every operation of the store port that is not a read. Writes to the record stay pull
requests. A baseline is ``none`` or ``record`` only: a path would let a client read files.

Over HTTP it binds 127.0.0.1 unless ``--host``/``KG_MCP_HOST`` says otherwise; a bind that is not
a loopback address needs ``KG_MCP_TOKEN``, which every request then carries as
``Authorization: Bearer <token>``. A request whose ``Origin`` is not a loopback host is refused, so
a web page in the operator's browser cannot reach the server (DNS rebinding).

Standard library only, like the page and the gate command: MCP's JSON-RPC 2.0 messages, newline
delimited on stdio, one JSON response per POST over HTTP.
"""
from __future__ import annotations

import argparse
import hmac
import ipaddress
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

SERVER = {"name": "knowgov", "title": "knowgov gate (read-only)", "version": "1"}
PROTOCOL_VERSIONS = ["2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05"]   # newest first
DEFAULT_HOST, DEFAULT_PORT = "127.0.0.1", 8765

# The store port's reads this server may call (harness/store.py); anything else raises.
READS = frozenset({"key_evidence", "declared_gaps_for_key", "conflict_gaps", "stale_on_keys", "suspect_derived",
                   "extraction_activities", "assertions_on_key", "census"})

READ_ONLY = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}

INSTRUCTIONS = ("knowgov answers whether an assistant may build on the knowledge a task needs. Call gate_verdict "
                "before generating code or a document from the organisation's knowledge: BLOCKED means do not build, "
                "QUALIFIED means build only with every key below verified stated as an assumption, PROCEED means the "
                "required keys are verified or approved. Call three_valued_answer for one key: 'unknown' is not "
                "'documented_absent'. A status is the repository's; you may not upgrade it. This server only reads.")

TOOLS = [
    {"name": "store_status", "title": "What the store holds",
     "description": "The subject, the scenario the store holds (null when none is loaded), the store kind, the task "
                    "classes with their required keys, and the keys the subject asks the three-valued question of.",
     "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
     "annotations": READ_ONLY},
    {"name": "gate_verdict", "title": "May I build on this?",
     "description": "The gate's verdict (PROCEED, QUALIFIED or BLOCKED), its findings on the severity ladder and the "
                    "blocking keys, for a task class or for a key set of your own, on the scenario the store holds. "
                    "The report is the one `gate_cli.py --no-load -f json` prints; exit_code 1 means do not proceed.",
     "inputSchema": {"type": "object", "additionalProperties": False, "properties": {
         "scenario": {"type": "string", "description": "the scenario you expect the store to hold; refused if it holds another (default: whatever it holds)"},
         "task": {"type": "string", "description": "the task class whose required keys are resolved (default: codegen); with keys, its block levels and bar apply"},
         "keys": {"type": "array", "items": {"type": "string"}, "minItems": 1, "description": "resolve these entity|attribute keys instead of the task's"},
         "fail_on": {"type": "string", "enum": ["blocker", "critical", "major", "minor", "info"], "description": "the severity at or above which exit_code is 1 (default: blocker)"},
         "baseline": {"type": "string", "enum": ["none", "record"], "description": "record: exit_code 1 only on a regression against the subject's record (codegen only)"}}},
     "annotations": READ_ONLY},
    {"name": "three_valued_answer", "title": "Is it asserted, documented absent, or unknown?",
     "description": "For one key: 'asserted' with its values, 'documented_absent' when the documents say there is none, "
                    "or 'unknown' when no statement exists (not the same as absent). Each statement comes with its "
                    "provenance: status, basis, source document, fragments, author, verifications, approvals and gaps.",
     "inputSchema": {"type": "object", "additionalProperties": False, "required": ["key"], "properties": {
         "key": {"type": "string", "description": "an entity|attribute key, as store_status lists them"},
         "scenario": {"type": "string", "description": "the scenario you expect the store to hold (default: whatever it holds)"}}},
     "annotations": READ_ONLY},
]


class ToolError(Exception):
    """A tool could not answer: returned to the client as a result with isError, never a crash."""


class ReadOnlyStore:
    """A view of a store that lets through the port's reads only. An rdflib store opened on a file
    is released without being written back (its ``close`` would serialise the graph)."""

    def __init__(self, inner):
        self._inner = inner
        self.name = inner.name

    def __getattr__(self, attr):
        if attr in READS:
            return getattr(self._inner, attr)
        raise PermissionError(f"the MCP server only reads: {attr} is not a read of the store port")

    def release(self) -> None:
        if self._inner.name == "rdflib":
            self._inner.path = None   # nothing to release in memory; never serialise over the file
        self._inner.close()


def open_read_only(open_store=None) -> ReadOnlyStore:
    from subject import SUBJECT
    if open_store is None:
        from store import open_store
    return ReadOnlyStore(open_store(instance=SUBJECT.id))


def _held(st) -> str | None:
    acts = st.extraction_activities()   # act:extract:<scenario>:<version>, as gate_cli --no-load reads it
    return acts[0].split(":")[2] if acts else None


def _check_scenario(st, scenario: str | None) -> str:
    held = _held(st)
    if held is None:
        raise ToolError("the store holds no scenario; load one through the page or a run first (this server never loads)")
    if scenario and scenario != held:
        raise ToolError(f"the store holds {held}, not {scenario!r}")
    return held


class Tools:
    """The three tools over a store opener; each call opens the store, reads and releases it."""

    def __init__(self, opener=open_read_only):
        self.opener = opener

    def _with_store(self, fn):
        try:
            st = self.opener()
        except Exception as e:  # noqa: BLE001
            raise ToolError(f"the store cannot be opened: {type(e).__name__}: {e}") from e
        try:
            return fn(st)
        except (ToolError, PermissionError):
            raise
        except Exception as e:  # noqa: BLE001
            raise ToolError(f"the store did not answer: {type(e).__name__}: {e}") from e
        finally:
            try:
                st.release()
            except Exception:  # noqa: BLE001
                pass

    def store_status(self, args: dict) -> dict:
        from subject import SUBJECT
        from tasks import TASKS

        def go(st):
            return {"subject": SUBJECT.id, "store": st.name, "scenario": _held(st),
                    "scenarios": list(SUBJECT.order),
                    "tasks": {n: {"keys": t["keys"], "block_levels": sorted(t["block_levels"]),
                                  "max_unverified_share": t["max_unverified_share"]} for n, t in TASKS.items()},
                    "three_valued_keys": list(SUBJECT.three_valued)}
        return self._with_store(go)

    def gate_verdict(self, args: dict) -> dict:
        import gate_cli
        from subject import SUBJECT
        from tasks import TASKS
        task = args.get("task") or "codegen"
        if task not in TASKS:
            raise ToolError(f"{SUBJECT.id}: no task {task!r}; the subject declares {sorted(TASKS) or 'none'}")
        keys = args.get("keys")
        if keys is not None and (not isinstance(keys, list) or not keys or not all(isinstance(k, str) and k for k in keys)):
            raise ToolError("keys must be a non-empty list of entity|attribute strings")
        threshold = args.get("fail_on") or "blocker"
        if threshold not in gate_cli.SEVERITIES:
            raise ToolError(f"fail_on must be one of {gate_cli.SEVERITIES}")
        which = args.get("baseline") or "none"
        if which not in ("none", "record"):
            raise ToolError("baseline must be none or record; a file path is not served")
        if keys is not None and which == "record":
            raise ToolError("the record is a baseline for a task class, not for a key set of your own")
        spec = dict(TASKS[task])
        name = task
        if keys is not None:
            spec["keys"] = list(dict.fromkeys(keys))
            name = "keys"

        def go(st):
            scenario = _check_scenario(st, args.get("scenario"))
            try:
                base = gate_cli._baseline(which, SUBJECT, scenario, task)
            except gate_cli.CannotRun as e:
                raise ToolError(str(e)) from e
            return gate_cli.evaluate(st, subject=SUBJECT.id, scenario=scenario, task=name, spec=spec,
                                     threshold=threshold, baseline=base, loaded=False,
                                     version=gate_cli.held_version(st))
        return self._with_store(go)

    def three_valued_answer(self, args: dict) -> dict:
        from gate import THREE_VALUED_STATUSES, three_valued
        from subject import SUBJECT
        key = args.get("key")
        if not isinstance(key, str) or not key:
            raise ToolError("key is required, an entity|attribute string")

        def go(st):
            scenario = _check_scenario(st, args.get("scenario"))
            ans = three_valued(st, key)
            prov = {r["id"]: r for r in st.key_evidence(key, THREE_VALUED_STATUSES)}
            statements = [prov.get(r["id"], r) for r in ans.get("assertions", [])]
            out = {"subject": SUBJECT.id, "store": st.name, "scenario": scenario, "key": key, "answer": ans["answer"],
                   "statements": statements}
            if "why" in ans:
                out["why"] = ans["why"]
            return out
        return self._with_store(go)


def _result(id_, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def _error(id_, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}


class Server:
    """MCP's JSON-RPC methods; ``handle`` takes one decoded message and returns the response, or
    None for a notification or a response."""

    def __init__(self, tools: Tools | None = None):
        self.tools = tools or Tools()

    def handle(self, msg) -> dict | None:
        if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0":
            return _error(msg.get("id") if isinstance(msg, dict) else None, -32600, "not a JSON-RPC 2.0 message")
        if "method" not in msg:
            return None                      # a response to something we never send
        method, id_ = msg["method"], msg.get("id")
        if "id" not in msg:
            return None                      # a notification: notifications/initialized and the like
        params = msg.get("params") or {}
        if method == "initialize":
            asked = params.get("protocolVersion")
            version = asked if asked in PROTOCOL_VERSIONS else PROTOCOL_VERSIONS[0]
            return _result(id_, {"protocolVersion": version, "capabilities": {"tools": {"listChanged": False}},
                                 "serverInfo": SERVER, "instructions": INSTRUCTIONS})
        if method == "ping":
            return _result(id_, {})
        if method == "tools/list":
            return _result(id_, {"tools": TOOLS})
        if method == "tools/call":
            name, args = params.get("name"), params.get("arguments") or {}
            if name not in {t["name"] for t in TOOLS}:
                return _error(id_, -32602, f"unknown tool {name!r}")
            if not isinstance(args, dict):
                return _error(id_, -32602, "arguments must be an object")
            try:
                data = getattr(self.tools, name)(args)
            except (ToolError, PermissionError) as e:
                return _result(id_, {"content": [{"type": "text", "text": str(e)}], "isError": True})
            return _result(id_, {"content": [{"type": "text", "text": json.dumps(data, indent=1, ensure_ascii=False, default=str)}],
                                 "structuredContent": data, "isError": False})
        return _error(id_, -32601, f"method not found: {method}")

    def handle_text(self, text: str) -> dict | None:
        try:
            msg = json.loads(text)
        except json.JSONDecodeError as e:
            return _error(None, -32700, f"parse error: {e}")
        return self.handle(msg)


def serve_stdio(server: Server, inp=None, out=None) -> None:
    inp, out = inp or sys.stdin, out or sys.stdout
    for line in inp:
        if not line.strip():
            continue
        resp = server.handle_text(line)
        if resp is not None:
            out.write(json.dumps(resp, ensure_ascii=False, default=str) + "\n")
            out.flush()


def is_loopback(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host.strip("[]")).is_loopback
    except ValueError:
        return False


def origin_allowed(origin: str | None) -> bool:
    """No Origin (a non-browser client) or a loopback one; anything else may be a page doing DNS rebinding."""
    if not origin:
        return True
    host = urlsplit(origin).hostname or ""
    return is_loopback(host)


def bind_check(host: str, token: str | None) -> str | None:
    """None when the bind may go ahead, else why it may not."""
    if not is_loopback(host) and not token:
        return f"{host} is not a loopback address: set KG_MCP_TOKEN so every request must carry it"
    return None


def make_handler(server: Server, token: str | None):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
        server_version = "knowgov-mcp/1"

        def log_message(self, fmt, *a):   # stderr only, never stdout
            sys.stderr.write("mcp-http: " + fmt % a + "\n")

        def _send(self, code: int, body: dict | None = None, extra: dict | None = None):
            data = b"" if body is None else json.dumps(body, ensure_ascii=False, default=str).encode("utf-8")
            self.send_response(code)
            if body is not None:
                self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(data)

        def _guard(self) -> bool:
            if urlsplit(self.path).path != "/mcp":
                self._send(404, _error(None, -32600, "the MCP endpoint is /mcp"))
                return False
            if not origin_allowed(self.headers.get("Origin")):
                self._send(403, _error(None, -32600, "a non-loopback Origin is refused"))
                return False
            if token:
                got = self.headers.get("Authorization", "")
                if not (got.startswith("Bearer ") and hmac.compare_digest(got[7:].encode(), token.encode())):
                    self._send(401, _error(None, -32600, "a bearer token is required"), {"WWW-Authenticate": "Bearer"})
                    return False
            return True

        def do_POST(self):
            if not self._guard():
                return
            n = int(self.headers.get("Content-Length") or 0)
            text = self.rfile.read(n).decode("utf-8", "replace")
            resp = server.handle_text(text)
            if resp is None:
                self._send(202)
            else:
                self._send(200, resp)

        def do_GET(self):
            if self._guard():
                self._send(405, None, {"Allow": "POST"})   # no server-initiated stream: nothing is ever pushed

        def do_DELETE(self):
            if self._guard():
                self._send(405, None, {"Allow": "POST"})   # stateless: there is no session to end
    return Handler


def serve_http(server: Server, host: str, port: int, token: str | None) -> ThreadingHTTPServer:
    why = bind_check(host, token)
    if why:
        raise SystemExit(f"mcp_server: refusing to bind: {why}")
    return ThreadingHTTPServer((host.strip("[]"), port), make_handler(server, token))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="mcp_server.py", description="The gate and the three-valued answer as a read-only MCP server.")
    ap.add_argument("--http", action="store_true", help="serve Streamable HTTP at /mcp instead of stdio")
    ap.add_argument("--host", default=os.environ.get("KG_MCP_HOST", DEFAULT_HOST), help=f"HTTP bind address (default: KG_MCP_HOST, else {DEFAULT_HOST})")
    ap.add_argument("--port", type=int, default=int(os.environ.get("KG_MCP_PORT", DEFAULT_PORT)), help=f"HTTP port (default: KG_MCP_PORT, else {DEFAULT_PORT})")
    args = ap.parse_args(argv)
    server = Server()
    if not args.http:
        serve_stdio(server)
        return 0
    token = os.environ.get("KG_MCP_TOKEN") or None
    why = bind_check(args.host, token)
    if why:
        print(f"mcp_server: refusing to bind: {why}", file=sys.stderr)
        return 2
    httpd = serve_http(server, args.host, args.port, token)
    print(f"mcp_server: http://{args.host}:{httpd.server_address[1]}/mcp (read-only{', bearer token required' if token else ''})", file=sys.stderr)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
