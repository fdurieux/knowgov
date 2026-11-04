---
id: TASK-0088
title: >-
  The register-cites saved query joins directory artefacts as
  register_node_statements does
status: To Do
assignee: []
created_date: '2026-11-04T01:31:00Z'
labels:
  - register
  - impact
milestone: m-6
dependencies:
  - TASK-0077
priority: low
ordinal: 92000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by task-0077: register-cites still joins citations to artefacts by exact path, so for directory artefacts (J-F's contracts/, uml/) with <file>: locators its digest comparison means nothing.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 register-cites matches directory artefacts by locator, as the fixed join does
- [ ] #2 check_saved_queries.py and a stdlib test cover a J-F directory citation
<!-- AC:END -->
