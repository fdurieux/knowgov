---
id: TASK-0363
title: >-
  The 0.10.0 release PR: the contract changes of decision-0047, the soak
  restarted (decision-0016 point 2)
status: In Progress
assignee: []
created_date: '2026-11-16T19:16:00Z'
updated_date: '2026-11-28T02:13:35Z'
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
- [x] #1 VERSION and CHANGELOG move together to 0.10.0, Unreleased renamed, the contract changes under their heading
- [x] #2 The Known limits and decision-0016 A1's soak start date are restated for 0.10.0
- [ ] #3 The Release title and description are handed to the owner, ready to paste
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. VERSION 0.10.0; the CI templates' KNOWGOV_REF to v0.10.0 (held equal to VERSION), as 0.9.1 did.
2. CHANGELOG: Unreleased becomes 0.10.0 — 2026-11-28, its sections kept, with an intro (what it does, decision-0016 A1's soak restarted 2026-11-28 so 1.0.0 no earlier than 2026-12-28, the contract changes setting the minor), a carries table and Known limits (0.9.0's and 0.9.1's restated where 0.10.0 moved them, plus the limits the 0.10.0 tasks and decision-0048 record).
3. task-0367 Done citing #608 / f513c2b.
4. python tests/run_tests.py, test_release green.
5. PR, no auto-merge; the Release title and description to the coordinator.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
VERSION 0.10.0 and CHANGELOG's top section 0.10.0 — 2026-11-28 (tests/test_release.py green); Unreleased renamed, its plain list under ### Changes, Contract changes, Fixes kept; intro names what 0.10.0 does, the soak restarted 2026-11-28 (1.0.0 no earlier than 2026-12-28) and the contract changes that set the minor. CI templates' KNOWGOV_REF v0.10.0 (test_ci_wrappers). Known limits: 0.9.0's and 0.9.1's stand, three of 0.9.0's restated where 0.10.0 moved them (owner read, CI previous register, the 0.9.x residues), six added (decision-0048's client below the budget, who_knows' file reads and null holders, task-0370's silent added keys, task-0342's provenance, task-0354's no R oracle, task-0369's CargoQuote order residue). python tests/run_tests.py: 1305/1420 passed, 115 skipped, 0 failed (unpinned).
<!-- SECTION:NOTES:END -->
