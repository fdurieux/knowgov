---
id: TASK-0115
title: >-
  The instance layout check's problems go into the pre-load report, so they
  annotate
status: To Do
assignee: []
created_date: '2026-11-04T14:55:00Z'
labels:
  - ci
  - preload
milestone: m-8
dependencies: []
priority: low
type: task
ordinal: 115000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Proposed by task-0106; chosen by the maintainer 2026-11-04. The layout check's problems reach only the job log; the pre-load report should carry them so KG_ANNOTATE shows them as annotations.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A layout problem in the example instance appears in the pre-load report and as a GitHub annotation and a GitLab code-quality entry
- [ ] #2 The preload report schema change is additive; the exit code is unchanged
<!-- AC:END -->
