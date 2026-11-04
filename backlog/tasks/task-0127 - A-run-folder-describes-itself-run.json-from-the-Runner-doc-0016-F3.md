---
id: TASK-0127
title: 'A run folder describes itself: run.json from the Runner (doc-0016 F3)'
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-04T20:09:00Z'
updated_date: '2026-11-04T21:00:00Z'
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
- [ ] #1 Runner.start writes run.json with status running; the run's end rewrites it with finished, status and exit_code; a run that fails to start leaves a run.json with status failed
- [ ] #2 run.json carries no secret: a test fails if any value names a key variable's value or KG_PAGE_TOKEN
- [ ] #3 The page's /api/runs reads run.json where present and is unchanged for a folder without one; the stack job's run steps pass
- [ ] #4 A JSON Schema under harness/schemas/ pins run.json, checked by harness/schema_check.py in a test
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. demo/app/server.py: Runner writes run.json (write_run_json, atomic) at start (status running) and at end (finished, status, exit_code); a Popen failure leaves status failed and refuses the start. Fields from the record minus log text, env and absolute paths; by (page|mcp), POST /api/run takes by.
2. harness/schemas/run.schema.json pins it; test validates through schema_check.
3. list_runs: a folder with run.json carries it as run, and its mode; without one, unchanged.
4. Tests: start/end/failed, no secret (key var value, KG_PAGE_TOKEN), list_runs with and without; CHANGELOG Unreleased.
<!-- SECTION:PLAN:END -->
