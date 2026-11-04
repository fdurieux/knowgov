---
id: TASK-0091
title: Capture ingest refuses a handle without the gives role
status: To Do
assignee: []
created_date: '2026-11-04T03:18:00Z'
labels:
  - capture
  - security
milestone: m-5
dependencies:
  - TASK-0059
priority: medium
ordinal: 94000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by task-0059: capture.check_answers checks that a handle is issued (task-0055) but never that it holds the gives role (ieam-register decision 0009), so a handle issued only to approve can give knowledge.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Ingest refuses an answer whose handle lacks gives on the answer's date
- [ ] #2 A test covers it; docs/security.md's permission matrix and gap list move with the fix
<!-- AC:END -->
