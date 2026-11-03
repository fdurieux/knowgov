---
id: TASK-0044
title: >-
  Register walk from every kind: what depends on a node (ieam-register decision
  0010), vendored and shown
status: Done
assignee:
  - '@claude'
created_date: '2026-11-03T22:40:00Z'
updated_date: '2026-11-03T23:26:00Z'
labels:
  - impact
  - register
milestone: m-6
dependencies: []
references:
  - backlog/docs/doc-0011
priority: high
type: feature
ordinal: 56000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0011 point 1 (measured on the example instance): the register's impact walk (tools/impact.py FORWARD) reaches nothing from 28 of 37 approved CAP, ENT, PRD and journey-step starts; following every type both ways collapses to one 15-node slice from every start. A per-kind dependants table fixes it: crud⁻¹ and manages⁻¹ from an entity, requires⁻¹ from a capability, concerns⁻¹ and delivers⁻¹ from a product, is_supported_by forward from a step; zero-reach starts 28 → 6 (domains and portfolios only). The walk is the register's (its decision 0007): propose it there as decision 0010 with its test, then re-vendor here and keep the page's panel and saved Cypher equal to the walk on every node (as task-0023 and task-0026 did).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 ieam-register decision 0010 (proposed, the maintainer approves by the merge) changes impact.py to walk dependants per start kind under 0007's approved-only rule; its test shows zero-reach approved starts go from 28 to 6 and no start reaches the whole slice
- [x] #2 knowgov re-vendors the register at the tag that carries 0010
- [x] #3 The impact panel and the register-impact saved query equal the vendored walk on every node of both subjects, held by the existing equality test and the stack job
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Vendor ieam-register v0.2.6 (decision 0010). 2. harness/store_neo4j.py IMPACT_WALK: IMPACT_STEPS per taxonomy and direction; a quantified path of live steps (SHORTEST 1) finds the expanded nodes, every step from each is a row; IMPACT_PATHS the OPTIONAL form. 3. tests/test_register_view.py parses the step predicate, checks it equals the vendored FORWARD, simulates it on every node of the register and the fixture. 4. Panel text and demo README name the per-kind steps; counts and tags to the new truth. 5. Verify on a live Neo4j 5.26 and check_saved_queries.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Register v0.2.6 (tag at 2b95f43) carries decision 0010, approved by the merge of ieam-register #14; vendored with tools/vendor_register.py. IMPACT_WALK is no longer a fixed set of chains: the kinds form cycles (process delivers product, product delivers inverse), so the expanded nodes come from a quantified path of live steps (SHORTEST 1 per node) and the edges met from each are the rows. Verified on a live Neo4j 5.26 community: IMPACT_ROWS equals walk() on all 57 nodes (469 rows) and on every node of the deprecated/withdrawn fixture; IMPACT_PATHS gives one row per edge (one for an edgeless start); check_saved_queries.py runs every saved query. The test's simulator parses the adapter's text and its steps equal the vendored FORWARD.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Re-vendored ieam-register at v0.2.6 and made the impact walk's Cypher (harness/store_neo4j.py IMPACT_WALK, IMPACT_ROWS, IMPACT_PATHS) follow decision 0010's per-kind dependants, reversed edges included: a quantified path over the step predicate finds the nodes the walk expands, the same predicate gives the edges met from each. tests/test_register_view.py parses that predicate, checks it equals impact.py's FORWARD and simulates it against walk() on every register node and the fixture; counts and tags updated to the new truth (57 nodes, APP-0002 10 edges, 469 rows in all). The panel's intro and the demo README name the per-kind steps. Verified against a live Neo4j 5.26 on every node. Risk: SHORTEST 1 needs Neo4j 5.21 or later; the stack pins 5.26.
<!-- SECTION:FINAL_SUMMARY:END -->
