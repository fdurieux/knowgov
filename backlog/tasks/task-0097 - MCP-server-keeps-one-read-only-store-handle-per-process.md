---
id: TASK-0097
title: MCP server keeps one read-only store handle per process
status: To Do
assignee: []
created_date: '2026-11-04T08:46:00Z'
labels:
  - mcp
  - ci
milestone: m-8
dependencies:
  - TASK-0095
priority: low
ordinal: 100000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by task-0095: the MCP server reopens the store on every call, about 4 s per J-F call on rdflib; one read-only handle per process would save about 30 s a J-F scenario in every MCP step (check_mcp_server, the lighthouse).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The server opens the store once per process behind the same read-only view and serves every call from it
- [ ] #2 check_mcp_server and the lighthouse step pass unchanged and the step timings in the task notes show the saving
<!-- AC:END -->
