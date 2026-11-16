---
id: TASK-0357
title: >-
  dmn_decisions: requirement citations in a decision's description are not
  loaded (run finding 3)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-16T04:37:00Z'
updated_date: '2026-11-16T21:33:00Z'
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
- [ ] #1 subjects/README.md states that requirement citations are read from a rule's description
- [ ] #2 check_subject.py warns on requirement ids cited in a decision's description that no rule cites
- [ ] #3 A test holds the warning; the scored record is unchanged
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Build the reader extension; run J-F's comparator. 2. It moved the record (actions_gate cites JDL-088 at decision level only: +1 assertion, +1 fragment per scenario, 60 leaves over 6 scenarios), so it is withdrawn and the fix kept: README states rule-level citations; check_subject warns (rule citation) on decision-level ids no rule cites and on id-shaped tokens the pattern does not read. 3. J-F's one warning admitted by name in test_check_subject and harness.yml's rdflib-readers check. 4. Tests; both comparators.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
The maintainer, 2026-11-16: "Yes" to these joining 0.10.0 (decision-0047 point 4): the soak they waited for restarts with 0.10.0 anyway.

Maintainer, 2026-11-16: "keep the JDL-088 warning; drop the reader extension". The reader-extension criterion (dmn_decisions loading a decision's own citations) is removed: built, it moved J-F's record (actions_gate cites JDL-088 in its description and in no rule; +1 assertion, +1 fragment per scenario, 60 leaves over 6 scenarios), so the mapper stays as it was. J-F's one citation warning is admitted by name in tests/test_check_subject.py and harness.yml's rdflib-readers J-F check, each still failing on any other finding.
<!-- SECTION:NOTES:END -->
