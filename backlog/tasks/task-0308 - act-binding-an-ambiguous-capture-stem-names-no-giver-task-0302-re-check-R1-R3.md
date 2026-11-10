---
id: TASK-0308
title: >-
  act binding: an ambiguous capture stem names no giver (task-0302 re-check
  R1-R3)
status: Done
assignee: []
created_date: '2026-11-09T22:59:00Z'
updated_date: '2026-11-09T23:59:00Z'
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
- [x] #1 R1: with issued handles ops and ops-2 and both ops files deleted, ops-2's identical answer does not inherit the approval; the gate reads proposed with a major ambiguous act; a test reproduces it
- [x] #2 A digit-ending handle with a single reading (employee-1) still binds; every existing case of tests/test_act_binding.py and tools/check_act_binding.py keeps its outcome
- [x] #3 R2: the gone message names that only another person's identical answer remains
- [x] #4 R3: check_act_binding.py --help prints usage and writes nothing
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Bind a vanished capture's act by its giver only when the capture stem has a single reading against the issued handles; an ambiguous one names no giver (review.bind with the handle list, review.check's only caller passing it). Reword gone; give check_act_binding.py a proper --help.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Built by session_01HTAA1RY37AukHuJsZcGjsM (#453), recorded by the coordinator because that environment had no backlog CLI; merged through train #454 with #449. A re-ingest by ops-2 recreates the same id as ops's second file, so even an exact id no longer binds when the stem is ambiguous. With no handle list the second reading is not assumed; review.check refuses without one, so every production path has it. R2 is one string covering both cases. Not taken: a giver field in the review file, a same-day suffix a handle cannot carry (format changes, the maintainer's call).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
An approval no longer passes to another person through an ambiguous capture stem (task-0302 re-check R1): a stem that reads as two issued handles names no giver and is reported ambiguous at major; a single reading binds as before. Tests: test_a_stem_that_reads_as_two_givers_names_none_task_0308, test_a_digit_ending_handle_with_one_reading_still_binds_task_0308, every earlier case of tests/test_act_binding.py and tools/check_act_binding.py unchanged, test_the_gone_message_says_only_another_persons_identical_answer_may_remain_task_0308 (R2), test_the_check_tool_prints_usage_on_help_and_refuses_a_stray_option_task_0308 (R3). The contract does not move; the record holds.
<!-- SECTION:FINAL_SUMMARY:END -->
