---
id: TASK-0336
title: register_impact walks the thread (decision-0039 §3.3)
status: To Do
assignee: []
created_date: '2026-11-11T22:53:00Z'
labels:
  - contract
  - 0.9.0
dependencies: []
priority: high
ordinal: 328000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0039 §3.3 (a), doc-0038 §3.3, B-D7. register_impact's walk enum is [dependants, realisers]; FR-06 names thread too. Add walk=thread, using the register's THREAD walk as proposal_impact already loads it (harness/proposal_impact.py), with register_impact's answer shape (edges, reached, keys, gate). It is offered on the MCP tool's inputSchema, the CLI and the page's impact route where it lists walks. check_mcp_server and the page's agreement check hold it.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 register_impact walk=thread from a capability and from a process reaches the entities and keys the register's THREAD walk reaches; tests against tools/impact.py
- [ ] #2 The MCP inputSchema, CLI and page offer it, and check_mcp_server holds stdio equal to HTTP; the record holds
<!-- AC:END -->
