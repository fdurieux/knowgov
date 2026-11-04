---
id: TASK-0083
title: >-
  CI wrappers: prove the GitLab include on a real runner, and convert KG_REPORT
  to each platform's annotations
status: To Do
assignee: []
created_date: '2026-11-04T00:44:00Z'
labels:
  - ci
milestone: m-7
dependencies:
  - TASK-0052
priority: low
ordinal: 87000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
task-0052's GitLab template is checked by running its script lines in sh, not on a GitLab runner; the gate report stays JSON where platforms show annotations (GitHub checks, GitLab code quality, SARIF).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The GitLab include runs green on a GitLab runner, evidence noted
- [ ] #2 A converter turns KG_REPORT into GitHub annotations and GitLab code-quality JSON, tested on S6
<!-- AC:END -->
