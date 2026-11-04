---
id: TASK-0117
title: >-
  Adopter docs: connecting Claude Desktop and Claude Code to the knowgov MCP
  server
status: To Do
assignee: []
created_date: '2026-11-04T15:07:00Z'
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
- [ ] #1 Each of the eight pitfalls in the findings' §2.5 is answered in the README or stated as a limit
- [ ] #2 The stateless example carries clientCapabilities and a test runs it against the server
- [ ] #3 Every command flag the section names exists (a docs-flags style guard, added if none covers this README)
<!-- AC:END -->
