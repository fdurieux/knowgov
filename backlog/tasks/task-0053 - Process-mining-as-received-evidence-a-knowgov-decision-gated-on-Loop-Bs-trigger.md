---
id: TASK-0053
title: >-
  Process mining as received evidence: a knowgov decision, gated on Loop B's
  trigger
status: To Do
assignee: []
created_date: '2026-11-03T22:41:00Z'
labels:
  - process-mining
milestone: m-4
dependencies: []
references:
  - backlog/docs/doc-0011
priority: low
type: task
ordinal: 65000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0011 point 2 and follow-ups 8, 9, 10, 12: a client's process-mining tool owns the log; knowgov would receive an aggregate conformance result keyed by register PROC ids, which flags a statement and never verifies it, behind one vendor-neutral schema-pinned file with a converter per tool (SAP, ARIS PM, PM4Py). Parked: start only when pumllint's ROADMAP Loop B trigger fires; it then needs an ieam-register proposal for an observed record beside elicited.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Unparked only when the Loop B trigger fires; then a knowgov decision 'observed evidence flags, never verifies' with the aggregate-only privacy rule
- [ ] #2 Then a synthetic conformance experiment on CargoQuote and the conformance contract with a PM4Py reference converter
<!-- AC:END -->
