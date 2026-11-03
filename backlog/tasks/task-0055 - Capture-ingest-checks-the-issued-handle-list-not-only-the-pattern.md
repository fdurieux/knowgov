---
id: TASK-0055
title: Capture ingest checks the issued-handle list, not only the pattern
status: To Do
assignee: []
created_date: '2026-11-03T22:50:00Z'
labels:
  - capture
milestone: m-5
dependencies:
  - TASK-0037
priority: medium
type: bug
ordinal: 67000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by task-0037 (#82): harness/capture.py ingest checks answered.from against the handle pattern only; decision 0009 (register v0.2.4) lists issued handles in people/handles.toml and its checker refuses an unissued handle. Ingest should refuse the same: a handle not issued, issued after the answer's date, or withdrawn by then. The capture CI step currently answers as steward-1, which is not issued.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 ingest refuses an unissued, not-yet-issued or withdrawn handle, naming the rule, when the register lists issued handles; the pattern alone applies when it lists none
- [ ] #2 The CI capture step and the docs use an issued handle (employee-1)
- [ ] #3 Tests cover each refusal
<!-- AC:END -->
