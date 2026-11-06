---
id: TASK-0177
title: >-
  Response sizes bounded on the page and the MCP server (doc-0028 section 10 K9,
  T-c)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-06T13:27:00Z'
updated_date: '2026-11-06T14:17:00Z'
labels:
  - security
  - page
  - mcp
dependencies: []
priority: medium
type: task
ordinal: 178000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
H2 (task-0141.04) bounded what a request may cost, but not what a response may: no cap exists in demo/app or harness/mcp_server.py (0.7.0 and 0.8.0 Known limits). A query over a large instance, such as held_keys, evidence_bundle or a register listing without limit, can return an unbounded body. Each server gets a per-response cap, set above the largest legitimate response measured on both public subjects. A response over it is refused, naming the setting, and never truncated silently. Drafted by the v1.0 session (task-0173), minted under doc-0029.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The largest response of every page endpoint and MCP tool is measured on both public subjects, and the defaults sit above it with a stated margin
- [x] #2 KG_PAGE_MAX_RESPONSE and KG_MCP_MAX_RESPONSE are bounded settings, each refused outside its bounds with the variable's name; a response over the cap is refused: 500 with a JSON error naming the setting on the page, an error result on MCP; nothing is truncated
- [x] #3 LIMIT-08 in tests/test_http_limits.py holds both servers under a small injected cap
- [x] #4 The Known limit is removed with its CHANGELOG line (a contract change: a new refusal), and docs/security.md's HTTP row says so
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Measure every page route (both subjects: 57 register nodes x walks x children, every scenario's views, cascades, guides) and every MCP tool (1813 recorded answers of check_mcp_server's full runs).
2. http_boundary.response_cap: a bounded setting (4 KiB..1 GiB, else refused naming the variable); Limits.max_response.
3. Page: Handler._send refuses a body over KG_PAGE_MAX_RESPONSE with a 500 JSON error naming it.
4. MCP: Server._capped turns a tools/call result over KG_MCP_MAX_RESPONSE into an error result (no structuredContent), both transports and knowgov-runs (same Server); a bad cap exits 2 at start.
5. LIMIT-08 and the bounds test; CHANGELOG Contract changes; docs/security.md HTTP row.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Measured 2026-11-06, largest response per route or tool, on both public subjects:
- page (rdflib store holding S1; every route, 57 nodes x 2 walks x children, every scenario, cascades, guides): /api/results/S6 cargo_quote 391605 B; /api/register (J-F, today=wall) 152062; impact ENT-0006 children 84702; / 66422; footprint S7 43435; the rest under 25 KB.
- MCP (1813 answers recorded from check_mcp_server on every scenario of both subjects, stdio and HTTP, measured as the JSON-RPC response): evidence_bundle J-F D4 653400 B; held_keys D2 258165; document_statements D1 229642; register_impact 145548; proposal_impact 132781; gate_verdict 83795; the rest under 42 KB.
Defaults: KG_PAGE_MAX_RESPONSE 8 MiB (21x the page's largest), KG_MCP_MAX_RESPONSE 16 MiB (25x the MCP largest); bounds 4 KiB..1 GiB.
Refused MCP response: an error result {content: [text naming KG_MCP_MAX_RESPONSE, the size and the cap], isError: true}, no structuredContent: the shape of every error result, so no output schema (task-0172) is bent. knowgov-runs is capped by the same Server class (its answers are small; capped all the same).
Suites: stdlib 627/651, pinned 649/651, 0 failed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Both servers cap a response: the page at KG_PAGE_MAX_RESPONSE (8 MiB), a 500 JSON error naming it above; the MCP reader and knowgov-runs at KG_MCP_MAX_RESPONSE (16 MiB) per tools/call result, on either transport, an error result naming it above, no structuredContent. Nothing truncated. Defaults about twenty times the largest measured response on both public subjects; caps bounded 4 KiB..1 GiB, refused with the variable name (MCP servers exit 2 at start). LIMIT-08 and a bounds test; CHANGELOG Contract changes; docs/security.md HTTP row.
<!-- SECTION:FINAL_SUMMARY:END -->
