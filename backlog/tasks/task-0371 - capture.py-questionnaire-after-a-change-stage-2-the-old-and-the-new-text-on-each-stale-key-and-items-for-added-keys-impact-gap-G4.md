---
id: TASK-0371
title: >-
  capture.py questionnaire after a change: stage 2, the old and the new text on
  each stale key, and items for added keys (impact gap G4)
status: In Progress
assignee: []
created_date: '2026-11-18T07:35:00Z'
updated_date: '2026-11-27T18:09:57Z'
labels:
  - impact
  - reverse-engineering
  - contract
  - 0.10.0
dependencies: []
priority: high
ordinal: 360000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Source: a private instance's impact and traversal study (2026-11-17), gap G4.

`capture.py questionnaire` loads stage 1 only. After a document's new version invalidates statements, the regenerated questionnaire asks the same keys with version 1's text and nothing about the keys the new version adds. In the study it re-asked 137 keys in the old words.

Placement: a contract change (decision-0016), so 0.10.0 before its cut or 1.1.0 after it; the maintainer's word. Minted on the maintainer's word, 2026-11-18: "yes, mint the six knowgov tasks".
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 capture.py questionnaire takes --stage 2 (or reads a published store) and asks each key on which a statement was invalidated
- [x] #2 An item on a stale key carries the invalidated statement's text and its successor's, each with its version
- [x] #3 Keys the new version adds that a task class requires get an item; unmapped ones are reported (see the G3 task)
- [x] #4 Tests on S6's change; ingest still accepts the output; CHANGELOG line under Contract changes
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. capture.py questionnaire --stage {1,2}: stage 2 loads the scenario then the gate's own stage-2 routine (gate_cli._change, before re-verification) into the scratch store; no published-store read.
2. Stage 2 only: each known string names its statement's version (artefact_assertions, an existing port read), and an invalidated statement the gate's level drops (superseded by a settled sibling) is kept beside its successor.
3. change.added_keys (held_keys before and after the change) for the added keys; stderr notes for added keys no class requires, added keys another class requires, and invalidated statements on keys the task does not require. The gate finding stays task-0370's, on the same seam.
4. TOML shape unchanged, so no format bump; stage 1 byte-identical.
5. Tests on S6's stage 2 and a public plant that adds P4|rounding and S-review|final; ingest of an answered stage-2 file; CHANGELOG line under Contract changes.

6. In scope on the coordinator's word (2026-11-27): a finding's route after a change names capture.py questionnaire --stage 2 (gate_cli.route_stage: a change passed, or a held version the scenario's [scenario.stage2] names), in gate reports, the MCP gate_verdict and trace check. Stage 1's routes are unchanged.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Placed in 0.10.0 on the maintainer's word, 2026-11-27: "A, and put task-0371 into 0.10.0". The reason: a private instance's arrival questionnaire, generated with this tool at the pin, asked every reworded key with its first version's text (33 of 33) and every added key with no statement at all (11 of 11, level absent). It is not committed and waits for this task. The public check stays on S6's change; the instance re-runs its own arrival once this lands.

Scope set by the coordinating session on 2026-11-27 after a relevance check, recorded here:
- AC1 is met by --stage 2 on the scratch store. The "or reads a published store" alternative is dropped, so the command stays deterministic under KG_CLOCK=pinned (load.now reads KG_TODAY).
- AC2 is met by each known string naming its version, e.g. "316.00 (invalidated, v1, extracted, contract/decision_table.md)" beside "341.00 (proposed, v2, ...)". It lists the statement's value, not its source sentence, and the item shape is unchanged.
- AC3: an added key the task requires is an item. One no class requires is a stderr note. The gate finding is task-0370's.
- Removed statements, which have no successor, are not special-cased. A required key holding one is asked at its level with the invalidated statement alone.

Route: gate_cli.route_stage decides the stage a route names. It is 2 for gate_cli --stage 2, and for --no-load, MCP gate_verdict and trace check on a store holding the version the scenario's [scenario.stage2] names. No golden or expected file held S6 stage-2 route text; tests/test_gate_cli.py holds S2's stage-1 route, which is unchanged.

Proven locally on rdflib under a pinned clock (2026-11-27):
- tests/test_questionnaire_stage2.py, 9 tests: S6's stale keys with both versions; the planted added key P4|rounding and the unrequired S-review|final; the any-level rule; ingest of an answered stage-2 file; the stage-2 routes.
- The pinned suite: 1397/1398 passed.
- The comparator: 0 differing leaves.
- check_round_trip --chain rdflib,rdflib, check_gate_after_change, check_trace_walkthrough and check_mcp_server all pass.
- Stage-1 questionnaires are byte-identical to main on S1-S7.
- Neo4j is left to the stack job.
<!-- SECTION:NOTES:END -->
