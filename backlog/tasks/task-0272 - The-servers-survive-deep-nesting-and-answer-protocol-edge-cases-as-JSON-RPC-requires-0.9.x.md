---
id: TASK-0272
title: >-
  The servers survive deep nesting and answer protocol edge cases as JSON-RPC
  requires (0.9.x)
status: To Do
assignee: []
created_date: '2026-11-09T09:33:00Z'
labels:
  - validation
  - security
dependencies: []
references:
  - backlog/decisions/decision-0032
  - task-0256
priority: high
ordinal: 266000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
`json.loads` raises RecursionError on a deeply nested request, and `handle_text`, `handle_http` and `http_boundary.read_json_body` do not catch it:
- MCP stdio exits 1 on one 200k-level line, so the next request is never answered. That breaks task-0200 M6's promise that the loop survives; `mcp_runs` shares the path.
- A 20k-level body (40 KB, under every limit) drops the MCP HTTP connection, and the page's, with no response.

Protocol edge cases:
- An `id` of [1] or 1.5 is accepted and echoed, where JSON-RPC requires -32600.
- A `_meta` protocolVersion of 5, an int, drops to the handshake era without its checks.
- Invalid UTF-8 in an HTTP body is decoded with "replace" and answered, where -32700 is required.
- A lower-case `bearer` scheme gets 401 on both servers and the page, though RFC 7235 makes the scheme case-insensitive.

Content edges:
- The page's startup line names bolt://localhost:7687 under `KG_STORE=rdflib`.
- The `add_artefact` prompt's `file` token accepts NUL, control characters, `..` and absolute paths, and places them verbatim in the prompt text.

These are fix-only.

Source: group 2 F6, F11 and F12, decision-0032 (task-0256), probed on main 2a8bbeb.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A request nested beyond the parser's depth gets -32700 on the MCP (both transports, both servers) or 400 on the page, and the stdio loop answers the next request. A test sends the 200k-level line.
- [ ] #2 The JSON-RPC `id`, the `_meta` version type and invalid UTF-8 are refused as named, and the bearer scheme is compared case-insensitively.
- [ ] #3 `add_artefact`'s `file` refuses control characters, `..` and absolute paths, as `subject_check` confines paths.
- [ ] #4 `check_mcp_server` and `check_transports` pass on both transports and both eras.
<!-- AC:END -->
