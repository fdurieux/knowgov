---
id: TASK-0132
title: >-
  proposal_impact branch mode: the overlay from a register branch's diff against
  a base ref (doc-0017 candidate 2)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-04T20:25:00Z'
updated_date: '2026-11-04T20:48:00Z'
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
- [ ] #1 On a scratch branch of the vendored register carrying doc-0017's worked example as files, branch mode's report equals the held-overlay report for the same proposal, ids aside
- [ ] #2 The register checkout's digest is unchanged after a run (test)
- [ ] #3 instance/ci/ gains an optional step, proven in harness.yml on the public register; instance/README.md says what it does and what it reports
<!-- AC:END -->
