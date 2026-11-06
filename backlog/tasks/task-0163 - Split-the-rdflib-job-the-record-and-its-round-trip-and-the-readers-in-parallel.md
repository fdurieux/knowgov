---
id: TASK-0163
title: >-
  Split the rdflib job: the record and its round trip, and the readers, in
  parallel
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-06T07:42:00Z'
updated_date: '2026-11-06T08:57:00Z'
labels:
  - ci
dependencies:
  - TASK-0097
ordinal: 166000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
task-0159 measured the rdflib job over task-0084's 12-minute pull-request budget: 27.4 min in the one quiet run, median 24.9 over 128 PR runs. Most of its time is the readers: the MCP server step (8.3 min), the lighthouse (2.6), SNAP, review, capture and transcript. The record's own steps (the suite, the comparators, the J-F record and oracle, the round trip) are a separate set. Two parallel jobs bring each under the budget without dropping a step. task-0097 (a per-process cache of rdflib's parsed snapshot) comes first, so this task is sized on the numbers after it. The new job gates only once the maintainer adds it to the ruleset's required checks on main (today tests and rdflib); that settings change is theirs, and until then it runs and reports without gating. The coordinating session took this proposal under the maintainer's delegation on 2026-11-06 (task-0159's notes).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 rdflib runs the record's steps and its round trip; a second job runs the reader steps; no step of either workflow is dropped or run on fewer scenarios than today
- [ ] #2 Each job measured after task-0097 on an uncontended runner, against task-0084's 12 minutes, the figures in the task notes
- [ ] #3 The new job's name is given to the maintainer for the ruleset's required checks; CLAUDE.md's CI paragraph names both jobs
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-06: the maintainer approved option A, 'go ahead with the rdflib job split' (relayed by the coordinating session). Shape from the coordinator's brief: rdflib keeps its name (the ruleset requires it) and runs the record and its round trip; a second job runs the readers; nothing dropped or subset; each job self-standing; security-events: write only on the job running the action's SARIF step.
<!-- SECTION:NOTES:END -->
