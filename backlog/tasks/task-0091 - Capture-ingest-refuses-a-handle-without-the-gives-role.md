---
id: TASK-0091
title: Capture ingest refuses a handle without the gives role
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-04T03:18:00Z'
updated_date: '2026-11-04T03:35:00Z'
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

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. capture.check_answers: a handle on the issued list without gives is refused, with a message naming the role (roles are per handle; the date rule is the existing issued/withdrawn check).
2. tests/test_capture.py::test_ingest_refuses_a_handle_without_gives: a handle with approves and closes only is refused; the same with gives answers; every handle the vendored register issues holds gives, so the CI capture steps (employee-1) stay valid.
3. docs/security.md: Gap 2 removed and the rest renumbered; the matrix row and its evidence row cite the test; instance/README.md's ingest paragraph names the rule.
<!-- SECTION:PLAN:END -->
