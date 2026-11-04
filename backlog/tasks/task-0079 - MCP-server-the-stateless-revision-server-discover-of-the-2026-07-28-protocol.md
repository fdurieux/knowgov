---
id: TASK-0079
title: >-
  MCP server: the stateless revision (server/discover) of the 2026-07-28
  protocol
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-04T00:44:00Z'
updated_date: '2026-11-04T01:48:00Z'
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

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Dual-era server in harness/mcp_server.py: a request whose _meta carries io.modelcontextprotocol/protocolVersion is served statelessly (2026-07-28): server/discover (supportedVersions, capabilities, instructions, serverInfo stamp, ttlMs/cacheScope), resultType and serverInfo on every result, caching hints on tools/list, -32022 with supported versions, -32602 without clientCapabilities, ping/initialize not methods of the era.
2. HTTP: MCP-Protocol-Version, Mcp-Method, Mcp-Name (base64 sentinel decoded) must match the body (400, -32020); modern errors 400, unknown method 404; handshake era unchanged.
3. Unit tests (stdio dispatch and HTTP); check_mcp_server.py compares a stateless gate_verdict with the handshake one on a live store.
4. SDK (mcp 2.3.0) client in auto mode, outside the repository, over stdio and HTTP: adopts discover, no initialize; legacy mode still handshakes.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
SDK check (scratchpad, not in the repo, mcp==2.3.0 in its own venv): stdio and HTTP mode=auto -> protocol 2026-07-28 via discover, initialize_result none; mode=legacy -> 2025-11-25 via initialize. Same script on the pre-change server: auto fell back to initialize (2025-11-25). First run found the SDK refuses a modern tools/list without ttlMs/cacheScope (the caching page makes them MUST); added.
<!-- SECTION:NOTES:END -->
