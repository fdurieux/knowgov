---
id: TASK-0026
title: >-
  The register at v0.2.2: the walk follows approved links only, in the panel and
  in its Cypher
status: Done
assignee:
  - '@claude'
created_date: '2026-11-02T11:24:00Z'
updated_date: '2026-11-02T12:23:00Z'
labels:
  - register
  - page
milestone: m-3
dependencies:
  - TASK-0023
  - TASK-0021.04
references:
  - demo/register/SOURCE.md
  - demo/app/register_view.py
  - harness/store_neo4j.py
  - subjects/jef_data_load/register_map.toml
  - tests/test_register_view.py
  - tests/test_jef_subject.py
type: feature
ordinal: 36000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
ieam-register decision 0007 (v0.2.2, merged 2026-11-02) re-read three evidence anchors of the J-F slice and made the register impact walk follow approved links only: an edge whose link is not approved, or whose far node is deprecated or retired, is reported and marked withdrawn, not followed and not counted among what was reached. The demo carried the register at v0.2.1, whose walk followed any link state, and its register-impact Cypher (task-0023) reproduced that older rule, so the panel, the saved query and the Browser guide would disagree with the vendored tool once the copy moved. The J-F register map was reconciled with the links at v0.2.1 (task-0021.04): the three re-read anchors move endpoints between rows (JDL-072, JDL-113 and JDL-150 lose the nodes the old citations added; JDL-058, JDL-069 and JDL-108 gain the endpoints of the links that now cite them), and tests/test_jef_subject.py holds every row to the links. One pull request: re-vendor, map rows, walk, Cypher, counts, pins.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 demo/register is the tool-written copy at ieam-register v0.2.2, every file held to its digest, the vendored checker clean at the pinned date
- [x] #2 The impact panel reports every edge the vendored walk meets with whether it was followed, counts withdrawn edges apart, and lists as reached the far ends of live edges only; its sentences stay within the controlled-English rules
- [x] #3 The register-impact and register-impact-paths Cypher follow approved links through intermediate nodes only and report the last edge with its state; the simulation test proves equality with the vendored walk on every node of the copy and on a fixture where a proposed link is the only route
- [x] #4 The J-F register map names both endpoints of every approved link that cites a key at v0.2.2 and no node a withdrawn citation alone put there; its register_commit names the v0.2.2 commit
- [x] #5 The stdlib suite is green and the stack job compares the saved query rows with the panel edges for the same start at v0.2.2
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Re-vendor demo/register from a clean checkout of ieam-register at v0.2.2 with tools/vendor_register.py (90 files; the two relationship files, impact.py and decision 0007 change). 2. register_view.impact: rows take a followed column from the edge's live flag, reached is impact.reached(edges), the summary counts withdrawn edges, the intro says the rule in controlled sentences; the page's one-line note says the same. 3. store_neo4j: name the intermediate links r1/r2 and filter them on state approved; the rows form adds a followed column computed as the walk computes live. 4. tests: the Cypher simulation parses link variables and the approved filter, compares the live flag too, and the fixture gains a proposed-only route (REL-12, PROC-3, PRD-4). 5. register_map.toml: six rows moved per decision 0007, register_commit at v0.2.2, header paragraph dated. 6. Repin tag and commit in tests and demo.yml; earlier copies list gains v0.2.1. 7. Suite green; PR; stack job green including the saved-query row count and check_impact_cypher.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Re-vendored at v0.2.2 (0242646): 90 files, the two relationship files, crud.toml, impact.py and decision 0007 changed; 56 nodes, 65 links as before. register_view.impact now takes live from the vendored walk and reached from impact.reached; the rows carry a followed column; the summary reads "9 edges walked, 2 withdrawn; 2 processes, 2 products and 3 journey elements reached" from APP-0005 (the tool prints the same) and "5 edges walked, 0 withdrawn" from APP-0002. Cypher: r1/r2 named on intermediate links, filtered state approved; rows form adds followed. The simulation test parses link variables and the approved filter and compares live; the fixture gains REL-12 (proposed) APP-1 -> PROC-3 -> PRD-4, 9 edges from APP-1 with 4 withdrawn and PRD-4 never reached. Map: six rows moved, register_commit at v0.2.2; the approved-link citations still count 31 keys. Pins moved in three tests and demo.yml. Stdlib suite 91/91.

The maintainer approved the six v0.2.2 rows as they stand on 2026-11-02, after an opportunity canvas on them; recorded on the map (knowgov #45). The open line of the final summary is closed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Merged as knowgov #43 on a green matrix (tests, rdflib, stack). The demo carries ieam-register v0.2.2 (0242646, decision 0007); the impact panel lists every edge the vendored walk meets with a followed column, counts withdrawn edges apart and reaches the far ends of live edges only; the saved Cypher walk filters intermediate links on approved and adds the same column, equal to the walk on every node of the copy, on a fixture with a proposed-only route (test) and against a local Neo4j 5.26 for five starts (rows and paths forms, every saved query running); the stack job compared the saved query rows with the panel edges and ran check_impact_cypher for all 56 nodes. The J-F map moved six rows per decision 0007 and pins v0.2.2; its approved-link citations still count 31 keys. Open: the maintainer has not yet said the word on the six revised map rows (the map header says so); when given, the status comment line records it as for v0.2.1.
<!-- SECTION:FINAL_SUMMARY:END -->
