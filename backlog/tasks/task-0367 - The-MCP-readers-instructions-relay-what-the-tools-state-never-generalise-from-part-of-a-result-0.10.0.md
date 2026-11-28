---
id: TASK-0367
title: >-
  The MCP reader's instructions: relay what the tools state, never generalise
  from part of a result (0.10.0)
status: In Progress
assignee: []
created_date: '2026-11-16T20:28:00Z'
updated_date: '2026-11-28T01:01:05Z'
labels:
  - 0.10.0
  - mcp
  - docs
dependencies:
  - TASK-0364
  - TASK-0365
  - TASK-0366
priority: medium
ordinal: 357000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer, 2026-11-16: "yes, add them as 0.10.0 tasks", after a Claude Desktop session over MCP gave a private subject's counts and links loosely: it summarised a report too large to read whole, carried the wrong count forward, and inferred a subject-to-application link no tool states. The reader already sends instructions naming the down and up sequences; they say nothing about how an assistant should use what the tools return.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The server's instructions tell the assistant: quote numbers from the tool's fields and name the tool; never state a count it did not read; when a result is marked partial, re-ask with the summary or a filter; re-query before repeating an earlier claim; prefer subject_overview and gate_verdict's summary as first calls for a large subject
- [ ] #2 The same text is sent on both transports and in both protocol eras; a test holds it
- [ ] #3 The adopter docs give the same rules as a client-side instruction an organisation can paste into its assistant's project
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. mcp_server.READING_RULES: six rules, appended to INSTRUCTIONS before "This server only reads.". The names match what shipped: io.knowgov/clipped and io.knowgov/large (#604), gate_verdict summary and filter (#601), subject_overview and key_nodes (#606).
2. tests/test_reading_rules.py: every rule is in INSTRUCTIONS; the same text goes out over stdio and HTTP, from initialize and from server/discover; the README block has six numbered rules naming the same tools and marks.
3. instance/README.md gains "Telling your assistant how to use the answers", a paste-able text block in plain words.
4. A CHANGELOG line in the plain Unreleased list, since the instructions text is not a contract (the contracts table lists tools and prompts).
<!-- SECTION:PLAN:END -->
