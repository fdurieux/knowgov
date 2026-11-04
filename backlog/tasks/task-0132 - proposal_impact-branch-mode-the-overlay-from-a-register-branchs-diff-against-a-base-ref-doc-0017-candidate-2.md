---
id: TASK-0132
title: >-
  proposal_impact branch mode: the overlay from a register branch's diff against
  a base ref (doc-0017 candidate 2)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T20:25:00Z'
updated_date: '2026-11-04T22:45:00Z'
labels:
  - register
  - proposal
  - ci
milestone: m-6
dependencies:
  - TASK-0130
priority: low
type: feature
ordinal: 132000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0017 §6, candidate 2. In branch mode the overlay is every node file and link added or changed on a register checkout's branch against a base ref; ids are the branch's own. CLI first (`--register-branch DIR --base REF`), then an optional step in `instance/ci/` that runs it on a register pull request and posts nothing but its report. Same report and schema as task-0130; the checkout is read, never written.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 On a scratch branch of the vendored register carrying doc-0017's worked example as files, branch mode's report equals the held-overlay report for the same proposal, ids aside
- [x] #2 The register checkout's digest is unchanged after a run (test)
- [x] #3 instance/ci/ gains an optional step, proven in harness.yml on the public register; instance/README.md says what it does and what it reports
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. branch_overlay(): git diff --name-status between merge-base(base, HEAD) and HEAD; added node files -> overlay nodes, changed node files -> reused changed, new link ids -> overlay links, added exceptions; everything else under branch.not_read. 2. evaluate_branch(): the merge base's register from git archive into a temp dir, evaluate() against it, register line = merge base commit (+ tag), branch section in the report (schema additive). 3. CLI --register-branch DIR --base REF. 4. instance/ci/proposal-impact.sh, advisory (0 report, 2 cannot run), KG_PROPOSAL_REPORT for the JSON. 5. tools/check_proposal_branch.py: scratch git copy of the vendored register, the worked example as draft files on a branch, the step run, report equal to the held overlay's ids aside, checkout digest and HEAD unchanged; a harness.yml step; tests; instance/README section; CHANGELOG.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Equality 'ids aside' compares with link ids mapped to type:source:target, overlay digest and title, register line, branch section and reused.declared dropped (a branch declares reuse only through its links), every list in canonical order (a branch lists by path). Node files read from HEAD, never the working tree. Base tag: git describe of the merge base, else the vendored copy's SOURCE.md tag. Tests: tests/test_proposal_impact.py (branch equality via check_proposal_branch.main, a changed node read as changed with its owner's approval, a removed link under not_read, a bad base and a non-register refused, the CLI refusing --register-branch without --base); both suites pass.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Branch mode for proposal_impact: --register-branch DIR --base REF reads a register checkout's additions since the merge base as the overlay, against the merge base's register from git archive in a temporary directory, never writing the checkout. instance/ci/proposal-impact.sh is the optional advisory step for a register PR, proven in harness.yml by tools/check_proposal_branch.py on a scratch branch of the public register (report equal to the held overlay's, ids aside; checkout unchanged). Report gains branch (null when held). Limits: only additions are read; a deleted node file or a link changed in place is listed, not read; the step opens no store, so keys carry no level.
<!-- SECTION:FINAL_SUMMARY:END -->
