---
id: TASK-0041
title: >-
  Route (c): interview transcript to inferred statements, ending in a
  questionnaire, never in an ingest
status: To Do
assignee: []
created_date: '2026-11-02T23:22:00Z'
updated_date: '2026-11-03T22:40:00Z'
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
type: feature
ordinal: 53000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0007 §6: a model reading a transcript of a conversation with a person may propose statements; they load as basis inferred, proposed, never promoted (as S5's machine note does), and the questionnaire already lists such candidates in `known` (seen on S5). What is missing is the step from a transcript to inferred statements. The transcript is never the record (doc-0001 §0); only the person's answer to the questionnaire becomes elicited. The model endpoint is instance configuration (harness/arms.py endpoint()).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A command turns a transcript into inferred, proposed statements on required keys, attributed to the model, and writes no capture
- [ ] #2 The questionnaire generated afterwards lists those candidates in `known`, and the person confirms by answering
- [ ] #3 The transcript is not copied into the store, the captures or the register
- [ ] #4 With no model key configured the command refuses to run (exit 2), as the arms do
<!-- AC:END -->
