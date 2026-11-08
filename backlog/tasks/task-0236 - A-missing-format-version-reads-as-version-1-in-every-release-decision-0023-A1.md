---
id: TASK-0236
title: >-
  A missing format version reads as version 1 in every release (decision-0023
  A1)
status: To Do
assignee: []
created_date: '2026-11-08T23:46:00Z'
labels:
  - formats
  - contracts
  - instance
dependencies: []
priority: high
ordinal: 231000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0023 Amendment A1 (2026-11-08, taken under the maintainer's overnight delegation): a file that names no format version reads as version 1, in every release, not as the current one until 1.0. At 0.9.0 every input's current version is 1, so no behaviour changes now; the rule is what decision-0016 point 4 needs, no change of meaning at 1.0.0. harness/formats.py holds the missing version apart from CURRENT; instance/README.md's "Format versions" section and its contracts row, harness/formats.py's docstring and the CHANGELOG's task-0174 line (Unreleased) drop "until 1.0".
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 harness/formats.py reads a missing version as 1 for every kind, through a constant held apart from CURRENT
- [ ] #2 A test moves CURRENT to 2 for a kind and reads an unstamped file as 1, a format = 2 file as 2 and a format = 3 file as refused (FormatTooNew, exit 2)
- [ ] #3 instance/README.md (Format versions, the contracts row), the formats.py docstring and the CHANGELOG's Unreleased task-0174 line state the rule without "until 1.0"; no other reader or writer changes
<!-- AC:END -->
