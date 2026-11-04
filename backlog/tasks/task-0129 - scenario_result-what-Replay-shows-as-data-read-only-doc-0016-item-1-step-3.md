---
id: TASK-0129
title: >-
  scenario_result: what Replay shows, as data, read-only (doc-0016 item 1, step
  3)
status: To Do
assignee: []
created_date: '2026-11-04T20:10:00Z'
labels:
  - mcp
  - runs
milestone: m-8
dependencies:
  - TASK-0128
priority: low
type: feature
ordinal: 129000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0016 §3 step 3, optional. A read-only tool `scenario_result {scenario, source}` returns what the page's Replay shows for a record or run source, as data: the D6 gate, the keys' levels, the arms' decisions and suite, from the files `harness/runs_index.py` lists. It never reads the store and says so, so a replayed result is never mistaken for the held one.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 scenario_result for each CargoQuote record source returns the D6 gate and the arms' decisions equal to the page's Replay JSON for that source
- [ ] #2 A source not listed by scenario_runs is refused; no path argument
- [ ] #3 The reply names that it reads files, not the store
<!-- AC:END -->
