"""The lighthouse evaluation protocol (task-0069): the document names the seven criteria, states
executing business actions out of scope with the reason, keeps the pilot's evidence private, and
the evidence script's summary reads a collection. Standard library only."""
from __future__ import annotations

import os
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
    sub = {"subject": "demo", "walk": {"register_nodes": 3, "starts": {"APP-1": {"edges": 2, "not_followed": 0, "reached": ["PROC-1"]}},
                                       "statements_at_anchor": {"APP-1": {"statements": 4}}, "statements_scenario": "S1"},
           "gate": {"S1": {"verdict": "PROCEED", "exit_code": 0, "record_verdict": "PROCEED",
                           "classes": {"codegen": {"verdict": "PROCEED", "exit_code": 0}, "design": {"verdict": "QUALIFIED", "exit_code": 0}}}},
           "mcp": {"S1": {"task_classes": ["codegen", "design"], "gate_verdict_equals_gate_cli": True, "store_unchanged": True,
                          "three_valued": {"a|b": {"answer": "unknown"}}}},
           "invalidation": {"S6": {"artefact": "doc.md", "version": "v2", "invalidated": ["x@v1"],
                                   "before_reverification": {"verdict": "BLOCKED"},
                                   "after_reverification": {"verdict": "PROCEED", "exit_code": 1, "suspect_derived": ["d"],
                                                            "superseded_by": {"x@v1": ["x@v2"]}}}},
           "export": {"manifest": "m.toml", "files": 2, "digest_match": 2, "reconcile": {"present": True}},
           "timings_s": {"gate S1": 1.0}, "store_census": {"nodes": 5, "relationships": 6}}
    text = lh.summary({"store": "rdflib", "instance_unchanged": True, "subjects": [sub], "failures": ["demo: one"]})
    assert "S1 PROCEED (exit 0; record PROCEED)" in text and "x@v1 → x@v2" in text
    assert "**Gate, design class** (no record): S1 QUALIFIED (exit 0)" in text and "store_status lists: codegen, design" in text
    assert "2 digest(s) match" in text and "out of scope" in text and "- demo: one" in text


def test_the_http_client_reaches_the_server_and_lists_evidence_bundle():
    """task-0095: --transport http starts mcp_server.py --http on a free loopback port and speaks the
    handshake over POSTs; listing the tools opens no store."""
    import check_mcp_server as cms
    old = os.environ.get("KG_TODAY")
    os.environ["KG_TODAY"] = "2026-11-04"   # the server reads its date at start; the runner refuses the wall clock (task-0100)
    try:
        client = cms.HttpClient()
    finally:
        if old is None:
            os.environ.pop("KG_TODAY")
        else:
            os.environ["KG_TODAY"] = old
    try:
        assert client.url.startswith("http://127.0.0.1:") and client.url.endswith("/mcp")
        names = {t["name"] for t in client.request("tools/list", {})["result"]["tools"]}
        assert {"gate_verdict", "three_valued_answer", "evidence_bundle"} <= names
    finally:
        client.close()
    assert client.p.returncode is not None


def test_the_evidence_reads_the_bundle_through_the_mcp_server():
    """task-0095: criterion 4 is evidenced by the path an agent uses, not by a bundle rebuilt here."""
    import inspect
    import lighthouse_evidence as lh
    src = inspect.getsource(lh.collect_mcp)
    assert 'client.call("evidence_bundle"' in src and "render_bundle" not in inspect.getsource(lh)
    text = DOC.read_text(encoding="utf-8")
    grounding = text.split("### Agent grounding", 1)[1].split("\n### ", 1)[0]
    assert "evidence_bundle" in grounding and "--transport" in text


def test_the_protocol_names_the_class_each_pilot_transition_uses():
    """task-0101: each hook stage (instance/ci/claude/knowgov_hook.py STAGES) names one task class."""
    sys.path.insert(0, str(ROOT / "instance" / "ci" / "claude"))
    import knowgov_hook
    text = DOC.read_text(encoding="utf-8")
    sec = text.split("## Which task class each pilot transition uses", 1)[1].split("\n## ", 1)[0]
    rows = {m.group(1): m.group(2) for m in re.finditer(r"^\| [^|]+ \| `(\w+)` \| `(\w+)` \|", sec, re.M)}
    assert rows == {"spec": "design", "plan": "codegen", "push": "codegen"} and set(rows) == set(knowgov_hook.STAGES)
    assert "--task codegen --task-for spec=design" in sec
    lines = [line for line in text.split("## The seven criteria", 1)[0].splitlines() if line.startswith("| gate |")]
    assert lines and "`design`" in lines[0] and "`codegen`" in lines[0]
