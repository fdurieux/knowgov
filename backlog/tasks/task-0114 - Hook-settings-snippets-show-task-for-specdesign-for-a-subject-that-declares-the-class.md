---
id: TASK-0114
title: >-
  Hook settings snippets show --task-for spec=design for a subject that declares
  the class
status: To Do
assignee: []
created_date: '2026-11-04T14:55:00Z'
labels:
  - ci
  - gate
milestone: m-8
dependencies:
  - TASK-0101
priority: low
type: task
ordinal: 114000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Proposed by task-0101; chosen by the maintainer 2026-11-04. instance/ci/claude/ snippets name --task codegen only; the pilot protocol uses design at the spec commit. Show --task-for spec=design, with a note that it applies only where the subject declares [tasks.design].
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The repository and managed snippets carry --task-for spec=design; the README says when to drop it
- [ ] #2 tests/test_claude_hook.py holds the snippets equal to each other
<!-- AC:END -->
