---
id: TASK-0164
title: >-
  Per-subject read snapshots: a reader for another subject answers from that
  subject's last committed run (decision-0013 A1, O3; parked until the pilot)
status: To Do
assignee: []
created_date: '2026-11-06T08:20:00Z'
labels:
  - mcp
  - store
dependencies:
  - TASK-0157
priority: low
ordinal: 166000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0013's shared-store gap: the store holds one scenario of one subject at a time, so under B7 a store-backed tool for a subject not held refuses (O1). O3: after each committed run, the run exports its subject and scenario to a read-only Turtle snapshot (export_turtle, with the generation and the date); a child for another subject, or another scenario, reads that snapshot through rdflib, whatever the live store (Neo4j or rdflib). It also lifts one-scenario-at-a-time for reads. Parked until the lighthouse pilot measures store refusals for another subject per assistant session; it needs its own decision before it is built, since it adds a second read path. Rejected alternatives, in decision-0013's acceptance: subject-scoped data in one Neo4j (O4), load on demand in a reader (O5), one Neo4j per subject (O6). O2 (one rdflib file per subject) is the cheaper fallback, rdflib only.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A decision records the snapshot read path before any build: where snapshots live, rotation, and how a snapshot answer states its generation and date
- [ ] #2 Every answer read from a snapshot carries its subject, scenario, generation and date, and equals the live store's answer for the same generation (tools/check_round_trip.py)
- [ ] #3 The pilot's measure that triggered it is cited (store refusals for another subject per session)
<!-- AC:END -->
