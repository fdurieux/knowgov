---
id: TASK-0070
title: >-
  Round-trip proof: the store through Turtle into the other adapter, the same
  gate
status: Done
assignee:
  - '@claude'
created_date: '2026-11-03T23:53:00Z'
updated_date: '2026-11-04T00:33:00Z'
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
- [x] #1 A test loads a scenario, serialises the store, reloads it into a fresh store of the other kind and compares gate reports and three-valued answers for every scenario of both subjects
- [x] #2 The Neo4j direction runs in the stack job
- [x] #3 Any port method added is named as a contract change under decision-0003
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Port: Store.export_turtle() and Store.import_turtle(text) in harness/store.py, the interchange form the rdflib adapter's own graph (urn:kg:n/label/p/e, reified edges, _seq for store order); a contract change under decision-0003.
2. rdflib: serialise the graph / wipe, parse, reindex. Neo4j: read every node and relationship into an in-memory RdflibStore and serialise it; import parses through the same layer and creates nodes by label set and relationships by type through a temporary indexed label, then removes it. Register nodes carry reg_id and no id in Neo4j: named reg:<label>:<reg_id> as the rdflib adapter names them.
3. tools/check_round_trip.py --chain: load each scenario (and S6's stage 2) with gate_cli's load, ask the MCP server's tools for every task's gate report and the three-valued answer of every named and required key, hand the store on as Turtle hop by hop, require equal answers (store name and list order aside), equal census, and the same nodes and edges after the chain.
4. CI: rdflib,rdflib on both subjects in harness.yml; neo4j,rdflib,neo4j on both subjects in the stack job (demo.yml). tests/test_round_trip.py holds the port, both adapters, the comparison and the CI lines.
5. Prove locally on rdflib and on Neo4j 5.26 community.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Contract change under decision-0003: Store.export_turtle() -> str and Store.import_turtle(text) added to the port (harness/store.py), implemented by both adapters. CHANGELOG left to the release PR.
Two store-order dependences the round trip found and fixed at the source: gate_cli.findings joined Neo4j collect() lists in store order in its messages (S6 stage 2's suspect_derived and stale messages); now sorted. extraction_activities ordered on at alone, and S6's v1 and v2 extractions share a second, so held_version depended on store order after an import into Neo4j; both adapters now break the tie on id.
Lists inside answers (provenance verifications) are compared order-insensitively: their order is the store's (collect()), as the deterministic comparator treats lists.
Local proof: rdflib,rdflib on both subjects (CargoQuote S1-S7 and S6 stage 2; J-F C, D1-D5) every answer survives; Neo4j 5.26.0 community (Java 21) neo4j,rdflib,neo4j on both subjects, and rdflib,neo4j,rdflib on CargoQuote, every answer survives; compare_deterministic on rdflib 0 differing leaves; tests 183/183.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Store.export_turtle()/import_turtle(text) added to the port (contract change under decision-0003; CHANGELOG left to the release PR), both adapters, in the rdflib adapter's form. tools/check_round_trip.py --chain loads every scenario (and S6's stage 2), hands the store on as Turtle and holds the MCP server's gate reports and three-valued answers, the census and the graph equal. CI: rdflib,rdflib on both subjects in harness.yml; neo4j,rdflib,neo4j on both subjects in the stack job; tests/test_round_trip.py guards it. Two store-order dependences found and fixed: gate_cli message ids sorted; extraction_activities ties broken on id. PR #117 merged on a green matrix (tests, rdflib, stack). Follow-up risk: the stack job is ~7 min longer (J-F on Neo4j).
<!-- SECTION:FINAL_SUMMARY:END -->
