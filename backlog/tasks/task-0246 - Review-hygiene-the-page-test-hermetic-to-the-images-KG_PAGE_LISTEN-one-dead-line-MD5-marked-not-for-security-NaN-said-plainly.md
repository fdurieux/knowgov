---
id: TASK-0246
title: >-
  Review hygiene: the page test hermetic to the image's KG_PAGE_LISTEN, one dead
  line, MD5 marked not for security, NaN said plainly
status: Done
assignee:
  - '@claude'
created_date: '2026-11-09T06:59:00Z'
updated_date: '2026-11-09T07:58:00Z'
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
- [x] #1 test_page_subject passes with KG_PAGE_LISTEN=0.0.0.0 in the environment and unset
- [x] #2 index.html's dead line is gone; annotate.py's md5 calls pass usedforsecurity=False with their fingerprints unchanged; store.py's NaN check reads math.isnan, a test holding NaN refused
- [x] #3 The deterministic comparator passes with the record unchanged
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. tests/test_page_subject.py: the request_names test sets KG_PAGE_LISTEN=127.0.0.1 for its run and restores the previous value.
2. demo/app/index.html: drop the unused const st line in assertionCell.
3. harness/annotate.py _fingerprint: md5(..., usedforsecurity=False) in both calls, with a test pinning the values to plain md5.
4. harness/store.py: math.isnan(v) in place of v != v, with a test refusing nan in every spelling for every float setting.
5. CHANGELOG Unreleased › Changes; the deterministic comparator unchanged.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
(1) test_every_route_answers_within_the_subject_the_request_names saves KG_PAGE_LISTEN, sets it to 127.0.0.1 and restores it in finally. It passes unset and with 0.0.0.0; with 0.0.0.0 it failed before (403 ahead of 404).
(2) assertionCell's const st = sid && byId[sid] ? null : null; removed; nothing read st.
(3) _fingerprint's two hashlib.md5 calls pass usedforsecurity=False. tests/test_annotate.py::test_the_fingerprint_is_the_md5_of_its_base_as_before_usedforsecurity holds both values equal to the plain md5 of their base strings, so no annotation fingerprint moves.
(4) store.py imports math, and the float-setting check reads if math.isnan(v) or not (lo <= v <= hi). tests/test_store_generations.py::test_a_nan_setting_is_refused_by_isnan refuses nan, NaN, -nan and +nan for every float setting.
Checks: run_tests 903/904 (1 skipped) on the pins, unset and with KG_PAGE_LISTEN=0.0.0.0, and 848/904 (56 skipped) bare. Deterministic comparator: CargoQuote 0 differing leaves over 7 scenarios, J-F 0 over 6. check_round_trip --chain rdflib,rdflib on CargoQuote: equal.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Four review findings fixed, none changing behaviour. The page test pins KG_PAGE_LISTEN to 127.0.0.1 for its run, so it passes inside the image, whose Dockerfile sets 0.0.0.0. index.html loses an unused line. annotate.py's MD5 fingerprints pass usedforsecurity=False, so a FIPS-mode Python accepts them, and a test pins their values. store.py's NaN check reads math.isnan, and a test refuses every spelling of nan for every float setting. The suite is green on the pins (unset and 0.0.0.0) and bare, and both deterministic comparators show 0 differences with the record unchanged.
<!-- SECTION:FINAL_SUMMARY:END -->
