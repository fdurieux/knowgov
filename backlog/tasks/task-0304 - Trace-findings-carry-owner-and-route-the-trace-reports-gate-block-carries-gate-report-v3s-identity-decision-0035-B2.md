---
id: TASK-0304
title: >-
  Trace findings carry owner and route; the trace report's gate block carries
  gate-report v3's identity (decision-0035 B2)
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
ordinal: 297000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Under decision-0035, accepted 2026-11-09 ("Option (A)", doc-0037 §3.4). Found by the functional review, group B, at main f194aac.

Trace-report findings carry no `owner` or `route`, and the trace report's `gate` block (`additionalProperties: false`) has no `task_profile`, `register` or `knowgov`, unlike gate-report v3 (decision-0029). A suspect-code annotation cannot name who answers, and an auditor (U5) cannot see what the trace decided on.

Repro: `$T/tw/trace-stage2.json`'s findings, after `tools/check_trace_walkthrough.py $T/tw`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Each trace finding that rests on keys carries the keys' `owner` and `route`, as the gate report's key findings do (task-0102); a finding with no key names none.
- [ ] #2 The trace report's gate block carries `task_profile`, `register` and `knowgov`, read as the gate report reads them.
- [ ] #3 The trace-report schema, the CI annotations (`harness/annotate.py`) and the docs say so, and `check_trace_walkthrough` holds the fields.
- [ ] #4 The record does not move, and a CHANGELOG line names it under Contract changes.
<!-- AC:END -->
