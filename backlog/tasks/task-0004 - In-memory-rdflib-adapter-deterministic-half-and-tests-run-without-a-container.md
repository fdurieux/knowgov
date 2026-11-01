---
id: TASK-0004
title: 'In-memory rdflib adapter: deterministic half and tests run without a container'
status: Done
assignee:
  - '@claude'
created_date: '2026-11-01T14:27:00Z'
updated_date: '2026-11-01T15:58:00Z'
labels:
  - platform
  - store
milestone: m-1
dependencies:
  - TASK-0003
priority: low
type: feature
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
shacl.py already builds an RDF projection with rdflib from Cypher reads, and rdflib is in the image. A second adapter proves the port is real and removes the Neo4j container from unit tests and from a first replay-plus-deterministic start. The Neo4j Browser link and saved Cypher stay a Neo4j-adapter feature.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The rdflib adapter passes the deterministic comparator on CargoQuote
- [x] #2 Unit tests run with no Neo4j service; the container is needed for the Neo4j adapter's own tests only
- [x] #3 The page says which adapter is active and hides the Browser link when it is not Neo4j
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/store_rdflib.py: the second adapter, an rdflib Graph as the storage with a small property-graph layer (nodes with labels and properties, edges as reified nodes so edge properties fit), insertion order kept as a property so answers come out in the order Neo4j gives when Cypher has no ORDER BY; every port operation implemented over it; optional persistence to a Turtle file (KG_RDFLIB_FILE) so the page can read what a run left.
2. run.py records the store kind in deterministic.json; the comparator ignores that key and skips D1 (the Neo4j edition's constraint measurement) when the run's store differs from the record's, saying so.
3. The page's store card reads the adapter's describe(): name, no Browser link and no saved Cypher when the store is not Neo4j.
4. A CI workflow (harness.yml) with the Python pins and no Neo4j: the deterministic half on the rdflib adapter for S1 to S7, the comparator, and the minimal subject.
5. Proof: comparator green on both adapters; the page served with KG_STORE=rdflib.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Done as planned. store_rdflib.py: an rdflib Graph as the storage, a property-graph layer on it (nodes with labels and properties, edges as reified nodes so edge properties fit, insertion order as a sequence property), all 55 port operations; KG_RDFLIB_FILE persists the graph as Turtle so the page can read what a run left (the page sets it to runs/store.ttl under KG_STORE=rdflib). The first full run reproduced the record on all seven scenarios. Two comparator changes, both stated in its docstring: lists of scalars compare as sets (Cypher's collect() answers in store order, and the record's 'reverified' list is in Neo4j's order, not creation order), and D1, the Neo4j edition's constraint measurement, is compared only between runs of the same store kind (a run records its store; the comparator says D1 was skipped). The Neo4j adapter stays at 0 differing leaves with the changed comparator. Proof: 55/55 tests (both adapters implement every port operation; the rdflib adapter speaks no Cypher; the comparator's store rule under test); KG_STORE=rdflib deterministic S1 to S7, 0 differing leaves over 7 scenarios, D1 skipped; the page served on rdflib: store card names the adapter and hides the Browser link and the saved Cypher, S4 deterministic through the page identical to the record on 113 leaves, the page then reads the persisted store (587 nodes, 1455 relationships), the gaps API matches, the register projection lands in rdflib (179 relationships at v0.1.1). harness.yml runs S1 to S7 on rdflib and the minimal subject in CI with no Neo4j.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The port has a second implementation: store_rdflib.py, an rdflib graph in memory with optional Turtle persistence, implementing every port operation. The deterministic half for S1 to S7 reproduces the record on it with 0 differing leaves, D1 aside, which the comparator now skips across store kinds and says so; lists of scalars compare as sets. The page names the adapter in its store card and shows the Browser link and saved Cypher only for Neo4j; under KG_STORE=rdflib a run through the page persists its store so the page can read it. CI gains harness.yml: the deterministic half and the minimal subject on rdflib with no database container; the stack job remains the Neo4j adapter's proof. Verification: 55/55 tests; both adapters green on the comparator; the page served on rdflib through a run, the gaps and the projection.
<!-- SECTION:FINAL_SUMMARY:END -->
