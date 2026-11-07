---
id: TASK-0203
title: >-
  Worker job isolation and the run-folder lifecycle (doc-0030 F8: R2, R3, R4,
  R7, R10)
status: To Do
assignee: []
created_date: '2026-11-07T07:15:00Z'
labels:
  - review
  - worker
  - runs
dependencies: []
priority: medium
type: bug
ordinal: 203000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer accepted doc-0030's advice on 2026-11-07 ("accept the advise on all four"): the hardening tranche before 0.9.0's cut, in the order F7; F1 with the check_instance guard, H7 and M3; F3, F4 and F2; F5 and F8. The ids below are doc-0030's (the code review at 8d80b2b); each finding there quotes its lines and its probe.

R4: the reaper kills one level of escaped descendants per round for 50 rounds (worker.py:298-317); a 70-deep setsid chain leaves 21 processes alive, never killed. R7: model code can forge the job result through the parent's stdout during the 5 s drain. R10: write_confined is attested at Landlock ABI 1 though truncation is denied only from ABI 3. R2: a worker-reported timeout or kill raises and aborts the whole run (execution.py:282), where the host records a failed cell. R3: a reused --out folder carries an earlier attempt's sandbox, usage and stage-2 input into the record. Fixes.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 After each job no process of uid 65534 but the worker remains, within a time bound, by a probe with a deep setsid chain
- [ ] #2 worker_job.py is non-dumpable and its output is closed at exit, so the forge probe fails; write_confined is attested only at Landlock ABI 3 or later
- [ ] #3 A job-stage error becomes the kind's failed cell, and summary.json, usage.json and SHA256SUMS are still written
- [ ] #4 A fresh cell clears its sandbox, usage.json merges only under --resume, and stage 2's derived input is an explicit flag
- [ ] #5 The scored record (S1 to S7), the deterministic run and the comparator stay equal
<!-- AC:END -->
