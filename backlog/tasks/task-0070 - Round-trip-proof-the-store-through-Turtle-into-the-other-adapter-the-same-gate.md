---
id: TASK-0070
title: >-
  Round-trip proof: the store through Turtle into the other adapter, the same
  gate
status: To Do
assignee: []
created_date: '2026-11-03T23:53:00Z'
labels:
  - store
milestone: m-8
dependencies:
  - TASK-0056
references:
  - backlog/docs/doc-0013
priority: low
ordinal: 74000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0013 P4. Portability is asked of every platform, knowgov included; the rdflib store already writes Turtle. The proof is the exit argument for a buyer.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A test loads a scenario, serialises the store, reloads it into a fresh store of the other kind and compares gate reports and three-valued answers for every scenario of both subjects
- [ ] #2 The Neo4j direction runs in the stack job
- [ ] #3 Any port method added is named as a contract change under decision-0003
<!-- AC:END -->
