"""task-0059: the security description (docs/security.md) held to the code. Every test it cites
exists, every row names its evidence or says Practice, the permission matrix has every actor and
action and nobody executes, and the claims no other test held are held here: the store gets a
document's digest and size, never its text; nothing opens a connection but the model client and the
store driver; runs/ stays out of git. The gaps the document names are still the code's, so a fix
fails here until the document says so. Standard library only."""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "docs" / "security.md"
sys.path.insert(0, str(ROOT / "harness"))
sys.path.insert(0, str(ROOT / "demo" / "app"))   # the page's server, for task-0096's guard

from tests import test_pins  # noqa: E402  (task-0092: the pins the closed gap named)

CITE = re.compile(r"`(tests/test_\w+\.py)::(test_\w+)`")
ACTORS = ["The model", "An agent over MCP", "The pipeline", "A person by role", "The register approver",
          "Anyone who reaches the page's port"]
ACTIONS = ["Read", "Propose", "Approve", "Close", "Edit the model", "Execute a business action"]


def _text() -> str:
    return DOC.read_text(encoding="utf-8")


def _section(text: str, heading: str) -> str:
    return text.split(f"\n## {heading}", 1)[1].split("\n## ", 1)[0]


def _tables(section: str) -> list[list[list[str]]]:
    """Each markdown table of a section, as rows of cells, header and rule dropped."""
    tables, cur = [], []
    for line in section.splitlines() + [""]:
        if line.startswith("|"):
            cur.append([c.strip() for c in line.strip().strip("|").split("|")])
        elif cur:
            tables.append([r for r in cur[2:]])
            cur = []
    return tables


def test_every_cited_test_and_named_file_exists():
    text = _text()
    cites = CITE.findall(text)
    assert len(cites) >= 40, len(cites)
    for path, name in set(cites):
        tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
        names = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
        assert name in names, f"{path}::{name}"
    for path in set(re.findall(r"`((?:harness|demo|tools|instance|\.github)/[\w./-]+\.(?:py|yml|toml|md|html))`", text)):
        assert (ROOT / path).is_file() or path == ".github/dependabot.yml", path   # the one a gap proposes
    for path in ("demo/Dockerfile", "SECURITY.md", ".gitignore"):
        assert path in text and (ROOT / path).is_file(), path


def test_every_claim_row_names_a_test_a_ci_step_or_a_practice():
    text = _text()
    for heading in ("Data flows", "What leaves the network, per model-endpoint setting", "Dependencies and pins"):
        tables = _tables(_section(text, heading))
        assert tables, heading
        for table in tables:
            for row in table:
                evidence = row[-1]
                assert CITE.search(evidence) or evidence.startswith("**Practice") or "CI:" in evidence, (heading, row[0])
    rows = _tables(_section(text, "Who may do what"))[1]
    for row in rows:
        assert CITE.search(row[1]) or "Practice" in row[1] or "see Gaps" in row[1], row[0]


def test_the_permission_matrix_has_every_actor_and_action_and_nobody_executes():
    text = _text()
    matrix = text[text.index("<!-- permission matrix: begin -->"):text.index("<!-- permission matrix: end -->")]
    lines = [ln for ln in matrix.splitlines() if ln.startswith("|")]
    header = [c.strip() for c in lines[0].strip("|").split("|")]
    assert header == ["Actor"] + ACTIONS, header
    rows = [[c.strip() for c in ln.strip("|").split("|")] for ln in lines[2:]]
    assert [r[0].split(" (")[0] for r in rows] == ACTORS
    for r in rows:
        assert len(r) == 7 and r[6].startswith("no"), r[0]
    assert '"Execute a business action: none."' in text
    by = {r[0].split(" (")[0]: r for r in rows}
    # nothing over MCP or from the model rules; only a person by role approves or closes
    for actor in ("The model", "An agent over MCP", "The pipeline", "Anyone who reaches the page's port"):
        assert by[actor][3] == "no" and by[actor][4] == "no", actor
    assert "`approves`" in by["A person by role"][3] and "`closes`" in by["A person by role"][4]
    assert by["An agent over MCP"][2] == "no"


def test_the_mcp_servers_reads_are_the_ones_the_document_names():
    import mcp_server
    assert "`READS` in `harness/mcp_server.py`" in _text()
    port = ast.parse((ROOT / "harness" / "store.py").read_text(encoding="utf-8"))
    store = next(n for n in port.body if isinstance(n, ast.ClassDef) and n.name == "Store")
    methods = {n.name for n in store.body if isinstance(n, ast.FunctionDef)}
    assert set(mcp_server.READS) <= methods and not any(m.startswith(("create", "upsert", "wipe", "register", "apply")) for m in mcp_server.READS)


def test_the_store_gets_a_documents_digest_and_size_never_its_text():
    """The port's document-version write takes a digest and a byte count and no text; the loader
    passes the subject's version_digest, a SHA-256 and a length (task-0160: a file's raw bytes, else the
    text's). Excerpts (fragments) and statement values are stored, as
    the document says: the gate's evidence is the excerpt."""
    port = ast.parse((ROOT / "harness" / "store.py").read_text(encoding="utf-8"))
    args = {n.name: [a.arg for a in n.args.args] for n in ast.walk(port) if isinstance(n, ast.FunctionDef)}
    assert args["upsert_artefact_version"] == ["self", "path", "family", "fmt", "vid", "sha", "nbytes", "ts", "tag", "aid"]
    assert "text" in args["create_fragment"]
    load = (ROOT / "harness" / "load.py").read_text(encoding="utf-8")
    calls = re.findall(r"st\.upsert_artefact_version\((.*)\)", load)
    assert calls and all(", digest, size, " in c and "text" not in c for c in calls), calls
    assert "digest, size = SUBJECT.version_digest(path, text)" in load
    from subject import SUBJECT
    key = next(k for k, p in SUBJECT.kit_files if p.is_file())
    d, n = SUBJECT.version_digest(key, SUBJECT.artefact_text(key))
    assert re.fullmatch(r"[0-9a-f]{64}", d) and isinstance(n, int), "a digest and a size, never the text"
    assert '"text": a["text"]' in load and '"value": a["value"]' in load


def test_the_baseline_arm_sends_whole_documents():
    import arms
    sent = arms.baseline_documents({"kit/a.md": "line one\nline two", "kit/b.md": "other"}, ["kit/a.md", "kit/b.md"])
    assert "line one\nline two" in sent and "other" in sent


NETWORK = {"requests", "httpx", "urllib3", "aiohttp", "socket", "smtplib", "ftplib", "telnetlib", "websocket",
           "websockets", "paramiko", "grpc", "boto3", "google", "anthropic", "pycurl"}
NETWORK_DOTTED = {"urllib.request", "http.client", "xmlrpc.client"}
CLIENTS = {"openai": {"harness/arms.py", "harness/agent.py"}, "neo4j": {"harness/store_neo4j.py"}}
# the stack job's own check of the page it just started: it asks the local page and nothing else
# and the MCP check's HTTP client (task-0095), which asks only the loopback server it started itself;
# and knowgov-runs (task-0133), a client of the page's run API at the operator's KG_PAGE_URL, the local page by default
LOCAL_CHECKS = {"demo/tools/check_impact_cypher.py": 'os.environ.get("KG_DEMO_URL", "http://localhost:8080")',
                "tools/check_mcp_server.py": '"--http", "--host", "127.0.0.1", "--port", "0"',
                "harness/mcp_runs.py": 'DEFAULT_PAGE = "http://localhost:8080"'}
# the worker's attestation probe (no_socket_escape): it tries to open AF_VSOCK and AF_PACKET sockets and to
# connect to TEST-NET-1 (RFC 5737, never routed), and holds only when every attempt is refused
PROBES = {"harness/worker.py": 'OUTSIDE = ("192.0.2.1", 9)'}


def test_nothing_reaches_the_network_but_the_model_client_and_the_store_driver():
    found: dict[str, set[str]] = {}
    for folder in ("harness", "demo/app", "tools", "demo/tools"):
        for path in sorted((ROOT / folder).glob("*.py")):
            rel = path.relative_to(ROOT).as_posix()
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for n in ast.walk(tree):
                if isinstance(n, ast.Import):
                    mods = [a.name for a in n.names]
                elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
                    mods = [n.module] + [f"{n.module}.{a.name}" for a in n.names]
                else:
                    continue
                for m in mods:
                    if rel in LOCAL_CHECKS and m == "urllib.request":
                        assert LOCAL_CHECKS[rel] in path.read_text(encoding="utf-8"), rel
                        continue
                    if rel in PROBES and m == "socket":
                        assert PROBES[rel] in path.read_text(encoding="utf-8"), rel
                        continue
                    assert m.split(".")[0] not in NETWORK and m not in NETWORK_DOTTED, (rel, m)
                    if m.split(".")[0] in CLIENTS:
                        found.setdefault(m.split(".")[0], set()).add(rel)
    assert found == CLIENTS, found
    page = (ROOT / "demo" / "app" / "index.html").read_text(encoding="utf-8")
    assert not re.search(r"<(script|link|img|iframe)[^>]+(src|href)=[\"']https?://", page, re.I)


def test_runs_are_ignored_by_git_and_security_md_points_here():
    assert "runs/" in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    policy = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    assert "docs/security.md" in policy and "Report a vulnerability" in policy and "public issue" in policy
    assert re.search(r"no(?:ne)?\b.*bank-related data|bank-related data", policy)


def test_the_gaps_named_here_are_still_the_codes():
    text = _text()
    gaps = text[text.index("<!-- gaps: begin -->"):text.index("<!-- gaps: end -->")]
    compose = (ROOT / "demo" / "docker-compose.yml").read_text(encoding="utf-8")
    # 1. every published port carries the host address KG_BIND, 127.0.0.1 unless widened (task-0090);
    # the guard refuses the default password on a wider bind; the page still has no login
    ports = [l.strip() for f in sorted((ROOT / "demo").glob("docker-compose*.yml"))
             for b in re.findall(r"\n    ports:\n((?:      - .*\n)+)", f.read_text(encoding="utf-8")) for l in b.splitlines()]
    unbound = not ports or not all(l.startswith('- "${KG_BIND:-127.0.0.1}:') for l in ports)
    guarded = "/knowgov/bind-guard.sh" in compose and "neo4j/kgpoc2026" in (ROOT / "demo" / "neo4j" / "bind-guard.sh").read_text(encoding="utf-8")
    server = (ROOT / "demo" / "app" / "server.py").read_text(encoding="utf-8")
    assert unbound == ("listen on every interface" in gaps)
    assert guarded == ("the stack refuses to start until `KG_NEO4J_PASSWORD` is set" in gaps)
    # task-0096 closed the writes: every POST passes write_guard; the GETs still pass nothing
    get_body = server.split("    def do_GET(self)", 1)[1].split("\n    def ", 1)[0]
    post_body = server.split("    def do_POST(self)", 1)[1].split("\n    def ", 1)[0]
    writes_guarded = "write_guard(self.headers)" in post_body
    assert writes_guarded and "The page has no login" not in gaps and "Its writes are closed (task-0096)" in gaps
    assert ("guard" not in get_body) == ("**The page's reads have no login.**" in gaps)
    assert ("kgpoc2026" in compose) == ("kgpoc2026" in gaps)
    # 2. no harness module checks the gives role
    checks_gives = any(re.search(r"[\"']gives[\"']", p.read_text(encoding="utf-8")) for p in (ROOT / "harness").glob("*.py"))
    assert (not checks_gives) == ("**The `gives` role is not checked.**" in gaps)
    # closed by task-0092: Dependabot runs, and nothing is pinned by tag only (tests/test_pins.py holds the pins)
    bot = (ROOT / ".github" / "dependabot.yml").exists()
    assert bot and "No automated dependency updates" not in gaps
    by_tag = [u for _, u in test_pins._uses() if not test_pins.SHA.fullmatch(u)]
    by_tag += [r for _, r in test_pins._images() if not test_pins.DIGEST.fullmatch(r)]
    assert not by_tag and "pinned by tag only" not in gaps, by_tag
    # 3. excerpts are stored (held above): the gap stays named while create_fragment takes text
    assert "**The store holds excerpts.**" in gaps


def _page(env: dict):
    """The page's handler on an ephemeral loopback port, with ``env`` over the process's for the
    duration; yields a function that sends a request and returns (status, json, headers)."""
    import contextlib
    import json
    import os
    import threading
    import urllib.error
    import urllib.request
    from http.server import ThreadingHTTPServer
    import server

    @contextlib.contextmanager
    def ctx():
        keep = {k: os.environ.get(k) for k in env}
        os.environ.update({k: v for k, v in env.items() if v is not None})
        for k, v in env.items():
            if v is None:
                os.environ.pop(k, None)
        class Quiet(server.Handler):
            def log_message(self, fmt, *args):
                pass
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), Quiet)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{httpd.server_address[1]}"

        def call(path, body=None, headers=None):
            data = json.dumps(body).encode() if body is not None else None
            req = urllib.request.Request(base + path, data=data, headers={"Content-Type": "application/json", **(headers or {})},
                                         method="POST" if data is not None else "GET")
            try:
                with urllib.request.urlopen(req, timeout=10) as r:   # noqa: S310 — the loopback test server
                    return r.status, json.loads(r.read()), dict(r.headers)
            except urllib.error.HTTPError as e:
                return e.code, json.loads(e.read()), dict(e.headers)
        try:
            yield call
        finally:
            httpd.shutdown()
            httpd.server_close()
            for k, v in keep.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
    return ctx()


# a run the guard lets through and the runner then refuses: nothing is ever started
_NO_RUN = {"scenario": "no-such-scenario", "mode": "deterministic"}


def test_the_pages_writes_need_its_token_and_a_wider_bind_without_one_refuses_them():
    """Task-0096: with KG_PAGE_TOKEN every POST carries it as a bearer token (401 without); without
    it, a page published beyond this machine (KG_BIND, else its own listen address) refuses every
    POST with a message naming the variable; on this machine a POST needs nothing, as the stack job
    sends it. A request from another web origin is refused whatever the bind. Reads stay open."""
    import server
    for bind in ("127.0.0.1", None):   # compose's default, and a process outside compose listening on its default
        with _page({"KG_BIND": bind, "KG_PAGE_LISTEN": None, "KG_PAGE_TOKEN": None}) as call:
            code, body, _ = call("/api/run", _NO_RUN)
            assert code == 400 and "unknown scenario" in body["error"], (bind, code, body)
            assert server.writes_view() == {"token_required": False, "refused": None}
            code, body, _ = call("/api/run", _NO_RUN, {"Origin": "http://evil.example"})
            assert code == 403 and "another web origin" in body["error"], body
    for env in ({"KG_BIND": "0.0.0.0", "KG_PAGE_TOKEN": None}, {"KG_BIND": None, "KG_PAGE_LISTEN": "0.0.0.0", "KG_PAGE_TOKEN": None},
                {"KG_BIND": "192.0.2.7", "KG_PAGE_TOKEN": None}):
        with _page(env) as call:
            for path in ("/api/run", "/api/register/project"):
                code, body, _ = call(path, _NO_RUN)
                assert code == 403 and "KG_PAGE_TOKEN" in body["error"] and "beyond this machine" in body["error"], (env, path, body)
            assert server.writes_view()["refused"] and not server.writes_view()["token_required"]
            code, body, _ = call("/api/subjects")
            assert code == 200 and body["subjects"], "reads stay open"
            assert call("/health")[:2] == (200, {"ok": True})
    secret = "t0ken-for-the-test"   # not a credential: the test's own value
    for bind in ("0.0.0.0", "127.0.0.1"):
        with _page({"KG_BIND": bind, "KG_PAGE_TOKEN": secret}) as call:
            assert server.writes_view() == {"token_required": True, "refused": None}
            for headers in ({}, {"Authorization": "Bearer wrong"}, {"Authorization": secret}):
                code, body, hdrs = call("/api/run", _NO_RUN, headers)
                assert code == 401 and hdrs.get("WWW-Authenticate") == "Bearer" and secret not in json.dumps(body), (bind, headers)
            code, body, _ = call("/api/run", _NO_RUN, {"Authorization": f"Bearer {secret}"})
            assert code == 400 and "unknown scenario" in body["error"], body
            code, body, _ = call("/api/subjects")
            assert code == 200 and secret not in json.dumps(body)


def test_the_page_sends_its_token_and_the_stack_passes_the_bind_and_the_token():
    """The page's JavaScript asks for the token only when the server says so, keeps it in the tab's
    sessionStorage, and sends it on POSTs only; compose passes KG_BIND and KG_PAGE_TOKEN to the app,
    whose image listens on every interface inside the container; the stack job's POSTs carry none."""
    page = (ROOT / "demo" / "app" / "index.html").read_text(encoding="utf-8")
    assert "opts.method === 'POST' && pageToken()" in page and "Authorization: 'Bearer ' + pageToken()" in page
    assert "sessionStorage.setItem('kg-page-token'" in page and "localStorage.setItem('kg-page-token'" not in page
    assert "STATE.writes = j.writes" in page and "writesWhy()" in page
    compose = (ROOT / "demo" / "docker-compose.yml").read_text(encoding="utf-8")
    app = compose.split("\n  app:\n", 1)[1].split("\n  litellm:", 1)[0]
    assert "KG_BIND: ${KG_BIND:-127.0.0.1}" in app and "KG_PAGE_TOKEN: ${KG_PAGE_TOKEN:-}" in app
    assert "KG_PAGE_LISTEN=0.0.0.0" in (ROOT / "demo" / "Dockerfile").read_text(encoding="utf-8")
    demo = (ROOT / ".github" / "workflows" / "demo.yml").read_text(encoding="utf-8")
    assert "KG_PAGE_TOKEN" not in demo and "KG_BIND" not in demo and "-X POST localhost:8080/api/run" in demo


def test_the_lighthouse_protocol_points_to_the_matrix():
    lh = (ROOT / "docs" / "lighthouse-evaluation.md").read_text(encoding="utf-8")
    assert "docs/security.md" in lh or "security.md" in lh


def test_the_workers_socket_use_is_only_the_probe_that_proves_it_cannot_reach_out():
    """The PROBES exception above, as tight as the guard: harness/worker.py touches ``socket`` only to
    try the two families no network namespace confines and one connect to TEST-NET-1. No bind, listen,
    accept, send, receive, name lookup or other address; a later edit that does more fails here."""
    tree = ast.parse((ROOT / "harness" / "worker.py").read_text(encoding="utf-8"))
    nodes = list(ast.walk(tree))
    assert not any(isinstance(n, ast.ImportFrom) and n.module == "socket" for n in nodes), "only `import socket`"
    used = {n.attr for n in nodes if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "socket"}
    assert used == {"socket", "SOCK_STREAM", "SOCK_RAW", "create_connection"}, used
    forbidden = {"bind", "listen", "accept", "send", "sendall", "sendto", "sendmsg", "sendfile", "recv", "recvfrom",
                 "recv_into", "recvfrom_into", "recvmsg", "connect", "connect_ex", "getaddrinfo", "gethostbyname",
                 "gethostbyname_ex", "create_server", "socketpair", "fromfd"}
    assert not {n.attr for n in nodes if isinstance(n, ast.Attribute)} & forbidden
    assigned = {ast.unparse(n.targets[0]): ast.literal_eval(n.value) for n in tree.body
                if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) in ("OUTSIDE", "(AF_VSOCK, AF_PACKET)")}
    assert assigned == {"OUTSIDE": ("192.0.2.1", 9), "(AF_VSOCK, AF_PACKET)": (40, 17)}, assigned
    connects = [n for n in nodes if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "create_connection"]
    assert len(connects) == 1 and isinstance(connects[0].args[0], ast.Name) and connects[0].args[0].id == "OUTSIDE"
    probe = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "sockets")
    loop = next(n for n in ast.walk(probe) if isinstance(n, ast.For))
    assert [e.elts[1].id for e in loop.iter.elts] == ["AF_VSOCK", "AF_PACKET"], "the two families, nothing else"
    opened = [n for n in ast.walk(probe) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "opener"]
    assert len(opened) == 1 and [a.id for a in opened[0].args] == ["family", "kind"]
    assert {n.name for n in tree.body if isinstance(n, ast.FunctionDef) and any(
        isinstance(m, ast.Name) and m.id == "socket" for m in ast.walk(n))} == {"sockets"}, "socket is used in sockets() only"
