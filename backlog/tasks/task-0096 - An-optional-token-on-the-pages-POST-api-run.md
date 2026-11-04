---
id: TASK-0096
title: An optional token on the page's POST /api/run
status: To Do
assignee: []
created_date: '2026-11-04T07:29:00Z'
labels:
  - security
  - page
milestone: m-8
dependencies:
  - TASK-0090
priority: medium
ordinal: 99000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
docs/security.md still names gap 1: the page has no login, and POST /api/run can start a run that calls the model. task-0090 binds the stack to 127.0.0.1 by default; on a wider bind a token, as KG_MCP_TOKEN does for MCP, would close the run endpoint.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 With KG_PAGE_TOKEN set, POST /api/run and every state-changing endpoint require it as a bearer token; on a wider bind without it the run endpoints refuse
- [ ] #2 docs/security.md's gap list, the demo README and test_security move with the fix; the stack job passes
<!-- AC:END -->
