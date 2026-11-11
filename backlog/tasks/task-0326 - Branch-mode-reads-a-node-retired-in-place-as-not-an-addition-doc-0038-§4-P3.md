---
id: TASK-0326
title: Branch mode reads a node retired in place as not an addition (doc-0038 §4 P3)
status: Done
assignee: []
created_date: '2026-11-11T13:34:00Z'
updated_date: '2026-11-11T15:52:00Z'
labels:
  - register
  - 0.9.0
dependencies: []
priority: high
ordinal: 318000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Fix-only, pulled before the 0.9.0 cut under decision-0032 (fails open in the advisory step). Redo group B's N4 (doc-0038 §4 P3). proposal_impact --register-branch reads a node whose state moves to retired or deprecated in place as a 'changed' reuse, approved, reaching nothing new, with a self-candidate 'D1 authored stated: CAP-0003: same as CAP-0003'; a link deprecated in place already goes to not_read. The advisory CI step (instance/ci/proposal-impact.sh) therefore reads a retirement PR as harmless. Fix: list such a node under not_read, pointing to register_impact and gate_cli --register-previous, with no self-candidate.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A branch moving CAP-0003 to retired lists CAP-0003 under not_read with a pointer to register_impact and --register-previous; no reuse entry and no self-candidate; a test (tools/check_proposal_branch.py case)
- [x] #2 Additions keep their outcome; the worked example tools/fixtures/proposal_contract_quote.json is unchanged
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Built by session_01HTAA1UjvoTDDjusu1chtAs (#481), merged in train #484 as a214137 on a whole green matrix with stack; recorded by the coordinator, the builder having no backlog CLI. proposal_impact.branch_overlay through _node_file and _left_in_place. retired_in_place() fails on main's harness/ (not_read [], 2 failures) and passes on the fix. Re-check sent to group B.

Re-checked by group B at a214137: FIXED (CAP-0003 retired in place under not_read; a deprecated parent with re-parented children likewise). Residual R1-R3 to task-0329.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Branch mode lists a node whose state moves to retired or deprecated in place under branch.not_read, pointing to register_impact and gate_cli --register-previous, with no reuse entry, reach or self-candidate. Tests: test_p3_a_node_retired_in_place_is_not_read_as_a_reuse_and_has_no_self_candidate and tools/check_proposal_branch.py retired_in_place (AC1); the worked example is unchanged (AC2).
<!-- SECTION:FINAL_SUMMARY:END -->
