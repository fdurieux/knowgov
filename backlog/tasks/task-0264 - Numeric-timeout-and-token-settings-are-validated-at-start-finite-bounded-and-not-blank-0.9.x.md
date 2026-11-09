---
id: TASK-0264
title: >-
  Numeric, timeout and token settings are validated at start: finite, bounded
  and not blank (0.9.x)
status: Done
assignee: []
created_date: '2026-11-09T09:32:00Z'
updated_date: '2026-11-09T16:01:00Z'
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
- [x] #1 One parser reads numeric settings: a value must be finite and within the setting's bounds, or it is refused at start naming the setting (exit 2), as `KG_MCP_MAX_RESPONSE` already is. Every setting above uses it, and a test lists them.
- [x] #2 Every startup failure of `mcp_server`, `mcp_runs` and the page (limits, port, bind) exits 2 naming its cause.
- [x] #3 A token that is blank once stripped reads as unset, so a wide bind refuses and writes refuse.
- [x] #4 The defaults and the record are unchanged.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Re-probe and spot check at main 9861953 (decision-0032 points 4 and 5, task-0256): group 1 re-confirmed N3 (KG_MCP_PORT abc, 99999, -1, 18766.0: traceback, exit 1), N4 (KG_MCP_HOST=0.0.0.0 with KG_MCP_TOKEN=' ' starts, the wide-bind check passed) and N5 (KG_SUBJECT_CALL_TIMEOUT nan, inf, 0, abc start the server). Pulled forward before the 0.9.0 cut by the coordinator: AC #3 breaks the documented promise that a wider bind needs a token.

Built on claude/task-0264-settings-validated. harness/settings.py (modelled on switches.py): NUMBERS lists every numeric setting with its kind, bounds and default; parse refuses a value that is not its kind, not finite or out of bounds with BadSetting naming the setting; check reads a set at start; port reads a listening port (0, the system's choice, to 65535); token reads a token blank once stripped as unset; neo4j_uri checks KG_NEO4J_URI's port (1 to 65535). Readers: Limits.from_env (MAX_BODY, READ_TIMEOUT, IDLE_TIMEOUT, MAX_CONNECTIONS for KG_MCP and KG_PAGE), mcp_server route_to_child (KG_SUBJECT_CALL_TIMEOUT), store_rdflib (KG_RDFLIB_LOCK_TIMEOUT, 0 kept), execution (KG_WORKER_JOB_SECONDS), worker._num (KG_WORKER_MAX_JOB_SECONDS, MEMORY, PROCESSES, FILE_BYTES), store_neo4j (the URI's port), mcp_server --port and KG_MCP_PORT, the page's KG_DEMO_PORT. Starts: mcp_server checks MCP_SETTINGS and its limits (exit 2 'cannot start: <line>'), --port by argparse (exit 2); mcp_runs KG_SUBJECT_CALL_TIMEOUT; the page PAGE_SETTINGS, page_limits, the URI's port and a failed bind; the worker WORKER_SETTINGS. Tokens: KG_MCP_TOKEN (wide bind), KG_PAGE_TOKEN (page_token, mcp_runs' Page). Tests: tests/test_settings.py (8; the re-probe's forms as subprocess runs, each exit 2 naming the setting with no traceback; the blank token on both; the defaults equal the old constants and Limits). Local, CPython 3.13 with rdflib: run_tests 970/1022 (52 skipped) default and 969/1022 (53 skipped) J-F, 0 failed; check_mcp_server --scenarios S1,S2,S6 with check_transports every check holds; check_round_trip --chain rdflib,rdflib every answer survives; the CQ comparator 0 differing leaves: the record held.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Numeric settings and tokens are read through one parser (harness/settings.py): a value must be its kind, finite and within its bounds, else mcp_server, mcp_runs, the page and the worker stop at start with exit 2 and a line naming the setting, never a traceback or a silent default. It covers KG_SUBJECT_CALL_TIMEOUT, KG_RDFLIB_LOCK_TIMEOUT, KG_WORKER_JOB_SECONDS and the worker's limits, KG_MCP_PORT, KG_DEMO_PORT and --port, each transport's body, timeout and connection limits, and KG_NEO4J_URI's port. A token blank once stripped reads as unset, so a wide bind refuses and writes refuse. Defaults unchanged; fix-only; the record holds.
<!-- SECTION:FINAL_SUMMARY:END -->
