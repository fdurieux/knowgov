---
id: TASK-0202
title: >-
  Decide how conflict gap ids are numbered: a defined order or content-derived
  ids (doc-0030 question 4)
status: To Do
assignee: []
created_date: '2026-11-07T07:15:00Z'
labels:
  - review
  - decision
  - record
dependencies:
  - TASK-0201
priority: medium
type: task
ordinal: 202000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer accepted doc-0030's advice on 2026-11-07 ("accept the advise on all four"): the hardening tranche before 0.9.0's cut, in the order F7; F1 with the check_instance guard, H7 and M3; F3, F4 and F2; F5 and F8. The ids below are doc-0030's (the code review at 8d80b2b); each finding there quotes its lines and its probe.

S2: candidate_pairs and conflict_gaps answer in store order, and R-CONFLICT numbers `gap:conflict:<key>:<n>` in that order, so one id names a different conflict on Neo4j and on rdflib (S4: `:0` is bpmn against the table on the Neo4j record, the table against puml on rdflib), and since decision-0017 the default gate and the page can disagree. Fixing it renumbers ids the scored record holds, so the maintainer decides first, after the tranche, as accepted.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A decision record with the four parts weighs a defined order (ORDER BY ids) against content-derived ids, as person pairs already have, and names what the record's note says
- [ ] #2 No code changes the record's conflict ids before that decision is accepted
<!-- AC:END -->
