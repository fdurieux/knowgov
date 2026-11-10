---
id: TASK-0310
title: >-
  capture.py review refuses a ruling its load would never apply (task-0308
  re-check G1)
status: Done
assignee: []
created_date: '2026-11-10T00:35:00Z'
updated_date: '2026-11-10T01:42:00Z'
labels:
  - integrity
  - captures
  - 0.9.0
dependencies: []
priority: high
ordinal: 303000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Fix-only, before the 0.9.0 cut: a regression of task-0308 (the coordinator, 2026-11-10). Found by the re-check of task-0308 (group 3, session_01HTAA1RJ9Rg2FP5uZoxBXic, main 9a1df7e).

With handles X and X-<n> both issued, an answer whose capture stem reads as two givers can never be approved. review.bind names no giver for it, so every load reports `ambiguous`. But `capture.py review` accepts the ruling on the day it is written (check(strict) binds by id under the pre-0.9 read rule, because the reviewer's input carries no key, value or sha256), prints "reviewed" and saves the file.

Fix: write time refuses what load time would refuse. A ruling whose statement's stem reads as two issued handles is refused by `capture.py review` (exit 2 under the capture CLI's contract), with a message that names the two readings and says no review of it can apply until the giver is recorded. The real fix (the giver in the review file, a different suffix, or a register rule) is the maintainer's decision, put on 2026-11-10.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 With ops and ops-2 issued, `capture.py review` approving A:cap:2026-11-05-ORG-0002-ops-2:1@capture is refused on the day, naming both readings; nothing is written
- [x] #2 A ruling on a single-reading stem (employee-1) is accepted as before; every case of tests/test_act_binding.py and tools/check_act_binding.py keeps its outcome
- [x] #3 A test reproduces the refusal and fails on 9a1df7e
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Make capture.py review refuse at write time what every load refuses: a ruling whose capture stem reads as two issued handles (review.check strict through _bind_ruling and _unbound_reason), naming both readings, writing nothing.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Built by session_01HTAA1UftiBGVvA4ssF7TZz (#456, merged as 02167e4 on a whole green matrix with stack); recorded by the coordinator, the builder having no backlog CLI. The refusal exits 1 with 'refused:', the capture CLI's existing contract. tools/check_act_binding.py's giver-stem case drove the old path (exit 0, then the saved file reached the load-time ambiguous act); it now asserts the refusal, then writes the review file a reviewer would have saved earlier (key, value, sha256 via review.review_toml), so the load-time ambiguous act stays proven, outcome unchanged. Re-check sent to group 3.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
capture.py review no longer tells a reviewer 'reviewed' for an act no load applies: a ruling whose capture stem reads as two issued handles is refused on the day, naming both readings, and nothing is written. Single-reading stems are accepted as before; load-time behaviour is unchanged. Tests: test_a_review_of_an_ambiguous_stem_is_refused_at_write_time_task_0310 (fails on 9a1df7e), test_a_single_reading_stem_is_still_accepted_at_write_time_task_0310, every earlier case of tests/test_act_binding.py and tools/check_act_binding.py. The real fix (the giver recorded in the review file) awaits the maintainer's decision. The contract does not move; the record holds.
<!-- SECTION:FINAL_SUMMARY:END -->
