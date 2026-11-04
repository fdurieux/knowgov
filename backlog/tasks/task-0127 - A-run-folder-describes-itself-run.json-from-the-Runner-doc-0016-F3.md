---
id: TASK-0127
title: 'A run folder describes itself: run.json from the Runner (doc-0016 F3)'
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T20:09:00Z'
updated_date: '2026-11-04T21:23:00Z'
labels:
  - runs
  - page
milestone: m-8
dependencies: []
priority: medium
type: enhancement
ordinal: 127000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0016 §2 F3. A run's status, start, end, exit code and initiator live in the page's `Runner` memory and are lost on restart; mode, model and as_of are inferred from the run files. The Runner writes `runs/<subject>/<stamp>/run.json` at start and at end: id, subject, scenario, mode, n, row, model, effort, as_of, started, finished, status, exit_code, `by` (page or mcp). Never a key or a token. The page's run list reads it when present and infers as today when absent. Prerequisite of task-0128 and of a run tool (doc-0016 item 2).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Runner.start writes run.json with status running; the run's end rewrites it with finished, status and exit_code; a run that fails to start leaves a run.json with status failed
- [x] #2 run.json carries no secret: a test fails if any value names a key variable's value or KG_PAGE_TOKEN
- [x] #3 The page's /api/runs reads run.json where present and is unchanged for a folder without one; the stack job's run steps pass
- [x] #4 A JSON Schema under harness/schemas/ pins run.json, checked by harness/schema_check.py in a test
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. demo/app/server.py: Runner writes run.json (write_run_json, atomic) at start (status running) and at end (finished, status, exit_code); a Popen failure leaves status failed and refuses the start. Fields from the record minus log text, env and absolute paths; by (page|mcp), POST /api/run takes by.
2. harness/schemas/run.schema.json pins it; test validates through schema_check.
3. list_runs: a folder with run.json carries it as run, and its mode; without one, unchanged.
4. Tests: start/end/failed, no secret (key var value, KG_PAGE_TOKEN), list_runs with and without; CHANGELOG Unreleased.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Runner.start writes run.json (write_run_json, by a rename) before the spawn; _wait rewrites it at the end; an OSError on spawn writes failed with error and raises RuntimeError (409). Fields are RUN_JSON_FIELDS plus the log's file name: no env, log text, out_dir or cmd. by in RUN_BY (page, mcp); POST /api/run takes by. list_runs adds run and takes modes from it; unchanged without one. Evidence: tests/test_run_json.py (5 tests); both suites 384/384; rdflib comparator 0 differing; PR #214 tests, rdflib and stack green at e8b14ab, the stack step reading run.json and /api/runs' run.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
A run folder now describes itself: the page's Runner writes runs/<subject>/<stamp>/run.json at start (running) and end (done/failed, exit_code, finished); a spawn failure leaves failed with an error. It carries by (page|mcp), never a key, a token or the environment. harness/schemas/run.schema.json pins it (version 1). /api/runs carries it as run where present, unchanged otherwise. Verified by tests/test_run_json.py, both suites, the rdflib comparator and the stack job (PR #214). Follow-ups: task-0128 reads it through harness/runs_index.py; task-0133 sends by=mcp.
<!-- SECTION:FINAL_SUMMARY:END -->
