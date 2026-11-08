---
id: TASK-0231
title: >-
  The MCP servers name the knowgov they run: store_status and serverInfo carry
  VERSION, the commit and the distance (task-0227's identity)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-08T19:54:00Z'
updated_date: '2026-11-08T20:18:00Z'
labels:
  - mcp
  - adopter
dependencies: []
priority: medium
type: feature
ordinal: 229000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer, 2026-11-08: "can I use the MCP to see what current version of knowgov I am using?" The answer was no: both servers' serverInfo read "version": "1" and no tool reported knowgov's version. Then "yes, mint it and dispatch it", relayed by the coordinating session. task-0227's harness/build_identity.py already gives the page {version, commit, describe}; this carries the same identity to the MCP reader and knowgov-runs.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 store_status (harness/mcp_server.py) gains an additive knowgov object, {version, commit, describe}, the same shape and values as the page's /api/subjects, read once at start through harness/build_identity.py; each part null when unknown, never guessed; its schema (harness/schemas/store-status.schema.json) holds the field
- [x] #2 knowgov-runs: run_options, its status of what may be run, carries the same object for that server's own copy; run-options' schema holds it; no new tool
- [x] #3 serverInfo.version: what it touches measured (tests, pinned bytes, the stateless _meta stamp), and either (a) set to knowgov's VERSION on both servers and both eras, or (b) left as "1"; the choice recommended in the PR under DECIDE with its evidence
- [x] #4 instance/README.md's MCP section says how to ask (call store_status; its knowgov field names the version); CHANGELOG under Unreleased > Contract changes, additive
- [x] #5 New tests fail on main first; run_tests (stdlib, without yaml, pins), check_mcp_server and check_transports on stdio and HTTP, and the comparator stay green
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. mcp_server: KNOWGOV = build_identity.identity() once at import; SERVER version = KNOWGOV['version'] or 'unknown'; store_status carries knowgov.
2. mcp_runs: SERVER version from mcp_server.SERVER; run_options carries knowgov (no new tool).
3. store-status and run-options schemas: knowgov required, three nullable strings.
4. Tests failing on main first; instance/README; CHANGELOG under Contract changes.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Measured what serverInfo.version touches: no test, pinned sample, workflow or doc asserts its value; tests/test_mcp_server.py and tools/check_mcp_server.py read serverInfo's name only; the stateless _meta stamp copies self.info['version']; the managed allowlist admits servers by name. So option (a) was taken: both servers report knowgov's VERSION in both eras ('unknown' if VERSION cannot be read). The new tests (tests/test_mcp_knowgov_version.py) all failed on main 76e1e04 (KeyError knowgov, serverInfo version '1'). Local: run_tests stdlib 812/860, bare venv without yaml 806/860, pins 859/860, each 0 failed; check_mcp_server (with check_transports, stdio and HTTP, both eras) every check holds on CargoQuote S1,S2,S6 and J-F C,D3; comparator on rdflib CargoQuote 0 diffs over 7, J-F 0 over 6.

serverInfo.version: the maintainer, 2026-11-08, "keep (a)" (relayed by the coordinating session): both servers report knowgov's VERSION, in the initialize reply and in the stateless era's _meta stamp. The evidence that nothing pins "1": no test asserts serverInfo.version (tests/test_mcp_server.py and tests/test_mcp_runs.py read its name only, as does tools/check_mcp_server.py); the stateless stamp copies info['version']; no doc, sample, workflow or settings snippet shows "version": "1" for either server; the managed allowlist and the hook settings admit servers by name; the only "version": "1" strings in the repository are clients' clientInfo.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The MCP servers name the knowgov they run. harness/mcp_server.py reads task-0227's identity once at start (KNOWGOV, build_identity.identity()); store_status and knowgov-runs' run_options carry it as knowgov {version, commit, describe}, the page's /api/subjects shape, each null when unknown; their schemas hold the field. Both servers' serverInfo.version, in the initialize reply and the stateless _meta stamp, is now knowgov's VERSION instead of '1' (option (a): nothing in the repo or its docs is bound to '1'). instance/README.md says to ask store_status which version is running and how to compare it with git describe; CHANGELOG under Unreleased > Contract changes, additive.
<!-- SECTION:FINAL_SUMMARY:END -->
