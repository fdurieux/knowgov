---
id: TASK-0370
title: >-
  A new document version names the keys it adds that no task class requires and
  no register-map row maps (impact gap G3)
status: To Do
assignee: []
created_date: '2026-11-18T07:35:00Z'
updated_date: '2026-11-18T07:36:00Z'
labels:
  - impact
  - reverse-engineering
  - contract
dependencies: []
priority: high
ordinal: 359000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Source: a private instance's impact and traversal study (2026-11-17), gap G3.

When a stage-2 change loads a document's new version, the statements it adds whose keys no `[tasks.<class>]` requires and no `register_map.toml` row names are held in the store and reached by nothing: no gate finding, no owner, no questionnaire item. Only `held_keys` lists them, under unrequired. In the study, an arrival's 11 added statements were silent, among them a change the maintainer had ruled must be kept.

Placement: a contract change (decision-0016), so 0.10.0 before its cut or 1.1.0 after it; the maintainer's word. Minted on the maintainer's word, 2026-11-18: "yes, mint the six knowgov tasks".
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The gate's stage-2 change report lists, per changed artefact, the keys the new version adds that no task class requires and no map row names
- [ ] #2 Each such key is an info finding naming the artefact and version, and the route (extend register_map.toml and the task's keys)
- [ ] #3 gate-report schema extended additively; a test on a public fixture with an added unmapped statement; the scored records unchanged
- [ ] #4 CHANGELOG line under Contract changes
<!-- AC:END -->
