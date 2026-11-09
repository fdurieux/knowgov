---
id: TASK-0274
title: >-
  Neo4j: a generation is never visible before its data (SNAP-04, decision-0014
  A1)
status: Done
assignee: []
created_date: '2026-11-09T10:09:00Z'
updated_date: '2026-11-09T11:08:00Z'
labels:
  - store
  - correctness
  - validation
dependencies: []
references:
  - backlog/decisions/decision-0033
  - task-0256
priority: high
ordinal: 267000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
On #401's stack run, SNAP-04 read a state that is no committed generation: S2's counts, with `held`, `register` and `verdict` null.

The cause: Neo4j applies a committing transaction to lock-free, read-committed readers one record at a time. The publication's `end`, written inside the unit's transaction (decision-0014's step 3), could be visible before the unit's last records. A reader that pinned in that window read a half-applied unit, and later checks passed because the pair never moved again.

decision-0014 Amendment A1, accepted 2026-11-09 ("accept A1"), sets `end` after the unit's commit, in its own transaction, and closes every gap forward. The fix is built in #415. It is fix-only under decision-0032: no report, schema, port or setting changes.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `store_neo4j`'s publish raises `begin`, fences in the unit (the epoch checked under the node's lock, held to the commit), commits, then sets `end = begin` in its own transaction.
- [x] #2 Every gap closes forward: the writer's failure path, a reader's recovery of an abandoned publication, and a takeover. No backward close can reuse a pinned generation number.
- [x] #3 A new race check, holding a writer between commit and `end` and racing publications under several readers, fails on the old code and passes on the fix. `check_snapshots --disposable` holds every check on Neo4j and on rdflib.
- [x] #4 `tests/test_store_generations.py` holds the publish order, the forward close and the absence of a backward close.
- [x] #5 The record does not move.
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Built in #415 (decision-0014 amendment A1, accepted 2026-11-09). `store_neo4j` `_Unit.publish` now raises `begin` in its own transaction, fences in the unit (`owned(tx)` under the node's lock, held to the commit), commits, then sets `end = begin` in its own transaction (`committed()`). Every gap closes forward: the writer's failure path (`abandon`), a reader's `recover` and a takeover; no backward close remains, so no pinned generation number is reused.

Verification:
- SNAP-11 in `tools/check_snapshots.py`: a writer held between commit and `end` is refused with the data in, then read whole; one killed there is refused while its lease is live, then closed forward and read whole; 24 publications under six readers, every read whole. On main's code every such batch read partials (11 to 21).
- `check_snapshots --disposable` exits 0 on Neo4j 5.26 and on rdflib after merging main.
- `tests/test_store_generations.py` holds the order, the forward close and the absence of a backward close.
- The record does not move: the deterministic run on Neo4j against the comparator shows 0 differing leaves over seven scenarios.
- `tools/complexity.py --check` holds.

It is fix-only under decision-0032: no report, schema, port or setting changes. Residual risk: a writer killed between its commit and `end` leaves readers waiting one lease (bounded).
<!-- SECTION:FINAL_SUMMARY:END -->
