---
id: TASK-0331
title: >-
  An opposed act settles when the owners rule again, and names every file it
  cancels (task-0328 re-check)
status: Done
assignee: []
created_date: '2026-11-11T16:01:00Z'
updated_date: '2026-11-11T18:02:00Z'
labels:
  - integrity
  - captures
  - 0.9.0
dependencies: []
priority: high
ordinal: 323000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Completes task-0328 (doc-0038 §4 P5), pulled before the cut under decision-0032. Group C's re-check at main a214137 (session_01HTAA1R97DK5D3Q1B1z6cKo), on rdflib and Neo4j alike: repro B FIXED, approve against referred FIXED, no regression (an earlier-day approval is kept; an invalid opposing ruling cancels nothing).
- R1 (medium): an opposed act is never settled. load._set_aside records it at once with record_act_finding; it never joins pending, so _record_pending and review.settling never see it. After 'the owners rule again in one review', as the act asks (case D: carol approves on 11-08), the key reads from the new ruling, but both 11-06 acts stay major for good, so a pipeline on --fail-on major stays red after the remedy. Fix: an opposed act is settled, and reads info 'settled by <file>', by a later applied decided ruling of the same statement, as task-0322's ambiguous acts are; a later ruling that does not approve leaves it major (review.RULED).
- R2 (low-medium): the act's message joins task-0321's generic ambiguous clause ('several statements hold that content … or its id reads as two givers'') to the opposed reason; false here. The message names only the opposed reason. Its route is 'the owners rule again in one review (capture.py review)', not the questionnaire.
- R3 (low): with three or more same-day rulings, opposed_reason names against[0] only; every act of one cancelled set names every file of the set, so they carry the same reason.
- R4 (low): capture.py review writes a ruling that cancels another reviewer's same-day ruling without a word. Warn on stderr before writing, naming the file it opposes, and still write it.
- R5 (doc): instance/README's 'Reviewing what people said' states the rule and how to clear it.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 R1: an opposed pair followed by a later applied ruling of the same statement reads info 'settled by <file>'; a later rejection leaves it major; a test on both stores (tools/check_act_binding.py case)
- [x] #2 R2, R3: the message names only the opposed reason and every file of the set, the same reason on every act; the route is capture.py review; tests
- [x] #3 R4: capture.py review warns before writing a ruling that opposes another reviewer's same-day ruling; a test
- [x] #4 R5: instance/README states the rule and the remedy; tests/test_docs_* hold
- [x] #5 Every existing case of test_act_binding.py and check_act_binding.py keeps its outcome; the record holds
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Built by session_01HTAA1ScrqyiziKsTCYLfmT (#488, merged as 11218a5 on a whole green matrix with stack, check_act_binding on Neo4j); recorded by the coordinator. Each new test and check case fails on main. Re-checked by group C on both stores: R1 (approval) R2-R5 FIXED, no regression; a later rejection leaves the acts major for good (R1', the AC's own wording, the coordinator's error) with R6, R7: task-0333.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
An opposed same-day act settles (info, 'settled by <file>') on a later day's applied approval of the statement; the act's message names only the opposed reason and every file of the cancelled set, its route is capture.py review on a later day; capture.py review warns before writing an opposing ruling; instance/README states the rule. Tests: test_a_later_decided_ruling_settles_an_opposed_act_and_a_rejection_leaves_it_major_task_0331, test_the_gate_reads_an_opposed_act_at_major_naming_both_files_without_the_generic_clause_task_0331, test_every_act_of_a_cancelled_set_names_every_file_of_it_task_0331, test_capture_review_warns_before_it_writes_a_ruling_that_opposes_the_days_task_0331, test_the_readme_states_the_opposed_rule_and_the_remedy_task_0331, check_act_binding opposed_cases. A later rejection settling too is task-0333.
<!-- SECTION:FINAL_SUMMARY:END -->
