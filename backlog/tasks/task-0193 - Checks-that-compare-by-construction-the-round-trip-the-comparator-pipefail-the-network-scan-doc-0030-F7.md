---
id: TASK-0193
title: >-
  Checks that compare by construction: the round trip, the comparator, pipefail,
  the network scan (doc-0030 F7)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-07T07:14:00Z'
updated_date: '2026-11-07T08:10:00Z'
labels:
  - review
  - ci
  - tests
dependencies: []
priority: high
type: task
ordinal: 193000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer accepted doc-0030's advice on 2026-11-07 ("accept the advise on all four"): the hardening tranche before 0.9.0's cut, in the order F7; F1 with the check_instance guard, H7 and M3; F3, F4 and F2; F5 and F8. The ids below are doc-0030's (the code review at 8d80b2b); each finding there quotes its lines and its probe.

First in the tranche, because until it lands a regression of every later fix can pass CI. P5: tools/check_round_trip.py collects `store_reads` in `answers()` and `differences()` never compares them, so task-0144's cross-store claim is vacuous. P6: .github/workflows/demo.yml sets no `shell:`, so steps run `bash -e` without pipefail and `check_saved_queries.py | tee` (lines 206, 232, 322, 334) discards an exit 1. P7: demo/tools/compare_deterministic.py skips a requested scenario missing from the run (1 of 7 present: exit 0). R11: tests/test_security.py scans one directory level and misses asyncio, ssl, socketserver, multiprocessing.connection, dynamic imports, instance/ci/claude and subjects/*/oracle. A fix, not bound by decision-0016's freeze.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 differences() compares every key answers() returns; a test that differs only in store_reads is reported
- [ ] #2 compare_deterministic.py counts each named or defaulted scenario missing from the run as a difference (1 of 7 present exits 1)
- [ ] #3 demo.yml and harness.yml run bash with pipefail (defaults: run: shell: bash); a failing saved query fails its step
- [ ] #4 test_security scans recursively (vendored folders excepted), names asyncio, ssl, socketserver, multiprocessing.connection, imaplib, poplib and nntplib, and flags import_module or __import__ of a network module; instance/ci/claude and subjects/*/oracle are scanned
- [ ] #5 The scored record (S1 to S7), the deterministic run and the comparator stay equal
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. P5: check_round_trip.differences() walks every part answers() returns (store_reads included), first-seen order; tests for a store_reads-only difference and for answers()'s key set. 2. P7: compare_deterministic counts a named or defaulted scenario not in the run as a difference; demo.yml's two page-run comparisons and the README walkthrough name --scenarios S1. 3. P6: top-level defaults.run.shell bash in demo.yml and harness.yml; scan every pipe for an early-exit reader or a producer exiting non-zero on purpose; read the last main stack log for the saved-query and impact checks behind tee. 4. R11: test_security scans harness, demo/app, tools, demo/tools, instance/ci and subjects/*/oracle recursively, vendor/ excepted; adds asyncio, ssl, socketserver, imaplib, poplib, nntplib, multiprocessing.connection; reads import_module/__import__ of a literal. 5. The record: S1-S7 and J-F deterministic on rdflib, compared; suite both ways.
<!-- SECTION:PLAN:END -->
