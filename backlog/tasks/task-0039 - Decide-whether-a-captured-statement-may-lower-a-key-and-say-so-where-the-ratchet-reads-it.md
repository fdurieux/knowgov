---
id: TASK-0039
title: >-
  Decide whether a captured statement may lower a key, and say so where the
  ratchet reads it
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
priority: low
type: task
ordinal: 51000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0007 F4: a key's level is the lowest of its live statements, so John's correct but unreviewed answer on response|statuses lowered the key from validated to proposed in S2, and `gate_cli.py --baseline record` then exits 1 (REGRESSION). A pipeline that ratchets on the record after a capture fails and is likely switched off. Either the behaviour is right and documented, or an elicited statement beside validated document statements is not counted in the level until reviewed.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The choice is recorded as a decision in backlog/decisions, with the S2 case as its example
- [ ] #2 gate.resolve and its tests follow the decision; the comparator stays green
- [ ] #3 instance/README.md and the gate_cli docstring say what a capture does to a ratchet against the record
<!-- AC:END -->
