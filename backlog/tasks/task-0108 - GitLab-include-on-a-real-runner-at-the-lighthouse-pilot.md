---
id: TASK-0108
title: GitLab include on a real runner, at the lighthouse pilot
status: To Do
assignee: []
created_date: '2026-11-04T11:45:00Z'
labels:
  - ci
  - lighthouse
milestone: m-8
dependencies:
  - TASK-0062
priority: low
type: task
ordinal: 110000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Carries task-0083 AC #1, which the hosted sessions cannot meet (no GitLab account or runner token). Maintainer's decision 2026-11-04: proved where it matters, on the chosen pilot's GitLab if it runs GitLab; parked if the pilot runs GitHub. Until then the shell proof stands (tools/check_ci_wrappers.py, the code-quality report on a broken diagram since #172) and the CHANGELOG's known limit says so.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The include runs on a GitLab runner: include resolution, rules, the image, and artifacts:reports:codequality shown on a merge request; evidence noted
- [ ] #2 If the pilot runs no GitLab, the task is closed as not applicable with the reason
<!-- AC:END -->
