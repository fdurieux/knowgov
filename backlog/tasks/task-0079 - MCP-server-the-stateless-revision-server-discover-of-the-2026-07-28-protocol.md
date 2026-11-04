---
id: TASK-0079
title: >-
  MCP server: the stateless revision (server/discover) of the 2026-07-28
  protocol
status: To Do
assignee: []
created_date: '2026-11-04T00:44:00Z'
labels:
  - mcp
milestone: m-8
dependencies:
  - TASK-0056
priority: low
ordinal: 83000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
task-0056's server speaks the handshake; the SDK client probes server/discover first and falls back. Supporting the stateless revision removes the fallback for current clients.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 server/discover answers per the revision over stdio and HTTP
- [ ] #2 The official SDK client in auto mode uses it without falling back, checked outside the repository and noted
- [ ] #3 The handshake still works for older clients
<!-- AC:END -->
