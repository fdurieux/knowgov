---
id: TASK-0236
title: >-
  A missing format version reads as version 1 in every release (decision-0023
  A1)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-08T23:46:00Z'
updated_date: '2026-11-09T01:07:00Z'
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
- [x] #1 harness/formats.py reads a missing version as 1 for every kind, through a constant held apart from CURRENT
- [x] #2 A test moves CURRENT to 2 for a kind and reads an unstamped file as 1, a format = 2 file as 2 and a format = 3 file as refused (FormatTooNew, exit 2)
- [x] #3 instance/README.md (Format versions, the contracts row), the formats.py docstring and the CHANGELOG's Unreleased task-0174 line state the rule without "until 1.0"; no other reader or writer changes
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Built for R1, as dispatched; held in PR 2 until the maintainer answers decision-0023 Amendment A1 (proposed).
1. harness/formats.py: MISSING = 1, held apart from CURRENT; version() returns MISSING when a file names none, for every kind; the docstring drops "until 1.0".
2. tests/test_formats.py: for each kind, CURRENT moved to 2. An unstamped file reads 1, format = 2 reads 2, and format = 3 is FormatTooNew and exit 2 through cli_exit.run. The old assertion (missing reads the current one) is reversed.
3. instance/README.md ("Format versions" and the contracts row), the CHANGELOG's Unreleased task-0174 line (edited in place) and CLAUDE.md state the rule without "until 1.0".
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Both format tests fail on main's formats.py: the old-rule one fails, and the new one errors on the missing MISSING. They pass here, bare and with the pins.
grep finds no "until 1.0" left in instance/README.md, formats.py, CHANGELOG.md or CLAUDE.md. CLAUDE.md, the maintainer's own description of the rule, was updated too, though the AC does not name it.
No reader or writer besides version() changes: at 0.9.0 every CURRENT is 1, so no behaviour moves.
If the maintainer picks R0 (refuse a missing version from 0.9.0), the ACs are restated and this is reworked.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
decision-0023 Amendment A1 (R1), built and held for the maintainer.
- A file that names no format version reads as version 1, in every release: harness/formats.py's MISSING, apart from CURRENT.
- A test moves each kind's CURRENT to 2 and holds an unstamped file at 1, format = 2 at 2, and format = 3 refused, exit 2.
- "until 1.0" is gone from the Format versions text and the contracts row, the docstring, the CHANGELOG's task-0174 line and CLAUDE.md.
- No behaviour moves at 0.9.0, since every current version is 1.
Merges only on the maintainer's word on A1.
<!-- SECTION:FINAL_SUMMARY:END -->
