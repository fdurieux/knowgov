---
id: TASK-0260
title: >-
  register_impact reports a key's findings as gate_verdict does, intended and
  act included, and its schema is widened (G9-17)
status: To Do
assignee: []
created_date: '2026-11-09T09:32:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0032
  - task-0256
priority: high
ordinal: 254000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
`register_impact`'s docstring promises that "a key reads here exactly as gate_verdict reports it". But `register_impact.OWNED` is `("key","stale","lapsed")` while `gate_cli.OWNED` is `("key","intended","stale","lapsed","act")`.

So a key whose capture does not bind (an act finding at major) shows the act finding on `gate_verdict` and none on `register_impact`. The same gap reaches `proposal_impact`'s keys and slices, through `with_levels`.

The register-impact schema's `finding.kind` enum lacks `intended` and `act`, and has no `act` object under `additionalProperties: false`, so the fix widens it.

The finding is contract-bearing, and the fix is additive.

Source: group 3 CB1, with its reproduction in the prober's `probe/ri_intended.py`, decision-0032 (task-0256), probed on main 2a8bbeb.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `register_impact` takes `OWNED` from `gate_cli`, so there is one definition.

Its findings per key equal `gate_verdict`'s for the same store, task and `as_of`:
- on group 3's reproduction, a capture and a review whose sha256 does not bind, with S2 published;
- on S1, S4 and S6.
- [ ] #2 `register-impact.schema.json`'s finding admits the kinds `intended` and `act`, and the `act` object. So does any schema that nests these findings.
- [ ] #3 A test holds `register_impact`'s and `gate_cli`'s owned kinds equal.
- [ ] #4 `CHANGELOG.md`'s Unreleased section names the change under Contract changes.
<!-- AC:END -->
