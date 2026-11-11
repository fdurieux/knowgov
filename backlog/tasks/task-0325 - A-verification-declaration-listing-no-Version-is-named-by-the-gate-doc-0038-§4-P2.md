---
id: TASK-0325
title: >-
  A [verification] declaration listing no Version is named by the gate (doc-0038
  §4 P2)
status: Done
assignee: []
created_date: '2026-11-11T13:34:00Z'
updated_date: '2026-11-11T15:47:00Z'
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
- [x] #1 With execution's versions removed, the gate reports an attestation finding naming [verification] execution and that it lists no Version; the same for review; a test each
- [x] #2 The finding appears in the CLI report, MCP gate_verdict and the annotations alike
- [x] #3 The record holds
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Built in #480 (5555343) by session_01HTAA1UxBF2zxSbQtTZDKCD; recorded by the coordinator, the builder having no backlog CLI. gate.attestation_behind covers execution and review listing no versions; gate_cli.unlisted_finding. Re-checked by group C: FIXED in the CLI, MCP gate_verdict and the annotations; NOT in knowgov_hook.py, which drops non-blocker findings (H1), plus a placeholder digest (H2) and info severity (H3): all task-0330.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
A [verification] execution or review declaration listing no Version is an attestation finding naming it, in the CLI report, MCP gate_verdict and the annotations alike. Test: test_declaration_listing_no_version_is_an_attestation_finding; the record holds. The hook, the digest it names and its severity are task-0330.
<!-- SECTION:FINAL_SUMMARY:END -->
