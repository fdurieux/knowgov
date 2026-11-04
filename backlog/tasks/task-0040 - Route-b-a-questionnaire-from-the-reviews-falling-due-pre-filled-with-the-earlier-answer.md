---
id: TASK-0040
title: >-
  Route (b): a questionnaire from the reviews falling due, pre-filled with the
  earlier answer
status: Done
assignee:
  - '@claude'
created_date: '2026-11-02T23:22:00Z'
updated_date: '2026-11-04T00:19:00Z'
labels:
  - capture
milestone: m-5
dependencies:
  - TASK-0037
documentation:
  - >-
    backlog/docs/doc-0007 -
    Capturing-an-employees-knowledge-to-resolve-a-non-conformity-the-John-Doe-walkthrough.md
priority: low
type: feature
ordinal: 52000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0001 §0 names review-driven elicitation on review_due as one of the three cheap capture routes; doc-0007 §6 finds it not built. Elicited knowledge is due for review six months after it was given (ieam-register decision 0008). When a review falls due, the person who gave the answer (or the owner unit, if they left) should be asked again: still true? A confirmation resets the clock; a change is a new capture beside the old one.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A command lists the captured statements and register links with an elicited block whose review falls due on or before a given date
- [x] #2 It writes one questionnaire per handle, each item pre-filled with the earlier answer and its date, ingestible by capture.py unchanged
- [x] #3 An ingested confirmation is a new capture with a new `on`; the old capture is never edited
- [x] #4 No name is written: questionnaires are addressed by handle only
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. capture.py due: per handle and key the latest captured answer, due six months after its on (review.add_months), none a review rejected; register links with an elicited block by review_due.
2. One questionnaire per handle (owner unit when the handle is withdrawn), capture.py's own format, answer pre-filled, earlier/earlier_on/due shown; ingest unchanged, a confirmation a new capture.
3. ingest reads KG_TODAY (review.today()).
4. tests/test_review_due.py end to end on the example instance; instance/README.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
End to end: due 2027-05-01 nothing; 2027-05-02 one questionnaire for employee-1; ingested unchanged with KG_TODAY=2027-05-03: a new capture, the old file byte-identical; due 2027-05-03 nothing; 2027-11-03 due again. No store code changed; review walkthrough green on rdflib and Neo4j 5.26 after merging main.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Route (b): capture.py due finds the captured answers whose six-month review has come (the latest per handle and key, none a review rejected). It writes one questionnaire per handle, pre-filled with the earlier answer and its date, in the format ingest already reads. A confirmation is therefore a new capture with a new on, and the old capture is never edited. A withdrawn handle's answers go to the owner unit. Register links with an elicited block are listed by review_due, since the register reviews them. ingest now reads KG_TODAY, as review does. Only handles and units are written.
<!-- SECTION:FINAL_SUMMARY:END -->
