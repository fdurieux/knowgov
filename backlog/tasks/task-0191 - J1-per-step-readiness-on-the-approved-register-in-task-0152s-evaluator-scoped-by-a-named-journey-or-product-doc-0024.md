---
id: TASK-0191
title: >-
  J1: per-step readiness on the approved register, in task-0152's evaluator,
  scoped by a named journey or product (doc-0024)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-06T23:05:00Z'
updated_date: '2026-11-06T23:40:00Z'
labels:
  - proposal-impact
  - register
  - contract
dependencies: []
references:
  - harness/proposal_impact.py
  - harness/register_impact.py
priority: medium
type: feature
ordinal: 191000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer accepted doc-0024's advice on 2026-11-06 ("accept the advice on all three"): J1's home is task-0152's evaluator, one evaluator and one schema for an initiative and for what exists. doc-0024 measured on register v0.2.11 that proposal_impact refuses an overlay that adds nothing ("the proposal adds no node and no link"), so task-0152's slices cannot yet be read on the approved register alone. J1 adds two things. (a) A scope by a named journey or product, with no overlay. (b) Per slice, the register_map.toml keys landing on its thread, with levels per task class and as_of, read as keys.by_node reads them (register_impact's landed_rows, with_levels). The cells: the worst level, gaps, lapses, keys behind withdrawn edges, and owner handoffs. The thread is decision 0018's THREAD walk, vendored; knowgov adds no walker. Facts only: denominators and unknown shown, no score (doc-0015 §1). An additive schema change: under decision-0016 it joins the 0.9.0 gathering, or waits for 0.10.0 if it misses the cut.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A named journey or product with no overlay gives its slices on the approved register, through the register's own THREAD walk
- [x] #2 Each slice lists its keys with levels per task class and as_of, equal to register_impact's landed_rows and with_levels for the same nodes
- [x] #3 Cells carry their denominators and unknown, with no score; on CargoQuote JRN-0002 the keys match doc-0024's measure (22 of 36)
- [x] #4 The proposal-impact schema grows additively, the MCP tool and the CLI both take the scope, and CHANGELOG.md has the line under its contract heading
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Scope: evaluate(proposal | None, scope=ID), the CLI's --scope and the MCP tool's scope; an approved journey, step, touchpoint, product or variant, else refused; an empty overlay accepted only with a scope.
2. In slices(): a journey-taxonomy scope slices its own steps (touchpoints riding a step), a product its journeys' steps or delivering processes; the THREAD walk and A1 are the vendored register's, as task-0152 reads them.
3. Per slice: keys = register_impact.landed_rows for the slice's start, live descendants and reached nodes; the denominator the map's distinct keys; the rows behind a non-live thread edge; owner handoffs on live edges.
4. with_levels: one gate_cli.evaluate per slice over its keys, register_impact.with_levels on the rows, the cells (levels by count, unread, worst by the gate's ORDER, unknown = absent, gaps = declared_gap, lapsed); never a score.
5. Schema additive (slices.scope, per slice handoffs and keys); tests; check_mcp_server holds each scoped slice to gate_verdict's levels; CHANGELOG Unreleased > Contract changes.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
AC1: scope JRN-0001 or PRD-0002 with no overlay gives slices JRN-0002 and JRN-0003, each the vendored impact.walk_children(THREAD) from the step (test compares the thread and descendants to the walk read apart); a step names its own slice, a touchpoint riding it; JRN-0005 gives JRN-0006, -0007, -0009, -0010, -0011; an application, an unknown id or a node not approved is refused, and an empty overlay with no scope still is.
AC2: each slice's rows equal ri.landed_rows(map, start, reached, live descendants, withdrawn descendants) computed apart; with a scenario held, ri.with_levels over gate_verdict on the slice's keys (test over the MCP stub; check_mcp_server over stdio on rdflib for every scenario of S1,S2,S6 and C,D3).
AC3: JRN-0002 22 of 36 (doc-0024). JRN-0003 lands 22, not doc-0024's 18: landed_rows includes the four rows naming the step itself (doc-0024 counted reached nodes only), as register_impact does; its proposed edge to PROC-0005 has 4 keys behind it, 1 landed no other way. J-F 65/66/100 of 163 as measured. Cells: levels by count, unread, worst (gate ORDER), unknown (absent), gaps (declared_gap), lapsed; S1 as of 2027-09-01 reads 9 and 3 lapsed. No score field.
AC4: schema additive (slices.scope; per slice handoffs, keys); MCP scope, proposal no longer required; CLI --scope; CHANGELOG Unreleased > Contract changes; demo README "What exists, step by step".
Suites: stdlib 654/684, J-F 653/684, pinned 682/684, pinned J-F 681/684, 0 failed; check_mcp_server and check_proposal_branch hold.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
proposal_impact takes a scope (MCP scope, CLI --scope): a named journey, step or product sliced on the approved register with no overlay, by the vendored THREAD walk and A1. Each slice carries its keys: register_impact.landed_rows for its nodes with the map's key count as denominator, the keys behind withdrawn thread edges, and with a scenario held each row at the level with_levels reads, with the cells (levels by count, unread, worst, unknown, gaps, lapsed) and owner handoffs; facts only, no score. Schema additive; CHANGELOG contract line for 0.9.0.
<!-- SECTION:FINAL_SUMMARY:END -->
