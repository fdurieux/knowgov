---
id: TASK-0322
title: >-
  A same-day re-ruling settles an earlier ambiguous act, and settling is by the
  same answer (task-0321 re-check J1, J2)
status: Done
assignee: []
created_date: '2026-11-11T11:49:00Z'
updated_date: '2026-11-11T12:56:00Z'
labels:
  - integrity
  - captures
  - 0.9.0
dependencies: []
priority: high
ordinal: 315000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Fix-only, before the 0.9.0 cut: completes task-0321's H2 (the coordinator, 2026-11-11). Found by group 3's re-check of task-0321 (session_01HTAA1RJ9Rg2FP5uZoxBXic, main 23661cd): H1 FIXED; H2 fixed across days. The contract does not move.

J1: reviews are ordered by (on, file name). capture.py names a second review the same day `<on>-<by>-2.toml`, and "-" (0x2d) sorts before "." (0x2e), so `2026-11-06-employee-2-2.toml` sorts BEFORE `2026-11-06-employee-2.toml`. A same-day re-ruling (the natural reaction to the major finding) is therefore not "later": the key reads approved and the legacy act stays major. Fix: order by (on, the file stem without its trailing -<n>, n numeric with the base file as 0), in one helper used wherever reviews are ordered.
J2: a later approval of ANOTHER person's identical answer settles the legacy act ("settled by …, so the key reads from that ruling") though the answer it named stays unruled. Fix: settle only on a later applied ruling of the same statement (the same assertion id, or the same giver with the same key, value and sha256); otherwise keep the act and word it "superseded for the key by <file>; the answer it named stays unruled", at the level the key's own reading justifies (info when the key reads approved).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 J1: a legacy ambiguous review re-ruled the same day (…-employee-2-2.toml) reads info, settled by that file; review ordering is (on, stem, n) in one helper; a test fails on 23661cd
- [x] #2 J2: a later approval of another person's identical answer does not say settled; the act names the superseding file and that the named answer stays unruled; a test
- [x] #3 Every case of tests/test_act_binding.py and tools/check_act_binding.py keeps its outcome; the record holds
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Built by session_01HTAA1Sy42bPRLQSYGNSGPj (#477, merged as e5a5158 on a whole green matrix with stack); recorded by the coordinator, the builder having no backlog CLI. J1: review.order_key orders reviews by (on, by, n), the base file <on>-<by> as 0 and <on>-<by>-<n> as n, a stem not of that shape after its date by name; load applies reviews and reads "later" by it. J2: review.settling (moved from load._settling at eb38fcf so its tests need no PyYAML; CPython 3.13 with nothing installed failed two tests at 0432d1f and 2413b0b on import yaml through load → extract) settles only on a later applied ruling of the same statement (its id, or the same key, value and sha256 by a giver the stem reads as); a later approval of the same content on another statement is "superseded for the key by <file>; the answer it named stays unruled", and a later non-approving ruling "the key was ruled by <file> (<outcome>)". The prefixes are review.SETTLED, SUPERSEDED, RULED with INFO_REASONS, MAJOR_REASONS, REASON_PREFIXES, read by gate_cli._act_severity: settled and superseded at info only while the key reads approved, ruled major. Re-check sent to group 3.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Reviews are applied, and read as later, in (on, by, n) order (review.order_key), so a same-day re-ruling <on>-<by>-2.toml comes after the first and settles a legacy ambiguous act (J1). Only a later ruling of the same statement settles it (review.settling); another person's identical answer approved later supersedes the act for the key, naming the file and that the named answer stays unruled, at info only while the key reads approved (J2). Reason prefixes are constants in harness/review.py shared by load and gate_cli. Tests: test_a_second_review_the_same_day_orders_after_the_first_task_0322 (AC1), test_only_a_ruling_of_the_same_statement_settles_an_ambiguous_act_task_0322 and test_the_gate_reads_a_superseded_act_at_info_only_while_the_key_is_approved_task_0322 (AC2), test_every_reason_load_writes_is_one_the_gate_recognises_task_0322 and check_act_binding's same_day_cases with every earlier case unchanged (AC3). The record holds; the review format and report shape are unchanged.
<!-- SECTION:FINAL_SUMMARY:END -->
