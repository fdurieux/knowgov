---
id: TASK-0094
title: Per-file digests for a directory artefact's Version
status: To Do
assignee: []
created_date: '2026-11-04T07:29:00Z'
labels:
  - register
  - store
milestone: m-6
dependencies:
  - TASK-0088
priority: low
ordinal: 97000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by task-0088: a directory artefact's Version carries one digest for the whole bundle, so register-cites can only count a cited file's fragments, never compare its bytes with the register's digest.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The load records a digest per file of a directory artefact, in both adapters and across export/import_turtle
- [ ] #2 register-cites compares a J-F part's digest with the register's; check_saved_queries pins the result
<!-- AC:END -->
