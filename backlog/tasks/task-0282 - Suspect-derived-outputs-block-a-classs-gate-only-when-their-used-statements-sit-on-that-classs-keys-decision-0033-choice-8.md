---
id: TASK-0282
title: >-
  Suspect derived outputs block a class's gate only when their used statements
  sit on that class's keys (decision-0033 choice 8)
status: Done
assignee: []
created_date: '2026-11-09T10:10:00Z'
updated_date: '2026-11-09T11:19:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0033
  - task-0256
priority: high
ordinal: 275000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
A `design` gate reads QUALIFIED with exit 1 because of a `codegen` output whose 15 invalidated statements sit on no `design` key. To reproduce: with `KG_REGISTER` set to `check_register_change`'s register-changed, run `gate_cli --scenario S1 --task design --register-previous demo/register`.

Under decision-0033 (accepted 2026-11-09, "all as advised") choice 8(a), blocker severity applies only to outputs whose used statements sit on the class's keys, and the rest are listed at info. The condition: the record must not move. If it would, the build stops and comes back to the maintainer.

Source: validation-pass group 3 CB6, task-0256.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A suspect derived output is a blocker for a class's gate only when at least one of its invalidated used statements sits on one of that class's keys. Otherwise it is listed at info, with the output and its keys named.
- [x] #2 Group 3's reproduction no longer exits 1 under `design` for the `codegen` output, and the same run under `codegen` still does.
- [x] #3 The record does not move: the comparator, S6's stage-2 gates, `check_gate_after_change` and `check_trace_walkthrough`.
- [x] #4 `CHANGELOG.md`'s Unreleased section names the change under Contract changes.
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Built in #420 (decision-0033 choice 8(a)). `gate_cli.evaluate` computes `suspect_scope`: for each suspect derived output, the keys its invalidated or changed used statements sit on (read through the port's `derived_outputs`), and whether any is one of the task class's keys. On them the output is a blocker as before. Off them it is an info finding naming the output and its keys, and `--baseline`'s `new_suspect` counts only on-task outputs. The classification is never stored in the gate's result, so `run.py`'s `gate_summary` and the record do not move.

Verification, after merging main (`ee84120`):
- `tests/test_suspect_scope.py`: with the register-changed fixture, `gate_cli` S1 `design` exits 0 with the `codegen` output at info, and `codegen` exits 1 with it a blocker.
- On rdflib: the comparator shows 0 differing leaves over seven scenarios, and `check_gate_after_change` (S6's stage-2 gates), `check_trace_walkthrough` and `check_register_change` all exit 0.
- The full suite passes 887/938 (51 skipped), and `tools/complexity.py --check` holds.
- CHANGELOG Unreleased names it under Contract changes; CLAUDE.md notes it beside task-0048.

The stack job carries the Neo4j side.
<!-- SECTION:FINAL_SUMMARY:END -->
