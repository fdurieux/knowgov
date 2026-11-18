---
id: TASK-0372
title: >-
  who_knows reports each key as (subject, key), never merged across subjects by
  its text (impact gap G2)
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
ordinal: 361000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Source: a private instance's impact and traversal study (2026-11-17), gap G2.

`who_knows` reads every subject and merges keys by their string. Two subjects that share key ids for different statements get one answer: in the study, 119 key strings were shared by two subjects, 63 of them worded differently and 7 asked of different units. The answer to who knows is then confidently wrong.

Placement: a contract change (decision-0016), so 0.10.0 before its cut or 1.1.0 after it; the maintainer's word. Minted on the maintainer's word, 2026-11-18: "yes, mint the six knowgov tasks".
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 keys in scope are reported as (subject, key) pairs, and keys_in_scope counts pairs
- [ ] #2 a key argument may name its subject; without one, every subject holding the key is listed separately
- [ ] #3 the who-knows schema changed, its version and the MCP tool description updated; a test with two subjects sharing a key id with different statements
- [ ] #4 CHANGELOG line under Contract changes
<!-- AC:END -->
