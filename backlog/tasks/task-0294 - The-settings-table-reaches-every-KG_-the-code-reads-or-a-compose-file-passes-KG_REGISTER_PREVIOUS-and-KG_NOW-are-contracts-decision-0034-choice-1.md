---
id: TASK-0294
title: >-
  The settings table reaches every KG_* the code reads or a compose file passes;
  KG_REGISTER_PREVIOUS and KG_NOW are contracts (decision-0034 choice 1)
status: To Do
assignee: []
created_date: '2026-11-09T16:51:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0034
  - backlog/decisions/decision-0032
  - task-0256
priority: high
ordinal: 287000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Under decision-0034 (accepted 2026-11-09, "N7, D1, D3 as advised") choice 1(b).

The code reads 41 `KG_*` names the 75-row table in `instance/README.md` does not list (group 1's N7 at 9861953, checked by the coordinator). Among them:
- a shipped compose file passes `KG_REGISTER_PREVIOUS` (`demo/docker-compose.instance.yml`), `KG_ARMS_EFFORT`, `KG_OUTCOMES`, `KG_PORT_BOLT` and `KG_BUILD_COMMIT`/`KG_BUILD_DESCRIBE`;
- the operator-facing knobs are the worker's own limits (`KG_WORKER_MEMORY`, `KG_WORKER_PROCESSES`, `KG_WORKER_FILE_BYTES`, `KG_WORKER_MAX_JOB_SECONDS`), the servers' boundary limits (`KG_MCP_`/`KG_PAGE_` `MAX_BODY`, `MAX_CONNECTIONS`, `IDLE_TIMEOUT`, `READ_TIMEOUT`), `KG_PAGE_LISTEN`, the `KG_AGENT_*` ceilings, `KG_TRACEBACK`, `KG_DEMO_RUNS` and `KG_DEMO_PORT`;
- `KG_NOW` is the clock's instant, which `KG_CLOCK=pinned` requires for the live-run read;
- the rest are internal or test-only (`KG_MUTANT`, `KG_NS`, `KG_ROOT`, `KG_TEST_REPORT`, `KG_UNLISTED_`, `KG_QUALITY_REF`, `KG_THINKING_UNCOUNTED`, `KG_ANTHROPIC_KEY`, `KG_TRANSCRIPT_CHECK_NO_KEY`, and the `KG_MODEL_`/`KG_NEO4J_`/`KG_MCP`/`KG_PAGE` prefixes).

Rows: `KG_REGISTER_PREVIOUS` and `KG_NOW` are contracts; every other compose-passed setting and operator-facing knob is "no" with its reason (`KG_ARMS_EFFORT`: its values are the model API's).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `instance/README.md`'s table has a row for every setting a shipped compose file passes and every operator-facing knob listed in the description, `KG_REGISTER_PREVIOUS` and `KG_NOW` marked contracts and the rest "no" with a reason.
- [ ] #2 `tests/test_settings_table.py` fails on any `KG_*` the code reads (harness/, demo/app/, tools/, instance/) or a compose file under demo/ passes that has neither a row nor an entry, with its reason, on an explicit internal list in the test.
- [ ] #3 The README's settings paragraph says the table reaches every setting the code reads or a compose file passes, citing decision-0034 choice 1.
- [ ] #4 `CHANGELOG.md`'s Unreleased section names the two new contracts under Contract changes.
<!-- AC:END -->
