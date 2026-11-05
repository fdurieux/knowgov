---
id: TASK-0150
title: The page finds a new subject without a restart (doc-0021 B2)
status: To Do
assignee: []
created_date: '2026-11-05T21:46:00Z'
labels: []
dependencies: []
priority: medium
type: bug
ordinal: 157000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
demo/app/server.py lists the subjects under KG_SUBJECTS once, at import (doc-0021 G3), so a subject added to an instance answers 404 until the page restarts: a restart doc-0021 counts in every onboarding. Maintainer's go, 2026-11-05. task-0141 H1/H2 change the same file's request handling; this change stays in the subject listing.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A subject added under KG_SUBJECTS after start is served on its first request (a rescan on an unknown id, or by modification time), and a removed one stops being listed
- [ ] #2 A test adds a subject to a temporary instance after the server starts and reads it without a restart; the stack job's page checks hold
- [ ] #3 task-0148's prompt drops its restart step in the same PR if 0148 has landed; instance/README.md says so
<!-- AC:END -->
