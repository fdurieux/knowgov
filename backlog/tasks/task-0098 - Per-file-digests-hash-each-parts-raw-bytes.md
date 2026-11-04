---
id: TASK-0098
title: Per-file digests hash each part's raw bytes
status: To Do
assignee: []
created_date: '2026-11-04T08:46:00Z'
labels:
  - store
milestone: m-6
dependencies:
  - TASK-0094
priority: low
ordinal: 101000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by task-0094: part_sha256 hashes the part as bundled, and the bundler adds a newline to a file that lacks one, so a raw file and its digest could disagree; every J-F file matches the register today.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 part digests hash the file's raw bytes in both adapters and across export/import_turtle
- [ ] #2 register-cites still reads 14 same, 0 differ on J-F C; a test covers a file without a final newline
<!-- AC:END -->
