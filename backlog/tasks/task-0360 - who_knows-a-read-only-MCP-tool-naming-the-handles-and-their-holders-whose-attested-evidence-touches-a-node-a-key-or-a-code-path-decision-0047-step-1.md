---
id: TASK-0360
title: >-
  who_knows: a read-only MCP tool naming the handles, and their holders, whose
  attested evidence touches a node, a key or a code path (decision-0047 step 1)
status: To Do
assignee: []
created_date: '2026-11-16T19:16:00Z'
labels:
  - contract
  - 0.10.0
  - mcp
dependencies: []
references:
  - backlog/decisions/decision-0047
priority: high
ordinal: 350000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0047 point 2. knowgov holds who said what under a handle (captures, reviews, declared-gap closes) and, after ieam-register decision 0021, who holds each handle; nothing lets a reader ask who knows about a register node, a key or a code path. Ships in 0.10.0 (decision-0047 point 4, the maintainer's option (A)). Never a score or ranking, never across registers (point 6).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 who_knows takes exactly one of a register node id, a key, or a code path under code_map.toml's root, and refuses anything else with -32602
- [ ] #2 Its answer lists, per handle, unit, roles, holder (the register's person, or null with why) and evidence items of kinds answered, approved/rejected, closed and owns, sorted by kind, key and date, handles by id, with no rank, weight or score
- [ ] #3 It reads the reader's subjects and their one register from files, so the report is equal on the Neo4j and rdflib stacks and over stdio and HTTP; schema who-knows; check_mcp_server.py holds it
- [ ] #4 CHANGELOG Unreleased carries it under its contract-change heading; the adopter docs say an organisation serves holders only under its recorded basis (ieam-register 0021 §4)
<!-- AC:END -->
