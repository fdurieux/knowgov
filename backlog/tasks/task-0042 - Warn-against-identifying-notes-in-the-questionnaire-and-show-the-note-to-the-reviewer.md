---
id: TASK-0042
title: >-
  Warn against identifying notes in the questionnaire, and show the note to the
  reviewer
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
type: chore
ordinal: 54000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0007 F6: a capture's free-text `note` is copied into the assertion's text and the gate's bundle. A note such as "as the author of the 2025 memo" identifies the person behind an opaque handle, which the privacy rule (ieam-register decision 0008) exists to prevent. A pattern cannot catch it; the questionnaire can warn and the reviewer can check.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The questionnaire header says a note must not identify the person who answers
- [ ] #2 instance/README.md "Capturing what people know" says the same in the adopter register
- [ ] #3 tests/test_capture.py checks the warning is in a generated questionnaire
<!-- AC:END -->
