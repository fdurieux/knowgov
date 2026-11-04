---
id: TASK-0128
title: >-
  scenario_runs: the subject's scenarios with the record and the runs per mode,
  a sixth read-only MCP tool (doc-0016 item 1)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-04T20:09:00Z'
updated_date: '2026-11-04T23:18:00Z'
labels:
  - mcp
  - runs
milestone: m-8
dependencies:
  - TASK-0126
  - TASK-0127
priority: medium
type: feature
ordinal: 128000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0016 §3. One harness module, `harness/runs_index.py`, reads the record's sources per scenario (deterministic; arms with n and model; the extra sources of scenarios.toml) and the run folders under `KG_DEMO_RUNS/<subject id>` (run.json, else inferred as `views.sources_for` does today); the page's `list_runs` and `sources_for` read through it. A read-only tool `scenario_runs {scenario?, limit?}` returns per scenario its title and card line, `record`, `runs` newest first (id, mode, model, effort, as_of, started, finished, status, gate verdict, by), and `held` (version, stage, loaded at), plus `run_in_progress`. Replay is reported as what the record holds, never as a run. `store_status` gains `loaded_at`. While run.json shows a run loading the store, the scenario-reading tools refuse and name the run (F2). No path argument; one subject per process.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 scenario_runs on CargoQuote lists S1-S7 with the record's arms at n = 5 and S6's three sources; on J-F, C and D1-D5 deterministic only
- [x] #2 After a page run, the run appears with mode, as_of, by and a gate verdict equal to its deterministic.json
- [ ] #3 The page's /api/scenarios and /api/runs are unchanged byte for byte for the same folders (a test, and the stack job)
- [x] #4 While a run.json reads running for the server's subject, gate_verdict, three_valued_answer and evidence_bundle refuse naming the run
- [x] #5 Every tool still carries readOnlyHint; tools/check_mcp_server.py covers the new tool; instance/README.md's tool table and CHANGELOG updated
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/runs_index.py: the one reader of the run folders (record sources, run folders, run.json), with sources_for and list_runs as the page had them, scenario_runs for the tool, and liveness (heartbeat within STALE_S=120 of review.now(); close_stale at page start, coordinator 2026-11-04).
2. Page: views.sources_for and server.list_runs read through it; the Runner rewrites run.json with heartbeat_at every 30 s (run.json v2) and closes stale running files at start as failed, page restarted.
3. Store port: extraction_times read (both adapters); store_status.loaded_at.
4. MCP: scenario_runs {scenario?, limit?}, read-only, no path; gate_verdict, three_valued_answer, evidence_bundle refuse while the subject's run.json is live, naming the run.
5. review.now(): KG_NOW, refused under KG_CLOCK=pinned without it; test_clock names it.
6. Tests (AC 1-5), tools/check_mcp_server.py check_runs, a stack step (scenario_runs after the page run; /api/runs and /api/scenarios against the old readers), instance/README.md, CHANGELOG.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Heartbeat rule per the coordinator (2026-11-04), not a pid: a reader in another container shares only the runs volume. run.json v2 adds heartbeat_at (schema version enum 1|2, since the schema refuses unknown fields); the Runner's _heartbeat thread rewrites it every 30 s under a lock the end write shares, so no beat lands after the end. runs_index.is_live: running and heartbeat (else started, v1) within 120 s of review.now(); now() is read only when a running run.json exists, so a pinned reader with none never asks the clock. close_stale at page start: failed, error 'page restarted'. The refusal covers gate_verdict, three_valued_answer, evidence_bundle (the AC); register_impact and proposal_impact still read levels mid-run (NEXT). scenario_runs during a live run skips the store (store_skipped). Evidence: tests/test_scenario_runs.py (11 tests); tools/check_mcp_server.py check_runs on rdflib (CargoQuote S1, S6; J-F C) every check holds; both suites 417/417; rdflib comparator 0 differing.
<!-- SECTION:NOTES:END -->
