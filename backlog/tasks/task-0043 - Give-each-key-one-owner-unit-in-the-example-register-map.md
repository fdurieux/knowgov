---
id: TASK-0043
title: Give each key one owner unit in the example register map
status: To Do
assignee: []
created_date: '2026-11-02T23:22:00Z'
labels:
  - capture
milestone: m-2
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
- [ ] #1 Each required key of cargo_quote maps to register nodes of one owner unit, or the questionnaire picks one owner per key by a stated rule
- [ ] #2 capture.py questionnaire on S2 writes questionnaires whose key sets do not overlap
- [ ] #3 The comparator and tests/test_subject.py stay green
<!-- AC:END -->
