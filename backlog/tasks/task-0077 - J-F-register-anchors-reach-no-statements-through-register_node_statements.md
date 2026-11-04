---
id: TASK-0077
title: J-F register anchors reach no statements through register_node_statements
status: To Do
assignee: []
created_date: '2026-11-04T00:44:00Z'
labels:
  - register
  - impact
milestone: m-6
dependencies: []
priority: medium
ordinal: 81000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by the task-0071 session: register_node_statements (task-0046) returns statements for CargoQuote's anchored citations but none for J-F's. Either J-F's citations carry no anchors the store can match, or the join misses its fragment ids.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The cause is named in the task notes with the measured counts per subject
- [ ] #2 Either the join is fixed and a J-F node reaches its statements in CI, or the missing anchors are listed as a proposal to ieam-register
<!-- AC:END -->
