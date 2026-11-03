---
id: TASK-0046
title: >-
  Anchor-grain saved query: a register node to the statements its cited anchor
  supports, and on to derived code
status: To Do
assignee: []
created_date: '2026-11-03T22:40:00Z'
updated_date: '2026-11-03T22:41:00Z'
labels:
  - impact
  - queries
milestone: m-6
dependencies: []
references:
  - backlog/docs/doc-0011
priority: medium
type: feature
ordinal: 58000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0011 follow-up 2: #81's register-node-store query works at document grain (REL-08001 cites contract/openapi.yaml, so every statement of the file is reached). Matching a REG_CITES anchor to the fragments it names narrows it: ENT-0004 → DT-P → 13 statements, against 39 at document grain. Through both store adapters.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A saved query reaches, from a register node, only the statements whose fragments the cited anchor names, then the derived outputs that used them
- [ ] #2 The same result through the rdflib port; ENT-0004 gives 13 statements and derived:S1:G:run1
- [ ] #3 The stack job and check_saved_queries.py run it
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Starts after knowgov #81 (the three saved queries, document grain) merges: same file, store_neo4j.py's saved queries.
<!-- SECTION:NOTES:END -->
