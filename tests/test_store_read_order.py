"""task-0369: every store read whose rows reach a rule, the gate, the SHACL projection or a report as a list names
its order, on both adapters, so a run answers in one order whatever the store's traversal. Three Neo4j runs of one
record gave R-VAGUE in three orders before this, which the comparator (lists read without order) never saw.

Stdlib only: the adapters' source is read, not imported. The behaviour on a loaded store, and the two adapters'
answers compared, is ``tools/check_read_order.py`` (rdflib in harness.yml, Neo4j beside rdflib in the stack job), and
two deterministic runs compared leaf by leaf, order included, is ``tools/check_run_order.py``."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness"))
import store  # noqa: E402

ORDERED = ["reverify", "structural_violations", "vague_fragments", "unresolved_assertions", "declared_open",
           "requirements_without", "silent_entities", "invalidate_stale", "declared_gaps_for_key", "stale_on_keys",
           "derived_rows", "derived_outputs", "artefact_assertions", "attestations", "lint_gaps", "act_findings",
           "assertions_on_key", "assertion_rows", "supported_by", "candidate_for", "fragments_with_version",
           "requirements_verified_by", "held_keys", "candidate_pairs", "conflict_gaps", "key_evidence"]
ORDERING = {"by_id", "by_fields", "by_content", "sorted"}


def _methods(path: Path) -> dict[str, ast.FunctionDef]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {f.name: f for c in tree.body if isinstance(c, ast.ClassDef) for f in c.body if isinstance(f, ast.FunctionDef)}


def _orders(fn: ast.FunctionDef) -> bool:
    calls = {n.func.id for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    calls |= {n.func.attr for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    text = ast.unparse(fn)
    return bool(calls & ORDERING) or "ORDER BY" in text


def test_every_list_read_names_its_order_on_both_adapters():
    for name in ("store_neo4j.py", "store_rdflib.py"):
        methods = _methods(ROOT / "harness" / name)
        missing = [m for m in ORDERED if m not in methods]
        assert not missing, (name, missing)
        unordered = [m for m in ORDERED if not _orders(methods[m])]
        assert not unordered, f"{name}: {unordered} return a list in the store's own order"


def test_the_rule_reads_order_by_id_then_their_second_field():
    rows = [{"id": "A:2", "fid": "F:1"}, {"id": "A:1", "fid": "F:2"}, {"id": "A:1", "fid": "F:1"}, {"id": None, "fid": "F:0"}]
    assert store.by_fields(rows, "id", "fid") == [{"id": "A:1", "fid": "F:1"}, {"id": "A:1", "fid": "F:2"},
                                                  {"id": "A:2", "fid": "F:1"}, {"id": None, "fid": "F:0"}], "a missing value last"
    assert store.by_fields([{"f": "F:1", "v": None}, {"f": "F:1", "v": "V:1"}], "f", "v") == [{"f": "F:1", "v": "V:1"}, {"f": "F:1", "v": None}]


def test_the_checks_are_wired_into_both_workflows():
    harness = (ROOT / ".github" / "workflows" / "harness.yml").read_text(encoding="utf-8")
    demo = (ROOT / ".github" / "workflows" / "demo.yml").read_text(encoding="utf-8")
    assert "tools/check_read_order.py --stores rdflib,rdflib" in harness and "tools/check_run_order.py" in harness
    assert "tools/check_read_order.py --stores neo4j,rdflib" in demo and "tools/check_run_order.py" in demo
