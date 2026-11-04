---
id: TASK-0094
title: Per-file digests for a directory artefact's Version
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T07:29:00Z'
updated_date: '2026-11-04T08:15:00Z'
labels:
  - register
  - store
milestone: m-6
dependencies:
  - TASK-0088
priority: low
ordinal: 97000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by task-0088: a directory artefact's Version carries one digest for the whole bundle, so register-cites can only count a cited file's fragments, never compare its bytes with the register's digest.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The load records a digest per file of a directory artefact, in both adapters and across export/import_turtle
- [x] #2 register-cites compares a J-F part's digest with the register's; check_saved_queries pins the result
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Port: record_part_digests(vid, parts) and part_digests(); part_sha256 on the Version as "<sha256>  <rel>" by path (store.part_list/part_rows), both adapters.
2. load.py: a key ending in / records each bundle part's sha256 after upsert_artefact_version.
3. check_round_trip: compare part_digests row for row; --expect-parts in harness.yml and demo.yml for J-F.
4. register-cites: a directory part compared by its digest from part_sha256 with the register's at the tag.
5. check_saved_queries: fail an uncompared loaded citation; summary counts same/differ; demo.yml pins 14 same as tag, 0 differ on J-F C.
6. Tests: tests/test_part_digests.py, the task-0088 test updated.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Local proof. rdflib: comparator 0 differing leaves on CargoQuote (7) and J-F (6); J-F round trip rdflib,rdflib --expect-parts on C, D3: 47 file digests equal. Neo4j 5.26 community (Java 21): comparator 0 differing on both subjects; round trip neo4j,rdflib,neo4j (C, D3) and rdflib,neo4j,rdflib (C) equal; check_saved_queries on J-F C after the projection: 15 documents, 1 file artefacts, 13 files of a directory artefact, 1 the subject does not load; 14 same as tag, 0 differ; on D1 uml/sync_run.puml reads differs (the diagram plant). Tests 292/292 plain and under jef_data_load after merging main. PR #163: tests, rdflib, stack green on the first head. Contract change: two new port methods (decision-0003); CHANGELOG left to the release PR. The part digest is of the bundled part, which adds a newline to a file lacking one; every J-F file matches the register today.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
A directory artefact's Version now keeps each file's sha256 in part_sha256, written through the new port methods record_part_digests/part_digests in both adapters and carried by export_turtle/import_turtle. tools/check_round_trip.py compares them (--expect-parts for J-F in both workflows). register-cites compares a cited file of contracts/, contracts/dmn/ or uml/ with the register's digest at the tag instead of counting fragments; check_saved_queries pins 14 same as tag, 0 differ on J-F C in the stack job. Deterministic record unchanged (0 differing leaves, both stores). Follow-up candidate: hash a part's raw bytes rather than the bundled text.
<!-- SECTION:FINAL_SUMMARY:END -->
