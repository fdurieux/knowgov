---
id: TASK-0176
title: The heap a Neo4j load needs, stated and checked (doc-0028 section 10 K4, T-b)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-06T13:27:00Z'
updated_date: '2026-11-06T15:18:00Z'
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
- [x] #1 Peak transaction memory is measured against statement count on both public subjects and a synthetic scale-up, and the relation is recorded with its data
- [x] #2 instance/README.md states the heap and db.memory.transaction.total.max an instance needs, as a function of its statement count
- [x] #3 A load whose predicted peak exceeds the configured transaction memory refuses before it starts (exit 2, naming the setting and both figures), and keeps the previous generation; a test holds it
- [x] #4 The Known limit names the new check; no record result moves
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Measure. tools/measure_load_memory.py --disposable samples SHOW TRANSACTIONS estimatedUsedHeapMemory every 20 ms during each unit. It covers each scenario's gate_cli load, the whole deterministic run in one unit, and a synthetic scale-up (the first kit x1..x32), each followed by an x1 unit so that written and deleted vary apart. Both public subjects, on Neo4j 5.26 Community. The rows and the least-squares plane go in docs/load-memory.json.
2. Model (harness/load_memory.py). Peak = BASE + PER_WRITTEN x written + PER_DELETED x deleted. Statements are assertions plus fragments: written counted from the extraction before the first write, deleted by the unit's wipes (the first deletes the published generation). The intercept is raised so that every measured peak lies under the plane, then multiplied by 1 + KG_LOAD_MEMORY_MARGIN (default 0.25, bounded in store.SETTINGS).
3. Limit. The port's transaction_memory(): Neo4j reads the smallest set of db.memory.transaction.max, db.memory.transaction.total.max and dbms.memory.transaction.total.max with SHOW SETTINGS, plus the published statements, outside the unit; rdflib and the base port return None.
4. Refusal. load_scenario notes its statements before its first write and raises LoadTooLarge; Neo4jStore.wipe calls wiped(). gate_cli maps it to CannotRun (exit 2). run.py runs preflight over every scenario before its first load and its first model call, and exits 2. KG_LOAD_MEMORY_CHECK=off loads anyway.
5. Proof and docs. check_snapshots --memory-limited, on a server with db.memory.transaction.max=2m: the refusal names the setting and both figures, gate_cli exits 2, and the generation is kept; with the check off, the in-transaction failure as before. Stdlib tests. instance/README.md 'Sizing the Neo4j heap'. docs/security.md. CHANGELOG under Unreleased › Contract changes, with the known limit. No record result moves: the deterministic record on rdflib and Neo4j against the comparator.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-06 evidence, all local (Neo4j 5.26.0 Community tarball, Java 21, disposable; neo4j driver 6.4.1; no model call; the clock pinned).
- AC #1. tools/measure_load_memory.py --disposable, once per public subject, gives 41 rows in docs/load-memory.json. The peak is SHOW TRANSACTIONS estimatedUsedHeapMemory sampled every 20 ms; statements are assertions plus fragments, written over the unit and deleted by its wipes.
  - CargoQuote gate loads: 4-10 MiB at about 230 written.
  - J-F gate loads: 26-52 MiB at about 1,500.
  - Whole runs: 17 MiB (CQ, 1,633 written and 1,633 deleted) and 98 MiB (J-F, 9,049 and 9,049).
  - Synthetic: up to 48,288 written, 467.7 MiB, and 48,288 deleted, 469.7 MiB.
  - Plane: 9,583 B per statement written, 9,610 per statement deleted, base 4.3 MiB, r² 0.984. Raised to cover every row: base 24.4 MiB.
  - Earlier figures (41 and 64 MiB) were whole runs measured after other loads; the deletion term explains them.
- AC #2. instance/README.md 'Sizing the Neo4j heap' gives the formula, the gate-load rule (30.5 MiB + 23.4 KiB per statement), the three settings with their defaults, heap = need / 0.7, a table at 1.5k, 10k, 50k and 100k statements, and python harness/load_memory.py (CQ needs 67.8 MiB, heap 97 MiB; J-F needs 237.5 MiB, heap 339 MiB). The correct name of the 70%-of-heap default is dbms.memory.transaction.total.max, not db.*; docs/security.md is corrected.
- AC #3. On a server restarted with db.memory.transaction.max=2m, tools/check_snapshots.py --memory-limited:
  - the writer reads the limit {2 MiB, db.memory.transaction.max};
  - a load forecast at 35.8 MiB raises LoadTooLarge before its first write, naming the setting, both figures and KG_LOAD_MEMORY_CHECK=off;
  - gate_cli exits 2 with 'refused before loading';
  - the published S1 is read whole after each refusal;
  - with the check off, MemoryPoolOutOfMemoryError inside the transaction, S1 whole and the sequence lock closed.
  run.py --deterministic exited 2 up front ('the run's 7 loads in one unit', 67.8 MiB) and wrote nothing. tests/test_load_memory.py (stdlib) holds the refusal before any write, the off switch, no limit, the margin's bounds, the unit's counts, the run preflight, gate_cli's mapping and run.py's order.
- AC #4. Unreleased › Contract changes carries the entry, with its Known limit naming the check. No record result moves:
  - CargoQuote on rdflib and on Neo4j: 0 differing leaves over 7 scenarios;
  - J-F on Neo4j: 0 over 6;
  - check_snapshots: every check holds on Neo4j and on rdflib.
- Suites, all 0 failed: stdlib 638/662; J-F 637/662; pins with KG_TEST_REQUIRE=rdflib,node 661/662. A first pinned run had test_http_limits' test_limit_07 fail once while Neo4j loads ran beside it; that test passed 3 of 3 alone and the whole suite passed on the re-run. The advice's escape: KG_LOAD_MEMORY_CHECK=off, and KG_LOAD_MEMORY_MARGIN (0-4, default 0.25) as a bounded setting.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
A Neo4j load whose forecast peak transaction memory exceeds the server's limit is now refused before its first write: LoadTooLarge; gate_cli and run.py exit 2, naming the setting and both figures; the store keeps what it held; run.py checks its whole run before its first load and its first model call. The forecast comes from measurements on both public subjects and a synthetic scale-up to 48k statements (docs/load-memory.json): about 9.4 KiB per statement written or deleted, raised to cover every measured peak, plus a 25% margin. The limit is the smallest set of db.memory.transaction.max, db.memory.transaction.total.max and dbms.memory.transaction.total.max. KG_LOAD_MEMORY_CHECK=off is the escape. instance/README.md states the heap an instance needs as a function of its statement count, and harness/load_memory.py prints a subject's. Proven live on a 2 MiB-limited server; no record result moves. Known limit: measured on Neo4j 5.26 Community, and a multi-scenario run is over-forecast by up to about two times.
<!-- SECTION:FINAL_SUMMARY:END -->
