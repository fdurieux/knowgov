---
id: TASK-0068
title: Lapse by date for review verifications, as the review-lapse decision says
status: To Do
assignee: []
created_date: '2026-11-03T23:53:00Z'
labels:
  - gate
milestone: m-5
dependencies:
  - TASK-0067
references:
  - backlog/docs/doc-0013
priority: medium
ordinal: 72000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0013 P2: build what the decision in TASK-0067 settles. Today valid_until carries no date on a review verification, so a document's review never falls due.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 valid_until carries a date on review verifications where the decision says so, in both adapters
- [ ] #2 A lapsed verification lowers the key and the gate report names it as a finding
- [ ] #3 The deterministic record is unchanged, or the comparator's change is recorded with its reason
- [ ] #4 instance/README.md and docs/guide.md say when a review falls due
<!-- AC:END -->
