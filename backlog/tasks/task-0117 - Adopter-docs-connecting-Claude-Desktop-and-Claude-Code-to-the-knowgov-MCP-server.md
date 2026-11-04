---
id: TASK-0117
title: >-
  Adopter docs: connecting Claude Desktop and Claude Code to the knowgov MCP
  server
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T15:07:00Z'
updated_date: '2026-11-04T15:30:00Z'
labels:
  - mcp
  - docs
milestone: m-8
dependencies: []
priority: medium
type: docs
ordinal: 117000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From the 'Connecting agents to knowgov MCP' findings (2026-11-04, section 2.5 and task D). instance/README.md §'Letting an AI assistant ask the gate' gains: a Claude Desktop recipe (config file path on macOS and Windows, absolute paths and the full docker path, merge into an existing file, quit and reopen, Chat mode not Code sessions, the permission prompt, the log path); 'replace /path/to/knowgov with your absolute path'; claude mcp add -s user; KG_SUBJECT is a path to the subject root, not its id; the stateless HTTP example carries _meta clientCapabilities; the phone via Remote Control, never a public endpoint; the server reads whatever scenario the page last loaded, so pass scenario in every call, and restart the client after switching (until task-0097).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Each of the eight pitfalls in the findings' §2.5 is answered in the README or stated as a limit
- [x] #2 The stateless example carries clientCapabilities and a test runs it against the server
- [x] #3 Every command flag the section names exists (a docs-flags style guard, added if none covers this README)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Read mcp_server.py (KG_SUBJECT, _meta, flags, per-call store open), compose (no 8765), claude mcp add --help, MCP docs for Desktop paths.
2. Rewrite instance/README.md §'Letting an AI assistant ask the gate' from the stdio paragraph on: subject and scenario, Claude Code (-s user), Claude Desktop recipe, phone via Remote Control, HTTP with a stateless curl example, example prompts.
3. tests/test_mcp_server.py: run the README's curl example against the server (and -32602 without clientCapabilities); a guard on every flag the section names; the pitfalls held by phrase.
4. CHANGELOG line; both suites.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Verified here: claude mcp add flags (-s/-e/-t/-H) from Claude Code's own --help; claude remote-control exists; mcp_server.py flags through its --help in the guard; the curl body and headers posted as printed to a stub server over HTTP (200, BLOCKED on the stub) and -32602 without clientCapabilities; compose publishes 8080/7474/7687 only; the container's KG_SUBJECT is /repo/subjects/cargo_quote; the host-run server's Neo4j defaults reach the stack's bolt://localhost:7687.
Not run here (no macOS, no Claude Desktop): the Desktop recipe, the config and log paths (macOS and Windows taken from modelcontextprotocol.io 'Connect to local MCP servers', 2026-11-04), the missing Developer section, the permission prompt, the phone route through Remote Control, and docker compose exec from Desktop with the full docker path.
Scenario switch: the server opens the store per call today (task-0097 would hold one handle), and as_of is fixed per process (task-0100); the README says restart after switching, worded so it stays true once task-0097 lands.
Guard: EXTERNAL_FLAGS pins the flags of claude, docker compose and curl as their --help prints them; the repository's scripts are checked live through their --help.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
instance/README.md's assistant section now answers the eight connection pitfalls: KG_SUBJECT is a path to the subject root; scenario in every call and a restart after switching; Claude Code with -s user and 'replace /path/to/knowgov with your absolute path'; a Claude Desktop recipe (macOS and Windows config paths, absolute paths and the full docker path, merge into the existing file, quit and reopen, no Developer section in some builds, the permission prompt, Chat not a cloud Code session, the log); the stdio route because compose does not publish 8765, with -p and -e KG_SUBJECT variants; the phone through Remote Control, never a public endpoint; an HTTP run and a stateless curl example carrying clientCapabilities; example prompts. tests/test_mcp_server.py runs the curl example as printed against the server (and -32602 without clientCapabilities), guards every flag the section names (scripts live through --help, external tools pinned), and holds each pitfall's phrase. Both suites 332/332. The Desktop and phone steps were not run here (no macOS).
<!-- SECTION:FINAL_SUMMARY:END -->
