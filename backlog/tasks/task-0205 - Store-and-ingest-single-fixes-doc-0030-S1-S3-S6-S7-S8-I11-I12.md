---
id: TASK-0205
title: Store and ingest single fixes (doc-0030 S1, S3, S6, S7, S8, I11, I12)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-07T07:15:00Z'
updated_date: '2026-11-08T16:42:00Z'
labels:
  - review
  - store
  - load
dependencies: []
priority: medium
type: bug
ordinal: 205000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer accepted doc-0030's advice on 2026-11-07 ("accept the advise on all four"): the hardening tranche before 0.9.0's cut, in the order F7; F1 with the check_instance guard, H7 and M3; F3, F4 and F2; F5 and F8. The ids below are doc-0030's (the code review at 8d80b2b); each finding there quotes its lines and its probe.

S1: an artefact with a mapper and store = false still loads its statements, without a Version. S3: every rdflib publish forces the file to 0644 (store_rdflib.py:265), undoing an operator's chmod 600. S6: the load-memory preflight counts first loads only. S7: a writer that wrote nothing still publishes. S8: invalidated_at means two things. I11: a duplicate short and a duplicated fragment locator are not refused. I12: preload compares a raw-byte digest with a text digest, and a line-1 citation after a BOM is missed. Fixes.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A store = false artefact's statements are not loaded (or the pair is refused by check_subject), and the counts match the nodes
- [x] #2 A publish keeps the existing file's mode; the preflight counts stage-2 loads; a writer that wrote nothing publishes nothing, on both adapters; invalidated_at has one meaning
- [x] #3 check_subject refuses a duplicate short and a duplicated fragment locator, and a document's parse error names the document
- [x] #4 preload compares raw-byte digests, so an unchanged CRLF document reads checked; citation parsing strips a leading BOM
- [x] #5 The scored record (S1 to S7), the deterministic run and the comparator stay equal
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. S1: the load, the pristine values and the execution map read the stored artefacts' bags only (load.stored_bags); statements_of counts what a load writes.
2. S3: an rdflib publication keeps the store file's mode (0644 for a first one).
3. S7: a dirty flag gates publish on both adapters: rdflib's mutating primitives set it (an unchanged property is not a write); Neo4j's run() sets it on a write statement (store_neo4j.WRITES) or a pending wipe, and a unit that only read is rolled back.
4. S8: invalidated_at is the change's ISO instant on both adapters, passed by the caller (change.py and gate_cli's register change, load.now()); the port's invalidate_stale/invalidate_keys take at.
5. S6: load_memory.preflight takes a stage-2 load as an addition to its scenario's graph; change.unit_loads lists each scenario's loads; run.py and the sizing use it.
6. I11: check_subject refuses a duplicate short and a duplicated fragment locator (rule duplicate, no schema change); extract_all raises DocumentUnreadable naming the document; the load refuses one short naming two artefacts; gate_cli reports a document it cannot load as the document's fault.
7. I12: preload.verdicts compares the subject's raw-byte version digest; citation.parse strips a leading BOM.
8. Tests (tests/test_store_singles.py, each failing on main first); SNAP-09 in tools/check_snapshots.py on both stores; record, comparator, round trips, snapshots, stage 2, load memory.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Evidence (merged head with main 1aca85f, pumllint 0.35.0, KG_CLOCK pinned, no model call):
- tests/test_store_singles.py: 12 tests, all 12 failing on main 21e4668 first, all passing here, under CargoQuote and J-F.
- tools/check_snapshots.py SNAP-09: fails on main's code (rdflib: the writer that only read republished, and chmod 600 went back to 0644; Neo4j: the counter moved), holds here; snapshots every check holds on rdflib and on Neo4j 5.26.
- run_tests: pins 814/815 (1 skipped), J-F pass 813/815 (2 skipped), no yaml 763/815 (52 skipped), 0 failed each.
- Comparator: CargoQuote 0 differing leaves over 7 scenarios on rdflib and on Neo4j; J-F 0 over 6.
- check_round_trip --chain rdflib,rdflib: both subjects, every answer survives; rdflib,neo4j,rdflib on S6 too.
- check_stage2_reload: both subjects on rdflib, CargoQuote on Neo4j; check_saved_queries on Neo4j; tests/test_load_memory.py passes.
- check_subject's subject-check schema is unchanged: both refusals use the rule duplicate.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The seven store and load single fixes of doc-0030, each with a test failing on main first. S1: the load, the pristine values and the execution map read only stored artefacts (load.stored_bags), so a store = false document with a mapper loads nothing and the counts match the nodes. S3: an rdflib publication keeps the file's mode. S6: change.unit_loads gives each scenario's loads, its stage-2 re-load an addition to its graph, for run.py's preflight and load_memory's sizing. S7: a dirty flag gates publish on both adapters (rdflib's mutating primitives; Neo4j's write statements, store_neo4j.WRITES, and a pending wipe); SNAP-09 proves it on both stores. S8: invalidated_at is the change's ISO instant (load.now()) on both adapters, the port's invalidate_stale and invalidate_keys taking at. I11: check_subject refuses a duplicate short and a duplicated row; extract_all raises kitio.DocumentUnreadable naming the document, which the gate reports as the document's fault. I12: preload compares the raw-byte version digest; citation.parse strips a leading BOM. The scored record, the deterministic run and the comparator are unchanged on rdflib and Neo4j.
<!-- SECTION:FINAL_SUMMARY:END -->
