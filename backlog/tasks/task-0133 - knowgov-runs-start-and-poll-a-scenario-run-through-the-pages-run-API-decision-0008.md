---
id: TASK-0133
title: >-
  knowgov-runs: start and poll a scenario run through the page's run API
  (decision-0008)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T20:56:00Z'
updated_date: '2026-11-05T00:30:00Z'
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
- [x] #1 Tests on a stub page: a mode not in KG_MCP_RUN_MODES is refused; n is never above 1; a second start is refused with the page's message; the token is passed and never echoed; start_run carries readOnlyHint false and destructiveHint true
- [x] #2 Stack job: start a deterministic S1, poll to done, then the reader's gate_verdict on S1 gives PROCEED and scenario_runs (task-0128, once built) lists the run with by mcp
- [x] #3 knowgov's tools/list is unchanged: every tool read-only; managed-mcp-allowlist.json still admits the reader only
- [x] #4 The reader re-opens its handle after a run's end recorded in run.json, so a gate call after an agent's run reads the new load (test on rdflib)
- [x] #5 instance/README.md section on knowgov-runs (adopter register): what it does, the modes, the spend and the shared store; CHANGELOG under Unreleased
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. mcp_server.Server takes a tool table, server info and instructions (defaults: the reader's).
2. harness/mcp_runs.py, knowgov-runs, stdio only: Page client (KG_PAGE_URL, KG_PAGE_TOKEN sent as Bearer, redacted from every reply), run_options (GET /api/scenarios), start_run (POST /api/run, n=1, by mcp, modes from KG_MCP_RUN_MODES, deterministic by default; row/effort only for arms), run_status (GET /api/run, else /api/runs' run.json). start_run annotated not read-only, destructive, not idempotent, open-world only when arms are allowed.
3. Reader re-open (F6): the reader opens the store per call (task-0097 not built), so the next call reads a run's new load; a test on rdflib holds it.
4. Tests on a stub page (AC1), the reader unchanged and the allowlist (AC3), the rdflib re-read (AC4); a stack step (AC2); instance/README.md section, CHANGELOG (AC5); the page's banner names a run started over MCP.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Built as planned. The reader opens the store per call (task-0097 not built), so F6 needs no re-open: tests/test_mcp_runs.py's rdflib test reads a run's new load on the next call. Token redacted from replies, errors and log tails; no Origin header (the page refuses another origin). tests/test_security.py names harness/mcp_runs.py a client of the local page. PR #225 green at 67c1c7a: tests, rdflib, stack (the step runs S1 through knowgov-runs over stdio, the reader's gate_verdict PROCEED, scenario_runs lists it by mcp).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
knowgov-runs (harness/mcp_runs.py), a second stdio MCP server per decision-0008, starts and polls scenario runs through the page's own run API: run_options (read-only), start_run (n = 1, by mcp, KG_MCP_RUN_MODES deterministic by default, arms only when named; not read-only, destructive, not idempotent), run_status. KG_PAGE_URL/KG_PAGE_TOKEN from the environment; the token is never echoed. mcp_server.Server takes a tool table; the reader and the shipped allowlist are unchanged. The page's banner names an MCP-started run. Verified by tests/test_mcp_runs.py, both suites and the stack step (PR #225).
<!-- SECTION:FINAL_SUMMARY:END -->
