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
import re
from dataclasses import dataclass, field

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
