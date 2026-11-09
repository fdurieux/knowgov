"""The HTTP trust boundary both servers share (task-0141.03, H1): which authority a request may name
and which browser origin may send it, each checked on its own, from configuration and the listener,
never from the request. Standard library only; nothing here touches a store.

A request is let through when
- it carries exactly one Host header, well formed (a DNS name or an IP literal, IPv6 in brackets, an
  optional port; no userinfo, path, list or suffix), whose host and effective port are one of the
  policy's authorities; else 400 (malformed) or 421 (an authority this server does not answer for);
- and, when it carries an Origin, that origin (scheme, host, effective port) is one of the policy's
  origins for the route; else 403. The opaque origin ``null`` is refused. No Origin is a non-browser
  client: allowed, and authentication, where the server asks for it, still applies.

A bearer token is checked apart from both (the servers do it): an allowed origin never stands in for
the token, and the token never admits a foreign authority. Forwarded headers (Forwarded,
X-Forwarded-Host, X-Forwarded-Proto) are never read: behind a reverse proxy, the proxy passes the
public Host through and the operator lists that authority and its origin, so a client cannot claim
one by sending a header. DNS names are compared as text, never resolved."""
from __future__ import annotations

import ipaddress
import json
import os
import re
import threading
from dataclasses import dataclass, field
from http.server import ThreadingHTTPServer

LOOPBACK_NAMES = ("localhost", "127.0.0.1", "::1")
WILDCARDS = ("0.0.0.0", "::", "")
DEFAULT_PORTS = {"http": 80, "https": 443}
_LABEL = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)$")


class BadAuthority(ValueError):
    """A Host or Origin value that is not one well-formed authority."""


def _host(text: str) -> str:
    """A host as compared: lower case, an IPv6 literal without brackets, a name of DNS labels."""
    if text.startswith("["):
        if not text.endswith("]"):
            raise BadAuthority("an IPv6 literal without its closing bracket")
        try:
            return str(ipaddress.IPv6Address(text[1:-1]))
        except ValueError as e:
            raise BadAuthority(f"not an IPv6 address: {text}") from e
    h = text.lower()
    try:
        return str(ipaddress.IPv4Address(h))
    except ValueError:
        pass
    labels = h.split(".")
    if not h or len(h) > 253 or not all(_LABEL.match(x) for x in labels):
        raise BadAuthority(f"not a host name: {text!r}")
    return h


def parse_authority(value: str, default_port: int) -> tuple[str, int]:
    """``host[:port]`` as a request's Host carries it, to (host, effective port)."""
    if not isinstance(value, str) or not value or value != value.strip() or any(c in value for c in "@/\\?#,; \t"):
        raise BadAuthority(f"not one authority: {value!r}")
    if value.startswith("["):
        end = value.find("]")
        if end < 0:
            raise BadAuthority("an IPv6 literal without its closing bracket")
        host, rest = value[:end + 1], value[end + 1:]
        if rest and not rest.startswith(":"):
            raise BadAuthority(f"text after an IPv6 literal: {value!r}")
        port_text = rest[1:] if rest else None
    else:
        if value.count(":") > 1:
            raise BadAuthority(f"an IPv6 literal must be bracketed: {value!r}")
        host, _, port_text = value.partition(":")
        port_text = port_text if ":" in value else None
    if port_text is None:
        port = default_port
    elif port_text.isdigit() and port_text.isascii() and 0 < int(port_text) < 65536 and not port_text.startswith("0"):
        port = int(port_text)
    else:
        raise BadAuthority(f"not a port: {port_text!r}")
    return _host(host), port


def parse_origin(value: str) -> tuple[str, str, int]:
    """``scheme://host[:port]`` as a browser sends it, to (scheme, host, effective port); ``null`` refused."""
    if not isinstance(value, str) or value == "null" or "://" not in value:
        raise BadAuthority(f"not a web origin: {value!r}")
    scheme, _, rest = value.partition("://")
    scheme = scheme.lower()
    if scheme not in DEFAULT_PORTS or "/" in rest:   # a browser's Origin has no path, not even "/"
        raise BadAuthority(f"not a web origin: {value!r}")
    host, port = parse_authority(rest, DEFAULT_PORTS[scheme])
    return scheme, host, port


def _display(host: str, port: int, scheme: str | None = None) -> str:
    h = f"[{host}]" if ":" in host else host
    return f"{scheme}://{h}:{port}" if scheme else f"{h}:{port}"


def is_loopback(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host.strip("[]")).is_loopback
    except ValueError:
        return False


@dataclass
class Policy:
    """What a server answers for: its authorities, the browser origins that may call it, and per route
    family the extra origins (the Neo4j Browser for the page's guides)."""
    authorities: frozenset
    origins: frozenset
    extra_origins: dict = field(default_factory=dict)

    def describe(self) -> dict:
        return {"authorities": sorted(_display(h, p) for h, p in self.authorities),
                "origins": sorted(_display(h, p, s) for s, h, p in self.origins)}


def build(listen_host: str, ports: list[int], *, authorities: str = "", origins: str = "",
          extra_origins: dict | None = None) -> Policy:
    """The policy from the listener and the configuration, never a request. The loopback names on each
    of ``ports`` (the listener's, and the published one when they differ) when the listener is a
    loopback or wildcard address; the listen host itself when it is a specific address; plus every
    authority in ``authorities`` (comma-separated ``host[:port]``, port 80 when none). The origins are
    ``http://`` each authority, plus every origin in ``origins`` (``https://kg.example.org`` behind a
    TLS proxy). A wildcard bind is never itself an identity."""
    auth: set[tuple[str, int]] = set()
    lh = (listen_host or "").strip("[]")
    for port in dict.fromkeys(p for p in ports if p):
        if lh in WILDCARDS or is_loopback(lh):
            auth.update((_host(f"[{n}]" if ":" in n else n), port) for n in LOOPBACK_NAMES)
        else:
            auth.add((_host(f"[{lh}]" if ":" in lh else lh), port))
    for item in filter(None, (x.strip() for x in authorities.split(","))):
        auth.add(parse_authority(item, 80))
    orig = {("http", h, p) for h, p in auth}
    for item in filter(None, (x.strip() for x in origins.split(","))):
        orig.add(parse_origin(item))
    extra = {k: frozenset(parse_origin(o) for o in v if o) for k, v in (extra_origins or {}).items()}
    return Policy(frozenset(auth), frozenset(orig), extra)


def check(policy: Policy, headers, route: str | None = None) -> tuple[int, str] | None:
    """None when the request may go on, else (status, reason). ``headers`` is an http.client message
    (``get_all``) or a mapping; ``route`` names a route family with extra origins."""
    hosts = headers.get_all("Host") if hasattr(headers, "get_all") else ([headers["Host"]] if "Host" in headers else None)
    if not hosts or len(hosts) != 1:
        return 400, "exactly one Host header is required"
    try:
        host = parse_authority(hosts[0], 80)
    except BadAuthority as e:
        return 400, f"the Host header is malformed: {e}"
    if host not in policy.authorities:
        return 421, f"this server does not answer for {_display(*host)}"
    origins = headers.get_all("Origin") if hasattr(headers, "get_all") else ([headers["Origin"]] if "Origin" in headers else None)
    if origins:
        if len(origins) != 1:
            return 403, "more than one Origin header"
        try:
            origin = parse_origin(origins[0])
        except BadAuthority:
            return 403, f"a request from another web origin ({origins[0][:80]!r}) may not call this server"
        if origin not in policy.origins and origin not in policy.extra_origins.get(route, frozenset()):
            return 403, f"a request from another web origin ({_display(origin[1], origin[2], origin[0])}) may not call this server"
    return None


# ---- H2 (task-0141.04): bounded input, connections and the time a request may take to arrive ----------------


class Refused(Exception):
    """A request refused before it reaches an operation: the status, and a reason safe to show."""

    def __init__(self, status: int, reason: str):
        super().__init__(reason)
        self.status, self.reason = status, reason


RESPONSE_MIN, RESPONSE_MAX = 4 << 10, 1 << 30   # a response cap's bounds: above every refusal's body, at most 1 GiB


def response_cap(var: str, default: int) -> int:
    """A response-size cap in bytes (task-0177): ``var`` from the environment, else ``default``; a value that
    is not an integer from RESPONSE_MIN to RESPONSE_MAX is refused with the variable's name."""
    raw = os.environ.get(var)
    if raw is None or raw == "":
        return default
    try:
        v = int(raw)
    except ValueError:
        raise ValueError(f"{var} must be an int, not {raw!r}") from None
    if not RESPONSE_MIN <= v <= RESPONSE_MAX:
        raise ValueError(f"{var} must be from {RESPONSE_MIN} to {RESPONSE_MAX} bytes, not {raw!r}")
    return v


def over_cap(var: str, size: int, cap: int) -> str:
    """The reason a response over its cap is refused: never truncated, the setting named."""
    return (f"the response ({size} bytes) exceeds {var} ({cap} bytes) and was not sent; nothing is truncated: "
            f"narrow the request or raise {var}")


@dataclass
class Limits:
    """Finite, configurable bounds (env ``<PREFIX>_MAX_BODY``, ``_READ_TIMEOUT``, ``_IDLE_TIMEOUT``,
    ``_MAX_CONNECTIONS``, ``_MAX_RESPONSE``). ``read_timeout`` is absolute: a request's line, headers and
    body must all arrive within it, however the client paces them; ``idle_timeout`` bounds one silent wait
    on the socket. A connection over ``max_connections`` is answered 503 and closed without a thread.
    ``max_response`` caps one response's body (task-0177): a larger one is refused, never truncated."""
    max_body: int
    read_timeout: float
    idle_timeout: float
    max_connections: int
    max_response: int = 16 << 20

    @classmethod
    def from_env(cls, prefix: str, *, max_body: int, read_timeout: float = 10.0, idle_timeout: float = 5.0,
                 max_connections: int = 32, max_response: int = 16 << 20) -> "Limits":
        import settings

        def num(name, default, kind):   # task-0264: finite, within its bounds, or refused naming it
            var = f"{prefix}_{name}"
            if var in settings.NUMBERS:
                return settings.parse(var, os.environ.get(var), default)
            return settings.parse(var, os.environ.get(var), default, kind=kind, low=0, high=float("inf") if kind is float
                                  else 1 << 62, inclusive=False)
        return cls(num("MAX_BODY", max_body, int), num("READ_TIMEOUT", read_timeout, float),
                   num("IDLE_TIMEOUT", idle_timeout, float), num("MAX_CONNECTIONS", max_connections, int),
                   response_cap(f"{prefix}_MAX_RESPONSE", max_response))


def read_body(handler, limits: Limits, *, required: bool = True) -> bytes:
    """The request's body, its framing checked before a byte of it is read: one Content-Length of
    digits (411 when absent and ``required``, 400 when malformed or repeated, 413 above ``max_body``),
    no Transfer-Encoding (411: send a length), no Content-Encoding (415), a Content-Type, when sent,
    of JSON (415). Raises Refused; the handler answers it and closes the connection."""
    h = handler.headers
    if h.get_all("Transfer-Encoding"):
        raise Refused(411, "send the body with a Content-Length; a transfer encoding is not accepted")
    if h.get_all("Content-Encoding"):
        raise Refused(415, "a content encoding is not accepted")
    ctype = (h.get("Content-Type") or "").split(";", 1)[0].strip().lower()
    if ctype and ctype != "application/json":
        raise Refused(415, "the body must be application/json")
    lengths = h.get_all("Content-Length") or []
    if not lengths:
        if required:
            raise Refused(411, "a Content-Length is required")
        return b""
    raw = lengths[0].strip()
    if len(lengths) != 1 or not raw.isascii() or not raw.isdigit():
        raise Refused(400, "one Content-Length of digits is required")
    n = int(raw)
    if n > limits.max_body:
        raise Refused(413, f"the body exceeds {limits.max_body} bytes")
    data = handler.rfile.read(n) if n else b""
    if len(data) != n:
        raise Refused(400, "the body ended before its Content-Length")
    return data


class NotJson(ValueError):
    """A body or line that is not JSON the parser can read: malformed, not UTF-8, or nested past the
    parser's depth (task-0272: ``json.loads`` raises RecursionError there, which no caller caught)."""


def parse_json(text: str | bytes):
    """``json.loads`` with every way it can refuse as ``NotJson``: bytes must be strict UTF-8 (never a
    "replace" decode), and a nesting past the interpreter's recursion limit is a parse error, not a
    RecursionError that ends the stdio loop or drops the connection (task-0272)."""
    if isinstance(text, (bytes, bytearray)):
        try:
            text = bytes(text).decode("utf-8")
        except UnicodeDecodeError as e:
            raise NotJson(f"not UTF-8: {e.reason} at byte {e.start}") from None
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise NotJson(str(e)) from None
    except RecursionError:
        raise NotJson("nested deeper than the parser reads") from None


def bearer_matches(header: str | None, token: str) -> bool:
    """An ``Authorization`` value carries ``token`` under the Bearer scheme, the scheme compared without
    regard to case (RFC 7235 §2.1, RFC 6750 §2.1; task-0272), the token in constant time."""
    import hmac
    scheme, _, cred = (header or "").strip().partition(" ")
    return scheme.lower() == "bearer" and hmac.compare_digest(cred.strip().encode(), token.encode())


def read_json_body(handler, limits: Limits, *, required: bool = True) -> dict:
    """``read_body``, then UTF-8 JSON (400) whose top level is an object (400); an empty body is {}."""
    data = read_body(handler, limits, required=required)
    if not data:
        return {}
    try:
        body = parse_json(data)
    except NotJson:   # malformed, not UTF-8, or nested past the parser's depth (task-0272)
        raise Refused(400, "the body must be UTF-8 JSON") from None
    if not isinstance(body, dict):
        raise Refused(400, "the body must be a JSON object")
    return body


class ArrivalDeadline:
    """The absolute deadline on a request's arrival: armed when the handler starts reading a request,
    disarmed once its body is in; at the deadline the socket is shut, so a client trickling one byte
    at a time still releases its worker."""

    def __init__(self, sock, seconds: float):
        self._sock, self._timer = sock, threading.Timer(seconds, self._fire)
        self._timer.daemon = True
        self.fired = False
        self._timer.start()

    def _fire(self):
        self.fired = True
        try:
            self._sock.shutdown(2)   # SHUT_RDWR: both directions, so a blocked read returns
        except OSError:
            pass

    def cancel(self):
        self._timer.cancel()


class BoundedMixin:
    """For a BaseHTTPRequestHandler: the socket's idle timeout, and the arrival deadline per request.
    The handler calls ``self.arrived()`` once its body is read (or at once for a request without one)."""
    default_limits: Limits | None = None   # the handler's own when its server carries none (a plain server in a test)

    def _limits(self) -> Limits:
        return getattr(self.server, "limits", None) or self.default_limits or Limits(1 << 20, 10.0, 5.0, 32)

    def setup(self):
        self.timeout = self._limits().idle_timeout
        super().setup()

    def handle_one_request(self):
        self._deadline = ArrivalDeadline(self.connection, self._limits().read_timeout)
        try:
            super().handle_one_request()
        except OSError:   # a timeout, a reset, or the deadline's shutdown: the connection ends
            self.close_connection = True
        finally:
            self._deadline.cancel()

    def parse_request(self):
        """A request whose line or headers were cut by the deadline is never dispatched: the socket was
        shut, so what parsed is a fragment, not the request the client meant."""
        ok = super().parse_request()
        return ok and not self._deadline.fired

    def refuse(self, answer) -> None:
        """Answer a refusal and end the connection (task-0196 M3, doc-0030): the refused request's body is
        never read, so on keep-alive it would otherwise be parsed as the next request, with headers of its
        own (a forged Host past the rebinding check). ``answer`` writes the response; nothing more is read
        from the socket after it. The reader and the page both refuse through this."""
        self.close_connection = True
        answer()

    def arrived(self, body: bool = False):
        """Disarm the deadline: at once for a request without a body (its headers are in), or once the
        body is read (``body=True``), then Refused(408) when it fired first, so a body cut short is
        never handed on."""
        self._deadline.cancel()
        if body and self._deadline.fired:
            self.close_connection = True
            raise Refused(408, "the request did not arrive within its time")


class BoundedServer(ThreadingHTTPServer):
    """A threading server that admits at most ``limits.max_connections`` at once: the next one is
    answered 503 with Retry-After and closed on the accepting thread, no worker started; a slot is
    released when its connection ends, whatever ended it."""
    daemon_threads = True

    def __init__(self, address, handler, limits: Limits):
        self.limits = limits
        self._slots = threading.BoundedSemaphore(limits.max_connections)
        super().__init__(address, handler)

    def process_request(self, request, client_address):
        if not self._slots.acquire(blocking=False):
            try:
                body = b'{"error": "the server is at capacity; retry shortly"}'
                request.sendall(b"HTTP/1.1 503 Service Unavailable\r\nContent-Type: application/json\r\nRetry-After: 1\r\n"
                                b"Connection: close\r\nContent-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body)
            except OSError:
                pass
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self._slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._slots.release()

    def active(self) -> int:
        """Connections being served now (for a test or a status line)."""
        return self.limits.max_connections - self._slots._value
