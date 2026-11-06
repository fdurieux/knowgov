---
id: TASK-0163
title: >-
  Split the rdflib job: the record and its round trip, and the readers, in
  parallel
status: Done
assignee:
  - '@claude'
created_date: '2026-11-06T07:42:00Z'
updated_date: '2026-11-06T15:57:00Z'
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
- [x] #1 rdflib runs the record's steps and its round trip; a second job runs the reader steps; no step of either workflow is dropped or run on fewer scenarios than today
- [ ] #2 Each job measured after task-0097 on an uncontended runner, against task-0084's 12 minutes, the figures in the task notes
- [x] #3 The new job's name is given to the maintainer for the ruleset's required checks; CLAUDE.md's CI paragraph names both jobs
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-06: the maintainer approved option A, 'go ahead with the rdflib job split' (relayed by the coordinating session). Shape from the coordinator's brief: rdflib keeps its name (the ruleset requires it) and runs the record and its round trip; a second job runs the readers; nothing dropped or subset; each job self-standing; security-events: write only on the job running the action's SARIF step.

2026-11-06 measurement, #292 at 786c69f (GitHub API; all green: tests 5.1 min, rdflib, rdflib-readers; stack not triggered, its paths untouched):
| | before (#285's PR run, bbf49e7) | after (#292, 786c69f) |
|---|---|---|
| rdflib | 26.9 min, every step | 14.3 min, the record |
| rdflib-readers | - | 15.5 min, in parallel |
| harness wall clock | 26.9 | 15.5 (-42%) |
Both jobs ran with 13 other workflow runs active, so this is not uncontended; no quiet slot was found. Biggest steps after: rdflib, the round trip 6.35, J-F record 2.18, the suite 2.10, SNAP 1.65, the oracle 1.23; rdflib-readers, the MCP server 6.68, the lighthouse 2.45, citations 0.97, gate 0.93, review 0.83. Neither half is yet under task-0084's 12 minutes. The readers' half should drop with task-0097's cache (#286), which takes the MCP step's parse. The record's half is led by the round trip, the record itself, which is never subset.
AC #1: CI green; tests/test_rdflib_split.py holds every old step in exactly one job and the subsets as one workflow-level value. AC #3: 'rdflib-readers' given to the coordinator for the maintainer's ruleset; CLAUDE.md's CI paragraph names both jobs. AC #2 left open: it asks for the figures after task-0097 on an uncontended runner; the figures above are before it and under load.

2026-11-06 re-measure with the split and task-0097's cache (#286, on main since 38ac517), PR runs from the GitHub API; 'overlapping' counts this repository's other workflow runs active during the job:
| head | rdflib | rdflib-readers | overlapping runs |
|---|---|---|---|
| b590f9d (#292) | 8.4 min | 12.5 min | 21 |
| 6bab643 (#292, main merged in) | 13.2 min | 13.9 min | 19 |
The third run, this closing PR's own, follows.

Third run, this closing PR #299 at 5ad6322: rdflib 14.8 min, rdflib-readers 16.8 min, 13 other runs overlapping. In all three runs rdflib-readers is over 12 min (12.5, 13.9, 16.8) and rdflib in two of three (8.4, 13.2, 14.8). None of the three was uncontended. AC #2 stays open: no uncontended figure, and every contended one for rdflib-readers is over the budget. The task closes on the coordinating session's order (2026-11-06: 'Leave AC #2 open if the figure misses 12 min, with the numbers'). Whether the budget is met is left to a quiet-slot workflow_dispatch measurement.

Quiet-slot measurement (coordinator, 2026-11-06 15:38-15:56 UTC, under doc-0029): a re-run of #318's harness run (42241939066, attempt 2, PR subset) with 4 other runs active, all main's: rdflib 17.2 min, rdflib-readers 10.1 min. Readers are now under the 12-min budget (the split plus task-0097's cache). The record half is over and grew from 8.4-14.8 to 17.2, because today's checks landed in it (SNAP-08 by task-0175, task-0172's schema tests on rdflib stores); contention does not explain it. AC #2 stays open. The next lever, a third parallel job for the Turtle round trip (about 6.35 min of rdflib), is task-0180, minted unstarted: it adds a job to the ruleset's required checks, which is the maintainer's.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Split harness.yml's rdflib job in two (#292): rdflib keeps the record, the oracle and the round trip; rdflib-readers runs the MCP, lighthouse, SNAP and other reader steps in parallel. No step is dropped or subset; tests/test_rdflib_split.py holds every old step in exactly one job, and the scenario subsets are one workflow-level value. Timeouts are 45 and 90 min, above each half's worst. CLAUDE.md names both jobs, and 'rdflib-readers' went to the coordinator for the maintainer's ruleset. The harness wall clock fell from 26.9 min (#285, one job) to between 12.5 and 16.8 min across three contended runs with task-0097's cache. AC #2 is not met: no uncontended run has been measured, and rdflib-readers went over 12 min in every contended run (rdflib in two of three). That is left as a follow-up: a quiet-slot workflow_dispatch measurement, and if the readers still miss the budget, a further split of the MCP server step (about 6.7 min).
<!-- SECTION:FINAL_SUMMARY:END -->
