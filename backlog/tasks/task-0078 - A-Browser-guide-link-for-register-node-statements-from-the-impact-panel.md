---
id: TASK-0078
title: A Browser guide link for register-node-statements from the impact panel
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T00:44:00Z'
updated_date: '2026-11-04T02:31:00Z'
labels:
  - page
milestone: m-6
dependencies: []
priority: low
ordinal: 82000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The walk has a Browser link that pre-fills its query (task-0025); the anchor-grain statements view added by task-0047 has none.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The panel's statements view carries a Browser link that pre-fills register-node-statements for the node
- [x] #2 The stack job verifies the link as it does the walk's
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. store_neo4j.node_statements_cypher(start): the saved query register-node-statements from the typed node.
2. server: a third guide form, statements, served at /api/register/impact/<id>/guide/statements; impact_view gives the statements section a code block with its Browser link (register_view.with_statements_cypher).
3. check_impact_cypher.py: for every node, the statements link's guide block is the listed text, and its console rows equal the port's register_node_statements rows the panel shows.
4. Stdlib test beside task-0025's; prove on Neo4j 5.26 against the page.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Locally on Neo4j 5.26.0 community (tarball, Java 21), CargoQuote S1 loaded and the register projected, the page served from demo/app/server.py: check_impact_cypher.py 57 nodes agree, both walk forms and the statements view, 17 nodes reach statements (task-0077's 17), each statements guide's block the listed register-node-statements from the node and its console rows equal to the port's rows the panel shows. Playwright on the page: ENT-0004's 'Assertions its cited anchors name' section carries 'open in the Browser' to /api/register/impact/ENT-0004/guide/statements. On rdflib (no console) the view has no code and no guide. tests/run_tests.py 247/247 plain and with KG_SUBJECT=subjects/jef_data_load. The code label is 'Rows, one per assertion and cited document': 'statement' is a forbidden word on the page.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The impact panel's statements view now carries the saved query register-node-statements from the typed node (store_neo4j.node_statements_cypher) with an 'open in the Browser' link to a guide the server serves at /api/register/impact/<id>/guide/statements, the same play-guide mechanism as the walk's (task-0025): a click fills the editor, nothing runs. Only a store with a console gets it. check_impact_cypher.py follows every node's statements link as it follows the walk's: guide headers, the block equal to the listed text, and the console rows equal to the port's rows the panel shows; demo.yml pins 57 nodes and 17 reaching statements on S1. Proven on Neo4j 5.26 and in a browser on the page; stdlib test beside task-0025's.
<!-- SECTION:FINAL_SUMMARY:END -->
