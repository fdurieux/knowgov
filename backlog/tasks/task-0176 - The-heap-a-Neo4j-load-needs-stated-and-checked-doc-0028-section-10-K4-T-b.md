---
id: TASK-0176
title: The heap a Neo4j load needs, stated and checked (doc-0028 section 10 K4, T-b)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-06T13:27:00Z'
updated_date: '2026-11-06T15:11:00Z'
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

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Measure. tools/measure_load_memory.py --disposable samples SHOW TRANSACTIONS estimatedUsedHeapMemory every 20 ms during each unit. It covers each scenario's gate_cli load, the whole deterministic run in one unit, and a synthetic scale-up (the first kit x1..x32), each followed by an x1 unit so that written and deleted vary apart. Both public subjects, on Neo4j 5.26 Community. The rows and the least-squares plane go in docs/load-memory.json.
2. Model (harness/load_memory.py). Peak = BASE + PER_WRITTEN x written + PER_DELETED x deleted. Statements are assertions plus fragments: written counted from the extraction before the first write, deleted by the unit's wipes (the first deletes the published generation). The intercept is raised so that every measured peak lies under the plane, then multiplied by 1 + KG_LOAD_MEMORY_MARGIN (default 0.25, bounded in store.SETTINGS).
3. Limit. The port's transaction_memory(): Neo4j reads the smallest set of db.memory.transaction.max, db.memory.transaction.total.max and dbms.memory.transaction.total.max with SHOW SETTINGS, plus the published statements, outside the unit; rdflib and the base port return None.
4. Refusal. load_scenario notes its statements before its first write and raises LoadTooLarge; Neo4jStore.wipe calls wiped(). gate_cli maps it to CannotRun (exit 2). run.py runs preflight over every scenario before its first load and its first model call, and exits 2. KG_LOAD_MEMORY_CHECK=off loads anyway.
5. Proof and docs. check_snapshots --memory-limited, on a server with db.memory.transaction.max=2m: the refusal names the setting and both figures, gate_cli exits 2, and the generation is kept; with the check off, the in-transaction failure as before. Stdlib tests. instance/README.md 'Sizing the Neo4j heap'. docs/security.md. CHANGELOG under Unreleased › Contract changes, with the known limit. No record result moves: the deterministic record on rdflib and Neo4j against the comparator.
<!-- SECTION:PLAN:END -->
