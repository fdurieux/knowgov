"""task-0059: the security description (docs/security.md) held to the code. Every test it cites
exists, every row names its evidence or says Practice, the permission matrix has every actor and
action and nobody executes, and the claims no other test held are held here: the store gets a
document's digest and size, never its text; nothing opens a connection but the model client and the
store driver; runs/ stays out of git. The gaps the document names are still the code's, so a fix
fails here until the document says so. Standard library only."""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "docs" / "security.md"
sys.path.insert(0, str(ROOT / "harness"))

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
    passes sha256(text) and the length. Excerpts (fragments) and statement values are stored, as
    the document says: the gate's evidence is the excerpt."""
    port = ast.parse((ROOT / "harness" / "store.py").read_text(encoding="utf-8"))
    args = {n.name: [a.arg for a in n.args.args] for n in ast.walk(port) if isinstance(n, ast.FunctionDef)}
    assert args["upsert_artefact_version"] == ["self", "path", "family", "fmt", "vid", "sha", "nbytes", "ts", "tag", "aid"]
    assert "text" in args["create_fragment"]
    load = (ROOT / "harness" / "load.py").read_text(encoding="utf-8")
    calls = re.findall(r"st\.upsert_artefact_version\((.*)\)", load)
    assert calls and all("sha256(text), len(text.encode())" in c for c in calls), calls
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
LOCAL_CHECKS = {"demo/tools/check_impact_cypher.py": 'os.environ.get("KG_DEMO_URL", "http://localhost:8080")'}


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
    # 1. the published ports carry no host address, and the page binds every interface with no login
    unbound = all(f'"${{{v}:-{p}}}:{p}"' in compose for v, p in (("KG_PORT_APP", 8080), ("KG_PORT_BROWSER", 7474), ("KG_PORT_BOLT", 7687)))
    server = (ROOT / "demo" / "app" / "server.py").read_text(encoding="utf-8")
    assert unbound == ("listen on every interface" in gaps)
    assert ('ThreadingHTTPServer(("0.0.0.0"' in server) == ("The page has no login" in gaps)
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


def test_the_lighthouse_protocol_points_to_the_matrix():
    lh = (ROOT / "docs" / "lighthouse-evaluation.md").read_text(encoding="utf-8")
    assert "docs/security.md" in lh or "security.md" in lh
