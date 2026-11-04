---
id: TASK-0072
title: >-
  Crosswalk of knowgov's basis and status to provenance vocabularies (PROV-O) in
  the glossary and the guide
status: Done
assignee:
  - '@claude'
created_date: '2026-11-03T23:53:00Z'
updated_date: '2026-11-04T00:06:00Z'
labels:
  - docs
milestone: m-6
dependencies: []
references:
  - backlog/docs/doc-0013
priority: low
ordinal: 76000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0013 P6. Evaluators arrive with provenance vocabularies (derivation method, validation status, W3C PROV-O). A table spares them the mapping and states what has no counterpart.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A table maps every basis and status to them, including what has no counterpart
- [x] #2 demo/GLOSSARY.md and docs/guide.md carry it; no field changes
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. One table: every basis, status and the two key levels below them, against W3C PROV-O and the derivation method and validation status of doc-0013 §3, with no counterpart stated. 2. Carry it in demo/GLOSSARY.md and docs/guide.md §2 between markers. 3. A test holds the two copies equal and covers every basis and every gate ORDER level.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
tests/test_crosswalk.py: copies equal; every basis the harness writes and every ORDER level has a row; every row fills all four columns. No field changes.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The provenance crosswalk, one table carried in demo/GLOSSARY.md (new section) and docs/guide.md §2. It maps the six bases, the statuses (rejected included), the lapsed approval, and the absent and declared_gap levels onto W3C PROV-O and onto the derivation method and validation status. Rows with no counterpart are stated. tests/test_crosswalk.py holds the copies equal and complete. No field changes.
<!-- SECTION:FINAL_SUMMARY:END -->
