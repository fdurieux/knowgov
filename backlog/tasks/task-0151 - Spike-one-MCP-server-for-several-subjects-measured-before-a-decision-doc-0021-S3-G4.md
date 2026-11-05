---
id: TASK-0151
title: >-
  Spike: one MCP server for several subjects, measured before a decision
  (doc-0021 S3, G4)
status: To Do
assignee: []
created_date: '2026-11-05T21:46:00Z'
labels: []
dependencies:
  - TASK-0146
  - TASK-0148
priority: low
type: spike
ordinal: 158000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Both MCP servers answer for one subject per process (doc-0021 G4, doc-0018 F6), so every new subject means re-registering two servers in every client. Three designs: (a) a child process per call, the page's pattern; (b) a lazy pool, one child per subject; (c) the subject as a value through the harness. The maintainer (2026-11-05): measure first; decide under a decision record; build (doc-0021 B7) only after knowgov 0.7.0, so the reader is not changed under task-0141's H1 and H2.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Latency per call on rdflib and Neo4j for cargo_quote, lines touched and tests moved, for (a), (b) and (c), measured on a spike branch that is never merged
- [ ] #2 A proposed decision through the CLI: subject resolved by id under KG_SUBJECTS, never a path, defaulting to KG_SUBJECT so today's clients see no change; (a) if it measures under 1 s per call on Neo4j for CargoQuote, else (c)
- [ ] #3 A dated note (a backlog doc) with the numbers; B7 proposed as a task, built only after 0.7.0
<!-- AC:END -->
