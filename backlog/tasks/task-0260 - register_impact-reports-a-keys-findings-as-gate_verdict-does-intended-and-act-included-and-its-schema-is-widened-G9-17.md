---
id: TASK-0260
title: >-
  register_impact reports a key's findings as gate_verdict does, intended and
  act included, and its schema is widened (G9-17)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-09T09:32:00Z'
updated_date: '2026-11-09T11:02:00Z'
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
- [x] #1 `register_impact` takes `OWNED` from `gate_cli`, so there is one definition.

Its findings per key equal `gate_verdict`'s for the same store, task and `as_of`:
- on group 3's reproduction, a capture and a review whose sha256 does not bind, with S2 published;
- on S1, S4 and S6.
- [x] #2 `register-impact.schema.json`'s finding admits the kinds `intended` and `act`, and the `act` object. So does any schema that nests these findings.
- [x] #3 A test holds `register_impact`'s and `gate_cli`'s owned kinds equal.
- [x] #4 `CHANGELOG.md`'s Unreleased section names the change under Contract changes.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. register_impact imports OWNED from gate_cli (one definition). 2. register-impact.schema.json: finding kind admits intended and act; the gate report's act object, copied. 3. Group 3's reproduction as tools/check_owned_findings.py (a capture, a review whose sha256 no longer binds, S2 published; then S1, S4, S6 key for key), on rdflib in harness.yml and on Neo4j in demo.yml. 4. A test holds the two OWNED as one. 5. CHANGELOG under Unreleased > Contract changes.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
harness/register_impact.py imports OWNED from gate_cli (key, intended, stale, lapsed, act): one definition. register-impact.schema.json's finding: kind admits intended and act, and the act object is the gate report's, copied (a test holds them equal). No other schema nests these findings: proposal-impact types its keys' findings as open objects; step-grid and register-nodes carry none. Group 3's reproduction is tools/check_owned_findings.py, on rdflib in harness.yml (rdflib-readers) and on Neo4j in demo.yml. Its case: example instance, employee-1 answers ORG-0002's S2 questionnaire, employee-2 approves answers 1 and 3, then answer 1's sha256 is zeroed, so the ruling on QuoteAPI|on_screening_outage no longer binds; S2 published. On 6d27961-era code gate_verdict listed one major act finding on the key and register_impact from ENT-0003 none; now both list it, each answer valid under the schema. A ruling corrupted on a disputed key instead refuses the whole review (a keyless act at info), which is why the case rules on undisputed answers. S1, S4 and S6: 278 landed-key readings over the register map's 20 nodes equal gate_verdict's owned findings key for key, on rdflib and Neo4j. tests/test_mcp_server.py and tools/check_mcp_server.py compare with gate_cli.OWNED.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
register_impact takes gate_cli.OWNED, so a key's intended and act findings show on it as on gate_verdict (group 3 CB1); the register-impact schema's finding admits both kinds and the gate report's act object, additive. Group 3's reproduction (a capture, a review whose sha256 no longer binds, S2 published) is tools/check_owned_findings.py, run on rdflib and Neo4j in CI, with S1, S4 and S6 equal key for key; a test holds the two OWNED as one and the act objects equal. The record held: the comparator on S1-S7 and J-F, check_round_trip --chain, check_mcp_server. CHANGELOG under Unreleased > Contract changes.
<!-- SECTION:FINAL_SUMMARY:END -->
