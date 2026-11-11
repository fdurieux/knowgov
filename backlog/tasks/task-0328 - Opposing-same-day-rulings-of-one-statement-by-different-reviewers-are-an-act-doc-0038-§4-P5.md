---
id: TASK-0328
title: >-
  Opposing same-day rulings of one statement by different reviewers are an act
  (doc-0038 §4 P5)
status: To Do
assignee: []
created_date: '2026-11-11T13:34:00Z'
labels:
  - integrity
  - captures
  - 0.9.0
dependencies: []
priority: high
ordinal: 320000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Fix-only, pulled before the 0.9.0 cut under decision-0032 (fails open on a review's integrity). From task-0323 L2's repro B (group 3's re-check of task-0322), doc-0038 §4 P5. review.order_key orders same-day reviews by (on, by, n), so across reviewers it is alphabetical by handle. If employee-2 approves and boss rejects the same answer on one day, the key reads approved whichever was written first, and no finding names the conflict. Fix: opposing rulings (approved against rejected or referred) of one statement on one day by different reviewers are an act finding at major naming both files, and the key does not read approved from either alone. The rest of task-0323 (L1, L2's documentation, L3) stays 0.9.x.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Two same-day reviews by different reviewers, one approving and one rejecting one statement, give a major act naming both, and the key does not read approved; a test on both stores (tools/check_act_binding.py case)
- [ ] #2 Same-day rulings that agree, and a same reviewer's -2 re-ruling (task-0322), keep their outcome
- [ ] #3 The record holds
<!-- AC:END -->
