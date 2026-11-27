---
id: TASK-0371
title: >-
  capture.py questionnaire after a change: stage 2, the old and the new text on
  each stale key, and items for added keys (impact gap G4)
status: To Do
assignee: []
created_date: '2026-11-18T07:35:00Z'
updated_date: '2026-11-27T07:55:00Z'
labels:
  - impact
  - reverse-engineering
  - contract
  - 0.10.0
dependencies: []
priority: high
ordinal: 360000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Source: a private instance's impact and traversal study (2026-11-17), gap G4.

`capture.py questionnaire` loads stage 1 only. After a document's new version invalidates statements, the regenerated questionnaire asks the same keys with version 1's text and nothing about the keys the new version adds. In the study it re-asked 137 keys in the old words.

Placement: a contract change (decision-0016), so 0.10.0 before its cut or 1.1.0 after it; the maintainer's word. Minted on the maintainer's word, 2026-11-18: "yes, mint the six knowgov tasks".
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 capture.py questionnaire takes --stage 2 (or reads a published store) and asks each key on which a statement was invalidated
- [ ] #2 An item on a stale key carries the invalidated statement's text and its successor's, each with its version
- [ ] #3 Keys the new version adds that a task class requires get an item; unmapped ones are reported (see the G3 task)
- [ ] #4 Tests on S6's change; ingest still accepts the output; CHANGELOG line under Contract changes
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Placed in 0.10.0 on the maintainer's word, 2026-11-27: "A, and put task-0371 into 0.10.0". The reason: a private instance's arrival questionnaire, generated with this tool at the pin, asked every reworded key with its first version's text (33 of 33) and every added key with no statement at all (11 of 11, level absent). It is not committed and waits for this task. The public check stays on S6's change; the instance re-runs its own arrival once this lands.
<!-- SECTION:NOTES:END -->
