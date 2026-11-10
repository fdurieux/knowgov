---
id: TASK-0310
title: >-
  capture.py review refuses a ruling its load would never apply (task-0308
  re-check G1)
status: To Do
assignee: []
created_date: '2026-11-10T00:35:00Z'
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
- [ ] #1 With ops and ops-2 issued, `capture.py review` approving A:cap:2026-11-05-ORG-0002-ops-2:1@capture is refused on the day, naming both readings; nothing is written
- [ ] #2 A ruling on a single-reading stem (employee-1) is accepted as before; every case of tests/test_act_binding.py and tools/check_act_binding.py keeps its outcome
- [ ] #3 A test reproduces the refusal and fails on 9a1df7e
<!-- AC:END -->
