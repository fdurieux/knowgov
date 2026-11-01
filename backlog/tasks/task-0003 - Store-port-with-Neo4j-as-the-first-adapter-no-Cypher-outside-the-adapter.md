---
id: TASK-0003
title: 'Store port with Neo4j as the first adapter: no Cypher outside the adapter'
status: Done
assignee:
  - '@claude'
created_date: '2026-11-01T14:27:00Z'
updated_date: '2026-11-01T15:40:00Z'
labels:
  - platform
  - store
milestone: m-1
dependencies:
  - TASK-0001
priority: high
type: feature
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
About 210 Cypher sites sit in the loader, the rules, the gate, the runner, the page server and the register projection, and every rule and the gate take a Neo4j session as their argument. The evaluation's section 11 names the conditions under which an RDF or versioned store is preferable; with a port those become configuration. The port is not a generic graph API: it declares the operations the modules use (wipe, constraints, load documents, fragments, entities and assertions with provenance, verifications and approvals, the seven rules' reads and writes, the gate's resolve, the census, the register projection, the page's saved queries). Neo4j keeps the Cypher, the Browser link and the saved queries inside its adapter. Every write carries the instance id so a shared store stays possible later.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A port interface lists every store operation with its arguments and result shape
- [x] #2 Rules, gate, runner, page and projection call port methods and contain no Cypher
- [x] #3 The Neo4j adapter passes the deterministic comparator on CargoQuote with no change in the record
- [x] #4 Constraints Community refuses stay application checks and D1 still reports which were refused
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/store.py: the port, one method per operation the loader, the rules, the gate, the runner, the SHACL projection, the census, the page's store card and the register projection use; open_store() picks the adapter from KG_STORE (neo4j default) and returns a context manager holding one session.
2. harness/store_neo4j.py: the adapter with every Cypher statement, the constraint families, the saved queries for Neo4j Browser; the driver imported lazily so the module loads without it.
3. load, rules, gate, shacl, run call port methods; value compatibility and the gate's level logic stay in Python where they were.
4. The page: server's store card, gaps API and saved-query list through the port and the adapter; register_project keeps rows() pure and loads through the port.
5. Tests: the adapter implements every port operation (AST), no other module speaks Cypher, the port names the adapter and the default; the projection tests read the adapter's source.
6. Proof: comparator green on CargoQuote; the page's CI checks locally including a deterministic run through the page and the projection.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Done as planned. 55 port operations; about 210 Cypher sites now live in store_neo4j.py only. Rules and gate take the store as their argument where they took a session; run.py opens one store per run and the harness wipes it per scenario as before. The instance id is a constructor argument of the port (open_store(instance=SUBJECT.id)) that the adapter carries but does not yet stamp on writes: with one stack per instance (the brief's decision) nothing reads it, and stamping would be untested machinery; recorded here as the hook for a shared store later. The page's generic saved queries moved to the adapter (SAVED_QUERIES) since they are Neo4j Browser text; the subject's stay in queries.toml. Proof: 47/47 tests; deterministic S1 to S7 through the port against Neo4j 5.26.0, comparator 0 differing leaves over 7 scenarios; the page served locally: menu, replay, register, a deterministic S1 through the page identical to the record on 122 leaves, the store's gaps for the loaded scenario (35), the register projection through the port (179 relationships at v0.1.1), 12 saved queries served.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The store is a port (harness/store.py) with Neo4j as its first adapter (harness/store_neo4j.py). The port declares the 55 operations the harness and the page use and nothing more; the adapter holds every Cypher statement, the constraint families and the saved queries, and imports its driver lazily. Loader, rules, gate, runner, SHACL projection, the page's store card and gaps API, and the register projection call the port. KG_STORE picks the adapter. Verification: 47/47 tests, among them an AST check that the adapter implements every port operation and a source check that no other module speaks Cypher; the deterministic comparator at 0 differing leaves over 7 scenarios; the page's checks locally with a deterministic run and the projection through the port. D1 still records which constraint families Community refuses. Follow-ups: the rdflib adapter (task-0004) proves the port with a second implementation; stamping the instance id on writes waits for a shared store.
<!-- SECTION:FINAL_SUMMARY:END -->
