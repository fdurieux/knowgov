---
id: TASK-0202
title: >-
  Decide how conflict gap ids are numbered: a defined order or content-derived
  ids (doc-0030 question 4)
status: Done
assignee: []
created_date: '2026-11-07T07:15:00Z'
updated_date: '2026-11-08T11:56:00Z'
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
- [x] #1 A decision record with the four parts weighs a defined order (ORDER BY ids) against content-derived ids, as person pairs already have, and names what the record's note says
- [x] #2 No code changes the record's conflict ids before that decision is accepted
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-08, coordinator under the maintainer's autonomy window ("continue with the backlog & decisions made"): decision-0020 drafted, proposed, with its four parts. It weighs (a) a defined order with the :<n> numbering kept, (b) content-derived ids as person pairs have (gap:conflict:<key>:<a>~<b>), and (c) no change, and advises (b) over (a)'s order contract for 0.9.0. It names what the record keeps: the vendored results keep :0..3, read through the comparator's normaliser, and no vendored file is edited. AC #2 holds: no code changes the record's conflict ids until the maintainer accepts it.

2026-11-08: the maintainer accepted decision-0020's advice ((b), content-derived ids over a defined order). The build is task-0223; AC #2 held until acceptance (no code changed the record's conflict ids before it).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
decision-0020 drafted with its four parts and accepted by the maintainer on 2026-11-08: document conflict gaps take content-derived ids gap:conflict:<key>:<a>~<b>, as person pairs already do, over a defined order on both adapters, for 0.9.0 (doc-0028 G9-14). No code changed the record's conflict ids before acceptance. Build: task-0223.
<!-- SECTION:FINAL_SUMMARY:END -->
