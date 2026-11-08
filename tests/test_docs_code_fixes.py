"""task-0235: the places task-0230's docs pass found the docs right and the code wrong (#384; its notes (c) and (d)):
the Browser link's bolt port, two page texts, the MCP reader's instructions on `subject`, two stale
docstrings, a test's name, and two docs/security.md rows whose cited tests proved less than the row says.
Each held here, so it fails on the code as it was."""
from __future__ import annotations

import ast
import os
import re
import sys
import tomllib  # noqa: F401  (stdlib; kept for parity with the other docs tests)
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "demo" / "app"), str(Path(__file__).resolve().parent)]
PAGE = ROOT / "demo" / "app" / "index.html"
COMPOSE = ROOT / "demo" / "docker-compose.yml"
SECURITY = ROOT / "docs" / "security.md"


def _service(compose: str, name: str) -> str:
    """One service's block of the compose file, by indentation."""
    m = re.search(rf"(?ms)^  {name}:\n(.*?)(?=^  \S|^\S)", compose)
    assert m, name
    return m.group(1)


# 1. The Browser link's bolt port: the one the stack publishes, never a literal 7687.

def test_the_browser_link_names_the_bolt_port_the_stack_publishes():
    import server
    compose = COMPOSE.read_text(encoding="utf-8")
    app = _service(compose, "app")
    assert "KG_PORT_BOLT: ${KG_PORT_BOLT:-7687}" in app, "compose passes the published bolt port to the page"
    assert '"${KG_BIND:-127.0.0.1}:${KG_PORT_BOLT:-7687}:7687"' in _service(compose, "neo4j"), "the mapping it mirrors"
    keep = server.BOLT_PORT
    try:
        server.BOLT_PORT = 7688
        assert ":7688" in server.browser_connect_url() and ":7687" not in server.browser_connect_url()
        assert "7688" in server.browser_play_url("http://localhost:8081", "/x") and "7687" not in server.browser_play_url("http://localhost:8081", "/x")
    finally:
        server.BOLT_PORT = keep
    assert server.bolt_port({"KG_PORT_BOLT": "7690"}) == 7690
    for bad in ("", "x", "0", "70000", "-1"):
        assert server.bolt_port({"KG_PORT_BOLT": bad}) == 7687, bad
    assert server.bolt_port({}) == 7687
    src = (ROOT / "demo" / "app" / "server.py").read_text(encoding="utf-8")
    assert ":7687\"" not in src.split("def browser_connect_url", 1)[1].split("\ndef ", 1)[0]
    page = PAGE.read_text(encoding="utf-8")
    assert ":7687'" not in page and "s.browser_connect" in page, "the page uses the server's connect URL"
    status = server.store_status()
    if status["store"] == "neo4j":
        assert status["browser_connect"] == server.browser_connect_url()


# 2 and 3. The page's two texts.

def test_the_page_says_what_a_deterministic_run_registers_and_what_arms_needs():
    page = PAGE.read_text(encoding="utf-8")
    assert "deterministic mode creates no Derived node" not in page, "the page's runs give stage 2 the record's output (server.py)"
    assert "the page\\'s runs give it the record\\'s" in page, "said as the page's own JavaScript string writes it"
    note = re.search(r'<div class="note">Replay shows.*?</div>', page, re.S).group(0)
    assert "contained worker" in note and "--profile arms" in note, note


# 4. The reader's instructions say which tools take `subject`.

def test_the_instructions_name_the_one_tool_without_subject():
    import mcp_server
    text = mcp_server.INSTRUCTIONS
    assert "Every tool takes subject" not in text
    without = sorted(t["name"] for t in mcp_server.TOOLS if "subject" not in t["inputSchema"].get("properties", {}))
    assert without == ["list_subjects"], without
    assert "Every tool but list_subjects takes subject" in text


# 5. Two docstrings.

def test_two_docstrings_say_what_their_tools_do():
    pre = ast.get_docstring(ast.parse((ROOT / "tools" / "preload_check.py").read_text(encoding="utf-8")))
    assert "one file at a time" not in pre and "step 4's checks read documents together" in pre
    lh = ast.get_docstring(ast.parse((ROOT / "tools" / "lighthouse_evidence.py").read_text(encoding="utf-8")))
    assert "a summary per criterion" not in lh and "a summary per subject" in lh
    src = (ROOT / "tools" / "lighthouse_evidence.py").read_text(encoding="utf-8")
    assert 'out.append(f"## {s[\'subject\']}")' in src, "the summary is per subject"


# 6. The test that counts Dependabot's ecosystems is named for five.

def test_the_dependabot_test_is_named_for_the_five_it_holds():
    import test_pins
    assert hasattr(test_pins, "test_dependabot_watches_the_five_ecosystems_weekly")
    assert not hasattr(test_pins, "test_dependabot_watches_the_four_ecosystems_weekly")
    assert "test_dependabot_watches_the_five_ecosystems_weekly" in SECURITY.read_text(encoding="utf-8")


# 7. The two docs/security.md rows, each with a test that proves its claim.

RULINGS = {"apply_ruling", "approve_verified", "close_declared_gap", "settle_conflicts", "verify_by_review",
           "verify_by_execution", "verify_authored", "reverify", "corroborate"}


def _calls(path: Path) -> set[str]:
    return {n.func.attr for n in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}


def test_the_gate_never_rules():
    """docs/security.md: the pipeline proposes only; its gate never rules. Neither the gate (harness/gate.py)
    nor the command (harness/gate_cli.py) calls any port write that verifies, approves, closes, settles or
    corroborates; those are load.py's (a person's recorded act), change.py's (stage 2's re-verification) and
    rules.py's (corroboration at a load). A gate run with --no-load opens a read handle, which the port
    refuses any write."""
    import store
    for mod in ("gate.py", "gate_cli.py"):
        assert not _calls(ROOT / "harness" / mod) & RULINGS, (mod, _calls(ROOT / "harness" / mod) & RULINGS)
    assert not RULINGS & set(store.READS), "a read handle passes none of them"
    src = (ROOT / "harness" / "gate_cli.py").read_text(encoding="utf-8")
    assert 'access="read" if args.no_load else "write"' in src
    callers = {p.name for p in (ROOT / "harness").glob("*.py")
               if p.name not in ("store.py", "store_neo4j.py", "store_rdflib.py") and _calls(p) & RULINGS}
    assert callers == {"load.py", "change.py", "rules.py"}, callers
    row = next(ln for ln in SECURITY.read_text(encoding="utf-8").splitlines() if ln.startswith("| The pipeline proposes only; its gate never rules"))
    assert "tests/test_docs_code_fixes.py::test_the_gate_never_rules" in row, row


def test_the_stores_live_where_the_row_says():
    """docs/security.md: the Neo4j store lives in the neo4j-data volume on the host; the rdflib store in
    memory, or in KG_RDFLIB_FILE when set."""
    compose = COMPOSE.read_text(encoding="utf-8")
    assert "      - neo4j-data:/data\n" in _service(compose, "neo4j"), "Neo4j's data directory is the named volume"
    assert re.search(r"(?m)^volumes:\n(?:  .*\n)*?  neo4j-data:", compose), "declared at the top level: a volume on the host"
    src = (ROOT / "harness" / "store_rdflib.py").read_text(encoding="utf-8")
    assert 'self.path = path if path is not None else os.environ.get("KG_RDFLIB_FILE")' in src
    try:
        import store_rdflib
    except ImportError:
        store_rdflib = None
    if store_rdflib is not None:
        keep = os.environ.pop("KG_RDFLIB_FILE", None)
        try:
            s = store_rdflib.RdflibStore()
            assert s.path is None and s.describe()["uri"] == "memory"
            s.close()
        finally:
            if keep is not None:
                os.environ["KG_RDFLIB_FILE"] = keep
    row = next(ln for ln in SECURITY.read_text(encoding="utf-8").splitlines() if ln.startswith("| The Neo4j store lives in the `neo4j-data` volume"))
    assert "tests/test_docs_code_fixes.py::test_the_stores_live_where_the_row_says" in row, row
