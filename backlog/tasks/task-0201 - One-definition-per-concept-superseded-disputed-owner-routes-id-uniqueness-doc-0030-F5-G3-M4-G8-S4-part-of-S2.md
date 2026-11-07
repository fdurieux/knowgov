---
id: TASK-0201
title: >-
  One definition per concept: superseded, disputed, owner routes, id uniqueness
  (doc-0030 F5: G3, M4, G8, S4, part of S2)
status: To Do
assignee: []
created_date: '2026-11-07T07:15:00Z'
labels:
  - review
  - semantics
  - store
dependencies:
  - TASK-0197
  - TASK-0198
priority: medium
type: bug
ordinal: 201000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer accepted doc-0030's advice on 2026-11-07 ("accept the advise on all four"): the hardening tranche before 0.9.0's cut, in the order F7; F1 with the check_instance guard, H7 and M3; F3, F4 and F2; F5 and F8. The ids below are doc-0030's (the code review at 8d80b2b); each finding there quotes its lines and its probe.

G3: superseded is computed two ways (gate.py:46 by key; the stale finding, superseded_by and the bundle by artefact), so the gate reads PROCEED beside a major stale finding with no successor. M4: three_valued_answer says unknown for a key whose statements are all disputed (gate.py:116). G8: a key with several owners routes to a questionnaire file that is never written. S4: id uniqueness differs per adapter. S2: three port reads have no order; this task orders declared_gaps_for_key, which numbers nothing. Ordering candidate_pairs and conflict_gaps renumbers the record's conflict gap ids and waits for its own decision (the next task).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Supersession comes from one successor set used by the gate's level, the stale finding, superseded_by and the bundle; doc-0030 G3's weight_kg|max case agrees across all four
- [ ] #2 three_valued_answer reads disputed statements and says so (S4's QuoteAPI|on_screening_outage is not unknown)
- [ ] #3 Owner, route and questionnaire file come from one function, and a key with several owners is written where its route points
- [ ] #4 Both adapters refuse a duplicate id for the same labels, named in store.py; declared_gaps_for_key is ordered by id on both
- [ ] #5 The scored record (S1 to S7), the deterministic run and the comparator stay equal
<!-- AC:END -->
