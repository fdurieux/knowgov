---
id: TASK-0201
title: >-
  One definition per concept: superseded, disputed, owner routes, id uniqueness
  (doc-0030 F5: G3, M4, G8, S4, part of S2)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-07T07:15:00Z'
updated_date: '2026-11-08T11:02:00Z'
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
- [x] #1 Supersession comes from one successor set used by the gate's level, the stale finding, superseded_by and the bundle; doc-0030 G3's weight_kg|max case agrees across all four
- [x] #2 three_valued_answer reads disputed statements and says so (S4's QuoteAPI|on_screening_outage is not unknown)
- [x] #3 Owner, route and questionnaire file come from one function, and a key with several owners is written where its route points
- [x] #4 Both adapters refuse a duplicate id for the same labels, named in store.py; declared_gaps_for_key is ordered by id on both
- [x] #5 The scored record (S1 to S7), the deterministic run and the comparator stay equal
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
One PR, claude/task-0201-f5. G3: gate.resolve_spec reads supersession from stale_on_keys' own successors (superseded_by), the set the stale finding, superseded_by and the bundle read. M4: three_valued reads disputed and names them (an additive disputed field; answer values unchanged). G8: capture.routing, the one owner, route and file rule for findings, questionnaires and register_change.resting. S4: store.UNIQUE_IDS; Neo4j guards Derived and Activity at create (CONSTRAINTS, D1, unchanged). S2's part: declared_gaps_for_key by id. candidate_pairs and conflict_gaps untouched (task-0202). tools/check_one_definition.py.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Shipped in #345, merged on whole green at f533ebc (tests, rdflib, rdflib-readers, stack, knowgov gate; publish skipped). G3 takes the narrower reading, a statement's own settled successor (superseded_by over stale_on_keys), which leaves the record unchanged; the wider one would change the record's superseded_by and the bundle. M4 is additive: an optional disputed field, no new answer value (CHANGELOG under Contract changes). S4 guards Derived and Activity at create on Neo4j; CONSTRAINTS (D1) unchanged. candidate_pairs and conflict_gaps untouched, per task-0202 AC #2.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
One definition per concept (doc-0030 F5). G3: the gate's level, the stale finding, superseded_by and the bundle read one successor set, an invalidated statement's own verified or approved successor; S6's stage 2 with DT-V's V2 removed reads weight_kg|max invalidated on all four, where main read it approved beside a major stale finding. M4: three_valued and three_valued_answer read disputed statements and name them in an optional disputed field; S4's QuoteAPI|on_screening_outage reads asserted, not unknown. G8: capture.routing is the one owner, route and questionnaire file rule for the gate's findings, the questionnaires and register_change.resting; a key with several answering units routes to each unit's questionnaire, where it is written. S4: store.UNIQUE_IDS, the Neo4j adapter refusing a duplicate Derived or Activity at create, its constraints (D1) unchanged; declared_gaps_for_key by id on both adapters. Verified by tools/check_one_definition.py (3 failures on main on rdflib, 4 on Neo4j; green on both), the suites, the round trips, the MCP check and the five walkthroughs; the record S1-S7 and J-F unchanged. Held for task-0202: candidate_pairs and conflict_gaps keep the store's order.
<!-- SECTION:FINAL_SUMMARY:END -->
