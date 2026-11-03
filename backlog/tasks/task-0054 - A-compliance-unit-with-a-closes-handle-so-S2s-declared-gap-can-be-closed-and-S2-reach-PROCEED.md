---
id: TASK-0054
title: >-
  A compliance unit with a closes handle, so S2's declared gap can be closed and
  S2 reach PROCEED
status: To Do
assignee: []
created_date: '2026-11-03T22:50:00Z'
labels:
  - capture
  - register
milestone: m-5
dependencies:
  - TASK-0037
references:
  - backlog/docs/doc-0009
priority: high
type: feature
ordinal: 66000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by task-0037 (#82): CargoQuote's open decision OD-1 names compliance as the declared gap's owner, and the example register has no compliance unit, so decision-0002 point 3 refuses every close and real S2 cannot reach PROCEED; doc-0009's milestone measure (S2 BLOCKED to PROCEED by command) needs it. Register side: an organisation node for compliance (stand-in, synthetic), approved under a decision record, and an issued handle with roles closes (and approves) in people/handles.toml (ieam-register decision 0009). knowgov side: re-vendor at the tag, map OD-1's owner to that unit, and extend tools/check_review_walkthrough.py to run real S2 from BLOCKED to PROCEED.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 ieam-register gains an approved compliance organisation node and an issued closes handle in its unit, under a decision record the maintainer approves
- [ ] #2 knowgov re-vendors at that tag; OD-1's owner resolves to the unit
- [ ] #3 check_review_walkthrough.py runs real S2 from BLOCKED (exit 1) through capture and the owner's close to PROCEED (exit 0), on rdflib and on Neo4j in CI
<!-- AC:END -->
