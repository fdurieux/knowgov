---
id: TASK-0308
title: >-
  act binding: an ambiguous capture stem names no giver (task-0302 re-check
  R1-R3)
status: To Do
assignee: []
created_date: '2026-11-09T22:59:00Z'
labels:
  - integrity
  - captures
  - 0.9.0
dependencies: []
priority: high
ordinal: 301000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Fix-only, pulled ahead of the 0.9.0 cut (the coordinator, 2026-11-09). Found by the re-check of task-0302 (group 3, session_01HTAA1RJ9Rg2FP5uZoxBXic, main cee6833); C2-1 itself is fixed.

R1: when a review act's capture file has vanished, the giver is read from the file stem. capture.py names a second same-day capture `{on}-{owner}-{handle}-{n}`, and a handle may end in `-<digits>`, so the second file of `ops` has the stem of the first file of `ops-2`. The approval then passes to another person. Fix: a stem that names more than one issued handle names no giver and is reported `ambiguous` at major; a single reading still binds.
R2: the `gone` message says no statement is extracted while another person's identical answer is. Reword it.
R3: tools/check_act_binding.py took `--help` as its output folder.

Not taken (format changes, the maintainer's call): a giver field in the review file; a same-day suffix a handle cannot carry.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 R1: with issued handles ops and ops-2 and both ops files deleted, ops-2's identical answer does not inherit the approval; the gate reads proposed with a major ambiguous act; a test reproduces it
- [ ] #2 A digit-ending handle with a single reading (employee-1) still binds; every existing case of tests/test_act_binding.py and tools/check_act_binding.py keeps its outcome
- [ ] #3 R2: the gone message names that only another person's identical answer remains
- [ ] #4 R3: check_act_binding.py --help prints usage and writes nothing
<!-- AC:END -->
