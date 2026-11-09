---
id: TASK-0247
title: >-
  SOLID refactoring after 1.0: narrow store-consumer protocols, an explicit
  validated context in place of the import-time globals, MCP transport apart
  from its use cases, the three complexity hotspots (parked)
status: To Do
assignee: []
created_date: '2026-11-09T06:59:00Z'
labels:
  - refactoring
  - architecture
milestone: m-4
dependencies: []
priority: low
ordinal: 241000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From the third-party code review at 4c7fcb0, re-verified at main 6d27961 (doc-0033). Store declares 91 methods and consumers use small subsets; SUBJECT and TASKS are built at import and 48 modules import subject; harness/mcp_server.py (1,498 lines) carries tools, dispatch, both protocol eras and both transports; review.check, proposal_impact's main function and preload_check run at cognitive complexity 148, 127 and 111. None caused R1 to R4, and decision-0016 makes the contracts stable from 0.9.0, so the refactors wait until after 1.0 (doc-0033 advice 2); before then, only the refactor a fix needs (task-0242's validator). The store port's method set is a 1.0 contract and does not shrink: narrow protocols are views a consumer is held to, by an AST guard as the Cypher guard is; the context object respects decision-0013's process per other subject.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A decision with the four parts chooses the order and the scope after 1.0
- [ ] #2 Each refactor keeps the comparator, the round trip and the adapter parity tests equal, with characterisation tests in front of each hotspot
<!-- AC:END -->
