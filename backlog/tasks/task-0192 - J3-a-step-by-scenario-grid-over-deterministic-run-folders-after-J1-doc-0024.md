---
id: TASK-0192
title: >-
  J3: a step-by-scenario grid over deterministic run folders, after J1
  (doc-0024)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-06T23:06:00Z'
updated_date: '2026-11-07T00:24:00Z'
labels:
  - proposal-impact
  - runs
dependencies:
  - TASK-0191
references:
  - harness/upward.py
  - harness/run.py
priority: low
type: feature
ordinal: 192000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer accepted doc-0024's advice on 2026-11-06 ("accept the advice on all three"): the scenario grid is a command over deterministic run folders, after J1, and never goes through knowgov-runs. knowgov-runs' start_run wipes the shared store every viewer reads (decision-0008), so a sweep through it would replace the page's scenario once per cell. The grid reads harness/run.py --deterministic run folders, maps each key to its journey step through key_nodes and J1's THREAD slices, and shows per step and scenario the worst level and the findings. Facts only, with denominators and no score.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A CLI reads one or more run.py --deterministic folders and prints, per journey step and scenario, the worst level and the findings of the keys landing on that step
- [x] #2 It never loads or writes a shared store and never calls knowgov-runs; a test proves the configured store is unchanged
- [x] #3 Its JSON is pinned by a schema; on CargoQuote S1 to S7 each cell agrees with the scenario's gate report for the same keys
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/step_grid.py: columns from run.py --deterministic folders (or --record), each scenario's deterministic.json, never a store.
2. Rows: J1's slices (proposal_impact.evaluate with a scope, no overlay), each step's landed keys; default scopes every approved journey a step of which lands a key; keys on no step listed with key_nodes' nodes.
3. Cells: levels from gate_keys, findings from D6_gate restricted to the step's keys (blocked, below verified, flagged, stale, suspect derived, lapsed), stage 2's two gates' findings; conflicts counted per column, never by gap id (doc-0030); nothing recomputed (doc-0030 G3).
4. Schema step-grid; tests (AC1 rows and cells, AC2 no store and no knowgov-runs, AC3 against the gate on scratch stores of S1 to S7); CHANGELOG Contract changes; demo README.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
AC1: step_grid.py RUN_DIR... [--record] [--scope ID]... prints, per J1 step and scenario, the lowest level read and the findings of the step's keys; CargoQuote: JRN-0002 and JRN-0003 by S1..S7 (S2 absent, S4 disputed, S6 stage 2 stale on JRN-0003 only, S7 proposed), 4 of 36 keys on no step; J-F: JRN-0006, -0007, -0009..-0011 by C, D1..D5, 9 of 163 on no step.
AC2: in process with store.open_store refused and mcp_runs and urllib.request unimportable the grid answers; as a command beside a configured rdflib store file its bytes and mtime are unchanged and no lock or copy appears; with KG_STORE=neo4j at an address nothing serves it answers all the same.
AC3: step-grid.schema.json, every object closed (a stray field refused); a fresh run.py --deterministic folder of S1..S7 on a scratch store, then per scenario gate_cli.evaluate on a scratch store holding it, for each step's keys: levels, blocked keys, stale statements and lapsed keys equal each cell's (rdflib job).
Code-review notes (doc-0030): conflict gap ids follow store order, so conflicts are counted per column only; levels are the gate report's, never recomputed.
Suites: stdlib 658/689, J-F 658/689, pinned 687/689, pinned J-F 686/689, 0 failed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
harness/step_grid.py: a step-by-scenario grid over run.py --deterministic folders or the record. Rows are J1's THREAD slices with their landed keys, columns the scenarios, each cell the step's keys as the folder's gate report has them (levels from gate_keys, findings from D6_gate, stage 2's gates), conflicts counted per column, the keys on no step listed through key_nodes. Never opens a store or calls knowgov-runs. Schema step-grid; CHANGELOG contract line for 0.9.0.
<!-- SECTION:FINAL_SUMMARY:END -->
