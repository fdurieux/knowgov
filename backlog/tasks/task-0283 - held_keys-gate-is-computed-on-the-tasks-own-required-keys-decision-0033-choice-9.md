---
id: TASK-0283
title: >-
  held_keys' gate is computed on the task's own required keys (decision-0033
  choice 9)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-09T10:10:00Z'
updated_date: '2026-11-09T12:24:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0033
  - task-0256
priority: high
ordinal: 276000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
`held_keys`' `gate` gates every held key (93 on CargoQuote S1) under the task's bar and calls them "required". It reads "codegen BLOCKED" where `gate_verdict` gives codegen PROCEED.

Under decision-0033 (accepted 2026-11-09, "all as advised") choice 9(a), the field is computed on the task's own required keys, so it equals `gate_verdict`'s verdict on the same store, task and `as_of`.

Source: validation-pass group 2 F5, task-0256.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `held_keys`' `gate` equals `gate_verdict`'s verdict and `why` for the same store, task and `as_of`, on CargoQuote S1, S4 and S6 under `codegen` and `design`, and on J-F C.
- [x] #2 The tool's description and the held-keys schema's wording say what the field is.
- [x] #3 `check_mcp_server` holds it, and the record does not move.
- [x] #4 `CHANGELOG.md`'s Unreleased section names the change under Contract changes.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. store_reads.held_keys: levels from the held key set as before; the gate field from a second gate_cli.evaluate on TASKS[task] itself, with gate_verdict's arguments (threshold blocker, no baseline, the held version, the as_of, route_task).
2. The held_keys tool description and the held-keys schema's gate description say what the field is.
3. check_mcp_server: held_keys' gate equal to gate_verdict's verdict and why under every task class, every scenario (held_gate_failures, its own function to keep the ratchet).
4. A stdlib test on a stubbed gate; CHANGELOG under Unreleased, Contract changes.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Evidence (a8eea08, over main ee84120): the new check_mcp_server check failed on the old store_reads at S1 (held_keys codegen BLOCKED "34 of 93 required keys (37%) are below verified" where gate_verdict gives PROCEED; design BLOCKED where gate_verdict gives QUALIFIED). With the fix check_mcp_server holds on every CargoQuote scenario (S1, S4, S6 among them, S6 at stage 2 too) and every J-F scenario (C among them), under every task class (codegen and design on CargoQuote). tests/test_held_keys_gate.py, 3 stdlib tests on a stubbed gate; the core one fails on the old code. Comparator 0 diffs on CargoQuote S1-S7 and J-F (6); check_round_trip --chain rdflib,rdflib on both subjects; complexity --check holds with no raise (the new check is its own function, held_gate_failures). Suites: bare 882/939, J-F bare 881/939, pinned 937/939, J-F pinned 934/939, 0 failed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
held_keys' gate is now the task class's own verdict and why on its own required keys, computed by a second gate_cli.evaluate with gate_verdict's arguments; the keys' levels are still the held key set's. On CargoQuote S1 it read codegen BLOCKED (34 of 93) where gate_verdict gives PROCEED; it now equals gate_verdict for every scenario and task class on both subjects, as check_mcp_server holds. The tool's description and the held-keys schema say what the field is; CHANGELOG under Unreleased, Contract changes. The record does not move.
<!-- SECTION:FINAL_SUMMARY:END -->
