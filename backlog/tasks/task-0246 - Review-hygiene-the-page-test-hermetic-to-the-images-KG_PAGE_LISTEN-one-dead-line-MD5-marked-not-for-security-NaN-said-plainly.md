---
id: TASK-0246
title: >-
  Review hygiene: the page test hermetic to the image's KG_PAGE_LISTEN, one dead
  line, MD5 marked not for security, NaN said plainly
status: To Do
assignee: []
created_date: '2026-11-09T06:59:00Z'
labels:
  - hygiene
  - tests
dependencies: []
priority: low
ordinal: 240000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From the third-party code review at 4c7fcb0, re-verified at main 6d27961 (doc-0033). (1) tests/test_page_subject.py's request_names test fails inside the image, whose Dockerfile sets KG_PAGE_LISTEN=0.0.0.0: the wide-bind refusal (403) answers before subject routing (404); the test pins the variable it depends on. (2) demo/app/index.html:547, const st = … ? null : null, is unused. (3) harness/annotate.py's two MD5 fingerprints pass usedforsecurity=False, so a FIPS-mode Python does not refuse them. (4) harness/store.py:720's v != v becomes math.isnan(v) with the same meaning. No behaviour moves.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 test_page_subject passes with KG_PAGE_LISTEN=0.0.0.0 in the environment and unset
- [ ] #2 index.html's dead line is gone; annotate.py's md5 calls pass usedforsecurity=False with their fingerprints unchanged; store.py's NaN check reads math.isnan, a test holding NaN refused
- [ ] #3 The deterministic comparator passes with the record unchanged
<!-- AC:END -->
