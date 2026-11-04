---
id: TASK-0081
title: >-
  Proposals to ieam-register: the realiser walk and anchors for the unanchored
  CargoQuote citations
status: Done
assignee: []
created_date: '2026-11-04T00:44:00Z'
updated_date: '2026-11-04T12:19:00Z'
labels:
  - register
milestone: m-4
dependencies: []
priority: low
ordinal: 85000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Two register-side follow-ups knowgov can only propose: the realiser walk decision 0010 left open (a capability to the processes that realise it, as a second named walk), and anchors for the 10 CargoQuote citations task-0046 found without one (11 of 21 anchored). Both are ieam-register's decisions.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 One ieam-register issue or PR per proposal, with the nodes and walk rows it adds
- [x] #2 Nothing in knowgov changes until approved and vendored
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Realiser half: ieam-register #18 (decision 0012, `tools/impact.py --walk realisers`: a capability to the processes that realise it and the applications supporting them), its state line settled in #22; vendored here at v0.2.7 (2b9e093) by task-0109. Anchors half: moot per task-0077 (every subject's citations reach the statements of the documents it loads; no register anchors needed). Nothing changed in knowgov before the vendoring; the page's impact view does not yet offer the realiser walk (proposed to the coordinator as a follow-up).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Both proposals resolved: the realiser walk accepted in ieam-register (#18, #22; decision 0012) and vendored at v0.2.7 by task-0109; the anchors proposal moot per task-0077.
<!-- SECTION:FINAL_SUMMARY:END -->
