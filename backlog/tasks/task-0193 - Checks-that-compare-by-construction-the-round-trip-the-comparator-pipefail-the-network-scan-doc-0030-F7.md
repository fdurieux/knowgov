---
id: TASK-0193
title: >-
  Checks that compare by construction: the round trip, the comparator, pipefail,
  the network scan (doc-0030 F7)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-07T07:14:00Z'
updated_date: '2026-11-07T08:24:00Z'
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
- [x] #1 differences() compares every key answers() returns; a test that differs only in store_reads is reported
- [x] #2 compare_deterministic.py counts each named or defaulted scenario missing from the run as a difference (1 of 7 present exits 1)
- [x] #3 demo.yml and harness.yml run bash with pipefail (defaults: run: shell: bash); a failing saved query fails its step
- [x] #4 test_security scans recursively (vendored folders excepted), names asyncio, ssl, socketserver, multiprocessing.connection, imaplib, poplib and nntplib, and flags import_module or __import__ of a network module; instance/ci/claude and subjects/*/oracle are scanned
- [x] #5 The scored record (S1 to S7), the deterministic run and the comparator stay equal
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. P5: check_round_trip.differences() walks every part answers() returns (store_reads included), first-seen order; tests for a store_reads-only difference and for answers()'s key set. 2. P7: compare_deterministic counts a named or defaulted scenario not in the run as a difference; demo.yml's two page-run comparisons and the README walkthrough name --scenarios S1. 3. P6: top-level defaults.run.shell bash in demo.yml and harness.yml; scan every pipe for an early-exit reader or a producer exiting non-zero on purpose; read the last main stack log for the saved-query and impact checks behind tee. 4. R11: test_security scans harness, demo/app, tools, demo/tools, instance/ci and subjects/*/oracle recursively, vendor/ excepted; adds asyncio, ssl, socketserver, imaplib, poplib, nntplib, multiprocessing.connection; reads import_module/__import__ of a literal. 5. The record: S1-S7 and J-F deterministic on rdflib, compared; suite both ways.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Verified locally. Suite: KG_TEST_REQUIRE=rdflib 697/699 (2 skipped), 0 failed; KG_SUBJECT=subjects/jef_data_load 696/699 (3 skipped), 0 failed. P7 exposed a vacuous test: test_compare_tool_finds_the_record_identical_to_itself compared CargoQuote's record under the process subject's default scenarios, which on the J-F pass were C and D1-D5, all skipped, n == 0 by comparing nothing; it now names CARGO_QUOTE.order. The record: S1-S7 on rdflib against the record, 0 differing leaves over 7 scenarios; J-F C and D1-D5, 0 over 6. check_round_trip --chain rdflib,rdflib on CargoQuote with store_reads compared: every answer survives; the Neo4j->rdflib hop, where store_reads is first compared across store kinds, is the stack job's. Pipefail risk (a): every producer in a pipe in harness.yml (check_instance, preload_check twice) exits 0 under pipefail locally; demo.yml's producers are curl -fsS, cat, find and the check tools, and the last main stack run (42320011904, job 128242012548) printed 'every saved query ran' three times and 'every node agrees' for check_impact_cypher, so no step fails today behind | tee. Network scan risk (b): the recursive scan with the new modules, instance/ci and subjects/*/oracle flags nothing beyond the stated exceptions (openai, neo4j, the three local checks, the worker probe); no dynamic import names a network module, and none uses a computed name.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
F7's four checks now compare by construction. check_round_trip.differences() walks every part answers() returns, store_reads included (P5). compare_deterministic counts a named or defaulted scenario missing from the run as a difference (P7); demo.yml's page-run comparisons and the README name --scenarios S1, and a test that compared nothing on the J-F pass now names CargoQuote's scenarios. demo.yml and harness.yml run every step under bash -eo pipefail (P6); nothing fails behind a pipe today. test_security scans recursively with more network modules and dynamic imports, instance/ci and the oracles included (R11), flagging nothing new. The record and the comparator stay equal. Watch on the stack job: the round trip's first Neo4j->rdflib comparison of store_reads.
<!-- SECTION:FINAL_SUMMARY:END -->
