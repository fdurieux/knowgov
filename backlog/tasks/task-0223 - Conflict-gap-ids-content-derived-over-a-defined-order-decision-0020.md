---
id: TASK-0223
title: Conflict gap ids content-derived over a defined order (decision-0020)
status: To Do
assignee: []
created_date: '2026-11-08T11:56:00Z'
labels:
  - store
  - rules
  - contract
  - record
dependencies:
  - TASK-0202
references:
  - >-
    backlog/decisions/decision-0020 -
    Conflict-gap-ids-are-content-derived-as-person-pairs-already-are-over-a-defined-order-one-id-per-conflict-on-every-store.md
priority: high
type: feature
ordinal: 223000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0020, accepted (the maintainer, 2026-11-08: accept decision-0020's advice; task-0202, doc-0030 S2). R-CONFLICT (harness/rules.py r_conflict) names a person's conflict gap:conflict:<key>:<a>~<b> but numbers a document conflict :<n> in candidate_pairs' undefined store order, so one S4 conflict is :0 on Neo4j and another on rdflib, and the default gate (rdflib scratch, decision-0017) and the page (Neo4j) disagree. Name every document conflict gap:conflict:<key>:<a>~<b> with its assertion ids sorted; order candidate_pairs and conflict_gaps by key then id on both adapters; extend demo/tools/compare_deterministic.py's CONFLICT_ID normaliser to both forms per key; re-pin deliberately, and name, the bundle bytes and fixtures that carry :<n> (test_arms, S4). The vendored results keep :0..3 and are never edited; subjects/README.md notes the form change. A contract change (the gate report's conflict ids), for 0.9.0 (doc-0028 G9-14).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 r_conflict names every document conflict gap:conflict:<key>:<a>~<b> with its assertion ids sorted; person pairs are unchanged
- [ ] #2 candidate_pairs and conflict_gaps answer ordered by key then id on rdflib and Neo4j, and one conflict has one id on both (S4 shown)
- [ ] #3 Adding an unrelated conflict on the key leaves every other conflict's id unchanged, by a test
- [ ] #4 compare_deterministic.py normalises both forms per key; the scored record (S1 to S7), the deterministic run and the comparator stay equal
- [ ] #5 Every re-pinned byte or fixture is named in the PR; no vendored file is edited; subjects/README.md notes the form
- [ ] #6 CHANGELOG.md carries the line under Unreleased's contract heading
<!-- AC:END -->
