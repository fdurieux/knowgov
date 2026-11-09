---
id: TASK-0272
title: >-
  The servers survive deep nesting and answer protocol edge cases as JSON-RPC
  requires (0.9.x)
status: Done
assignee: []
created_date: '2026-11-09T09:33:00Z'
updated_date: '2026-11-09T10:54:00Z'
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
- [x] #1 A request nested beyond the parser's depth gets -32700 on the MCP (both transports, both servers) or 400 on the page, and the stdio loop answers the next request. A test sends the 200k-level line.
- [x] #2 The JSON-RPC `id`, the `_meta` version type and invalid UTF-8 are refused as named, and the bearer scheme is compared case-insensitively.
- [x] #3 `add_artefact`'s `file` refuses control characters, `..` and absolute paths, as `subject_check` confines paths.
- [x] #4 `check_mcp_server` and `check_transports` pass on both transports and both eras.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Built on claude/task-0272-servers-nesting (PR #412). http_boundary.parse_json is the one parse path (mcp_server handle_text and handle_http, which knowgov-runs shares; the page's read_json_body): strict UTF-8, json.loads, RecursionError and JSONDecodeError as NotJson; -32700 on both MCP servers and transports, 400 on the page, the stdio loop answering the next request. mcp_server.malformed() runs first in Server._handle and handle_http: an id not a string, whole number or null is -32600 with a null id; a non-string _meta protocolVersion is -32602. The HTTP transport passes the body's bytes, so invalid UTF-8 is -32700, never a replace decode. http_boundary.bearer_matches compares the scheme case-insensitively (RFC 7235), the token by hmac.compare_digest, on both servers and the page (write_guard). server.store_named names the store in use in the startup line (rdflib and its file, or in memory). wizard.file_refusal (via _check_argument) refuses control characters (C0, DEL, C1), a backslash, ~, absolute paths and .. segments in add_artefact's file. Tests: tests/test_protocol_edges.py, eight (the 200k-level stdio line then a request on both servers; a 20k-level 40 KB body and invalid UTF-8 over HTTP on both servers and the page; ids; _meta types; bearer case on both servers and the page; the startup line; add_artefact paths directly and over prompts/get; the changelog line). Complexity: wizard.get's rise removed by _check_argument; baseline 188 to 186. Local, CPython 3.13 with rdflib: run_tests 894/944 (50 skipped) default and 893/944 (51 skipped) J-F, 0 failed; check_mcp_server --scenarios S1,S2,S6 with check_transports, every check holds; the CQ comparator 0 differing leaves.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The servers survive deep nesting and answer JSON-RPC's protocol edge cases. One parse path (http_boundary.parse_json) makes a request nested past the parser's depth, or not UTF-8, a parse error: -32700 on both MCP servers and both transports, 400 on the page, and the stdio loop answers the next request. An id that is not a string, a whole number or null is -32600; a non-string _meta protocol version is -32602; the Bearer scheme is matched case-insensitively on both servers and the page. The page's startup line names the store in use, and add_artefact's file is confined as subject_check confines paths. Fix-only; tests/test_protocol_edges.py; both suites, check_mcp_server (both eras, both transports) and the comparator pass locally.
<!-- SECTION:FINAL_SUMMARY:END -->
