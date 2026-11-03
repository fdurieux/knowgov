"""Task-0038 (doc-0007 F3): a person's statement against the documents' in R-CORROBORATE and
R-CONFLICT, through a store stand-in that pairs as the adapters do (same version, or across
versions when exactly one side carries the basis named). The values are S2's: the contract's and
the spec's status lists, and employee-1's with held_unscreened. The store half, on the example
instance, is tools/check_capture_pairing.py: harness.yml runs it on rdflib, the stack job on Neo4j."""
from __future__ import annotations

import re
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(Path(__file__).resolve().parent)]
try:
    import extract  # noqa: F401  (needs PyYAML, which the stdlib test job lacks)
except ImportError:
    # rules.py takes only NONE from extract.py; stand in with the value the file defines
    _none = re.search(r'^NONE = "([^"]*)"$', (ROOT / "harness" / "extract.py").read_text(encoding="utf-8"), re.M).group(1)
    sys.modules["extract"] = types.SimpleNamespace(NONE=_none)
import rules  # noqa: E402

KEY = "response|statuses"
DOC = "error: store_unavailable|quoted|refused_screening|rejected: invalid_request|review_hold"
HELD = "error: store_unavailable|held_unscreened|quoted|refused_screening|rejected: invalid_request|review_hold"
CAP = "A:cap:2026-11-02-ORG-0002-employee-1:1@capture"


class PairStore:
    """candidate_pairs, corroborate and mark_conflict over a list of assertions, as both adapters do."""

    def __init__(self, xs: list[dict]):
        self.x = {a["id"]: dict(a) for a in xs}
        self.agree, self.gaps = set(), {}

    def candidate_pairs(self, across=None):
        dead = ("rejected", "deprecated", "invalidated")
        out = []
        for a in self.x.values():
            for b in self.x.values():
                if not a["id"] < b["id"] or a["key"] != b["key"] or a["artefact"] == b["artefact"]:
                    continue
                if a["status"] in dead or b["status"] in dead:
                    continue
                if a["version"] != b["version"] and (across is None or (a["basis"] == across) == (b["basis"] == across)):
                    continue
                out.append({"a": a["id"], "va": a["value"], "ba": a["basis"], "aa": a["artefact"], "b": b["id"], "vb": b["value"],
                            "bb": b["basis"], "ab": b["artefact"], "key": a["key"], "pred": a["key"].split("|", 1)[1]})
        return out

    def corroborate(self, a, b, promote=True):
        self.agree.add(frozenset((a, b)))
        for i in (a, b):
            if promote and self.x[i]["status"] == "proposed":
                self.x[i]["status"] = "validated"

    def mark_conflict(self, a, b, gid, key, scenario, text=None):
        self.x[a]["status"] = self.x[b]["status"] = "disputed"
        self.gaps[gid] = {"concerns": {a, b}, "text": text or f"two artefacts state different values for {key}"}


def _x(aid, value, basis="extracted", status="proposed", artefact=None, version="v1", key=KEY):
    return {"id": aid, "value": value, "basis": basis, "status": status, "artefact": artefact or aid.split(":")[1],
            "version": version, "key": key}


def _s2(*captures: dict) -> PairStore:
    """S2's two document statements of the status list, corroborating each other, plus captures."""
    st = PairStore([_x("A:oas:response|statuses@v1", DOC, artefact="contract/openapi.yaml"),
                    _x("A:spec:response|statuses@v1", DOC, artefact="contract/spec.md"), *captures])
    assert rules.r_corroborate(st) == 1 + 2 * sum(c["value"] == DOC for c in captures)
    return st


def _cap(value, i=1, **kw):
    return _x(f"A:cap:2026-11-02-ORG-0002-employee-1:{i}@capture", value, basis="elicited",
              artefact="minutes/2026-11-02.md", version="capture", **kw)


def test_without_a_capture_the_documents_pair_and_corroborate_as_before():
    st = _s2()
    assert all(x["status"] == "validated" for x in st.x.values()) and rules.r_conflict(st, "S2") == [] and not st.gaps


def test_a_capture_on_s2_that_contradicts_the_documents_raises_a_conflict_with_each():
    st = _s2(_cap(HELD))
    out = rules.r_conflict(st, "S2")
    assert sorted((c["a"], c["b"]) for c in out) == [(CAP, "A:oas:response|statuses@v1"), (CAP, "A:spec:response|statuses@v1")], out
    assert {x["id"]: x["status"] for x in st.x.values()} == {CAP: "disputed", "A:oas:response|statuses@v1": "disputed",
                                                             "A:spec:response|statuses@v1": "disputed"}
    for gid, g in st.gaps.items():
        other = (g["concerns"] - {CAP}).pop()
        assert CAP in g["concerns"] and gid == f"gap:conflict:{KEY}:{CAP}~{other}", gid
        assert g["text"].startswith(f"a person and a document state different values for {KEY}: minutes/2026-11-02.md says {HELD}; contract/"), g


def test_a_capture_on_s2_that_agrees_corroborates_and_raises_nothing():
    st = PairStore([_x("A:c4:quote_api|technology@v1", "Python 3.12, FastAPI", artefact="architecture/c4.dsl", key="quote_api|technology"),
                    _cap("Python 3.12, FastAPI", 2, key="quote_api|technology")])
    assert rules.r_corroborate(st) == 1 and rules.r_conflict(st, "S2") == []
    assert st.agree == {frozenset(("A:c4:quote_api|technology@v1", "A:cap:2026-11-02-ORG-0002-employee-1:2@capture"))}
    assert all(x["status"] == "proposed" for x in st.x.values()), st.x   # the person's stays proposed, the document's too
    # agreeing with the documents' validated list: recorded, and nothing rises or falls
    st = _s2(_cap(DOC))
    assert len(st.agree) == 3 and rules.r_conflict(st, "S2") == []
    assert st.x[CAP]["status"] == "proposed" and st.x["A:oas:response|statuses@v1"]["status"] == "validated"


def test_nobody_knows_pairs_with_nothing_and_a_person_is_not_weighed_against_a_model():
    st = _s2(_cap(""), _x("A:llm:x@v1", HELD, basis="inferred", artefact="llm", version="v1"))
    llm_vs_cap = [p for p, _ in rules.pairs(st) if {p["a"], p["b"]} == {CAP, "A:llm:x@v1"}]
    assert llm_vs_cap == [] and not any(CAP in g["concerns"] for g in st.gaps.values())
    rules.r_conflict(st, "S2")
    assert st.x[CAP]["status"] == "proposed" and not any(CAP in g["concerns"] for g in st.gaps.values())


def test_the_documents_conflict_ids_keep_their_numbering_beside_a_person_s():
    """The comparator normalises gap:conflict:<key>:<n>; a person's conflicts take a pair id and no number."""
    st = PairStore([_x("A:dt:k|v@v1", "1", key="k|v"), _x("A:seq:k|v@v1", "2", key="k|v"), _cap("3", key="k|v")])
    rules.r_conflict(st, "S1")
    assert sorted(g for g in st.gaps if g.endswith(":0") or g.endswith(":1")) == ["gap:conflict:k|v:0"], sorted(st.gaps)


def test_both_adapters_pair_across_versions_by_a_named_basis_and_ci_runs_the_instance_check():
    for name in ("store_neo4j.py", "store_rdflib.py"):
        src = (ROOT / "harness" / name).read_text(encoding="utf-8")
        assert "def candidate_pairs(self, across=None)" in src and "def corroborate(self, a, b, promote=True)" in src
        assert "elicited" not in src
    assert 'candidate_pairs(across=PERSON)' in (ROOT / "harness" / "rules.py").read_text(encoding="utf-8")
    for wf in ("harness.yml", "demo.yml"):
        assert "tools/check_capture_pairing.py" in (ROOT / ".github" / "workflows" / wf).read_text(encoding="utf-8"), wf
