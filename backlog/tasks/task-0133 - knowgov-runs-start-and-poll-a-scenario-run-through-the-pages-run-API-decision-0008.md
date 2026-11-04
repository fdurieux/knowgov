---
id: TASK-0133
title: >-
  knowgov-runs: start and poll a scenario run through the page's run API
  (decision-0008)
status: To Do
assignee: []
created_date: '2026-11-04T20:56:00Z'
labels:
  - mcp
  - runs
milestone: m-8
dependencies:
  - TASK-0127
priority: medium
type: feature
ordinal: 133000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0016 §4, decision-0008 (accepted 2026-11-04). A second stdio MCP server, `knowgov-runs`, a client of the page's `POST /api/run` and `GET /api/run` (`KG_PAGE_URL`, default http://localhost:8080 in the container; `KG_PAGE_TOKEN`). Tools: `run_options` (read-only: the allowed modes, the model rows and their availability, never a key), `start_run {scenario, mode, row?, effort?, as_of?}` (n fixed at 1; refused while another run is under way, with the page's message), `run_status {run?}` (status, elapsed, the log's tail, and when done the summary and the source id `scenario_result` reads). `KG_MCP_RUN_MODES` = deterministic by default; arms only when the operator names it, on a row whose key variable is set. The protocol layer is shared with `mcp_server.py` (`Server` takes a tool table). The reader re-opens its store handle when run.json records a run's end (doc-0016 F6, task-0097). Runs carry `by: mcp`. The shipped allowlist keeps admitting the reader only.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Tests on a stub page: a mode not in KG_MCP_RUN_MODES is refused; n is never above 1; a second start is refused with the page's message; the token is passed and never echoed; start_run carries readOnlyHint false and destructiveHint true
- [ ] #2 Stack job: start a deterministic S1, poll to done, then the reader's gate_verdict on S1 gives PROCEED and scenario_runs (task-0128, once built) lists the run with by mcp
- [ ] #3 knowgov's tools/list is unchanged: every tool read-only; managed-mcp-allowlist.json still admits the reader only
- [ ] #4 The reader re-opens its handle after a run's end recorded in run.json, so a gate call after an agent's run reads the new load (test on rdflib)
- [ ] #5 instance/README.md section on knowgov-runs (adopter register): what it does, the modes, the spend and the shared store; CHANGELOG under Unreleased
<!-- AC:END -->
