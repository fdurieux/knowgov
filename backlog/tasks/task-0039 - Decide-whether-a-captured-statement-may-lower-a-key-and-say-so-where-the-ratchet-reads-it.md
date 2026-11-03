---
id: TASK-0039
title: >-
  Decide whether a captured statement may lower a key, and say so where the
  ratchet reads it
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-02T23:22:00Z'
updated_date: '2026-11-03T23:35:00Z'
labels:
  - capture
milestone: m-5
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
decision-0004 drafted (proposed): options A (min rule, documented) and B (an unreviewed elicited statement does not lower a key holding a validated-or-better statement); recommends B. S2 case run by command: a capture agreeing on response|statuses gives REGRESSION validated -> proposed, exit 1. Implementation waits for the maintainer's merge.
<!-- SECTION:NOTES:END -->
