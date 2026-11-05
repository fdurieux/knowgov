---
id: TASK-0129
title: >-
  scenario_result: what Replay shows, as data, read-only (doc-0016 item 1, step
  3)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T20:10:00Z'
updated_date: '2026-11-05T00:42:00Z'
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
- [x] #1 scenario_result for each CargoQuote record source returns the D6 gate and the arms' decisions equal to the page's Replay JSON for that source
- [x] #2 A source not listed by scenario_runs is refused; no path argument
- [x] #3 The reply names that it reads files, not the store
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. runs_index.result(subject, runs, scenario, source): for a source sources_for lists, the D6 gate as the page's _gate_view has it, the date read, the keys' levels, the arms' runs (decision, code, flagged, suite, model), the stage-2 verdicts; None otherwise.
2. MCP scenario_result {scenario, source}, read-only, the store never opened, the reply's reads naming files not the store; an unlisted source refused, no path.
3. Tests against views.build for every CargoQuote record source; check_mcp_server; README table; CHANGELOG.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Coordinator's decision under the maintainer's night delegation (2026-11-05): build now, after task-0133, in the runs session. Canvas: Problem, an agent can list runs (task-0128) but cannot read what Replay shows without a load that wipes the shared store. Options: (a) build scenario_result now, read-only, from runs_index's listed sources; (b) leave it to the page. Value: an evaluator or agent reads the D6 gate, the keys' levels and the arms' decisions of any record or run with no load and no store read; it completes doc-0016 item 1. Cost: about 100 lines and tests on a module that exists. Risk: a replayed result mistaken for the held one, answered by its reply naming that it reads files, not the store (AC #3). Chosen (a).

Evidence: tests/test_scenario_result.py — runs_index.result equals views.build's gate, as_of date, arms' decisions and suites, and the required-key count for all 9 CargoQuote record sources (S1-S7; S6's rerun and d3check); an unlisted source, a path, an empty or missing source and an unknown scenario are refused; the store opener is never called. tools/check_mcp_server.py asks it for the record on rdflib (S1, S6: every check holds). Both suites 431/431 merged with task-0137.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
scenario_result, an eighth read-only MCP tool, returns what the page's Replay shows for a source scenario_runs lists (record, extra source, run): the D6 gate as the page's gate view, the date read, the keys' levels, each arm's runs and the stage-2 verdicts, read through harness/runs_index.py from the source's files; the store is never opened and the reply says so. Verified against views.build on every CargoQuote record source, by check_mcp_server on rdflib, and both suites.
<!-- SECTION:FINAL_SUMMARY:END -->
