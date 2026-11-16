---
id: TASK-0365
title: >-
  MCP reader: a clipped result says so, with its total and the narrower call
  (0.10.0)
status: To Do
assignee: []
created_date: '2026-11-16T20:28:00Z'
labels:
  - contract
  - 0.10.0
  - mcp
dependencies: []
priority: medium
ordinal: 355000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer, 2026-11-16: "yes, add them as 0.10.0 tasks", after a Claude Desktop session over MCP gave a private subject's counts and links loosely: it summarised a report too large to read whole, carried the wrong count forward, and inferred a subject-to-application link no tool states. A result cut to fit the reader's response limit reaches the assistant without a mark that it is partial, so the assistant generalises from a sample. Ships in 0.10.0 beside task-0364.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Every tool result cut to fit carries, in _meta, that it is partial, the full count of what it holds, and how to ask narrowly (the filter or summary argument that fits)
- [ ] #2 An uncut result carries no such mark; the mark is the same on both transports and both stores
- [ ] #3 check_mcp_server.py holds a clipped and an unclipped case; a schema or the _meta contract documents the fields; CHANGELOG Unreleased under contract changes
<!-- AC:END -->
