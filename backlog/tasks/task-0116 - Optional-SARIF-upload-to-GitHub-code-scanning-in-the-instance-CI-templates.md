---
id: TASK-0116
title: Optional SARIF upload to GitHub code scanning in the instance CI templates
status: To Do
assignee: []
created_date: '2026-11-04T14:56:00Z'
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
