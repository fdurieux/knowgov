---
id: TASK-0357
title: >-
  dmn_decisions: requirement citations in a decision's description are not
  loaded (run finding 3)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-16T04:37:00Z'
updated_date: '2026-11-17T09:04:00Z'
labels:
  - finding
  - reverse-engineering
  - 0.10.0
dependencies: []
type: bug
ordinal: 347000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found 2026-11-16 by the first private reverse-engineering runs (decision-0018's process on a private demonstration case, task-0220): kits written to subjects/README.md by a clean-room extraction session, then loaded by the instance tooling. The maintainer, 2026-11-16: "mint tasks for the five knowgov findings".

extract_dmn_decisions reads <req>|decided_by from the requirement ids a RULE's description cites; ids cited in the DECISION's own description are not read. One run's kit cited at decision level, so no decision-to-requirement link loaded. The claim convention reads both levels (a decision's claim is its rules'), which makes the asymmetry easy to miss; the guide does not state where citations go.

Placement: stating it in the guide and warning are fixes (0.9.x); inheriting decision-level citations into each rule is additive (1.1.0).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 subjects/README.md states where dmn_decisions reads requirement citations: a rule's description, and a decision's own for an id none of its rules cites
- [x] #2 check_subject.py warns on a malformed citation in a decision's or a rule's description (an id-shaped token with the document's id prefix the subject's pattern does not read); a decision-level citation is read, so it is no warning
- [x] #3 A test holds the reading and the warning; jef_data_load's record re-recorded once with every moved leaf accounted for; CargoQuote's record unchanged
- [x] #4 Reader extension (0.10.0): dmn_decisions loads requirement ids cited in a decision's description as that decision's citations, recorded in subjects/README.md and the CHANGELOG under contract changes
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Build the reader extension; run J-F's comparator. 2. It moved the record (actions_gate cites JDL-088 at decision level only: +1 assertion, +1 fragment per scenario, 60 leaves over 6 scenarios), so it is withdrawn and the fix kept: README states rule-level citations; check_subject warns (rule citation) on decision-level ids no rule cites and on id-shaped tokens the pattern does not read. 3. J-F's one warning admitted by name in test_check_subject and harness.yml's rdflib-readers check. 4. Tests; both comparators.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
The maintainer, 2026-11-16: "Yes" to these joining 0.10.0 (decision-0047 point 4): the soak they waited for restarts with 0.10.0 anyway.

Maintainer, 2026-11-16: "keep the JDL-088 warning; drop the reader extension". The reader-extension criterion (dmn_decisions loading a decision's own citations) is removed: built, it moved J-F's record (actions_gate cites JDL-088 in its description and in no rule; +1 assertion, +1 fragment per scenario, 60 leaves over 6 scenarios), so the mapper stays as it was. J-F's one citation warning is admitted by name in tests/test_check_subject.py and harness.yml's rdflib-readers J-F check, each still failing on any other finding.

Rulings. Maintainer, 2026-11-16 21:33, to this session: "keep the JDL-088 warning; drop the reader extension". Superseded by the maintainer, 2026-11-16, through the coordinating session, shown both rulings side by side: "Re-record now, option (b)" ("could we not do (b) now as we are restarting the soak anyway"). #1 to #3 restated for (b): the decision-level citation is read, not warned on, and the record moves once.

Accounting (re-record 52d1594, on Neo4j 5.26.24 community, driver 6.4.1, after task-0369's ordering fix). Against the 2026-11-01 files, 78 leaves over six scenarios (check_run_order sha256 e46adcfc...): 60 the comparator reads, 10 a scenario (load.assertions, load.fragments, verifications.approved, verifications.review, D2 approved +1 each; D2 nodes +4, relationships +10; D4 triples +5, info_only results and Info +1 each); 6 SHACL sample lines (Results (712) to (713)); the 66 sha256 e83204bc..., all from actions_gate's JDL-088; 12 as_of and D6_gate.lapsed the run has written since the record (sha256 078887f5...). No list moved order: task-0369's sorted order equals the 2026-11-01 run's. Two Neo4j runs of the code: 0 leaves. ENT-0009 28 to 29 statements, every register node 707 to 709 rows: REL-07006 (PROC-0007 to ENT-0009) cites the whole of actions_gate.dmn, so ENT-0009 and PROC-0007 (75 to 76) each gain the new statement. scenarios.toml's represented counts follow the run (+1 each). CargoQuote unchanged.

Evidence (PR #579, merged 75ed913 on a whole green matrix with stack; the coordinator checked the accounting before merging): subjects/README.md and instance/mappers.toml state both places; _cite_decision reads a decision's own citations no rule makes; check_subject warns only on an id-shaped token the pattern does not read, J-F's check holding with no finding and both JDL-088 exemptions removed; tests/test_kit_mapper_findings.py holds the reading, the claim and the warnings. Re-record 52d1594: 78 leaves, 66 from JDL-088, 12 as_of/lapsed, 0 order; ENT-0009 28 to 29, all nodes 707 to 709 via REL-07006; CargoQuote unchanged. Reader extension under CHANGELOG's Contract changes, the record line under Unreleased.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
dmn_decisions reads a decision's own requirement citations that no rule makes (maintainer's option (b)); jef_data_load re-recorded once on Neo4j with every leaf accounted for (78: 66 from JDL-088, 12 as_of/lapsed, 0 order) and ENT-0009's pins moved with it; check_subject warns only on malformed citations. Merged in #579.
<!-- SECTION:FINAL_SUMMARY:END -->
