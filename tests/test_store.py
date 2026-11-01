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
RDFLIB = ROOT / "harness" / "store_rdflib.py"
CYPHER = re.compile(r"\b(MATCH|MERGE|CREATE|DETACH DELETE|UNWIND)\b")


def _methods(path: Path, cls: str) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == cls:
            return {n.name for n in node.body if isinstance(n, ast.FunctionDef)}
    raise AssertionError(f"{cls} not in {path}")


def test_adapters_implement_every_port_operation():
    console = {"describe", "saved_queries", "console_query"}   # optional: what an adapter with a console offers the page
    port = _methods(PORT, "Store") - {"__enter__", "__exit__", "close"} - console
    adapter = _methods(ADAPTER, "Neo4jStore")
    assert port and port <= adapter, sorted(port - adapter)
    assert console <= adapter
    extra = adapter - port - {"__init__", "close", "run"} - console
    assert not extra, f"the adapter has operations the port does not declare: {sorted(extra)}"
    rdf = _methods(RDFLIB, "RdflibStore")
    assert port <= rdf, sorted(port - rdf)


def test_the_rdflib_adapter_speaks_no_cypher_and_the_port_names_both():
    text = RDFLIB.read_text(encoding="utf-8")
    assert "from rdflib import Graph" in text and "KG_RDFLIB_FILE" in text
    code = re.sub(r'"""[\s\S]*?"""', "", text)
    assert not re.search(r"\b(MATCH|MERGE|DETACH DELETE|UNWIND)\b", code.replace("merge_node", "").replace("merge_edge", ""))
    port = PORT.read_text(encoding="utf-8")
    assert "from store_rdflib import RdflibStore" in port and '"rdflib"' in port


def test_comparator_skips_d1_across_store_kinds_and_ignores_scalar_list_order():
    import json, sys, tempfile
    sys.path.insert(0, str(ROOT / "demo" / "tools"))
    import compare_deterministic as cd
    rec = {"scenario": "S9", "D1_constraints": [{"type": "existence", "accepted": False, "message": "Enterprise only"}],
           "D6_gate": {"verdict": "PROCEED", "blocked_keys": ["b", "a"]}, "rules": {"R-REQ": []}}
    run = {"scenario": "S9", "store": "rdflib", "D1_constraints": [{"type": "existence", "accepted": False, "message": "application check"}],
           "D6_gate": {"verdict": "PROCEED", "blocked_keys": ["a", "b"]}, "rules": {"R-REQ": []}}
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "record" / "S9").mkdir(parents=True); (d / "run" / "S9").mkdir(parents=True)
        (d / "record" / "S9" / "deterministic.json").write_text(json.dumps(rec), encoding="utf-8")
        (d / "run" / "S9" / "deterministic.json").write_text(json.dumps(run), encoding="utf-8")
        n, lines = cd.compare(d / "run", d / "record", ["S9"])
        assert n == 0 and "D1_constraints skipped: the run's store is rdflib, the record's neo4j" in lines[0], lines
        run["D6_gate"]["verdict"] = "BLOCKED"
        (d / "run" / "S9" / "deterministic.json").write_text(json.dumps(run), encoding="utf-8")
        n, lines = cd.compare(d / "run", d / "record", ["S9"])
        assert n == 1 and any("verdict" in ln for ln in lines), lines
        # the same store kind compares D1 too
        run["D6_gate"]["verdict"] = "PROCEED"; run["store"] = "neo4j"
        (d / "run" / "S9" / "deterministic.json").write_text(json.dumps(run), encoding="utf-8")
        n, lines = cd.compare(d / "run", d / "record", ["S9"])
        assert n == 1 and any("message" in ln for ln in lines), lines


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


def test_saved_query_check_splits_statements_and_only_a_console_store_runs_them():
    """The check tool runs each ';'-separated statement of a saved query; a comment-only piece
    is no statement. The port's default has no console (the rdflib adapter keeps it), so it
    refuses rather than pretending; the tests job has no rdflib, so the port is what is run."""
    import sys
    sys.path.insert(0, str(ROOT / "demo" / "tools"))
    import check_saved_queries as c
    text = "// documented absence\nMATCH (x) RETURN x;\n// a note alone\n;\nRETURN 1 AS n"
    assert c.statements(text) == ["// documented absence\nMATCH (x) RETURN x", "RETURN 1 AS n"]
    sys.path.insert(0, str(ROOT / "harness"))
    from store import Store
    try:
        Store().console_query("RETURN 1")
    except NotImplementedError as e:
        assert "no console" in str(e)
    else:
        raise AssertionError("the port's default ran a console query")
    assert "console_query" not in _methods(RDFLIB, "RdflibStore")
