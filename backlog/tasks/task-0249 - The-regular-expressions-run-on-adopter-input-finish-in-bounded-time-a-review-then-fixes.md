---
id: TASK-0249
title: >-
  The regular expressions run on adopter input finish in bounded time (a review,
  then fixes)
status: To Do
assignee: []
created_date: '2026-11-09T06:59:00Z'
labels:
  - security
  - parsing
dependencies: []
priority: low
ordinal: 243000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From the third-party code review at 4c7fcb0, re-verified at main 6d27961 (doc-0033) (Sonar's regex runtime warnings). No denial of service was reproduced, but the mappers, the pre-load check and the subject checker run patterns over adopter documents and manifests. Review each pattern that reads input knowgov does not author for catastrophic backtracking, bound or rewrite the ones at risk, and add a timing test for each fixed one. A fix-class item for 0.9.x, not a cut condition (doc-0033 advice 5).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Every regular expression applied to adopter-supplied text is listed with its verdict (bounded or rewritten)
- [ ] #2 Each rewritten pattern has a test holding its old matches and a worst-case input finishing under a stated bound
<!-- AC:END -->
