---
id: TASK-0363
title: >-
  The 0.10.0 release PR: the contract changes of decision-0047, the soak
  restarted (decision-0016 point 2)
status: To Do
assignee: []
created_date: '2026-11-16T19:16:00Z'
updated_date: '2026-11-27T19:15:00Z'
labels:
  - release
  - 0.10.0
dependencies:
  - TASK-0342
  - TASK-0354
  - TASK-0355
  - TASK-0356
  - TASK-0357
  - TASK-0360
  - TASK-0361
  - TASK-0362
  - TASK-0364
  - TASK-0365
  - TASK-0366
  - TASK-0367
  - TASK-0371
  - TASK-0376
priority: high
ordinal: 353000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer chose option (A) on 2026-11-16: who_knows and decision-0046's three tools ship in 0.10.0 rather than 1.1.0. Under decision-0016 point 2 a contract change in 0.9.x is 0.10.0 and restarts the 30-day soak of amendment A1; 1.0.0 is cut 30 days after 0.10.0 at the earliest. Scope beyond decision-0047's tools is the maintainer's to add.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 VERSION and CHANGELOG move together to 0.10.0, Unreleased renamed, the contract changes under their heading
- [ ] #2 The Known limits and decision-0016 A1's soak start date are restated for 0.10.0
- [ ] #3 The Release title and description are handed to the owner, ready to paste
<!-- AC:END -->
