"""Task-0201, doc-0030 F5 (G3, M4, G8, S4, S2's declared_gaps_for_key): one definition per concept.
tools/check_one_definition.py holds it end to end on the example instance; it runs here on rdflib, and in CI on
rdflib (harness.yml) and on Neo4j (demo.yml's stack job). The unit tests below need no store."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(Path(__file__).resolve().parent)]
from _skip import need_rdflib  # noqa: E402
import store  # noqa: E402

TOOL = "tools/check_one_definition.py"


class Rows:
    def __init__(self, rows):
        self.rows = rows

    def assertions_on_key(self, key, statuses):
        return [r for r in self.rows if r["status"] in statuses]


def test_m4_a_key_whose_statements_are_disputed_is_asserted_and_names_them():
    import gate
    ans = gate.three_valued(Rows([{"id": "A:b", "value": "x", "status": "disputed"}, {"id": "A:a", "value": "y", "status": "disputed"}]), "k|a")
    assert ans["answer"] == "asserted" and ans["disputed"] == ["A:a", "A:b"] and "disagree" in ans["why"], ans


def test_m4_an_answer_without_a_dispute_reads_as_before():
    import gate
    rows = [{"id": "A:a", "value": "NONE", "status": "approved"}]
    assert gate.three_valued(Rows(rows), "k|a") == {"answer": "documented_absent", "assertions": rows}
    assert gate.three_valued(Rows([]), "k|a")["answer"] == "unknown"


NODES = {"N1": {"owner": "ORG-1", "name": "one"}, "N2": {"owner": "ORG-2", "name": "two"}}


def test_g8_routing_names_where_each_key_is_written():
    import capture
    rmap = {"row": [{"key": "a|x", "nodes": ["N1", "N2"], "owner": "ORG-2"}, {"key": "b|x", "nodes": ["N1", "N2"]},
                    {"key": "c|x", "nodes": []}, {"key": "d|x", "nodes": ["N1"], "owner": "ORG-9"}]}
    r = capture.routing(rmap, NODES)
    assert r["a|x"] == {"units": ["ORG-2"], "unit": "ORG-2", "files": ["ORG-2"]}
    assert r["b|x"] == {"units": ["ORG-1", "ORG-2"], "unit": None, "files": ["ORG-1", "ORG-2"]}
    assert r["c|x"] == {"units": [], "unit": None, "files": [capture.UNASSIGNED]}
    assert r["d|x"]["unit"] == "ORG-1"   # a row owner that owns none of its nodes does not answer for it
    route = capture.questionnaire_route("sub", "S2", "codegen", None, r["b|x"]["files"])
    assert "DIR/questionnaire-sub-S2-ORG-1.toml or DIR/questionnaire-sub-S2-ORG-2.toml" in route and "-unassigned" not in route, route
    assert "DIR/questionnaire-sub-S2-ORG-2.toml," in capture.questionnaire_route("sub", "S2", "codegen", "ORG-2", r["a|x"]["files"])


def test_g8_every_owner_reader_goes_through_routing():
    cap = (ROOT / "harness" / "capture.py").read_text(encoding="utf-8")
    for fn in ("def answering_owners", "def finding_owners", "def questionnaires"):
        body = cap[cap.index(fn):][:1600]
        assert "routing(" in body, fn
    rc = (ROOT / "harness" / "register_change.py").read_text(encoding="utf-8")
    assert "capture.routing(" in rc and 'row.get("owner")' not in rc


def test_s4_one_uniqueness_rule_named_in_the_port():
    assert set(store.NEO4J_GUARDED) <= set(store.UNIQUE_IDS) and {"Derived", "Activity"} <= set(store.UNIQUE_IDS)
    import store_neo4j
    held = {q.split("FOR (n:")[1].split(")")[0] for kind, q in store_neo4j.CONSTRAINTS if kind == "uniqueness"}
    assert set(store.UNIQUE_IDS) == held | set(store.NEO4J_GUARDED), "every unique label held by a constraint or a guard"
    st = object.__new__(store_neo4j.Neo4jStore)
    st.run = lambda cypher, **kw: [{"n": 1}]
    try:
        st.register_derived("derived:x", "code", "s", [])
    except ValueError as e:
        assert "uniqueness constraint refuses it" in str(e)
    else:
        raise AssertionError("the Neo4j adapter took a Derived id it holds")


def test_g3_the_gate_reads_supersession_from_the_stale_successors():
    src = (ROOT / "harness" / "gate.py").read_text(encoding="utf-8")
    body = src[src.index("def resolve_spec"):src.index("def preload_behind")]
    assert "superseded_by(x)" in body and 'r["status"] in ("verified", "approved") or r.get("lapsed")' not in body


def test_the_check_holds_on_rdflib():
    need_rdflib()
    with tempfile.TemporaryDirectory() as td:
        env = {**os.environ, "KG_STORE": "rdflib", "PYTHONDONTWRITEBYTECODE": "1"}
        env.pop("KG_RDFLIB_FILE", None)
        p = subprocess.run([sys.executable, str(ROOT / TOOL), str(Path(td) / "out")], env=env, cwd=ROOT,
                           capture_output=True, text=True, timeout=1500)
        assert p.returncode == 0 and "every check holds" in p.stdout, p.stdout[-3000:] + p.stderr[-1500:]


def test_ci_runs_it_on_both_stores():
    assert f"KG_STORE=rdflib python {TOOL} runs/one-definition" in (ROOT / ".github" / "workflows" / "harness.yml").read_text(encoding="utf-8")
    assert f"python {TOOL} runs/one-definition" in (ROOT / ".github" / "workflows" / "demo.yml").read_text(encoding="utf-8")
