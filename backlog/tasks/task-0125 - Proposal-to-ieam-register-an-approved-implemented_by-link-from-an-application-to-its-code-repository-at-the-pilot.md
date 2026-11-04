---
id: TASK-0125
title: >-
  Proposal to ieam-register: an approved implemented_by link from an application
  to its code repository (at the pilot)
status: To Do
assignee: []
created_date: '2026-11-04T19:05:00Z'
labels:
  - register
milestone: m-8
dependencies: []
priority: low
type: task
ordinal: 125000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From doc-0015 (2026-11-04, maintainer's go). Code is outside the governed record: code_map.toml (instance, path globs -> APP) is unapproved and has no lifecycle. A coarse register link APP -> repository (or module), approved and owned like any link, would let the walk reach code and its owners, and decision 0015 and task-0122 flag code when an application retires. Path globs stay in code_map.toml (tool-owned, volatile). The register decides the node kind and relationship. Gated on the pilot, so real repositories shape it.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 An ieam-register PR proposes the relationship and its node kind, with the pilot's repositories as the worked example (in the private record) and a synthetic one in the public register
- [ ] #2 Nothing in knowgov changes until approved and vendored
<!-- AC:END -->
