---
id: TASK-0292
title: >-
  held_keys' gate equals gate_verdict on a store that holds no key too
  (decision-0033 choice 9)
status: To Do
assignee: []
created_date: '2026-11-09T15:43:00Z'
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
- [ ] #1 `held_keys`' `gate` is computed whatever the store holds, and equals `gate_verdict`'s verdict and why on every subject, scenario, stage and task class, minimal S0 included.
- [ ] #2 The held-keys schema's `gate` description no longer says null for an empty store; its type stays object or null, and the tool's description says when null remains (no task class).
- [ ] #3 `check_mcp_server.py` holds the equality on minimal S0 beside CargoQuote and J-F, and the reproduction is a test.
- [ ] #4 The record does not move.
- [ ] #5 `CHANGELOG.md`'s Unreleased section names the change under Contract changes.
<!-- AC:END -->
