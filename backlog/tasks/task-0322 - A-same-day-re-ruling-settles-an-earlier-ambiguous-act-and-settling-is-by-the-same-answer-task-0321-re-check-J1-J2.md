---
id: TASK-0322
title: >-
  A same-day re-ruling settles an earlier ambiguous act, and settling is by the
  same answer (task-0321 re-check J1, J2)
status: To Do
assignee: []
created_date: '2026-11-11T11:49:00Z'
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
- [ ] #1 J1: a legacy ambiguous review re-ruled the same day (…-employee-2-2.toml) reads info, settled by that file; review ordering is (on, stem, n) in one helper; a test fails on 23661cd
- [ ] #2 J2: a later approval of another person's identical answer does not say settled; the act names the superseding file and that the named answer stays unruled; a test
- [ ] #3 Every case of tests/test_act_binding.py and tools/check_act_binding.py keeps its outcome; the record holds
<!-- AC:END -->
