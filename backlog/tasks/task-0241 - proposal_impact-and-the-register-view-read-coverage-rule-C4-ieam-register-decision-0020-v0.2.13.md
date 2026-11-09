---
id: TASK-0241
title: >-
  proposal_impact and the register view read coverage rule C4 (ieam-register
  decision 0020, v0.2.13)
status: To Do
assignee: []
created_date: '2026-11-09T00:14:00Z'
labels:
  - register
  - proposal
  - contracts
dependencies: []
priority: high
ordinal: 235000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
ieam-register v0.2.13 (re-vendored by task-0240, #393, on the maintainer's word: "yes, re-vendor the register at v0.2.13 before 0.9.0") adds coverage rule C4: an approved process that realises an approved capability is supported by an approved application or module. knowgov's harness/proposal_impact.py (_cov, coverage) and demo/app/register_view.py (coverage, coverage_lines) read coverage C1 to C3 by name, and harness/schemas/proposal-impact.schema.json requires exactly C1, C2 and C3. So a proposal that breaks C4 reads clean in proposal_impact, and the register view has no C4 coverage line (its findings list and error badge do show a C4 error). Reading every rule the vendored checker defines, not a fixed list, changes the proposal-impact output, a contract (decision-0016 point 3). Placement is the maintainer's: in 0.9.0 (the coordinator's recommendation, 2026-11-09: it completes the re-vendor the maintainer asked for before the cut, and after the cut it is a 0.10.0), or after the cut with the gap named in 0.9.0's Known limits. Not built until the maintainer answers; depends on task-0240 (#393).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 proposal_impact reads every coverage rule the vendored check_register.py defines (C1 to C4 at v0.2.13), and its schema names C4; a proposal overlay that breaks C4 reports it, hypothetical, as it does C1 to C3
- [ ] #2 The register view's coverage summary and lines name C4 beside C1 to C3
- [ ] #3 A fixture breaking C4 is held by tests and by tools/check_proposal_branch.py or a sibling; the deterministic comparator and the round trip pass with the record unchanged
- [ ] #4 CHANGELOG.md names it under Unreleased › Contract changes
<!-- AC:END -->
