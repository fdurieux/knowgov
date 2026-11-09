---
id: TASK-0303
title: >-
  code_path's ledger leg returns the assertion ids and keys, and the leg's
  suspect state (decision-0035 B1)
status: To Do
assignee: []
created_date: '2026-11-09T21:29:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0035
  - backlog/docs/doc-0037
priority: high
ordinal: 296000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Under decision-0035, accepted 2026-11-09 ("Option (A)", doc-0037 §3.4). Found by the functional review, group B, at main f194aac.

`code_path`'s ledger leg returns `entry.assertions` as a count (88) and `keys` as a count, though the ledger holds both the assertion ids and the keys. So "this generated file → its keys → key_nodes" breaks over MCP. `derived_outputs` cannot stand in, because a load wipes the store's registration (the trace walkthrough's step 4). The leg has no suspect state either, only drift.

Repro: `tools/check_trace_walkthrough.py $T/tw`, then `harness/upward.py code --instance $T/tw/inst --ledger $T/tw/ledger.json reference_impl.py`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `code_path`'s ledger leg returns the entry's assertion ids and its keys, sorted, and states whether the entry is suspect, drifted or current, as `trace check` reads it.
- [ ] #2 The code-path schema says so, and `check_mcp_server` holds the leg's ids and keys on the walkthrough's ledger.
- [ ] #3 From the returned keys, `key_nodes` reaches the register's nodes in a test: file → keys → nodes.
- [ ] #4 The record does not move, and a CHANGELOG line names it under Contract changes.
<!-- AC:END -->
