---
id: TASK-0264
title: >-
  Numeric, timeout and token settings are validated at start: finite, bounded
  and not blank (0.9.x)
status: To Do
assignee: []
created_date: '2026-11-09T09:32:00Z'
updated_date: '2026-11-09T15:38:00Z'
labels:
  - validation
  - correctness
dependencies: []
references:
  - backlog/decisions/decision-0032
  - task-0256
priority: medium
ordinal: 258000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
These settings are read without validation:
- `KG_SUBJECT_CALL_TIMEOUT` is read per call. nan, inf or 1e400 give `subprocess.run` no timeout, which disables U2's bound; 0 or -1 time every call out.
- `KG_RDFLIB_LOCK_TIMEOUT`: nan waits nothing, and inf waits forever.
- `KG_WORKER_JOB_SECONDS`: nan refuses every job, and the worker's `_num` takes the default for garbage.
- `KG_NEO4J_URI`: port 99999 wraps.
- `Limits.from_env` accepts nan and inf for the MCP's and the page's read and idle timeouts. nan drops every request; inf disables the absolute deadline that `docs/security.md` promises.

Startup failures exit 1 with a traceback: `mcp_server --http` with `KG_MCP_MAX_BODY=-5`, `KG_MCP_MAX_CONNECTIONS=0`, `KG_MCP_READ_TIMEOUT=-1`, `KG_MCP_PORT=abc` or `--port 70000`.

A whitespace-only `KG_MCP_TOKEN` or `KG_PAGE_TOKEN` permits a wide bind and passes a blank bearer.

These are fix-only.

Source: group 1 F13, and group 2 F7, F8 and F9, decision-0032 (task-0256), probed on main 2a8bbeb.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 One parser reads numeric settings: a value must be finite and within the setting's bounds, or it is refused at start naming the setting (exit 2), as `KG_MCP_MAX_RESPONSE` already is. Every setting above uses it, and a test lists them.
- [ ] #2 Every startup failure of `mcp_server`, `mcp_runs` and the page (limits, port, bind) exits 2 naming its cause.
- [ ] #3 A token that is blank once stripped reads as unset, so a wide bind refuses and writes refuse.
- [ ] #4 The defaults and the record are unchanged.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Re-probe and spot check at main 9861953 (decision-0032 points 4 and 5, task-0256): group 1 re-confirmed N3 (KG_MCP_PORT abc, 99999, -1, 18766.0: traceback, exit 1), N4 (KG_MCP_HOST=0.0.0.0 with KG_MCP_TOKEN=' ' starts, the wide-bind check passed) and N5 (KG_SUBJECT_CALL_TIMEOUT nan, inf, 0, abc start the server). Pulled forward before the 0.9.0 cut by the coordinator: AC #3 breaks the documented promise that a wider bind needs a token.
<!-- SECTION:NOTES:END -->
