---
id: TASK-0073
title: >-
  Operational projection: a schema-pinned, one-way export for an operational
  ontology (parked)
status: To Do
assignee: []
created_date: '2026-11-03T23:53:00Z'
labels:
  - lighthouse
milestone: m-4
dependencies:
  - TASK-0063
references:
  - backlog/docs/doc-0013
priority: low
ordinal: 77000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0013 P8, parked: start only when the lighthouse pilot runs an operational ontology and asks (doc-0013 decided the inbound lighthouse wins over the outbound projection). Until then the read-only MCP server (task-0056) is the route for an operational platform's agent. Needs a maintainer decision to unpark.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A projection schema under harness/schemas/ covering register ids, approved links, statements with their epistemic fields and change signals
- [ ] #2 Dated, append-only delivery with a reconciliation that reports drift
- [ ] #3 No vendor named under harness/ or demo/app; the adapter verified on a real enrolment
<!-- AC:END -->
