---
id: TASK-0292
title: >-
  held_keys' gate equals gate_verdict on a store that holds no key too
  (decision-0033 choice 9)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-09T15:43:00Z'
updated_date: '2026-11-09T16:52:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0032
  - task-0256
  - backlog/decisions/decision-0033
  - task-0283
priority: high
ordinal: 285000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0033 choice 9(a), accepted 2026-11-09, computes `held_keys`' `gate` on the task's own required keys "so it equals `gate_verdict`'s verdict on the same store". task-0283 built it, and group 2's re-probe found it equal on CargoQuote (32 of 32, S6 stage 2 included) and J-F (12 of 12), on rdflib and Neo4j.

On a store that holds no key it is not. On minimal S0 (no statement held) `gate` is null where `gate_verdict` codegen is BLOCKED ("2 required key(s) at a blocking level…"). That is exactly where the class blocks. The cause: in `harness/store_reads.py` `held_keys`, the class's own `gate_cli.evaluate` (the `own` verdict) sits inside `if keys:`. The schema's "null when the store holds no key" was task-0283's wording, not the decision's.

Reproduction: `KG_SUBJECT=subjects/minimal KG_TODAY=2026-11-04`, `gate_cli.py --scenario S0 --publish`, then `Tools().held_keys({})["gate"]` is None.

Contract-bearing: it finishes task-0283's change and moves a schema description. Source: the bounded re-probe (decision-0032 point 4, task-0256), group 2 at main 9861953 (N1).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `held_keys`' `gate` is computed whatever the store holds, and equals `gate_verdict`'s verdict and why on every subject, scenario, stage and task class, minimal S0 included.
- [x] #2 The held-keys schema's `gate` description no longer says null for an empty store; its type stays object or null, and the tool's description says when null remains (no task class).
- [x] #3 `check_mcp_server.py` holds the equality on minimal S0 beside CargoQuote and J-F, and the reproduction is a test.
- [x] #4 The record does not move.
- [x] #5 `CHANGELOG.md`'s Unreleased section names the change under Contract changes.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. store_reads.held_keys: the class's own evaluation runs whatever the store holds; null only when the subject declares no task class.
2. The held-keys schema drops "null when the store holds no key"; the tool description says when null remains.
3. check_mcp_server --held-gate-only, run on minimal in harness.yml; tests.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Evidence: on the old code minimal S0's held_keys gate read None where gate_verdict gives BLOCKED (check_mcp_server --held-gate-only fails); with the fix both BLOCKED. check_mcp_server holds on every CargoQuote and J-F scenario (re-run on S1, S4, S6 and C after the merge). tests/test_held_keys_gate.py: the empty store and the no-class case. complexity: check_mcp_server.py::main 42 to 43 for the --held-gate-only dispatch, recorded with its reason. Record unmoved, suites as task-0286's.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
held_keys' gate is now gate_verdict's verdict and why whatever the store holds: minimal S0, holding no key, reads BLOCKED in both. It is null only when the subject declares no task class (where it raised before), as the tool description says; the schema no longer promises null for an empty store. check_mcp_server --held-gate-only holds it on minimal in harness.yml.
<!-- SECTION:FINAL_SUMMARY:END -->
