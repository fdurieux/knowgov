---
id: TASK-0175
title: >-
  A reader recovers from an abandoned Neo4j publication (doc-0028 section 10 K3,
  T-a)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-06T13:27:00Z'
updated_date: '2026-11-06T14:03:00Z'
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
- [x] #1 A writer killed between raising the counter and committing (tools/check_snapshots.py, a new SNAP case) leaves reads answering from the last committed generation once the lease has expired, with no new writer started
- [x] #2 While the lease is live, reads behave as now: wait, then refuse
- [x] #3 The clearing takes the sequence lock and cannot race a writer that takes the lease at the same moment; a test holds both orders
- [x] #4 The Known limit is removed from Unreleased's list with its CHANGELOG line, and docs/security.md says what a reader now does
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/store_neo4j.py _Unit: state() reads the counter's pair with the owner and whether its lease ran out. recover() runs in one managed write transaction: it takes the publication node's write lock (lock_seq) first, then acts only while begin > end and no live lease holds the node. It puts the counter back at the last committed generation (begin = end), frees the lease, moves the epoch past the abandoning writer and records it (abandoned_owner, abandoned_epoch, abandoned_begin, recovered_at).
2. pin(): a raised counter under a free or expired lease calls recover() and re-reads. If the role may not write, it refuses, naming the writer's epoch. Under a live lease it waits KG_NEO4J_READ_WAIT and refuses, as now.
3. tools/check_snapshots.py SNAP-08: a writer killed between raise and commit. Lease live: a read waits, then refuses, and clears nothing. Lease expired: a read answers the last committed generation with no new writer. Then the two orders: a reader first then a writer (the next publish), and a writer first, after which the reader's clearing finds nothing. Then a race of four readers and a writer. On rdflib, the killed replace leaves the last generation readable. SNAP-03's interrupted read is checked at once, while the lease is live.
4. A stdlib test of the lock order and guards; docs/security.md; CHANGELOG under Unreleased › Changes; the workflow step names and CLAUDE.md say SNAP-01..08.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-06 evidence, all local and with no model call. Neo4j 5.26 Community was a tarball started directly; rdflib used a temporary file; the clock was pinned.
- AC #1, SNAP-08 on Neo4j. A child writer loads S2 and dies in _on_publish, between raising the counter and committing (begin 261, end 260, its lease 4 s). Once the lease has run out, read_now() with no writer opened answers g1, the last committed generation. The reader's recovered record names the abandoning owner and epoch 386. The node then has begin = end = 260, a null owner, epoch 387, and abandoned_epoch 386. The next writer then takes the free lease and publishes.
- AC #1, SNAP-08 on rdflib. A writer killed in its atomic replace leaves the last generation, and it is read with no new writer.
- AC #2. With KG_NEO4J_READ_WAIT=1 inside the live lease, the read waited 1.0 s and then refused with StoreBusy ('in flight ... under writer epoch N's live lease'), and nothing was cleared. SNAP-03's interrupted read is now checked at once, while the lease is live (KG_NEO4J_READ_WAIT=0); without that, its 10 s default outlasts the dead writer's 3 s lease and a reader now clears it.
- AC #3. recover() takes the node's write lock (lock_seq), as acquire() and owned() do, before reading its guard: begin <> end and no live lease. SNAP-08 holds both orders:
  - reader first: it clears, then the next writer publishes;
  - writer first: acquire closes the gap itself, a reader's recover() then returns None and the writer keeps its lease and publishes;
  - a race of four readers and a writer from a barrier: exactly one reader cleared it, every read answered g1, and the end state is one generation with a free lease.
  tests/test_store_generations.py holds the lock order, the guard, what is set, and pin's branch order.
- AC #4. Unreleased has no Known limits list; the limit is in the released 0.8.0 section, left as released. Unreleased › Changes carries the line, saying 0.8.0's known limit is lifted. docs/security.md has a new 'An abandoned publication' item, and its table row names SNAP-01 to SNAP-08.
- Held: tools/check_snapshots.py --disposable reports 'every check holds' on Neo4j (SNAP-01..08; SNAP-07's round trip left to its steps, as in CI) and on rdflib (SNAP-01..08 with the round trip).
- Suites, all 0 failed: stdlib 623/646, J-F 622/646, pins with KG_TEST_REQUIRE=rdflib,node 645/646.
- store_neo4j.publication() reads the node without a pin, for SNAP-08. tests/test_security.py keeps the driver import in store_neo4j.py.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
A reader now recovers from an abandoned Neo4j publication. When it finds the counter raised and the writer's lease run out, it clears the stale begin in one transaction under the sequence lock: the counter goes back to the last committed generation, the lease is freed, the epoch moves past the dead writer so it can never commit, and the writer is recorded on the node. The reader then answers from that generation with no new writer. A role that may not write gets a refusal naming the writer's epoch. Under a live lease, reads wait and refuse as before. A writer that takes the lease first closes the gap itself, so the two never both act. SNAP-08 proves this on Neo4j and rdflib, with both orders and a race, and SNAP-01..07 still hold on both. docs/security.md, CHANGELOG (Unreleased › Changes), the workflow step names and CLAUDE.md are updated.
<!-- SECTION:FINAL_SUMMARY:END -->
