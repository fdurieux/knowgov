---
id: TASK-0177
title: >-
  Response sizes bounded on the page and the MCP server (doc-0028 section 10 K9,
  T-c)
status: To Do
assignee: []
created_date: '2026-11-06T13:27:00Z'
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
- [ ] #1 The largest response of every page endpoint and MCP tool is measured on both public subjects, and the defaults sit above it with a stated margin
- [ ] #2 KG_PAGE_MAX_RESPONSE and KG_MCP_MAX_RESPONSE are bounded settings, each refused outside its bounds with the variable's name; a response over the cap is refused: 500 with a JSON error naming the setting on the page, an error result on MCP; nothing is truncated
- [ ] #3 LIMIT-08 in tests/test_http_limits.py holds both servers under a small injected cap
- [ ] #4 The Known limit is removed with its CHANGELOG line (a contract change: a new refusal), and docs/security.md's HTTP row says so
<!-- AC:END -->
