---
id: TASK-0340
title: >-
  An execution attestation binds every file it lists, and only the instance's
  (task-0338 residues, decision-0039 §3.5)
status: To Do
assignee: []
created_date: '2026-11-12T01:44:00Z'
labels:
  - fix-only
  - 0.9.0
dependencies: []
priority: high
ordinal: 332000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Group A's re-check of task-0338 at 9ecb1e6 found three paths that fail open on the binding decision-0038 N-b and decision-0039 §3.5 promise, pulled before the cut under decision-0032. R1 (medium): load.execution_code checks only that each current file's digest is listed (listed contains current), never that each listed digest still has a file, so deleting a test or expectations file from a listed [oracle] suite directory (or an implementation directory, which predates task-0338) weakens the suite with PROCEED and check_subject exit 0; repro: list every file of vendor/tools/acceptance, delete runner_child.py. Fix: a listed implementation or suite digest no current file holds is stale and verifies nothing by execution, named by the gate's attestation finding and check_subject, as check_subject already says for document digests ('matches no current Version'). R2 (low): the load digests an [oracle] suite (or code) path outside the instance (suite = ["/etc/hostname"] shows that file's digest; listing it would PROCEED); refuse such a path at the load, exit 2 under cli_exit, as check_subject and subject_check already do. R4 (low-medium): attestation_paths.py lets an assistant re-point [oracle] script or [reference] code while [verification] stays; repro: script = the acceptance module (already listed), then smoke_test.py, the real runner, edits freely with PROCEED. Fix: guard [oracle] script and [reference] code writes as [oracle] suite is guarded, and check_subject notes a script also listed in [oracle] suite.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 R1: deleting a file from a listed suite or implementation directory makes the execution verify nothing and the gate's attestation finding and check_subject name the stale digest; tests on both stores
- [ ] #2 R2: a suite or code path outside the instance (absolute or escaping) is refused at the load with exit 2 naming it; tests
- [ ] #3 R4: attestation_paths.py refuses an assistant write that changes [oracle] script or [reference] code while [verification] stays; check_subject notes a script also listed in [oracle] suite; tests
- [ ] #4 The record holds on both subjects; no contract change; CHANGELOG line under Unreleased
<!-- AC:END -->
