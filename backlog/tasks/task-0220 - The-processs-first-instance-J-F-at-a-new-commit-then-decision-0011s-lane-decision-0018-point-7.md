---
id: TASK-0220
title: >-
  The process's first instance: J-F at a new commit, then decision-0011's lane
  (decision-0018 point 7)
status: To Do
assignee: []
created_date: '2026-11-08T11:18:00Z'
labels:
  - process
  - reverse-engineering
  - jef
dependencies:
  - TASK-0214
  - TASK-0215
  - TASK-0216
  - TASK-0217
  - TASK-0218
references:
  - >-
    backlog/decisions/decision-0018 -
    Reverse-engineering-and-knowledge-gap-identification-is-an-eight-step-process-knowgov-routes-and-re-finds-its-gaps-and-its-three-contract-changes-land-in-0.9.0.md
documentation:
  - >-
    backlog/docs/doc-0032 -
    Reverse-engineering-and-knowledge-gap-identification-as-a-repeatable-process-eight-steps-with-their-tools-and-gaps-the-bases-decision-0011-H7-and-what-F2-must-bind.-Opportunity-canvas-fit-gap-SWOT-advice.md
priority: medium
type: task
ordinal: 220000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0018 point 7. The cheapest proof of repeatability is the same subject at a new commit with its oracle in hand. Steps 1 and 2 read J-F's code, which is private and must remain private (the maintainer): the run needs the commit to read and a private route to the code, and what it may publish (a new kit, findings, scores) is the maintainer's call before anything is written to a public repository. Then decision-0011's lane, once that record is approved. Waits on the maintainer for the J-F commit and the route, and on tasks 0214 to 0218 for the steps it runs.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The maintainer names the J-F commit, the route to its code and what may be published, recorded here before step 1 starts
- [ ] #2 The run follows task-0218's pre-registration and leaves its record with its instance, every step's record named
- [ ] #3 Nothing of J-F's private code reaches a public repository
<!-- AC:END -->
