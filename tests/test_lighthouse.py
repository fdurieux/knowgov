"""The lighthouse evaluation protocol (task-0069): the document names the seven criteria, states
executing business actions out of scope with the reason, keeps the pilot's evidence private, and
the evidence script's summary reads a collection. Standard library only."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "docs" / "lighthouse-evaluation.md"
sys.path.insert(0, str(ROOT / "tools"))

CRITERIA = ["Semantic modelling", "Traceability", "Knowledge quality", "Agent grounding",
            "Operational safety", "Interoperability", "Performance and cost"]


def test_the_protocol_names_the_seven_criteria_each_with_the_stack_rehearsal_and_pilot():
    text = DOC.read_text(encoding="utf-8")
    sections = re.split(r"\n### ", text.split("## The seven criteria", 1)[1].split("\n## ", 1)[0])[1:]
    assert [s.splitlines()[0] for s in sections] == CRITERIA
    for s in sections:
        for part in ("**The stack today:**", "**Rehearsal evidence:**", "**Pilot:**"):
            assert part in s, (s.splitlines()[0], part)


def test_actions_are_out_of_scope_with_the_reason_and_the_pilot_evidence_stays_private():
    text = DOC.read_text(encoding="utf-8")
    out = text.split("## Out of scope: executing business actions", 1)[1].split("\n## ", 1)[0]
    assert "criterion 6" in out and "executes" in out and "pull request" in out
    pilot = text.split("## The pilot checklist", 1)[1]
    assert "private record" in pilot and pilot.count("- [ ] ") >= 8
    # no banking scenario: the word appears only where it is excluded
    for line in text.splitlines():
        if re.search(r"\bbank", line, re.I):
            assert re.search(r"\bno\b", line, re.I), line


def test_the_script_names_every_evidence_item_the_task_asks_for():
    import lighthouse_evidence as lh
    doc = lh.__doc__
    for item in ("walk", "gate", "mcp", "invalidation", "export", "cost"):
        assert re.search(rf"^    {item}\b", doc, re.M), item
    assert "example_instance.py" in doc and "pilot" in doc


def test_the_summary_reads_a_collection_and_names_its_failures():
    import lighthouse_evidence as lh
    sub = {"subject": "demo", "walk": {"register_nodes": 3, "starts": {"APP-1": {"edges": 2, "withdrawn": 0, "reached": ["PROC-1"]}},
                                       "statements_at_anchor": {"APP-1": {"statements": 4}}, "statements_scenario": "S1"},
           "gate": {"S1": {"verdict": "PROCEED", "exit_code": 0, "record_verdict": "PROCEED"}},
           "mcp": {"S1": {"gate_verdict_equals_gate_cli": True, "store_unchanged": True,
                          "three_valued": {"a|b": {"answer": "unknown"}}}},
           "invalidation": {"S6": {"artefact": "doc.md", "version": "v2", "invalidated": ["x@v1"],
                                   "before_reverification": {"verdict": "BLOCKED"},
                                   "after_reverification": {"verdict": "PROCEED", "exit_code": 1, "suspect_derived": ["d"],
                                                            "superseded_by": {"x@v1": ["x@v2"]}}}},
           "export": {"manifest": "m.toml", "files": 2, "digest_match": 2, "reconcile": {"present": True}},
           "timings_s": {"gate S1": 1.0}, "store_census": {"nodes": 5, "relationships": 6}}
    text = lh.summary({"store": "rdflib", "instance_unchanged": True, "subjects": [sub], "failures": ["demo: one"]})
    assert "S1 PROCEED (exit 0; record PROCEED)" in text and "x@v1 → x@v2" in text
    assert "2 digest(s) match" in text and "out of scope" in text and "- demo: one" in text
