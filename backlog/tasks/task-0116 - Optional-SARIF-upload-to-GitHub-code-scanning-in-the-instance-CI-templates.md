---
id: TASK-0116
title: Optional SARIF upload to GitHub code scanning in the instance CI templates
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-04T14:56:00Z'
updated_date: '2026-11-06T03:33:00Z'
labels:
  - ci
milestone: m-8
dependencies: []
priority: low
type: task
ordinal: 116000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Proposed by task-0106; chosen by the maintainer 2026-11-04. harness/annotate.py already writes SARIF 2.1.0; the GitHub action could upload it to code scanning when the instance opts in.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 instance/ci/github/action.yml has an opt-in input that uploads the SARIF; off by default
- [ ] #2 harness.yml exercises it once; the README says what it needs (permissions, code scanning enabled)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. instance/ci/github/action.yml: inputs sarif (default false) and sarif-category; the run step adds sarif:$RUNNER_TEMP/knowgov-<gate>.sarif to KG_ANNOTATE, keeps the gate's exit, writes the file to an output; a second step, if always() and sarif and a file, github/codeql-action/upload-sarif pinned by commit (v4.39.1, 9b32540); output sarif-id. 2. harness.yml: security-events: write on the rdflib job only; the existing S1 as-of step (exit 1, 30 located results) with sarif on except a fork's pull request; the check step asserts sarif-id. 3. README: what an instance needs. 4. Tests: test_ci_wrappers (input, pin, condition, permission scope, README), test_pins covers the pin. 5. CHANGELOG Unreleased > Changes.
<!-- SECTION:PLAN:END -->
