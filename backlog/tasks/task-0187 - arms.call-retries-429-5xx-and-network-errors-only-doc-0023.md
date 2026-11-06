---
id: TASK-0187
title: arms.call retries 429, 5xx and network errors only (doc-0023)
status: To Do
assignee: []
created_date: '2026-11-06T23:05:00Z'
labels:
  - arms
dependencies: []
references:
  - harness/arms.py
priority: low
type: bug
ordinal: 187000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer accepted doc-0023's advice on 2026-11-06 ("accept the advice on all three"). arms.call retries every exception four times with waits of 5, 10 and 15 s: in the probe, the 400 for an effort the model refuses cost 30 s and four requests before it was reported.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A 400 or another 4xx but 429 is reported at once, without a retry
- [ ] #2 429, 5xx and network errors are retried with the existing waits
- [ ] #3 Tests on scripted errors hold both
<!-- AC:END -->
