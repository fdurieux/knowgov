---
id: TASK-0214
title: >-
  The kit's per-statement claim field (observed, inferred, intended) read by the
  mappers into the basis (decision-0018 point 3)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-08T11:17:00Z'
updated_date: '2026-11-08T13:04:00Z'
labels:
  - process
  - reverse-engineering
  - contract
  - mappers
dependencies: []
references:
  - >-
    backlog/decisions/decision-0018 -
    Reverse-engineering-and-knowledge-gap-identification-is-an-eight-step-process-knowgov-routes-and-re-finds-its-gaps-and-its-three-contract-changes-land-in-0.9.0.md
documentation:
  - >-
    backlog/docs/doc-0032 -
    Reverse-engineering-and-knowledge-gap-identification-as-a-repeatable-process-eight-steps-with-their-tools-and-gaps-the-bases-decision-0011-H7-and-what-F2-must-bind.-Opportunity-canvas-fit-gap-SWOT-advice.md
priority: high
type: feature
ordinal: 214000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0018 point 3 (the maintainer, 2026-11-08, answering doc-0032 §11 question 3; doc-0032 §3). A kit statement carries an optional claim: observed (what the pinned original does), inferred (a proposed explanation or generalised rule) or intended (accepted by the responsible authority). The five bundle mappers (requirements_json, contracts_markdown, dmn_decisions, plantuml_realises, gherkin_tagged) read it into the basis: observed to extracted, inferred to inferred (never above proposed, harness/policy.md rule 2; a ruling refuses to approve it since task-0199 I4), intended to authored (approved only under an attestation, decision-0009 and decision-0019). A statement without claim loads as today (extracted), so the vendored kits and the scored record do not move. A contract change (the kit format), for 0.9.0 (doc-0028 G9-12).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Each of the five mappers reads claim when present and maps observed, inferred and intended to extracted, inferred and authored; a statement without claim loads as today
- [x] #2 An inferred statement never rises above proposed on either store, and a ruling approving it is refused (task-0199 I4), shown by a probe kit
- [x] #3 subjects/README.md and instance/mappers.toml document the field per mapper, and tools/check_subject.py refuses an unknown claim value
- [x] #4 CHANGELOG.md carries the line under Unreleased's contract heading
- [x] #5 The scored record (S1 to S7), the deterministic run and the comparator stay equal
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/extract.py: CLAIMS (observed->extracted, inferred->inferred, intended->authored), claim_of (UnknownClaim on an unknown value), _basis (the most conservative claim among the statements an assertion rests on; no claim counts as the mapper's own basis). 2. The five bundle mappers read it: requirements_json an item's claim; contracts_markdown a part's 'Claim:' line; dmn_decisions 'claim:' in a decision's or rule's description; gherkin_tagged '@claim:' on the Feature, a Rule or a Scenario, the nearest winning; plantuml_realises a "' claim:" comment line. 3. harness/load.py execution_map: an inferred verified_by link derives no execution. 4. harness/shacl.py: the inferred-assertion shape accepts a fragment-backed statement beside a gap candidate. 5. tools/check_subject.py: rule claim (schema enum, additive). 6. tools/fixtures/claim_probe + tools/check_claim_probe.py on both stores (harness.yml rdflib-readers, demo.yml stack); tests/test_claim.py. 7. subjects/README.md 'The claim', instance/mappers.toml, the wizard's reference part regenerated, CHANGELOG contract line.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Verified 2026-11-08, Python 3.12 venv with the CI pins (and the neo4j 6.4.1 driver against a local Neo4j 5.26.0 community tarball, Java 21):
- tools/check_claim_probe.py: every check holds on rdflib and on Neo4j, 25 statements in five mappers. The gate (codegen) reads QUALIFIED, with CLM-002 (inferred) and CLM-005 (observed, its only verifying link inferred) proposed. A ruling approving the inferred statement is refused (I4); rejecting it is not. A claim 'guessed' is refused by check_subject under rule claim, and the mapper raises.
- SHACL main conforms on the probe, 0 results (the inferred shape's sh:or).
- tests/run_tests.py: with the pins (KG_TEST_REQUIRE=rdflib,node,openai), 763/764 passed, 1 skipped (hook-live), 0 failed. Without PyYAML (a bare 3.13 venv, the tests job's interpreter), 720/764 passed, 44 skipped, 0 failed, and the same on the J-F pass (KG_SUBJECT=subjects/jef_data_load).
- The record: S1-S7 on rdflib against the record, 0 differing leaves over 7 scenarios. J-F C and D1-D5, 0 differing leaves over 6.
- check_round_trip --chain rdflib,rdflib: every answer survives, on CargoQuote S1-S7 and on J-F C,D3 with --expect-parts. On Neo4j to rdflib and back, S1,S5.
- check_mcp_server on rdflib: every check holds, CargoQuote S1,S2,S6 and J-F C,D3.
- check_subject: cargo_quote, jef_data_load and the probe hold. wizard.py --check fresh.
Choices made, beyond the ACs' letter:
- the per-mapper syntax above;
- an assertion resting on statements of different claims takes the most conservative (inferred, then extracted, then authored, no claim counting as the mapper's basis);
- an inferred verified_by link derives no execution (otherwise an inference would raise another statement to verified);
- the SHACL inferred shape widened to accept a fragment-backed statement (no record scenario trips it; comparator identical).

2026-11-08, after review: the coordinating session accepted the four choices above as taken. They are (1) the per-mapper syntax, (2) the most conservative basis for mixed claims, (3) an inferred verified_by link deriving no execution, and (4) the SHACL shape accepting a fragment-backed inferred statement. All four are named in subjects/README.md, "The claim". Merged origin/main at 3b931bb (task-0215's intended bar); CHANGELOG.md resolved with both contract lines, ours after it, and 0.8.0 byte-identical.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The kit's per-statement claim (decision-0018 point 3). The five bundle mappers read observed, inferred and intended into extracted, inferred and authored: requirements_json an item's claim, contracts_markdown a part's Claim: line, dmn_decisions claim: in a decision's or rule's description, gherkin_tagged an @claim: tag on the Feature, a Rule or a Scenario, plantuml_realises a ' claim: comment line. An assertion resting on statements of different claims takes the most conservative. A statement without a claim loads as before, so the public kits and the scored record do not move (comparator identical on S1-S7 and J-F). Inferred stays proposed on both stores: nothing verifies it, a ruling approving it is refused (I4), and an inferred verified_by link derives no execution. check_subject refuses an unknown claim (rule claim, additive in the schema); the load fails on it. tools/fixtures/claim_probe and tools/check_claim_probe.py prove every mapping on rdflib and Neo4j (harness.yml rdflib-readers, demo.yml stack). Documented in subjects/README.md (The claim), instance/mappers.toml and the onboarding skill's generated reference part; a CHANGELOG contract line for 0.9.0. Also: the SHACL inferred shape accepts a fragment-backed statement.
<!-- SECTION:FINAL_SUMMARY:END -->
