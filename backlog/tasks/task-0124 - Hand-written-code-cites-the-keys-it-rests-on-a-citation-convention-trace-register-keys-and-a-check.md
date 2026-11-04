---
id: TASK-0124
title: >-
  Hand-written code cites the keys it rests on: a citation convention, trace
  register --keys and a check
status: To Do
assignee: []
created_date: '2026-11-04T19:05:00Z'
labels:
  - trace
  - gate
milestone: m-8
dependencies: []
priority: medium
type: feature
ordinal: 124000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From doc-0015 (2026-11-04, maintainer's go). Hand-written code maps to an APP through code_map.toml but to no statements, so a source or register change never reaches it (doc-0011 §3, 'Reports only'). A citation convention lets it join the stale/suspect chain: a header line naming the keys a file rests on, and knowgov-trace register --keys K1,K2 to register a hand-written file as a derived output resting on those keys' current statements. A check, optional per instance, requires a citation in files under governed APPs. Code semantics stays out: the tests and the oracle judge correctness.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 knowgov-trace register --keys registers a hand-written file; after S6's change it reads suspect on the cited invalidated keys, as a generated file does
- [ ] #2 A header citation is parsed in Python and one other language; an unknown key is an error, a missing citation is a finding only where the instance turns the check on
- [ ] #3 The trace report schema change is additive; the CHANGELOG names it; the record is unchanged
<!-- AC:END -->
