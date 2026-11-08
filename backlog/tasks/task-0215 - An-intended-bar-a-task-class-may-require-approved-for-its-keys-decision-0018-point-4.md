---
id: TASK-0215
title: >-
  An intended bar: a task class may require approved for its keys (decision-0018
  point 4)
status: To Do
assignee: []
created_date: '2026-11-08T11:17:00Z'
labels:
  - process
  - reverse-engineering
  - contract
  - gate
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
ordinal: 215000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0018 point 4 (doc-0032 §3, gap 2; method 1.3: a source defect must not silently become desired behaviour). Today a task class can block on levels and cap the share below verified (gate.py), and PROCEED takes verified or approved, so an observed behaviour verified by execution on the original reads PROCEED without anyone intending it (decision-0011: verified shows the kit and the code agree, not that the behaviour is right). A task class gains an opt-in bar requiring approved for its keys; a key below it is a finding with its owner and route (capture.routing). Opt-in, so no existing task class and no record verdict moves. A contract change (the subject format, the gate report), for 0.9.0 (doc-0028 G9-12).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A task class may declare that its keys require approved; a key verified but not approved is then a finding naming its owner and route, and the verdict follows the class's blocking rule
- [ ] #2 Without the declaration every task class reads as today
- [ ] #3 subjects/README.md documents the field; tools/check_subject.py checks it; the gate report schema carries the finding
- [ ] #4 CHANGELOG.md carries the line under Unreleased's contract heading
- [ ] #5 The scored record (S1 to S7), the deterministic run and the comparator stay equal
<!-- AC:END -->
