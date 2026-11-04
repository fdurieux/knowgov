---
id: TASK-0128
title: >-
  scenario_runs: the subject's scenarios with the record and the runs per mode,
  a sixth read-only MCP tool (doc-0016 item 1)
status: To Do
assignee: []
created_date: '2026-11-04T20:09:00Z'
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
- [ ] #1 scenario_runs on CargoQuote lists S1-S7 with the record's arms at n = 5 and S6's three sources; on J-F, C and D1-D5 deterministic only
- [ ] #2 After a page run, the run appears with mode, as_of, by and a gate verdict equal to its deterministic.json
- [ ] #3 The page's /api/scenarios and /api/runs are unchanged byte for byte for the same folders (a test, and the stack job)
- [ ] #4 While a run.json reads running for the server's subject, gate_verdict, three_valued_answer and evidence_bundle refuse naming the run
- [ ] #5 Every tool still carries readOnlyHint; tools/check_mcp_server.py covers the new tool; instance/README.md's tool table and CHANGELOG updated
<!-- AC:END -->
