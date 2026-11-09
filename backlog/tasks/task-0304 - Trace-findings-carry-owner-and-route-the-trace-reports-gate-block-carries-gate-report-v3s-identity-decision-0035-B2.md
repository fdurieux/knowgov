---
id: TASK-0304
title: >-
  Trace findings carry owner and route; the trace report's gate block carries
  gate-report v3's identity (decision-0035 B2)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-09T21:29:00Z'
updated_date: '2026-11-09T22:04:00Z'
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

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. trace._finding takes the keys a finding rests on: suspect, the invalidated or changed statements' keys (trace._keys_of); missing, drift and unbound, the entry's keys (trace.entry_keys). trace._own sets owner and route through gate_cli.owner_route, extracted from gate_cli.findings' lint branch. A finding on no key (unmapped, citation findings, gate:task) names neither.
2. Owners from capture.finding_owners(SUBJECT); route the owner's questionnaire (capture.questionnaire_route) for the scenario held() names and the task; no route when no load is held (trace._routing). Gate findings pass on the owner and route gate_cli.findings gives them (carry).
3. The gate block gains task_profile, register and knowgov (trace.gate_identity: gate_cli.profile_digest of the subject's [tasks.<task>], register_identity, knowgov_identity), as gate report v3 reads them.
4. trace-report.schema.json: optional owner and route on a finding, the three identity fields on the gate block; additive, version 1.
5. harness/annotate.py ends a finding's message with 'Owner: ... Route: ...'; harness.yml's annotate step greps it on the suspect annotation; check_trace_walkthrough (check_answers) holds the identity fields and the owner and route on every finding on keys.
6. tests/test_traceability_answers.py; instance/README.md; CHANGELOG Contract changes line; the record held.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
gate_cli.owner_route is extracted from gate_cli.findings' lint branch, which now calls it, so a trace finding and a gate lint finding name the owner of the same keys alike. The complexity baseline tightens gate_cli.findings from 78 to 60, and trace.check stays at 93 by moving the key expressions into _keys_of.

annotate.py's suffix applies to every finding carrying owner or route, so the gate's own key, stale and lapsed findings, which carried them since task-0102, now show them in the annotation too.

With no load held, _routing passes no route, so a finding on keys two units own reads owner null and route null, not a string of empty routes.

Verified on the walkthrough: every finding on keys names ORG-0001 and its route, and the gate block's task_profile 42781013abbc... equals the gate report's.
<!-- SECTION:NOTES:END -->
