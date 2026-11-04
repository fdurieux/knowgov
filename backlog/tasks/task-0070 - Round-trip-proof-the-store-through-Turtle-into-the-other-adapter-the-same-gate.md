---
id: TASK-0070
title: >-
  Round-trip proof: the store through Turtle into the other adapter, the same
  gate
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-03T23:53:00Z'
updated_date: '2026-11-04T00:06:00Z'
labels:
  - store
milestone: m-8
dependencies:
  - TASK-0056
references:
  - backlog/docs/doc-0013
priority: low
ordinal: 74000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0013 P4. Portability is asked of every platform, knowgov included; the rdflib store already writes Turtle. The proof is the exit argument for a buyer.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A test loads a scenario, serialises the store, reloads it into a fresh store of the other kind and compares gate reports and three-valued answers for every scenario of both subjects
- [ ] #2 The Neo4j direction runs in the stack job
- [ ] #3 Any port method added is named as a contract change under decision-0003
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Port: Store.export_turtle() and Store.import_turtle(text) in harness/store.py, the interchange form the rdflib adapter's own graph (urn:kg:n/label/p/e, reified edges, _seq for store order); a contract change under decision-0003.
2. rdflib: serialise the graph / wipe, parse, reindex. Neo4j: read every node and relationship into an in-memory RdflibStore and serialise it; import parses through the same layer and creates nodes by label set and relationships by type through a temporary indexed label, then removes it. Register nodes carry reg_id and no id in Neo4j: named reg:<label>:<reg_id> as the rdflib adapter names them.
3. tools/check_round_trip.py --chain: load each scenario (and S6's stage 2) with gate_cli's load, ask the MCP server's tools for every task's gate report and the three-valued answer of every named and required key, hand the store on as Turtle hop by hop, require equal answers (store name and list order aside), equal census, and the same nodes and edges after the chain.
4. CI: rdflib,rdflib on both subjects in harness.yml; neo4j,rdflib,neo4j on both subjects in the stack job (demo.yml). tests/test_round_trip.py holds the port, both adapters, the comparison and the CI lines.
5. Prove locally on rdflib and on Neo4j 5.26 community.
<!-- SECTION:PLAN:END -->
