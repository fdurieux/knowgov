---
id: TASK-0080
title: MCP gate_verdict with the full evidence bundle for an agent's context
status: To Do
assignee: []
created_date: '2026-11-04T00:44:00Z'
labels:
  - mcp
milestone: m-8
dependencies:
  - TASK-0056
priority: low
ordinal: 84000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Proposed by the task-0056 session: gate_verdict returns the report; an agent building on the knowledge needs the evidence bundle (gate.render_bundle) the arms read.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A read-only tool or option returns the bundle for a task or key set
- [ ] #2 tools/check_mcp_server.py holds it equal to what the arms read
<!-- AC:END -->
