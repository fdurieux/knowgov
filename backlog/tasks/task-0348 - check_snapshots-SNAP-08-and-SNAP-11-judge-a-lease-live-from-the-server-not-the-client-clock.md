---
id: TASK-0348
title: >-
  check_snapshots: SNAP-08 and SNAP-11 judge a lease live from the server, not
  the client clock
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-15T17:24:00Z'
updated_date: '2026-11-15T18:09:00Z'
labels:
  - neo4j
  - probe
  - tools
dependencies: []
references:
  - backlog/tasks/task-0345
priority: medium
ordinal: 340000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer ran tools/check_snapshots.py --disposable against Neo4j Desktop 2026.10.2 enterprise through a reverse SSH tunnel (task-0345). One line failed: SNAP-08 'while the lease is live a read waits 1.1 s, then refuses (StoreBusy)'. The read was refused with 'live lease' after 1.1 s, so the store was right; the check's own condition 'live = time.monotonic() - t0 < LEASE_08' failed, because over the tunnel the client-side round trips since t0 (taken after the writer process died) exceeded the 4 s lease. The server holds the lease on its own clock (datetime()), so the check must decide 'live' from the server's evidence, not the client's.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 SNAP-08's live-lease read check decides 'live' from the server's lease (the refusal's 'live lease' and the publication node's lease fields), not from the client clock; the read's own wait assertion (took >= wait*0.9) is kept
- [ ] #2 Every other check in tools/check_snapshots.py that infers a lease's or a wait's state from time.monotonic() against a lease constant (e.g. SNAP-11's killed-writer read, the sleeps until a lease runs out) is fixed the same way or noted as safe, with why
- [ ] #3 The check still fails when the behaviour is wrong: shown by a deliberate local mutation (a read that answers, and a read refused after the lease expired), not committed, then reverted
- [ ] #4 tools/check_snapshots.py --disposable passes on a local Neo4j 5.26 Community tarball (Java 21) and on rdflib
- [ ] #5 No contract moves: no store, harness, schema, exit code or KG_* change; a CHANGELOG Unreleased line for the check's behaviour
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Server-side lease evidence in SNAP-08 (refusal names the node's epoch's live lease). 2. _await_lease_end polls the server's datetime() in place of every client-clock sleep against LEASE_08 (SNAP-03, 05, 08, 11). 3. Prove: slow-link simulation, mutation, both stores, suite.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Audit: client-clock inference of 'live' existed only in SNAP-08's `live = monotonic() - t0 < LEASE_08`. The sleeps in SNAP-03 (3.5 s), SNAP-05 (2.5 s), SNAP-08 x3 and SNAP-11 (LEASE_08+0.5-elapsed) err long under latency, so were safe, but now all poll the server's own expiry. SNAP-03/SNAP-11 'a read is refused while the lease is live' read at once with KG_NEO4J_READ_WAIT=0 right after a kill; they assert StoreBusy only, no client timing, safe. Slow-link simulation (scratch only): _Unit.state's answer delayed 3.8 s after the server answered; the old check fails exactly the reported line, the new passes. Mutation A (pin answers instead of refusing) and B (refusal names the wrong epoch) each fail SNAP-08's live line; reverted.
<!-- SECTION:NOTES:END -->
