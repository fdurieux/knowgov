---
id: TASK-0298
title: >-
  The settings parser refuses non-ASCII digits, padding and a malformed Neo4j
  URI; the page's per-request settings are checked at start; the settings scan
  reaches every folder that holds code (0.9.x)
status: To Do
assignee: []
created_date: '2026-11-09T19:01:00Z'
labels:
  - validation
  - correctness
dependencies: []
references:
  - backlog/decisions/decision-0032
  - task-0256
priority: medium
ordinal: 291000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Source: the re-check of the pass's second-round fixes (decision-0032 point 4, task-0256), groups 1 and 2 at main 0682e16 and c94dfa5. Fix-only: no contract changes.

- F-a: `settings.number` and `KG_MCP_PORT` read non-ASCII digits: `KG_MCP_PORT=０8802` binds 8802, `KG_WORKER_JOB_SECONDS=９00` reads 900. Dates (task-0262) and the Neo4j URI's port refuse them.
- F-b: number settings accept padding (`' 18801'`, `' 300'`), while task-0287 refuses padding for switches.
- F-c: a one-character `KG_MCP_TOKEN` is accepted on a wide bind, and a token with surrounding spaces is taken as given.
- F-d: `settings.neo4j_uri` accepts `notaurl`; the driver refuses it at open (exit 2).
- N5 (group 2): `KG_PUBLIC_PORT=abc` is not checked at start; the page starts, then drops every request (`page_policy`'s `int()` raises in `_boundary`).
- N6 (group 2): `KG_PAGE_MAX_RUNS` (`abc`, `nan`, `0`) is not checked at start; every run gets 400 with the raw error.
- B2-4 (group 1): `tests/test_settings_table.py`'s scan reads `harness/`, `demo/app/`, `tools/`, `instance/` and the compose files only, and skips files with no suffix. It misses `KG_ORACLE_TIMEOUT` (`subjects/jef_data_load/oracle/jef_suite.py`, read with `int()` unchecked) and `KG_DEMO_URL` (`demo/tools/`).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Number settings take ASCII digits only and refuse padding, one rule with the switches; a test lists the forms.
- [ ] #2 A token is refused on a wide bind when shorter than a stated minimum or padded; the minimum is documented.
- [ ] #3 `settings.neo4j_uri` refuses a URI without a scheme and host, exit 2 at start.
- [ ] #4 `KG_PUBLIC_PORT` and `KG_PAGE_MAX_RUNS` are read through `harness/settings.py` at the page's start, exit 2 on a bad value.
- [ ] #5 The settings scan also reads `subjects/*/oracle`, `demo/tools`, `demo/neo4j` and `demo/Dockerfile`, and `KG_ORACLE_TIMEOUT` and `KG_DEMO_URL` each have a row or an INTERNAL entry with its reason; `KG_ORACLE_TIMEOUT` is read through the parser.
- [ ] #6 No contract changes; the record does not move.
<!-- AC:END -->
