---
id: TASK-0079
title: >-
  MCP server: the stateless revision (server/discover) of the 2026-07-28
  protocol
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T00:44:00Z'
updated_date: '2026-11-04T02:40:00Z'
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
- [x] #1 server/discover answers per the revision over stdio and HTTP
- [x] #2 The official SDK client in auto mode uses it without falling back, checked outside the repository and noted
- [x] #3 The handshake still works for older clients
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

After merging main (task-0075 pins the clock under the test runner), an exception a tool raises outside ToolError (WallClock) killed the HTTP handler thread; tools/call now returns it as an isError result. Re-proven after the merge: tests 253/253 plain and jef; check_mcp_server rdflib both subjects and Neo4j 5.26 S1,S2,S6; the SDK check as before.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
harness/mcp_server.py is now dual-era. A request whose _meta declares io.modelcontextprotocol/protocolVersion is served statelessly per 2026-07-28: server/discover (supportedVersions modern then legacy, capabilities, instructions, serverInfo stamp, ttlMs/cacheScope), resultType and the serverInfo stamp on results, caching hints on tools/list, -32022 with the versions supported, -32602 without clientCapabilities. Over HTTP the MCP-Protocol-Version, Mcp-Method and Mcp-Name headers must match the body (400, -32020); modern errors are 400, or 404 for an unknown method. initialize and the handshake era are unchanged. Still standard library only; the store stays behind READS. Proof: the official SDK (mcp 2.3.0, in its own venv outside the repo) in mode=auto adopts discover at 2026-07-28 over stdio and HTTP with no initialize, where the pre-change server made it fall back to 2025-11-25; mode=legacy still handshakes. check_mcp_server.py compares a stateless gate_verdict with the handshake one on a live store. Not served: subscriptions/listen (nothing is pushed) and MRTR (no tool needs client input).
<!-- SECTION:FINAL_SUMMARY:END -->
