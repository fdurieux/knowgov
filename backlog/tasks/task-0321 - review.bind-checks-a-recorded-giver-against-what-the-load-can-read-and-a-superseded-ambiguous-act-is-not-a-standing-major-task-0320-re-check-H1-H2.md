---
id: TASK-0321
title: >-
  review.bind checks a recorded giver against what the load can read, and a
  superseded ambiguous act is not a standing major (task-0320 re-check H1, H2)
status: Done
assignee: []
created_date: '2026-11-11T10:35:00Z'
updated_date: '2026-11-11T11:44:00Z'
labels:
  - integrity
  - captures
  - 0.9.0
dependencies: []
priority: high
ordinal: 314000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Fix-only, pulled ahead of the 0.9.0 cut: H1 is the C2-1 rebinding class (the coordinator, 2026-11-11). Found by group 3's re-check of task-0320 (session_01HTAA1RJ9Rg2FP5uZoxBXic, main fb52a5d): G1 and G2 FIXED. The contract does not move.

H1: at load, the `giver` a review records is trusted unchecked. Repro: employee-1 answers; employee-2's review is saved with giver = "employee-1" (approved); delete employee-1's capture; employee-3 ingests the same value (a major `gone` act, proposed); edit the saved review's giver to "employee-3": response|hold_presence reads APPROVED with no act. Fix: at load, when the capture is present, the recorded giver must equal its content's signed handle; when it has vanished, the giver must be the one issued handle the id stem reads as, or one of its two readings when ambiguous; otherwise the ruling is set aside as an act finding (`giver_wrong`), major, naming both.
H2: a pre-change review (no giver) on an ambiguous stem keeps its major `ambiguous` act after a later applied ruling binds the same statement, so a `--fail-on major` pipeline stays red though the key reads approved. Fix: a superseded ambiguous act (a later applied ruling on the same statement) is reported at info and names the review that settled it.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 H1: a hand-edited giver that disagrees with the capture's content, or with the vanished stem's readings, is an act finding and binds nothing; a test reproduces the repro and fails on fb52a5d
- [x] #2 H1: an honest giver binds as before (present capture, vanished single-reading stem, ambiguous stem with the giver one of its readings); every case of tests/test_act_binding.py and tools/check_act_binding.py keeps its outcome
- [x] #3 H2: a superseded ambiguous act reads info naming the settling review; an unsettled one stays major; a test
- [x] #4 The record holds; the review format and report shape are unchanged
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
At load, check a review's recorded giver against what the load can read (the capture's from when present, the stem's readings when vanished); hold an earlier ambiguous ruling until the load ends and report it at info when a later applied ruling settles the same statement.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Built by session_01HTAA1Sy42bPRLQSYGNSGPj (#475, merged as 23661cd on a whole green matrix with stack); recorded by the coordinator, the builder having no backlog CLI. giver_wrong would have widened the gate-report enum (changed|gone|ambiguous|unbound|refused), so a wrong recorded giver is a major act with reason changed and reasons[0] naming both givers; the write-time giver_wrong refusal is unchanged. H2: load._record_skipped/_record_pending hold an earlier ambiguous ruling to the end of the load; a later review (by on, then file name) applying a ruling on the same key, value and sha256 records reasons ['settled by <file>'], which gate_cli reads at info. Re-check sent to group 3.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
A review's recorded giver is now checked at load: it must equal the capture's own from when the capture is present, or be a reading of the id's stem when it has vanished; otherwise the ruling binds nothing and is a major act naming both givers (reason changed, no enum change). An ambiguous act a later review has settled reads info naming that review; an unsettled one stays major. Tests: test_a_recorded_giver_the_load_cannot_confirm_is_an_act_task_0321, test_honest_givers_bind_as_before_task_0321, test_an_ambiguous_act_settled_by_a_later_review_reads_info_task_0321, and check_act_binding's forged_cases and stem_cases. The record holds; the review format and report shape are unchanged.
<!-- SECTION:FINAL_SUMMARY:END -->
