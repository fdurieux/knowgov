---
id: TASK-0003
title: 'Store port with Neo4j as the first adapter: no Cypher outside the adapter'
status: To Do
assignee: []
created_date: '2026-11-01T14:27:00Z'
updated_date: '2026-11-01T14:30:00Z'
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
- [ ] #1 A port interface lists every store operation with its arguments and result shape
- [ ] #2 Rules, gate, runner, page and projection call port methods and contain no Cypher
- [ ] #3 The Neo4j adapter passes the deterministic comparator on CargoQuote with no change in the record
- [ ] #4 Constraints Community refuses stay application checks and D1 still reports which were refused
<!-- AC:END -->
