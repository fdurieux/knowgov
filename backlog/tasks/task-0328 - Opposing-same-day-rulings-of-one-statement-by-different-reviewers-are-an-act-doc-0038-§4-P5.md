---
id: TASK-0328
title: >-
  Opposing same-day rulings of one statement by different reviewers are an act
  (doc-0038 §4 P5)
status: Done
assignee: []
created_date: '2026-11-11T13:34:00Z'
updated_date: '2026-11-11T16:01:00Z'
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
- [x] #1 Two same-day reviews by different reviewers, one approving and one rejecting one statement, give a major act naming both, and the key does not read approved; a test on both stores (tools/check_act_binding.py case)
- [x] #2 Same-day rulings that agree, and a same reviewer's -2 re-ruling (task-0322), keep their outcome
- [x] #3 The record holds
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Built by session_01HTAA1ScrqyiziKsTCYLfmT (#482), merged in train #484 as a214137 on a whole green matrix with stack (check_act_binding on Neo4j); recorded by the coordinator, the builder having no backlog CLI. First head e731c23 resolved by file order (approve-first demoted to rejected; rejected-first skipped the approval); reworked at 67cf54e: load checks every file first (review.opposed_rulings), applies neither ruling of an opposed pair, the statement keeps its prior status. Re-check sent to group C.

Re-checked by group C at a214137 on both stores: repro B and approve-against-referred FIXED, no regression; an opposed act is never settled by the owners' later ruling (R1), with R2-R5: task-0331, pulled before the cut.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Opposing rulings of one statement on one day by different reviewers (approved against rejected or referred) apply neither ruling, whatever their order; each is a major ambiguous act whose reason ('opposed the same day: ') names both files sorted; opposed rulings settle nothing. Tests: test_opposing_rulings_the_same_day_by_two_reviewers_cancel_whichever_is_first_task_0328 and check_act_binding opposed_cases on both stores (AC1), test_agreeing_rulings_another_day_another_statement_or_the_same_reviewer_are_not_opposed_task_0328 (AC2), test_the_gate_reads_an_opposed_act_at_major_naming_both_files_task_0328; the record holds (AC3).
<!-- SECTION:FINAL_SUMMARY:END -->
