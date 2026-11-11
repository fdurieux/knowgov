---
id: TASK-0325
title: >-
  A [verification] declaration listing no Version is named by the gate (doc-0038
  §4 P2)
status: To Do
assignee: []
created_date: '2026-11-11T13:34:00Z'
labels:
  - integrity
  - 0.9.0
dependencies: []
priority: high
ordinal: 317000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Fix-only, pulled before the 0.9.0 cut under decision-0032 (completes decision-0036; the upgrade path). Redo group C's N2 (doc-0038 §4 P2). When [verification] execution or review lists no versions, the gate gives BLOCKED with 26 'validated, below verified' majors routed to questionnaires and no finding naming the cause; only check_subject's NOTE says it verifies nothing. authored and approval without versions already get info findings. An existing instance upgrading to 0.9.0 sees PROCEED turn BLOCKED unexplained. Fix: an attestation finding naming each declaration that lists no Version, with its route (P1's wording).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 With execution's versions removed, the gate reports an attestation finding naming [verification] execution and that it lists no Version; the same for review; a test each
- [ ] #2 The finding appears in the CLI report, MCP gate_verdict and the annotations alike
- [ ] #3 The record holds
<!-- AC:END -->
