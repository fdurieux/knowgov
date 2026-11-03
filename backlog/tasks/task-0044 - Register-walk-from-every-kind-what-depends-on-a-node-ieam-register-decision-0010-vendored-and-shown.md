---
id: TASK-0044
title: >-
  Register walk from every kind: what depends on a node (ieam-register decision
  0010), vendored and shown
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-03T22:40:00Z'
updated_date: '2026-11-03T22:41:00Z'
labels:
  - impact
  - register
milestone: m-6
dependencies: []
references:
  - backlog/docs/doc-0011
priority: high
type: feature
ordinal: 56000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0011 point 1 (measured on the example instance): the register's impact walk (tools/impact.py FORWARD) reaches nothing from 28 of 37 approved CAP, ENT, PRD and journey-step starts; following every type both ways collapses to one 15-node slice from every start. A per-kind dependants table fixes it: crud⁻¹ and manages⁻¹ from an entity, requires⁻¹ from a capability, concerns⁻¹ and delivers⁻¹ from a product, is_supported_by forward from a step; zero-reach starts 28 → 6 (domains and portfolios only). The walk is the register's (its decision 0007): propose it there as decision 0010 with its test, then re-vendor here and keep the page's panel and saved Cypher equal to the walk on every node (as task-0023 and task-0026 did).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 ieam-register decision 0010 (proposed, the maintainer approves by the merge) changes impact.py to walk dependants per start kind under 0007's approved-only rule; its test shows zero-reach approved starts go from 28 to 6 and no start reaches the whole slice
- [ ] #2 knowgov re-vendors the register at the tag that carries 0010
- [ ] #3 The impact panel and the register-impact saved query equal the vendored walk on every node of both subjects, held by the existing equality test and the stack job
<!-- AC:END -->
