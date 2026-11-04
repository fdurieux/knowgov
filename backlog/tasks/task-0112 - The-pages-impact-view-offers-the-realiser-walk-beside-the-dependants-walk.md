---
id: TASK-0112
title: The page's impact view offers the realiser walk beside the dependants walk
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T14:55:00Z'
updated_date: '2026-11-04T19:05:00Z'
labels:
  - demo
  - register
milestone: m-8
dependencies: []
priority: medium
type: feature
ordinal: 112000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Proposed by task-0109; chosen by the maintainer 2026-11-04. ieam-register v0.2.7 (decision 0012) adds impact.py --walk realisers: what realises a capability (processes that support it, applications that realise it). The page's impact view shows only the dependants walk. Offer both, in both store adapters, with a saved query and the panel naming which walk it shows.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The impact view switches between dependants and realisers; CAP-0002/3/4 show three distinct realiser answers, as impact.py does
- [x] #2 Both adapters return the same walk; a saved query for the realiser walk runs in check_saved_queries
- [x] #3 The record and the comparator are unchanged; a CHANGELOG line under Unreleased
- [x] #4 The panel's children option reaches what register_impact with children=true reaches, on both walks and both subjects; withdrawn descendants are listed and not walked from
- [x] #5 A saved Neo4j query and its guide exist for each walk with and without children, run by check_saved_queries
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. register_view.impact(start, walk, children): the register's WALKS and walk_children; panel names the walk and the option; a Descendants section (state, walked or withdrawn); reached by the walk's kinds (processes and applications for realisers).
2. store_neo4j: IMPACT_STEPS per walk; impact_cypher(start, walk, children); the children form takes as starts the node and every approved descendant by REG_PARENT, then the same CALL block; saved queries for the three new combinations.
3. server: /api/register/impact/<id>?walk=&children=; guides under /api/register/impact/<id>/<variant>/guide/<form> (no & in the Browser's arg); the page's form gets a walk select and a children box.
4. Tests: Cypher simulated equal to walk/walk_children on every node, both walks, both options; panel reach equal to register_impact on both subjects; CAP-0001 children answers; default unchanged.
5. check_impact_cypher and check_saved_queries cover every variant; demo.yml greps updated; CHANGELOG line.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Widened 2026-11-04 (maintainer): the panel also offers descent to children (decision 0014, walk_children), so the page answers what the register and register_impact answer.

Evidence: tests 352/352 on both subjects; the Cypher of all four variants simulated equal to walk/walk_children on every node and on a fixture (deprecated child, approved grandchild); panel reach equal to register_impact on every node, both walks, both options, both subjects; CAP-0001 with children reaches JRN-0001, PRD-0002, PROC-0001 and lands 31 keys (dependants) and 36 (realisers); CAP-0002/3/4 three distinct realiser answers. Local Neo4j 5.26: check_impact_cypher every node agrees over 4 walks; check_saved_queries 15/2/6 rows for the new queries, equal to the panel's edges. rdflib deterministic vs record: 0 differing leaves. PR #200 green (tests, rdflib, stack), merged.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The page's impact panel offers the register's dependants and realisers walks, each with or without children (decision 0014, walk_children), built against v0.2.8. A withdrawn descendant is listed and not walked from. Each variant has Cypher, a Browser guide (/api/register/impact/<id>/<variant>/guide/<form>) and, for the three new ones, a saved query (register-impact-children, register-realisers, register-realisers-children); check_impact_cypher checks all four on every node. The default panel, its Cypher and the record are unchanged. Merged in #200. Follow-up proposed, not created: the panel could list the landed keys with their levels, as register_impact does.
<!-- SECTION:FINAL_SUMMARY:END -->
