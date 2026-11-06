---
id: TASK-0192
title: >-
  J3: a step-by-scenario grid over deterministic run folders, after J1
  (doc-0024)
status: To Do
assignee: []
created_date: '2026-11-06T23:06:00Z'
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
- [ ] #1 A CLI reads one or more run.py --deterministic folders and prints, per journey step and scenario, the worst level and the findings of the keys landing on that step
- [ ] #2 It never loads or writes a shared store and never calls knowgov-runs; a test proves the configured store is unchanged
- [ ] #3 Its JSON is pinned by a schema; on CargoQuote S1 to S7 each cell agrees with the scenario's gate report for the same keys
<!-- AC:END -->
