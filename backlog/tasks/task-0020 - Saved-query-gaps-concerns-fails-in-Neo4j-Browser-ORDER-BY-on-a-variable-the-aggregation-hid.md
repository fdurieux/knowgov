---
id: TASK-0020
title: >-
  Saved query gaps-concerns fails in Neo4j Browser: ORDER BY on a variable the
  aggregation hid
status: Done
assignee:
  - '@claude'
created_date: '2026-11-01T17:52:00Z'
updated_date: '2026-11-01T17:54:00Z'
labels: []
milestone: m-1
dependencies: []
type: bug
ordinal: 20000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer ran the page's saved query 'The gaps, with what they concern' in Neo4j Browser on the first local start of knowgov's stack and got Neo.ClientError.Statement.SyntaxError: the RETURN aggregates (collect DISTINCT) and the ORDER BY names g.id, which is not among the returned columns. The text was ported verbatim from pumllint's demo (kg_experiment/demo/app/server.py), where it failed the same way; nothing in either repository ever ran the saved queries, so a syntax error in one reached the maintainer's console. Found while verifying the stack after PR #12.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Every saved query the page lists (the adapter's generic ones and the subject's) runs without error in Neo4j Browser against a loaded scenario with the register projected
- [x] #2 A check in CI runs the saved queries against the loaded stack so a syntax error in one fails the build
- [x] #3 The stdlib test suite stays green
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Return g.id as a column (gap) and order on it. 2. Run every saved query through the driver against S6 loaded and the register projected; all pass. 3. Add demo/tools/check_saved_queries.py and run it in the stack job of demo.yml after the comparator. 4. PR, whole matrix green, merge.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Cause: Cypher forbids ORDER BY on a pre-aggregation variable once RETURN aggregates; g.id was not a returned column. Fix: RETURN g.id AS gap and ORDER BY kind, gap (store_neo4j.SAVED_QUERIES). Verified through the driver against the session's Neo4j 5.26 with S6 loaded deterministically and the register projected: 14 statements of 13 queries, all ran (gaps-concerns 39 rows); with the old text restored the new tool reports the one failing statement and exits 1. New port operation console_query (Neo4j implements it; the port's default refuses, rdflib keeps it). test_store's port/adapter method check names the console group. 61/61 stdlib tests with and without the pins. pumllint's copy (kg_experiment/demo/app/server.py) carries the same fault; it is retired by the pending pumllint PR, not fixed there.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The saved query 'The gaps, with what they concern' now returns the gap id as a column and orders on it, so Neo4j Browser runs it. demo/tools/check_saved_queries.py runs every listed saved query statement through the new store port operation console_query and exits 1 on any error; the stack job runs it after the comparator, so a saved query that fails in the console fails CI first. Verified against Neo4j 5.26 (S6 + register): 14 statements ran; the old text fails the check. 61/61 tests.
<!-- SECTION:FINAL_SUMMARY:END -->
