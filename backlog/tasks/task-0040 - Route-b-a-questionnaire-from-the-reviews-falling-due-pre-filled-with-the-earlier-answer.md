---
id: TASK-0040
title: >-
  Route (b): a questionnaire from the reviews falling due, pre-filled with the
  earlier answer
status: To Do
assignee: []
created_date: '2026-11-02T23:22:00Z'
labels:
  - capture
milestone: m-2
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
- [ ] #1 A command lists the captured statements and register links with an elicited block whose review falls due on or before a given date
- [ ] #2 It writes one questionnaire per handle, each item pre-filled with the earlier answer and its date, ingestible by capture.py unchanged
- [ ] #3 An ingested confirmation is a new capture with a new `on`; the old capture is never edited
- [ ] #4 No name is written: questionnaires are addressed by handle only
<!-- AC:END -->
