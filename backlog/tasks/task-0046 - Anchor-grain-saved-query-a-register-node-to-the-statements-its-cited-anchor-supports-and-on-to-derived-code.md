---
id: TASK-0046
title: >-
  Anchor-grain saved query: a register node to the statements its cited anchor
  supports, and on to derived code
status: Done
assignee:
  - '@claude'
created_date: '2026-11-03T22:40:00Z'
updated_date: '2026-11-03T23:17:00Z'
labels:
  - impact
  - queries
milestone: m-6
dependencies: []
references:
  - backlog/docs/doc-0011
priority: medium
type: feature
ordinal: 58000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0011 follow-up 2: #81's register-node-store query works at document grain (REL-08001 cites contract/openapi.yaml, so every statement of the file is reached). Matching a REG_CITES anchor to the fragments it names narrows it: ENT-0004 → DT-P → 13 statements, against 39 at document grain. Through both store adapters.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A saved query reaches, from a register node, only the statements whose fragments the cited anchor names, then the derived outputs that used them
- [x] #2 The same result through the rdflib port; ENT-0004 gives 13 statements and derived:S1:G:run1
- [x] #3 The stack job and check_saved_queries.py run it
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. store_neo4j._NODE_STATEMENTS: approved REG_LINK_OF links, REG_CITES anchor (part after '#', null when none), every Version of the cited Artefact (HAS_VERSION, so invalidated statements keep their derived code), fragments whose locator has the anchor as a '/' segment (whole document without one), SUPPORTED_BY assertions, USED_ASSERTION derived; one row per statement. Parameterised $start for the port; NODE_STATEMENTS the saved query with the information taxonomy's literal start, listed as register-node-statements (register+scenario).
2. Store port register_node_statements(start) in store.py; Neo4j runs the same Cypher, rdflib walks the same rule through its graph helpers; lists sorted so both compare equal.
3. tests/test_register_view.py holds the listing and the rule (stdlib, source-read for rdflib); harness.yml (rdflib) and the stack job (Neo4j) each run S6 with the record's S1 code as derived, project the register, and assert ENT-0004 -> 13 statements at DT-P, 4 invalidated, derived:S1:G:run1 (suspect); the stack job reruns check_saved_queries.py on S6.
4. docs/guide.md §8: the anchor-grain query beside the document-grain one.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Starts after knowgov #81 (the three saved queries, document grain) merges: same file, store_neo4j.py's saved queries.

Locators carry no kind prefix (DT-P/row/P1, row/REQ-05), so the match is a plain '/' segment test in both adapters. doc-0011's figures (39 document grain, 13 anchor grain for ENT-0004) count every version; CURRENT only gives 35 and 9, so the query reads HAS_VERSION. Measured, both stores: ENT-0004 13 rows (8 approved, 4 invalidated, 1 proposed), ENT-0002 18, APP-0002 26, JRN-0003 1, an unknown id 0; port output identical between rdflib and a local Neo4j 5.26 community server. 11 of CargoQuote's 21 citations carry an anchor (doc-0011 said 12 of 22); the guide carries the measured count. Verified: tests 147/147 (also KG_SUBJECT=subjects/jef_data_load and a bare venv); harness.yml's new step and the stack step's commands run locally, rdflib and Neo4j; check_saved_queries.py on Neo4j with S6: every saved query ran, register-node-statements 18 rows from ENT-0002.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
A saved query and a store-port operation now go from a register node to the statements its approved links cite at the grain of the cited anchor, and on to the derived code that used them. register-node-statements (store_neo4j, listed from the information taxonomy's default) and register_node_statements(start) on both adapters apply one rule: an anchored citation (path#DT-P) reaches only fragments whose locator holds the anchor as a path segment, an unanchored one the whole document, across every version. ENT-0004 on S6 with the S1 code as derived: 13 statements (39 at document grain), 4 invalidated, derived:S1:G:run1 (suspect), identical on rdflib and Neo4j. harness.yml and the stack job assert it; the stack job reruns check_saved_queries.py on S6. Guide §8 explains it. Limit: it narrows only where the register cites an anchor (11 of 21 CargoQuote citations).
<!-- SECTION:FINAL_SUMMARY:END -->
