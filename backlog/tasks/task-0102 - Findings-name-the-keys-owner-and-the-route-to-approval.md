---
id: TASK-0102
title: Findings name the key's owner and the route to approval
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T09:47:00Z'
updated_date: '2026-11-04T12:26:00Z'
labels:
  - gate
  - schema
milestone: m-8
dependencies: []
priority: medium
type: feature
ordinal: 105000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From doc-0014 (C7; playbook p. 40, a block explains itself). Each key, stale and lapsed finding gains the owner unit from register_map.toml (task-0043) and the route, the owner's questionnaire (task-0009). The gate-report schema takes an additive minor bump.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 S2's blocking finding names its owner unit and the questionnaire command
- [x] #2 The schema validates reports of both versions
- [x] #3 The page's gate box shows the owner
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. capture.finding_owners (key -> answering unit, task-0043's rule; register unreadable names none) and questionnaire_route (the owner's questionnaire, task-0009).
2. gate_cli.findings/report/evaluate: key, stale, lapsed findings gain owner and route when owners are given; evaluate defaults them from the loaded subject; text adds [owner UNIT]. MCP keys reports route to the class resolved under, no route outside it.
3. Schema: owner and route on a finding, optional; schema_version stays 2 (task-0071's precedent: minor at the release).
4. Page gate box: owner line for blocking keys, else keys below verified.
5. Folded notes: knowgov-gate.sh refuses KG_TASK=keys; hook _summary names owner and route; decide(unavailable_route=...), the dogfood hook passes its own.
6. Tests, both subjects; deterministic record and comparator unchanged.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Folded in from task-0099's report (coordinator brief): (1) instance/ci/knowgov-gate.sh refuses KG_TASK=keys explicitly (nothing reaches it today, but doc-0014 C4: the CI route requires a task class). (2) instance/ci/claude/knowgov_hook.py _summary names the key's owner once findings carry it; decide() gains an unavailable_route parameter, the counterpart of route, since the fixed UNAVAILABLE_ROUTE wording is wrong for a check other than the gate; the dogfood hook (.claude/hooks/protected_paths.py, task-0105) passes its own wording.

Verified: S2's blockers (QuoteAPI|on_screening_outage, response|hold_presence) name owner ORG-0002 and the route 'python harness/capture.py questionnaire --scenario S2 --task codegen --out DIR; ORG-0002 answers DIR/questionnaire-cargo_quote-S2-ORG-0002.toml ...' (gate_cli on rdflib, and the live hook's summary). Schema: owner/route optional on a finding; tests validate reports with and without them; schema_version stays 2 (task-0071's precedent; minor at the next release). Page gate box on S2: 'owner: ORG-0002 Architecture stewardship (stand-in) (2 keys)'. Local: tests 321/321 on both subjects, KG_HOOK_LIVE=1 too; CQ comparator 0 differing leaves; check_mcp_server S1,S2,S6 and J-F C,D3; round trip S2; check_gate_after_change. CI on PR #179: tests, rdflib, stack green; merged b26e528. No recorded report changed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Findings now name the key's owner unit and the route to approval (doc-0014 C7). gate_cli's key, stale and lapsed findings carry owner (capture.finding_owners: task-0043's answering unit, null when none or several) and route (the owner's questionnaire, task-0009); evaluate defaults them from the loaded subject, so CLI and MCP agree; an MCP keys report routes to the class it was resolved under. Schema additive (optional fields, version stays 2). The page's gate box names the owner. Folded in from task-0099: knowgov-gate.sh exits 2 on KG_TASK=keys; the hook's summary names owner and route; decide() takes unavailable_route, the dogfood hook passes its own. PR #179. Follow-ups proposed to the coordinator: a CHANGELOG entry at the next release; a declared gap's route might name the closing unit the declaration names (OD-1: compliance) rather than the answering owner.
<!-- SECTION:FINAL_SUMMARY:END -->
