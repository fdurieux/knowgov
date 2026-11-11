---
id: TASK-0333
title: >-
  A later decided ruling clears an opposed act, approved or rejected (task-0331
  re-check)
status: Done
assignee: []
created_date: '2026-11-11T18:01:00Z'
updated_date: '2026-11-11T20:48:00Z'
labels:
  - integrity
  - captures
  - 0.9.0
dependencies: []
priority: high
ordinal: 325000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Completes task-0331 (task-0328, doc-0038 §4 P5), pulled before the cut under decision-0032. Group C's re-check at main 11218a5 (session_01HTAA1R97DK5D3Q1B1z6cKo), on rdflib and Neo4j alike: R1 (approval settles), R2, R3, R4, R5 FIXED, no regression.
- R1' (medium): a later decided rejection never clears the opposed acts. In case D2 (employee-2 approves and boss rejects on 11-06, carol rejects on 11-08) the key reads from the new ruling (absent), as the route asked, but both acts stay major for good ('the key was ruled by … (rejected)'), so a pipeline on --fail-on major stays red after a legitimate rejection; the only exit is an approval that reverses the owners. task-0331's AC 'a later rejection leaves it major' was the coordinator's error: task-0322's review.settling already settles a legacy act on any later ruling of the same statement, and task-0323 L1 settles on a decided ruling, approved or rejected. Fix: an opposed act settles (info, 'settled by <file>') on any later applied decided ruling (approved or rejected) of the same statement; a later referral leaves it major. instance/README's remedy sentence follows.
- R6 (low): a settled opposed act still carries the route 'the owners rule again in one review, on a later day'; a settled act names no route (or 'none: settled by <file>').
- R7 (low): capture.py review's warning on a write that joins a cancelled set says 'is opposed by <files>, a ruling of another reviewer … the load applies neither'; with three rulings, name them as 'cancelled with <file> (<outcome>), …; none applies', matching the act's reason.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 R1': an opposed pair then a later rejection of the same statement reads info 'settled by <file>' on both acts and the key from the rejection; a later referral leaves them major; tests and check_act_binding cases on both stores
- [x] #2 R6, R7: a settled act carries no 'rule again' route; the warning names the cancelled set; tests
- [x] #3 instance/README states the remedy for both outcomes; every existing case keeps its outcome; the record holds
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Built by session_01HTAA1ScrqyiziKsTCYLfmT (#491, merged as ac51efb on a whole green matrix with stack, check_act_binding on Neo4j); recorded by the coordinator, the builder having no backlog CLI. main merged in by the builder after #489. Each new test and check case fails on main (referred-after passes by design). A settled act's route reads 'nothing to do: settled by <file>' for opposed and settled task-0322 legacy acts; superseded and open acts keep theirs. Re-check sent to group C.

Re-checked by group C at ac51efb on both stores: R1' (D2 later rejection settles to info, key absent), R6 (settled opposed and legacy acts route 'nothing to do: settled by'), R7 FIXED; a later referral stays major; no regression.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
An opposed same-day act settles (info, 'settled by <file>') on any later day's applied decided ruling of the statement, approved or rejected; a later referral leaves it major; a settled act's route reads 'nothing to do: settled by <file>' (opposed and task-0322 legacy alike); capture.py review's warning names the cancelled set ('cancelled with <file> (<outcome>), …: none applies'); instance/README states the remedy for both outcomes. Tests: test_a_later_decided_ruling_settles_an_opposed_act_approved_or_rejected_task_0333, test_a_settled_opposed_act_no_longer_carries_the_owners_rule_again_route_task_0333, the R7 assertion in test_capture_review_warns_before_it_writes_a_ruling_that_opposes_the_days_task_0331; check_act_binding cases settled, rejected-after, referred-after and the 0322 route assertions; the record holds.
<!-- SECTION:FINAL_SUMMARY:END -->
