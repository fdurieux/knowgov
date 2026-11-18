---
id: TASK-0375
title: >-
  A port-and-conflict sieve: two subjects sharing key ids, the keys a change
  invalidates in one and their state in the other (impact gap G9)
status: To Do
assignee: []
created_date: '2026-11-18T07:35:00Z'
updated_date: '2026-11-18T07:36:00Z'
labels:
  - impact
  - reverse-engineering
  - contract
dependencies: []
priority: low
ordinal: 364000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Source: a private instance's impact and traversal study (2026-11-17), gap G9.

A reverse-engineering run sorted an upstream author's changes into port, conflict and engineering by hand. The mechanical half is computable from the files: of the 45 keys an arrival invalidated in one subject, 36 were also changed in the other subject's kit and 9 untouched, and every conflict the run found fell in the 36 and every port in the 9. No tool makes that split. The layer (logic or engineering) stays a person's judgement.

Placement: a contract change (decision-0016), so 0.10.0 before its cut or 1.1.0 after it; the maintainer's word. Minted on the maintainer's word, 2026-11-18: "yes, mint the six knowgov tasks".
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 a read-only reader (CLI and MCP) given two subjects that share key ids lists, for each key a change invalidates in one, its state and text in the other: changed, removed, untouched
- [ ] #2 facts only: candidates, never a ruling; schema; files-only where possible
- [ ] #3 a test on a public fixture; CHANGELOG line under Contract changes
<!-- AC:END -->
