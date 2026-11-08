---
id: TASK-0229
title: A Neo4j writer's close joins its lease heartbeat before the driver closes
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-08T18:23:00Z'
updated_date: '2026-11-08T18:23:00Z'
labels:
  - store
  - neo4j
dependencies: []
priority: high
type: bug
ordinal: 228000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
main's stack job at c29cd3f (job 128803089628, step 30, the J-F chain neo4j,rdflib,neo4j) failed at close(): the neo4j driver's Driver.close() raised BufferError: Existing exports of data: object cannot be re-sized, in the GOODBYE's _chunk_data. Cause (ours, since task-0141.06): Neo4jStore.close() stopped the writer's lease heartbeat without joining its thread, then closed the driver, whose pool closes every connection, in-use ones included; a beat in the middle of a send (its outbox exported by sendall) then met the GOODBYE appended to the same outbox. Reproduced on Neo4j 5.26 with driver 6.4.1 at cb2707c and d09bc19 (5 of 10 closes mid-send). Not task-0205's S7: check_round_trip never commits a Neo4j handle.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 release() stops the heartbeat and joins its thread before it clears the lease and before close() closes the driver
- [ ] #2 The join is bounded by the beat's own bounds (the driver's retry time and connection timeout); past it close() raises HeartbeatAlive, a named error that is not a StoreBusy, closes the session and leaves the driver open; close() swallows nothing
- [ ] #3 tests/test_neo4j_heartbeat.py and tools/check_snapshots.py SNAP-10 (on both stores; on Neo4j ten closes in the middle of a beat's send) fail on main first and hold here
- [ ] #4 No pin changes; the snapshots, the round-trip chain on Neo4j and the suites hold
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. _Unit keeps its heartbeat Thread; release() sets beat_stop and joins it within join_s (RETRY_S + the connection timeout + 5 s), else raises HeartbeatAlive (a RuntimeError, never a StoreBusy).
2. Neo4jStore.close(): drop, then release in a finally; HeartbeatAlive closes the session and leaves the driver open; any other failure closes both and propagates.
3. tests/test_neo4j_heartbeat.py on a fake driver; tools/check_snapshots.py SNAP-10 on both stores; the names SNAP-01 to SNAP-10 as SNAP-09 did.
4. Proof: each new test fails on main first; the snapshots on both stores; the round-trip chain on Neo4j once; the suites.
<!-- SECTION:PLAN:END -->
