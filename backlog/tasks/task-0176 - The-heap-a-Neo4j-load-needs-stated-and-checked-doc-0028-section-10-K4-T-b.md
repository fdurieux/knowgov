---
id: TASK-0176
title: The heap a Neo4j load needs, stated and checked (doc-0028 section 10 K4, T-b)
status: To Do
assignee: []
created_date: '2026-11-06T13:27:00Z'
labels:
  - store
  - instance
dependencies: []
priority: medium
type: task
ordinal: 177000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The server's transaction memory bounds a Neo4j load. On the public subjects the peaks were about 41 MiB for CargoQuote and 64 MiB for J-F, against 70% of the compose file's 1 GiB heap (0.8.0 Known limits). An instance's load is larger, and today it fails inside the transaction, keeping the previous generation, with no forecast and no sizing guidance. The task measures peak transaction memory against statement count, states the heap an instance needs, and refuses up front a load predicted to exceed the configured limit. Drafted by the v1.0 session (task-0173), minted under doc-0029.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Peak transaction memory is measured against statement count on both public subjects and a synthetic scale-up, and the relation is recorded with its data
- [ ] #2 instance/README.md states the heap and db.memory.transaction.total.max an instance needs, as a function of its statement count
- [ ] #3 A load whose predicted peak exceeds the configured transaction memory refuses before it starts (exit 2, naming the setting and both figures), and keeps the previous generation; a test holds it
- [ ] #4 The Known limit names the new check; no record result moves
<!-- AC:END -->
