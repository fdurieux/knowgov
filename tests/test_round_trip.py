"""The store's round trip through Turtle (task-0070): the port declares the two operations, both
adapters implement them, the check compares what it should and only that, and CI runs it on both
subjects through rdflib and on Neo4j in the stack job. Source-level and stdlib only: the tests job
has no rdflib and no store; harness.yml and demo.yml run the check itself."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))


def _methods(path: Path, cls: str) -> set[str]:
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.ClassDef) and node.name == cls:
            return {n.name for n in node.body if isinstance(n, ast.FunctionDef)}
    raise AssertionError(f"{cls} not in {path}")


def test_the_port_declares_the_round_trip_and_both_adapters_implement_it():
    ops = {"export_turtle", "import_turtle"}
    assert ops <= _methods(ROOT / "harness" / "store.py", "Store")
    assert ops <= _methods(ROOT / "harness" / "store_neo4j.py", "Neo4jStore")
    assert ops <= _methods(ROOT / "harness" / "store_rdflib.py", "RdflibStore")
    neo = (ROOT / "harness" / "store_neo4j.py").read_text(encoding="utf-8")
    assert "from store_rdflib import RdflibStore" in neo, "the Neo4j adapter writes the rdflib adapter's form, through its layer"


def test_the_check_ignores_list_order_and_the_store_name_and_nothing_else():
    import check_round_trip as c
    base = {"gate": {"codegen": {"verdict": "BLOCKED", "findings": [{"related": ["a", "b"]}]}},
            "three_valued": {"k": {"answer": "asserted", "statements": [{"id": "x", "verifications": [{"id": "v1"}, {"id": "v2"}]}]}},
            "census": {"nodes": 3}}
    shuffled = {"gate": {"codegen": {"verdict": "BLOCKED", "findings": [{"related": ["b", "a"]}]}},
                "three_valued": {"k": {"answer": "asserted", "statements": [{"id": "x", "verifications": [{"id": "v2"}, {"id": "v1"}]}]}},
                "census": {"nodes": 3}}
    assert c.differences(base, shuffled, "S") == []
    worse = {**base, "gate": {"codegen": {**base["gate"]["codegen"], "verdict": "PROCEED"}}}
    assert c.differences(base, worse, "S") == ["S: gate codegen differs on ['verdict']"]
    unknown = {**base, "three_valued": {"k": {"answer": "unknown", "statements": []}}}
    assert c.differences(base, unknown, "S") == ["S: three_valued k differs on ['answer', 'statements']"]
    assert c.differences(base, {**base, "census": {"nodes": 2}}, "S")


def test_ci_runs_the_round_trip_on_both_subjects_and_on_neo4j():
    harness = (ROOT / ".github" / "workflows" / "harness.yml").read_text(encoding="utf-8")
    assert "KG_STORE=rdflib python tools/check_round_trip.py --chain rdflib,rdflib\n" in harness
    assert "KG_SUBJECT=subjects/jef_data_load python tools/check_round_trip.py --chain rdflib,rdflib" in harness
    demo = (ROOT / ".github" / "workflows" / "demo.yml").read_text(encoding="utf-8")
    assert "python tools/check_round_trip.py --chain neo4j,rdflib,neo4j" in demo
    assert "-e KG_SUBJECT=/repo/subjects/jef_data_load app python tools/check_round_trip.py --chain neo4j,rdflib,neo4j" in demo
