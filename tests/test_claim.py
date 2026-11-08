"""task-0214 (decision-0018 point 3, doc-0032 §3): the kit's per-statement claim, read by the five bundle mappers
into the basis. The mappers' half needs PyYAML (extract.py imports it) and, for plantuml_realises, pumllint: it
skips naming rdflib where they are absent, and the rdflib job, which installs the pins, requires it. The store
half, the ceiling on both adapters and the ruling refused, is tools/check_claim_probe.py: harness.yml runs it on
rdflib, the stack job on Neo4j."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(Path(__file__).resolve().parent)]
from _skip import skip  # noqa: E402

BUNDLE = ("requirements_json", "contracts_markdown", "dmn_decisions", "gherkin_tagged", "plantuml_realises")
DMN = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="https://www.omg.org/spec/DMN/20191111/MODEL/" id="d" name="d" namespace="urn:t">
  <decision id="gate" name="gate">{dec}
    <decisionTable id="t">
      <rule id="r1"><description>{r1}AB-001</description></rule>
      <rule id="r2"><description>AB-002</description></rule>
    </decisionTable>
  </decision>
</definitions>"""


def _extract():
    try:
        import extract
    except ModuleNotFoundError as e:
        skip("rdflib", f"{e.name} is not installed: the mappers need the pins")
    return extract


def _bases(bag) -> dict[str, str]:
    return {f"{a['entity']}|{a['predicate']}": a["basis"] for a in bag.assertions}


def _run(x, mapper: str, path: str, text: str):
    """``mapper`` on ``text`` whatever subject the test process bound extract.py to: the path given a short name
    and the default requirement-id shape for the call, both restored after it."""
    saved_re, had, prev = x._REQ_ID, path in x._SHORT, x._SHORT.get(path)
    x._REQ_ID = re.compile(r"\b([A-Z]{2,}-\d{2,})\b")
    x._SHORT[path] = prev or "tc"
    try:
        return x.EXTRACTORS[mapper](path, text)
    finally:
        x._REQ_ID = saved_re
        if had:
            x._SHORT[path] = prev
        else:
            x._SHORT.pop(path, None)


def _part(rel: str, text: str) -> str:
    return f"==> {rel} <==\n{text}\n"


def test_requirements_json_reads_each_claim_and_no_claim_as_before():
    x = _extract()
    items = [{"id": "AB-001", "statement": "a"}, {"id": "AB-002", "statement": "b", "claim": "observed"},
             {"id": "AB-003", "statement": "c", "claim": "Inferred"}, {"id": "AB-004", "statement": "d", "claim": "intended"}]
    got = _bases(_run(x, "requirements_json", "r.json", json.dumps(items)))
    assert got == {"AB-001|statement": "extracted", "AB-002|statement": "extracted",
                   "AB-003|statement": "inferred", "AB-004|statement": "authored"}, got


def test_contracts_markdown_a_part_claims_its_citations_and_mixed_takes_the_most_conservative():
    x = _extract()
    text = (_part("a.md", "# A\n\nClaim: inferred\n\nAB-001 and AB-002.") + _part("b.md", "# B\n\nAB-002 and AB-003.")
            + _part("c.md", "# C\n\nclaim: observed\n\nAB-004."))
    got = _bases(_run(x, "contracts_markdown", "contracts/", text))
    assert got == {"AB-001|elaborated_by": "inferred", "AB-002|elaborated_by": "inferred",   # inferred beside no claim
                   "AB-003|elaborated_by": "authored", "AB-004|elaborated_by": "extracted"}, got


def test_dmn_decisions_a_rules_claim_wins_over_its_decisions():
    x = _extract()
    got = _bases(_run(x, "dmn_decisions", "dmn/", _part("t.dmn", DMN.format(dec="<description>claim: intended</description>",
                                                                           r1="claim: observed "))))
    assert got == {"dmn:gate|rules": "extracted", "AB-001|decided_by": "extracted", "AB-002|decided_by": "authored"}, got
    plain = _bases(_run(x, "dmn_decisions", "dmn/", _part("t.dmn", DMN.format(dec="", r1=""))))
    assert set(plain.values()) == {"authored"}, plain


def test_gherkin_tagged_the_nearest_tag_wins():
    x = _extract()
    feature = """@claim:intended
Feature: f

  @AB-001
  Scenario: one
    Then a

  @AB-002 @claim:observed
  Scenario: two
    Then b

  @claim:inferred
  Rule: r

    @AB-003
    Scenario: three
      Then c
"""
    got = _bases(_run(x, "gherkin_tagged", "features/", _part("f.feature", feature)))
    assert got == {"AB-001|verified_by": "authored", "AB-002|verified_by": "extracted", "AB-003|verified_by": "inferred",
                   "feature:f|scenarios": "inferred"}, got


def test_plantuml_realises_a_comment_claims_the_diagram():
    x = _extract()
    try:
        import pumllint  # noqa: F401
    except ModuleNotFoundError:
        skip("rdflib", "pumllint is not installed: the PlantUML mapper imports its parser")
    d = "@startuml d\n' claim: inferred\nA -> B : x\nfooter realises AB-001\n@enduml"
    got = _bases(_run(x, "plantuml_realises", "uml/", _part("d.puml", d)))
    assert got == {"diagram:d|type": "inferred", "diagram:d|elements": "inferred", "AB-001|realised_by": "inferred"}, got


def test_an_unknown_claim_is_refused_by_every_mapper():
    x = _extract()
    bad = {
        "requirements_json": ("r.json", json.dumps([{"id": "AB-001", "statement": "a", "claim": "guessed"}])),
        "contracts_markdown": ("contracts/", _part("a.md", "Claim: guessed\n\nAB-001.")),
        "dmn_decisions": ("dmn/", _part("t.dmn", DMN.format(dec="", r1="claim: guessed "))),
        "gherkin_tagged": ("features/", _part("f.feature", "Feature: f\n\n  @AB-001 @claim:guessed\n  Scenario: s\n    Then a\n")),
    }
    for mapper, (path, text) in bad.items():
        try:
            _run(x, mapper, path, text)
        except x.UnknownClaim as e:
            assert "guessed" in str(e), (mapper, e)
        else:
            raise AssertionError(f"{mapper} read a claim 'guessed' instead of refusing it")


def test_the_public_kits_carry_no_claim_so_nothing_moves():
    x = _extract()
    from subject import Subject
    for sid in ("jef_data_load",):
        sub = Subject(ROOT / "subjects" / sid)
        for key, p in sub.kit_files:
            mapper = sub.mappers.get(key)
            if mapper in BUNDLE and mapper != "plantuml_realises":
                bag = _run(x, mapper, key, sub.artefact_text(key))
                assert not any(a["basis"] == "inferred" for a in bag.assertions), (sid, key)
                want = "extracted" if mapper == "requirements_json" else "authored"
                assert {a["basis"] for a in bag.assertions} == {want}, (sid, key, {a["basis"] for a in bag.assertions})


def test_the_claim_is_documented_per_mapper_and_the_probe_runs_on_both_stores():
    readme = (ROOT / "subjects" / "README.md").read_text(encoding="utf-8")
    section = readme.split("## The claim", 1)[1].split("\n## ", 1)[0]
    for m in BUNDLE:
        assert f"`{m}`" in section, m
    for c in ("observed", "inferred", "intended"):
        assert f"`{c}`" in section, c
    import tomllib
    table = tomllib.loads((ROOT / "instance" / "mappers.toml").read_text(encoding="utf-8"))["mapper"]
    for m in BUNDLE:
        assert re.search(r"claim", table[m]["reads"], re.I), m
    for wf in ("harness.yml", "demo.yml"):
        assert "tools/check_claim_probe.py" in (ROOT / ".github" / "workflows" / wf).read_text(encoding="utf-8"), wf
    schema = (ROOT / "harness" / "schemas" / "subject-check.schema.json").read_text(encoding="utf-8")
    assert '"zero-yield", "claim"]' in schema   # the subject check's rule, additive
