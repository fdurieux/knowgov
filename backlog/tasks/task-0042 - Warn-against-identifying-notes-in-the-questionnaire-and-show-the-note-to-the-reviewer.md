---
id: TASK-0042
title: >-
  Warn against identifying notes in the questionnaire, and show the note to the
  reviewer
status: Done
assignee:
  - '@claude'
created_date: '2026-11-02T23:22:00Z'
updated_date: '2026-11-03T23:33:00Z'
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
- [x] #1 The questionnaire header says a note must not identify the person who answers
- [x] #2 instance/README.md "Capturing what people know" says the same in the adopter register
- [x] #3 tests/test_capture.py checks the warning is in a generated questionnaire
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Questionnaire header: a note must not identify the person; nothing checks it but the reviewer.
2. capture.py review --show: each ruled answer with its note, from the capture files (review.capture_index gains value, note); writes nothing.
3. instance/README: the warning, and --show before ruling; reject and re-capture an identifying note.
4. Tests.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
No pattern check added, by design (F6). The gate CLI shows no assertion text; render_key's bundle shows text incl. note truncated at 300 chars, so --show reads the capture file whole. Ran --show on the example instance: prints value and note, exit 0, no review written.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Questionnaire header warns that a note must not identify the person and that only the reviewer checks it. New capture.py review FILE --show prints each ruled captured answer with its note (from the capture files) and writes nothing; README tells the reviewer to run it first and to reject a statement whose note identifies, the corrected answer being a new capture. No pattern pretends to catch an identifying note. Tests: the warning in every generated questionnaire and the README; show_rulings output.
<!-- SECTION:FINAL_SUMMARY:END -->
