"""The store's reads answer in one order on both adapters (doc-0020 follow-up, #243's stack red): a
collect() answers in the store's traversal order, which a reload can move, and the gate prints what it
reads: the bundle's suspect line, its stale statements with their verifications and successors, each
key's evidence. So every row and every collected list is by id (fragments by their fields), and the
same knowledge stored in another order renders the same bundle and the same gate report.

The Neo4j adapter is exercised on a fake driver result whose rows and lists come shuffled (stdlib); the
rdflib adapter on two stores built through the port's own writes in opposite orders (the pins)."""
from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT)]
import store  # noqa: E402
from tests._skip import need_rdflib  # noqa: E402

DAY = "2026-11-04"


class _Fake:
    """A Neo4jStore without a driver: ``run`` answers the rows it is handed, shuffled per call."""

    def __init__(self, rows, seed):
        self.rows, self.rng = rows, random.Random(seed)

    def __call__(self, cypher, **params):
        out = []
        for r in self.rows:
            r = {k: (self.rng.sample(v, len(v)) if isinstance(v, list) else v) for k, v in r.items()}
            out.append(r)
        return self.rng.sample(out, len(out))


def _neo4j(rows, seed):
    import store_neo4j
    st = object.__new__(store_neo4j.Neo4jStore)
    st.run = _Fake(rows, seed)
    return st


def test_by_id_puts_rows_without_an_id_last_and_by_content_is_total():
    assert store.by_id([{"id": "b"}, {"id": None}, {"id": "a"}]) == [{"id": "a"}, {"id": "b"}, {"id": None}]
    rows = [{"locator": "L2", "text": "x"}, {"locator": "L1", "text": "y"}, {"locator": "L1", "text": "a"}]
    assert store.by_content(rows) == store.by_content(list(reversed(rows)))


def test_neo4j_reads_answer_one_order_whatever_order_the_driver_returns():
    suspect = [{"id": f"derived:{d}", "kind": "python module", "sha256": "0" * 64,
                "used_invalidated": ["A:dt:P2|threshold@v1", "A:dt:P2|surcharge@v1", "A:dt:P3|order@v1"]} for d in "ba"]
    stale = [{"id": f"A:k|{k}@v1", "key": f"k|{k}", "value": "1", "invalidated_by": "v2",
              "verifications": [{"id": f"ver:{k}:{i}", "valid_until": "v2"} for i in range(3)],
              "successors": [{"id": f"A:k|{k}#{i}@v2", "value": "2", "status": "proposed"} for i in range(3)]} for k in "cab"]
    evidence = [{"id": f"A:k|a#{i}@v1", "value": "1", "text": "t", "basis": "extracted", "status": "verified",
                 "artefact": "doc.md", "agent": "x",
                 "fragments": [{"locator": f"L{j}", "text": "t", "artefact": "doc.md"} for j in range(4)],
                 "verifications": [{"id": f"ver:{j}", "method": "review", "scope": "s", "at": DAY, "valid_until": None} for j in range(3)],
                 "approvals": [{"id": f"ap:{j}", "at": DAY, "record": "r"} for j in range(2)],
                 "gaps": [{"id": f"G-{j}", "kind": "ambiguous", "declared": False, "text": "?"} for j in range(2)]} for i in range(2)]
    for read, rows, call in (("suspect_derived", suspect, lambda s: s.suspect_derived()),
                             ("stale_on_keys", stale, lambda s: s.stale_on_keys(["k|a", "k|b", "k|c"])),
                             ("key_evidence", evidence, lambda s: s.key_evidence("k|a", ["verified"]))):
        answers = [call(_neo4j(rows, seed)) for seed in range(8)]
        assert all(a == answers[0] for a in answers), read
    got = _neo4j(suspect, 3).suspect_derived()
    assert [d["id"] for d in got] == ["derived:a", "derived:b"]
    assert got[0]["used_invalidated"] == ["A:dt:P2|surcharge@v1", "A:dt:P2|threshold@v1", "A:dt:P3|order@v1"]


def _build(rdf, order):
    """Three keys, each with a verified statement on two fragments, a derived output built on all of them;
    a change invalidates the three keys and two successors land on each. ``order`` reverses every write."""
    st = rdf.RdflibStore(path="")
    seq = (lambda xs: list(reversed(xs))) if order else list
    st.ensure_agents("knowgov", "1", {"id": "agent:human", "name": "h"}, {"id": "agent:llm", "name": "l"})
    st.create_activity("act:extract:S0:v1", "extraction", DAY, "t", "", "agent:harness")
    st.upsert_artefact_version("doc.md", "prose", "md", "ver:doc@v1", "0" * 64, 1, DAY, "v1", "act:extract:S0:v1")
    keys = seq(["k|a", "k|b", "k|c"])
    for k in keys:
        st.ensure_entity(f"ent:{k}", "rule", k)
        for j in seq([0, 1]):
            st.create_fragment("ver:doc@v1", f"frag:{k}:{j}", f"L{j}", "0" * 64, f"text {j}", "doc.md")
    for k in keys:
        st.create_assertion({"id": f"A:{k}@v1", "predicate": "p", "value": "1", "text": f"{k} is 1", "basis": "extracted",
                             "status": "proposed", "artefact": "doc.md", "key": k, "version": "v1"},
                            f"ent:{k}", "act:extract:S0:v1", "agent:harness", seq([f"frag:{k}:0", f"frag:{k}:1"]))
        st.verify_by_review(k, ["1"], DAY, "review", "agent:human")
    st.register_derived("derived:S0:G:run1", "python module", "f" * 64, seq([f"A:{k}@v1" for k in ["k|a", "k|b", "k|c"]]))
    st.invalidate_keys({k: "v2" for k in keys})
    for k in keys:
        for i in seq([0, 1]):
            st.create_assertion({"id": f"A:{k}#{i}@v2", "predicate": "p", "value": "2", "text": f"{k} is 2", "basis": "extracted",
                                 "status": "proposed", "artefact": "doc.md", "key": k, "version": "v2"},
                                f"ent:{k}", "act:extract:S0:v1", "agent:harness", [f"frag:{k}:0"])
    return st


def test_the_same_knowledge_stored_in_another_order_renders_the_same_bundle_and_gate_report():
    rdf = need_rdflib()
    import gate
    spec = {"keys": ["k|a", "k|b", "k|c"], "block_levels": ["unknown"], "max_unverified_share": 1.0}
    out = []
    for order in (False, True):
        st = _build(rdf, order)
        reads = (st.suspect_derived(), st.stale_on_keys(spec["keys"]), [st.key_evidence(k, ["proposed", "verified"]) for k in spec["keys"]])
        res = gate.resolve_spec(st, "keys", spec, DAY)
        out.append((reads, res, gate.render_bundle(res, "policy")))
    assert out[0][0] == out[1][0]   # the adapter's reads
    assert out[0][1] == out[1][1]   # the gate's result, which its report prints
    assert out[0][2] == out[1][2]   # the bundle the governed arm and the MCP server's evidence_bundle read
    suspect = out[0][0][0]
    assert suspect and suspect[0]["used_invalidated"] == ["A:k|a@v1", "A:k|b@v1", "A:k|c@v1"]
