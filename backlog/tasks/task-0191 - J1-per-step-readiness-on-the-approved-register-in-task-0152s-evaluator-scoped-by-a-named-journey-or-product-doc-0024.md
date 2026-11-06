---
id: TASK-0191
title: >-
  J1: per-step readiness on the approved register, in task-0152's evaluator,
  scoped by a named journey or product (doc-0024)
status: To Do
assignee: []
created_date: '2026-11-06T23:05:00Z'
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
- [ ] #1 A named journey or product with no overlay gives its slices on the approved register, through the register's own THREAD walk
- [ ] #2 Each slice lists its keys with levels per task class and as_of, equal to register_impact's landed_rows and with_levels for the same nodes
- [ ] #3 Cells carry their denominators and unknown, with no score; on CargoQuote JRN-0002 the keys match doc-0024's measure (22 of 36)
- [ ] #4 The proposal-impact schema grows additively, the MCP tool and the CLI both take the scope, and CHANGELOG.md has the line under its contract heading
<!-- AC:END -->
