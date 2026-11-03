---
id: TASK-0038
title: >-
  Pair elicited statements with extracted ones in the conflict and corroboration
  rules
status: To Do
assignee: []
created_date: '2026-11-02T23:22:00Z'
labels:
  - capture
milestone: m-2
dependencies:
  - TASK-0009
documentation:
  - >-
    backlog/docs/doc-0007 -
    Capturing-an-employees-knowledge-to-resolve-a-non-conformity-the-John-Doe-walkthrough.md
priority: medium
type: bug
ordinal: 50000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0007 F3: `candidate_pairs` (both store adapters) pairs only assertions of the same `version`; a capture's version is `capture`, the documents' `v1`. So a person contradicting a document (S2: John's status list includes held_unscreened, the contract's does not) raises no conflict gap, and a person agreeing with one corroborates nothing. A person contradicting a document is exactly what a reviewer needs to see.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 An elicited statement whose value conflicts with an extracted one on the same key produces a conflict gap naming both, on both adapters
- [ ] #2 An elicited statement equal to an extracted one is recorded as agreeing, without raising either above its status (elicited stays proposed)
- [ ] #3 The deterministic record for S1 to S7, which has no captures, is unchanged: the comparator stays green
- [ ] #4 A test covers both cases with a capture on S2
<!-- AC:END -->
