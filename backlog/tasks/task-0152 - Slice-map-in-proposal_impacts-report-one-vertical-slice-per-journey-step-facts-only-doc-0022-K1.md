---
id: TASK-0152
title: >-
  Slice map in proposal_impact's report: one vertical slice per journey step,
  facts only (doc-0022 K1)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-05T22:38:00Z'
updated_date: '2026-11-06T00:06:00Z'
labels: []
dependencies: []
priority: medium
type: feature
ordinal: 159000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0022 (initiative slicing): knowgov reads an initiative and gates the board; it does not hold the backlog, the ranking or the estimates. proposal_impact already gives the intake read of a proposed addition; grouping its report into slices makes it the story map's backbone: per journey step, the thread step → process → capability → application → entity, from the register's own walks. It waits on doc-0022 K2, the register's thread walk and product–journey alignment rule (an ieam-register decision), being approved and vendored, so knowgov composes no second walk semantics. Maintainer's go, 2026-11-05: K1 after K2 is vendored, below task-0141 and the lighthouse prerequisites; slices by journey step, by end-to-end process for a product no journey concerns; facts only.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 After the ieam-register tag carrying doc-0022 K2 is vendored, proposal_impact's report gains a slices section built from the register's thread walk: one slice per journey step, or per end-to-end process for a product no journey concerns
- [x] #2 Every overlay element appears in exactly one slice or in a named remainder (for example a capability the product requires that no step reaches, an enabler), with the denominator shown
- [x] #3 Facts only: no planning label (walking skeleton, MVP, priority), no estimate, no rank; additive schema change, CHANGELOG Unreleased carries the line
- [x] #4 Tested on doc-0017's worked example and on the approved register (PRD-0002's CAP-0003 reached by no step; PRD-0005 with no journey)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/proposal_impact.py: slices(T, CR, read, ov) from the vendored impact.walk_children with THREAD (decision 0018) and check_register.check_alignment (A1) on the read register; products in scope: those whose footprint (product, journeys, their descendants, slice threads, required capabilities and their realisers) holds an overlay node or both ends of an overlay link.
2. Axis: per approved step (and touchpoint under no step) of a journey concerning the product; for a product no journey concerns, per process that delivers it. Each slice: start, walked descendants, the thread by layer with status new/reused/changed and owner, empty layers, withdrawn edges, owners, the overlay elements it holds.
3. Remainder, named: shared (on more than one slice's thread), required_not_reached (A1's, or the process axis' by the same walk; with the realisers walk), frame (products, journeys, stages and their concerns/delivers/requires links), exceptions, outside; the denominator (nodes+links+exceptions) and the count in slices and remainder.
4. Schema: slices, additive and required; render_text lines; CHANGELOG Unreleased under Contract changes.
5. Tests: the worked example (JRN-0013..15, CAP-0002/0003/0009 required not reached, 12 of 12), the approved register via a small overlay on PRD-0002 (CAP-0003) and PRD-0005 (no journey, PROC-0006 axis), exactly-once, no planning label, branch mode, CLI equals MCP; tools/check_mcp_server.py holds MCP slices equal to evaluate's.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-05: K2 is in. ieam-register decision 0018 approved by the maintainer and merged (ieam-register#29, 7f1680c), v0.2.11 published, vendored here by task-0155. The thread walk is the vendored impact.py's THREAD / --walk thread; this task reads it, never a second walker.

2026-11-06: built. harness/proposal_impact.py slices() reads the vendored impact.walk_children(THREAD) and check_register.check_alignment (A1) on the read register; no walker or walk rows of its own (a link is matched to a slice by the live edges the walk reports). Scope: a product whose footprint holds an overlay node or both ends of an overlay link. The required_not_reached group takes the realisers walk and each realising process's own thread, so an element added under PROC-0003 lands with CAP-0003. Evidence: AC1 tests test_the_worked_example_is_three_step_slices... (JRN-0013, JRN-0014, JRN-0015) and test_on_the_approved_register... (PRD-0005 by PROC-0006, axis process). AC2: both tests assert every node, link and exception placed once, denominators 12 (4 in slices, 8 remainder) and 5; test_an_overlay_no_product_touches... the outside group. AC3: the same test holds no planning word in the section; schema slices additive and required, schema_check valid; CHANGELOG Unreleased, Contract changes. AC4: worked example as doc-0022 §2's hand map (CAP-0002, CAP-0003, CAP-0009 required not reached); approved register: PRD-0002 required_not_reached CAP-0003 by A1, PRD-0005 no journey, sliced by PROC-0006, PRD-0004 reached_not_required CAP-0008. CLI = MCP: test_the_command_and_the_mcp_tool_give_the_same_slice_map; tools/check_mcp_server.py holds the MCP slices equal to evaluate's (KG_STORE=rdflib --scenarios S1: every check holds; 3 slices, 4 of 12 in them). Branch mode: tools/check_proposal_branch.py every check holds (ids_aside covers slices). tests/run_tests.py 504/509 stdlib (5 skipped), 508/509 with rdflib 7.6.0, pyshacl 0.40.2, KG_TEST_REQUIRE=rdflib (1 skipped), 0 failed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
proposal_impact's report gains slices (doc-0022 K1): one vertical slice per approved journey step of each product the proposal touches (a touchpoint rides its step), per delivering process for a product no journey concerns, from the register's own THREAD walk with parent descent (ieam-register decision 0018, v0.2.11) and its rule A1. Each slice: the thread by layer (process, capability, application, information), each node new, reused or changed with its owner, empty layers, withdrawn edges, owners, and the overlay elements it holds. Every overlay node, link and exception sits in one slice or one named remainder (shared, required_not_reached with realisers, frame, exceptions, outside), with the denominator. Facts only. Schema additive (slices required), CHANGELOG Unreleased under Contract changes, text output, MCP tool description, check_mcp_server.py equality. Limits: a stage's own support counts in A1 but makes no slice; scope is by footprint, so a proposal touching only a shared process brings every product on it.
<!-- SECTION:FINAL_SUMMARY:END -->
