---
id: TASK-0007
title: Gate CLI conforming to the site's gate contract
status: To Do
assignee: []
created_date: '2026-11-01T14:27:00Z'
updated_date: '2026-11-01T14:30:00Z'
labels:
  - platform
  - gate
milestone: m-3
dependencies:
  - TASK-0003
priority: low
type: feature
ordinal: 7000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The gate returns PROCEED, QUALIFIED or BLOCKED to an assistant and writes files; it has no command-line form and no exit code. The programme's gate contract on fdurieux.github.io asks for exit codes 0, 1 and 2, a severity threshold, a baseline and ratchet, JSON under a published schema, and evidence tags. A CLI form makes knowgov a programme project in the site's sense and lets it claim table rows honestly.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A command resolves a task against a loaded subject and exits 0 on PROCEED, 1 on BLOCKED or on QUALIFIED above a chosen threshold, 2 when it cannot run
- [ ] #2 The JSON report is validated against a shipped schema
- [ ] #3 The record is the baseline: a verdict worse than the record's for the same subject and task is a regression
<!-- AC:END -->
