---
id: TASK-0047
title: Impact panel shows the owning unit beside each reached node
status: Done
assignee:
  - '@claude'
created_date: '2026-11-03T22:40:00Z'
updated_date: '2026-11-04T00:13:00Z'
labels:
  - impact
  - page
milestone: m-6
dependencies: []
priority: low
type: feature
ordinal: 59000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0011 follow-up 3: the panel lists what a change reaches but not who owns it; the register's owns links and each node's owner field name the unit. Show it beside each reached node, so the walk answers who to tell.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Each reached node on the impact panel shows its owner unit (id and name)
- [x] #2 Controlled-English and glossary tests cover the new text
- [x] #3 A test holds the owner shown to the register's owner field
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. register_view.owning_unit/unit_text: the node's owner field, the unit's name, the approved owns links' sources; impact() adds an 'owning unit' column, owner on each Reached item, and a Who to inform section; the vendored walk untouched.
2. IMPACT_ROWS returns unit, unit name, owns links (approved REG_OWNS only; the owner field's edge has no state); check_impact_cypher compares them per edge.
3. server.node_statements + register_view.with_statements: the port's register_node_statements beside the walk for the typed node, or what the store lacks.
4. Glossary term 'owning unit'; tests for every node, the Cypher fragments over the projection rows, the statements section; harness.yml (rdflib) and demo.yml (Neo4j) check the panel on ENT-0004.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Proved locally: rdflib (S6 + projection) ENT-0004 panel 13 assertions beside the walk, equal to the port's rows; Neo4j 5.26.0 community (Java 21): check_impact_cypher.py every node agrees, 57 nodes, both forms, owning unit included; check_saved_queries register-impact 10 rows; /api/register/impact/ENT-0004 13 assertions. tests/run_tests.py 183/183. The realiser walk (register decision 0010) not built: the register's to decide.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The impact panel names the owning unit of each reached node (owner field, unit name, any approved owns link naming another unit) in a new column, on each Reached item and in a Who to inform list grouped by unit. IMPACT_ROWS returns unit, unit name and owns links; check_impact_cypher holds them equal to the panel on every node (Neo4j 5.26: 57 of 57). Beside the walk, the port's register_node_statements for the typed node (task-0046, #95), or a sentence naming what the store lacks; proved on rdflib in harness.yml and on Neo4j in demo.yml (ENT-0004: 13). Glossary term 'owning unit'. Vendored walk untouched; the realiser walk is left to the register.
<!-- SECTION:FINAL_SUMMARY:END -->
