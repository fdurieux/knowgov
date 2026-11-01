"""The store port (harness/store.py) and its Neo4j adapter (harness/store_neo4j.py): the adapter
implements every operation the port declares, and no other module of the harness or the page
speaks Cypher. Source-level checks: the tests job has no driver and no store."""
from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = ROOT / "harness" / "store.py"
ADAPTER = ROOT / "harness" / "store_neo4j.py"
CYPHER = re.compile(r"\b(MATCH|MERGE|CREATE|DETACH DELETE|UNWIND)\b")


def _methods(path: Path, cls: str) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == cls:
            return {n.name for n in node.body if isinstance(n, ast.FunctionDef)}
    raise AssertionError(f"{cls} not in {path}")


def test_adapter_implements_every_port_operation():
    port = _methods(PORT, "Store") - {"__enter__", "__exit__", "close", "describe", "saved_queries"}
    adapter = _methods(ADAPTER, "Neo4jStore")
    assert port and port <= adapter, sorted(port - adapter)
    extra = adapter - port - {"__init__", "close", "run", "describe", "saved_queries"}
    assert not extra, f"the adapter has operations the port does not declare: {sorted(extra)}"


def test_only_the_adapter_speaks_cypher():
    """Cypher keywords followed by a pattern or a parameter, in code outside the adapter."""
    hits = []
    for p in [*(ROOT / "harness").glob("*.py"), *(ROOT / "demo" / "app").glob("*.py"), *(ROOT / "demo" / "tools").glob("*.py")]:
        if p == ADAPTER:
            continue
        text = re.sub(r'"""[\s\S]*?"""', "", p.read_text(encoding="utf-8"))
        for i, ln in enumerate(text.splitlines(), 1):
            code = ln.split("#", 1)[0]
            if CYPHER.search(code) and re.search(r"\(\w*:\w+|\$\w+", code):
                hits.append(f"{p.relative_to(ROOT)}:{i}: {ln.strip()[:90]}")
    assert not hits, "\n".join(hits)
    for rel in ("harness/load.py", "harness/rules.py", "harness/gate.py", "harness/run.py", "demo/app/server.py", "demo/app/register_project.py"):
        assert "GraphDatabase" not in (ROOT / rel).read_text(encoding="utf-8"), rel


def test_port_names_the_adapter_and_the_default():
    text = PORT.read_text(encoding="utf-8")
    assert 'os.environ.get("KG_STORE")' in text and '"neo4j"' in text
    assert "from store_neo4j import Neo4jStore" in text
    adapter = ADAPTER.read_text(encoding="utf-8")
    assert "from neo4j import GraphDatabase" in adapter and adapter.index("class Neo4jStore") < adapter.index("from neo4j import GraphDatabase"), "the driver is imported lazily"
    assert "SAVED_QUERIES" in adapter and "CONSTRAINTS" in adapter
