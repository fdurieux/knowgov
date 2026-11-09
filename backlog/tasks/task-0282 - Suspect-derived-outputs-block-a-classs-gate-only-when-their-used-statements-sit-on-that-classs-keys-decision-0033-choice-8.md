---
id: TASK-0282
title: >-
  Suspect derived outputs block a class's gate only when their used statements
  sit on that class's keys (decision-0033 choice 8)
status: To Do
assignee: []
created_date: '2026-11-09T10:10:00Z'
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
- [ ] #1 A suspect derived output is a blocker for a class's gate only when at least one of its invalidated used statements sits on one of that class's keys. Otherwise it is listed at info, with the output and its keys named.
- [ ] #2 Group 3's reproduction no longer exits 1 under `design` for the `codegen` output, and the same run under `codegen` still does.
- [ ] #3 The record does not move: the comparator, S6's stage-2 gates, `check_gate_after_change` and `check_trace_walkthrough`.
- [ ] #4 `CHANGELOG.md`'s Unreleased section names the change under Contract changes.
<!-- AC:END -->
