---
id: TASK-0326
title: Branch mode reads a node retired in place as not an addition (doc-0038 §4 P3)
status: To Do
assignee: []
created_date: '2026-11-11T13:34:00Z'
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
- [ ] #1 A branch moving CAP-0003 to retired lists CAP-0003 under not_read with a pointer to register_impact and --register-previous; no reuse entry and no self-candidate; a test (tools/check_proposal_branch.py case)
- [ ] #2 Additions keep their outcome; the worked example tools/fixtures/proposal_contract_quote.json is unchanged
<!-- AC:END -->
