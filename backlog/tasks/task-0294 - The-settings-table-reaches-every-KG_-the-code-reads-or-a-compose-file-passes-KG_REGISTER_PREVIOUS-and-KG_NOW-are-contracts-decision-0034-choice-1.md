---
id: TASK-0294
title: >-
  The settings table reaches every KG_* the code reads or a compose file passes;
  KG_REGISTER_PREVIOUS and KG_NOW are contracts (decision-0034 choice 1)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-09T16:51:00Z'
updated_date: '2026-11-09T17:25:00Z'
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
- [x] #1 `instance/README.md`'s table has a row for every setting a shipped compose file passes and every operator-facing knob listed in the description, `KG_REGISTER_PREVIOUS` and `KG_NOW` marked contracts and the rest "no" with a reason.
- [x] #2 `tests/test_settings_table.py` fails on any `KG_*` the code reads (harness/, demo/app/, tools/, instance/) or a compose file under demo/ passes that has neither a row nor an entry, with its reason, on an explicit internal list in the test.
- [x] #3 The README's settings paragraph says the table reaches every setting the code reads or a compose file passes, citing decision-0034 choice 1.
- [x] #4 `CHANGELOG.md`'s Unreleased section names the two new contracts under Contract changes.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Add rows to instance/README.md's settings table for every KG_* a shipped compose file passes and every operator-facing knob the description lists: KG_REGISTER_PREVIOUS and KG_NOW yes, the rest no with a reason (KG_ARMS_EFFORT: its values are the model API's).
2. tests/test_settings_table.py: every KG_* in harness/, demo/app/, tools/, instance/ or a compose file under demo/ needs a row or an INTERNAL entry with its reason; a compose-passed name needs a row; an entry with a row, or no longer read, fails; counts held.
3. tests/test_adopter_docs.py's nineteen-out test: decision-0034's fifteen may be named only by their own row, marked as decided; the other four stay out.
4. The settings paragraph says the table reaches every setting the code reads or a compose file passes, citing decision-0034 choice 1.
5. CHANGELOG Unreleased > Contract changes.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
PR #439, branch claude/task-0294-settings-reach. 30 rows added: 105 in all, 65 contracts (KG_REGISTER_PREVIOUS, KG_NOW new). INTERNAL holds 14 names, each with its reason (six prefixes, six test or tool internals, KG_NS a constant, KG_THINKING_UNCOUNTED set by the page from a model row). task-0275's TABLE_ONLY dropped: every row must be read by code, which the reach test already requires.
KG_ANTHROPIC_KEY and KG_PORT_BROWSER have rows, both no: the description lists KG_ANTHROPIC_KEY as internal and does not name KG_PORT_BROWSER, but demo/docker-compose.yml passes both and AC #1 and decision-0034 choice 1 give every compose-passed setting a row, which overrides the description's informal list (the coordinator, 2026-11-09).
Checks on the merge with main 2831a80: tools/complexity.py --check holds (1766, 180); stdlib suite 976/1029, 53 skipped (pins, hook-live), 0 failed; a new KG_* in harness/ fails the reach test naming it (mutation check). The record does not move.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
instance/README.md's settings table now reaches every KG_* setting the code reads or a compose file under demo/ passes (decision-0034 choice 1): 30 rows added, 105 in all, 65 contracts. KG_REGISTER_PREVIOUS (the instance compose file passes it) and KG_NOW (KG_CLOCK=pinned requires it for the live-run read) are contracts; the other 28 are no with a reason, KG_ARMS_EFFORT's being that its values are the model API's. tests/test_settings_table.py fails on any such name with neither a row nor an INTERNAL entry with its reason, on a compose-passed name kept internal, on an entry that has a row or is no longer read, and holds 65 of 105; test_adopter_docs admits decision-0034's fifteen of decision-0027's nineteen as table rows only. The settings paragraph cites decision-0034 choice 1; CHANGELOG under Unreleased > Contract changes. Checks: complexity --check holds; stdlib suite 976/1029, 53 skipped for missing pins, 0 failed; mutation check. Risk: a new KG_* read anywhere in the code now needs a row or a reasoned INTERNAL entry in the same PR.
<!-- SECTION:FINAL_SUMMARY:END -->
