---
id: TASK-0043
title: Give each key one owner unit in the example register map
status: Done
assignee:
  - '@claude'
created_date: '2026-11-02T23:22:00Z'
updated_date: '2026-11-03T23:42:00Z'
labels:
  - capture
milestone: m-5
dependencies:
  - TASK-0009
documentation:
  - >-
    backlog/docs/doc-0007 -
    Capturing-an-employees-knowledge-to-resolve-a-non-conformity-the-John-Doe-walkthrough.md
priority: low
type: chore
ordinal: 55000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0007 §2: in the example register map both ORG-0001 and ORG-0002 own all 36 CargoQuote keys, so every scenario yields two identical questionnaires, and on a real register two people may answer one key and both statements load. The walkthrough should yield one questionnaire per person. The map is subject data (subjects/cargo_quote/register_map.toml); the units are the vendored register's and are not edited here.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Each required key of cargo_quote maps to register nodes of one owner unit, or the questionnaire picks one owner per key by a stated rule
- [x] #2 capture.py questionnaire on S2 writes questionnaires whose key sets do not overlap
- [x] #3 The comparator and tests/test_subject.py stay green
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. register_map.toml: an owner per row, one of its nodes' owners (product owner ORG-0001 for the decision tables and the flow, ORG-0002 for the API's behaviour and response); nodes unchanged, the register untouched.
2. capture.answering_owners: the row's owner, else every owner (other subjects unchanged); questionnaires use it. Ruling authority stays owners_of (decision-0002); OD-1's closer stays its declaration's owner, ORG-0004.
3. Docs: subjects/README, instance/README.
4. Tests: owner within node owners, one per key, S2 questionnaires disjoint.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Chose an explicit owner field over dropping nodes from rows: the nodes stay the reading of what a change touches, and review authority (decision-0002) is unchanged, so check_review_walkthrough passes untouched (run on rdflib). S2: ORG-0001 0 of 29, ORG-0002 3 of 7. Comparator on rdflib: 0 differing leaves over 7 scenarios. The owner field post-dates the map's 2026-10-31 approval; the map header says so.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Each cargo_quote register_map row names one owner, chosen from its nodes' owners in the vendored register (29 ORG-0001, 7 ORG-0002). capture.answering_owners sends a key's questionnaire to that unit only; a row without owner falls back to every owner. Rulings still check every owner of the key's nodes (decision-0002), and OD-1 is still closed by its declared owner ORG-0004. S2 yields disjoint questionnaires (3 open keys, all ORG-0002). Tests, walkthrough and comparator green locally.
<!-- SECTION:FINAL_SUMMARY:END -->
