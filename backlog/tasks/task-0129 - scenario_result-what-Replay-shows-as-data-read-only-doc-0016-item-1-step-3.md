---
id: TASK-0129
title: >-
  scenario_result: what Replay shows, as data, read-only (doc-0016 item 1, step
  3)
status: To Do
assignee: []
created_date: '2026-11-04T20:10:00Z'
updated_date: '2026-11-05T00:06:00Z'
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Coordinator's decision under the maintainer's night delegation (2026-11-05): build now, after task-0133, in the runs session. Canvas: Problem, an agent can list runs (task-0128) but cannot read what Replay shows without a load that wipes the shared store. Options: (a) build scenario_result now, read-only, from runs_index's listed sources; (b) leave it to the page. Value: an evaluator or agent reads the D6 gate, the keys' levels and the arms' decisions of any record or run with no load and no store read; it completes doc-0016 item 1. Cost: about 100 lines and tests on a module that exists. Risk: a replayed result mistaken for the held one, answered by its reply naming that it reads files, not the store (AC #3). Chosen (a).
<!-- SECTION:NOTES:END -->
