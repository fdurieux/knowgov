---
id: TASK-0207
title: Runs and trace single fixes (doc-0030 R6, R8, R12)
status: To Do
assignee: []
created_date: '2026-11-07T07:15:00Z'
labels:
  - review
  - runs
  - trace
dependencies: []
priority: low
type: bug
ordinal: 207000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer accepted doc-0030's advice on 2026-11-07 ("accept the advise on all four"): the hardening tranche before 0.9.0's cut, in the order F7; F1 with the check_instance guard, H7 and M3; F3, F4 and F2; F5 and F8. The ids below are doc-0030's (the code review at 8d80b2b); each finding there quotes its lines and its probe.

R6: the run's seconds ceiling reached mid-stream is recorded as an API error, so --resume re-runs it and spends again. R8: under --baseline, annotate marks the findings the baseline held as errors though the gate exited 0. R12: route (c) records the configured model, not the one that answered. Fixes.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A run that reaches its seconds ceiling is recorded as the ceiling, not an API error, and --resume does not re-run it
- [ ] #2 Gate findings a baseline held carry held, and annotate prints them below error
- [ ] #3 Route (c) records the model that answered (usage model)
<!-- AC:END -->
