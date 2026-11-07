---
id: TASK-0197
title: >-
  Stage 2 as a whole re-load: rules across versions, reviews re-applied, gaps
  kept closed (doc-0030 F3: H2, H4, I5, I6, G5)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-07T07:15:00Z'
updated_date: '2026-11-07T09:24:00Z'
labels:
  - review
  - load
  - stage2
dependencies:
  - TASK-0193
priority: high
type: bug
ordinal: 197000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer accepted doc-0030's advice on 2026-11-07 ("accept the advise on all four"): the hardening tranche before 0.9.0's cut, in the order F7; F1 with the check_instance guard, H7 and M3; F3, F4 and F2; F5 and F8. The ids below are doc-0030's (the code review at 8d80b2b); each finding there quotes its lines and its probe.

H2 (high, two reviewers): change.apply_change re-runs every rule and never re-applies the reviews; R-REQ resets a closed declared gap to open (S2 with OD-1 closed: PROCEED, then BLOCKED after a stage-2 re-ingestion). H4 (high): R-CONFLICT and R-CORROBORATE pair only statements of one version (store_rdflib.py:666, store_neo4j.py:886), so a stage-2 change that contradicts the other documents reads proposed where a fresh load reads disputed. I5: stage 2 resolves symbols from the one re-ingested file, and the definition sentence is no fragment. I6: load.py:105 drops a statement whose value changed while its other fragments were reused (J-F JDL-001). G5: a declared gap outlives its declaring statement. A fix, not bound by the freeze; doc-0028 G9-11.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A test holds a stage-2 gate equal to a fresh load of the stage-2 documents plus the stale and suspect findings, on S6 and on a cross-version plant (the table's accept row at 45 against 41 elsewhere reads disputed)
- [ ] #2 A review's close of a declared gap survives stage 2 (the S2 walk stays PROCEED), and R-REQ never reopens a closed gap
- [ ] #3 A changed symbol definition invalidates the statements resolved through it, and re-ingesting another file never flags a symbol undefined
- [ ] #4 A statement whose value changed while some of its fragments were reused gets a v2 successor, and R-STALE withdraws a gap whose declaring statement it invalidated
- [ ] #5 The scored record (S1 to S7), the deterministic run and the comparator stay equal
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. load.py re-ingest path: the whole later kit extracted (symbols from all documents, I5); a version only for artefacts whose bytes changed; each statement diffed by id stem against the store's, any status, on value and fragment set: unchanged writes nothing, else a v2 successor (I6, I5b). 2. change.apply_change loads kit2 whole with the changed set; kits injectable for plants. 3. Adapters (rdflib, Neo4j): candidate_pairs pairs document statements (extracted, authored) across versions (H4); R-REQ keeps a closed gap closed (H2); declared_open counts live statements only and R-STALE invalidates an older statement with a live same-stem successor and withdraws a declared gap whose declarations it invalidated (G5). 4. Reviews: not re-read at stage 2; their acts persist and no rule re-run undoes one (re-reading would refuse every close already applied, and F4 owns load_reviews). 5. tools/check_stage2_reload.py: S6 and plants equal to a fresh load plus stale/suspect, on rdflib and Neo4j; failing on the old code. 6. Record: S1-S7 on rdflib and Neo4j, J-F; check_gate_after_change, round trips, walkthroughs, MCP; suite both ways.
<!-- SECTION:PLAN:END -->
