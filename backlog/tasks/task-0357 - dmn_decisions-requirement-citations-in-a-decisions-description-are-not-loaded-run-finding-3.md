---
id: TASK-0357
title: >-
  dmn_decisions: requirement citations in a decision's description are not
  loaded (run finding 3)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-16T04:37:00Z'
updated_date: '2026-11-16T19:46:00Z'
labels:
  - finding
  - reverse-engineering
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
- [ ] #4 dmn_decisions loads requirement ids cited in a decision's description as that decision's citations; the warning then narrows as task-0356's
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Build the reader extension; run J-F's comparator. 2. If the record moves, withdraw it and keep the fix: README states rule-level citations; check_subject warns (rule citation) on decision-level ids no rule cites, and on id-shaped tokens the pattern does not read. 3. Tests; both comparators.
<!-- SECTION:PLAN:END -->
