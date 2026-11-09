---
id: TASK-0236
title: >-
  A missing format version reads as version 1 in every release (decision-0023
  A1)
status: To Do
assignee: []
created_date: '2026-11-08T23:46:00Z'
updated_date: '2026-11-08T23:53:00Z'
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
decision-0023 Amendment A1 (proposed 2026-11-08, parked for the maintainer): what a file that names no format version means after 0.9.0. "The current one until 1.0" would change a contract at 1.0.0, against decision-0016 point 4. R1 (recommended): a missing version reads as version 1, in every release, with an optional tools/check_instance.py note never a failure. R0: a missing version is refused from 0.9.0, exit 2, naming the key. The build is prepared for R1 and its PR waits for the maintainer's word; if R0 is chosen, the ACs are restated. Either way instance/README.md's "Format versions" section and contracts row, harness/formats.py's docstring and the CHANGELOG's Unreleased task-0174 line drop "until 1.0".
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 harness/formats.py reads a missing version as 1 for every kind, through a constant held apart from CURRENT
- [ ] #2 A test moves CURRENT to 2 for a kind and reads an unstamped file as 1, a format = 2 file as 2 and a format = 3 file as refused (FormatTooNew, exit 2)
- [ ] #3 instance/README.md (Format versions, the contracts row), the formats.py docstring and the CHANGELOG's Unreleased task-0174 line state the rule without "until 1.0"; no other reader or writer changes
<!-- AC:END -->
