---
id: TASK-0175
title: >-
  A reader recovers from an abandoned Neo4j publication (doc-0028 section 10 K3,
  T-a)
status: To Do
assignee: []
created_date: '2026-11-06T13:27:00Z'
labels:
  - store
  - security
dependencies: []
priority: medium
type: task
ordinal: 176000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
A Neo4j writer killed between raising the publication counter and committing leaves the counter raised. Every read then waits up to `KG_NEO4J_READ_WAIT` and refuses, until the next writer takes the lease (0.8.0 Known limits; decision-0014; named in task-0159's description, with no task of its own). A reader that finds the counter raised and the lease expired should not refuse indefinitely on a store whose last generation is whole. It should clear the stale begin under the sequence lock, or report which writer abandoned it, and then answer from the last committed generation. Drafted by the v1.0 session (task-0173), minted under doc-0029.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A writer killed between raising the counter and committing (tools/check_snapshots.py, a new SNAP case) leaves reads answering from the last committed generation once the lease has expired, with no new writer started
- [ ] #2 While the lease is live, reads behave as now: wait, then refuse
- [ ] #3 The clearing takes the sequence lock and cannot race a writer that takes the lease at the same moment; a test holds both orders
- [ ] #4 The Known limit is removed from Unreleased's list with its CHANGELOG line, and docs/security.md says what a reader now does
<!-- AC:END -->
