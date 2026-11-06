---
id: TASK-0141
title: >-
  Critical fixes from the 2026-11-05 code and architecture review: persistence,
  the HTTP boundary, execution containment, consistent publication
status: Done
assignee: []
created_date: '2026-11-05T20:33:00Z'
updated_date: '2026-11-06T06:16:00Z'
labels:
  - security
dependencies: []
priority: high
type: bug
ordinal: 141000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
An external review of knowgov at 98fc796 (2026-11-05) found defects that lose or misreport evidence without an attacker, and gaps at the trust boundaries: a file-backed store reader can publish a stale snapshot over a newer one on close; the page and the MCP server do not check the request authority and the browser origin independently; request bodies, connections and admitted work are unbounded; code an arm generates runs with the orchestrator's environment and filesystem; and a reader can see a store part-way through a rebuild. Its implementation plan (work packages E0, S1, H1, H2, X1, S2 and V1, with regression ids ENV-, ST-, HTTP-, LIMIT-, EXEC- and SNAP-) is the acceptance contract. It travels in the implementing session's brief and is not committed while the fixes are open, the repository being public. Order set by the maintainer: E0, S1, H1, H2, X1, S2, with V1 throughout, each package validated before the next. Out of scope: framework migration, evidence levels or approval rules, the record, bulk dependency upgrades.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Every subtask's regression ids are implemented, executed and linked to their evidence; a package is complete on its safety property and acceptance tests, never on an overall green suite
- [x] #2 A required check that is skipped or blocked by its environment is reported apart from the passes, and a required security job fails when its backend is absent (V1)
- [x] #3 The record, vendored bytes, deterministic results, schema versions and exit codes are unchanged, or the change is a recorded contract change with its CHANGELOG line
- [x] #4 The final summary carries the work-package matrix: regression ids and results, integration evidence, compatibility changes, remaining blockers
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-05, release timing (maintainer, "agreed, hold 0.7.0 until then"): knowgov 0.7.0 is held until task-0141.01-.04 (E0, S1, H1, H2) and tasks 0142 and 0143 have merged, so it ships with the connector MANIFEST change of #233 (decision-0010) as one release. X1 and S2 follow in a later release unless they land first.

2026-11-06, closing (S2 sub-session): every sub-task Done; each package merged on a full green matrix by the coordinating session. AC #2 rests on E0's skip accounting (tests/_skip.py, KG_TEST_REQUIRE; the rdflib job runs the suite with KG_TEST_REQUIRE=rdflib) and on the security checks needing their real backend: tools/check_worker.py fails without an attested worker, tools/check_snapshots.py runs against the stack's Neo4j and a file-backed store. Not done, from the plan's V1 and named by no AC: statement and branch coverage with a declared denominator; instance/** in demo.yml's path filter; job timeouts and cleanup traps; machine-readable test outcomes. Residuals: H2 caps request bodies, not response size; CI budget (task-0084): on #278 the rdflib job ran ~20 min and stack 10-17 min against 12; the Neo4j window between raising begin and committing (documented, decision-0014).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Work-package matrix (the review of 2026-11-05; plan not committed).

| Package | Regression ids and results | Integration evidence | Compatibility changes | Remaining |
|---|---|---|---|---|
| E0 task-0141.01, #237 fe48266 | ENV-01..04 pass (tests/test_ci_wrappers.py); mismatch reproduced on the baseline | CI wrappers in harness.yml; suite with KG_TEST_REQUIRE=rdflib | the shell wrappers need Python 3.12+, exit 2 with the reason | none |
| S1 task-0141.02, #243 af6f0eb | ST-01..09 pass (tests/test_store_persistence.py); ST-01, 04, 06, 07 reproduced first | comparator on rdflib and Neo4j; round trips | open_store(access=) required; writers publish on commit only; StoreBusy, StoreCorrupt; KG_RDFLIB_LOCK_TIMEOUT | none |
| .07 task-0141.07, #262 3587b26 | interim guard tests (tests/test_execution_guard.py) | page and run.py refuse beside a mounted instance | KG_ALLOW_UNCONTAINED_EXECUTION | superseded in practice by X1 |
| H1 task-0141.03, #264 01f7e06 | HTTP-01..08 pass (tests/test_http_boundary.py); baseline reproduced | check_impact_cypher on the real page; check_mcp_server | authority and origin allow-lists (KG_PAGE_*, KG_MCP_*); the MCP Inspector needs KG_MCP_ORIGINS; forwarded headers never read | none |
| H2 task-0141.04, #266 e0d9b9a | LIMIT-01..07 pass (tests/test_http_limits.py); baseline reproduced | both servers under small injected limits | page POSTs need Content-Length; n typed 1..5; KG_PAGE_*, KG_MCP_* limits | response size not capped |
| X1 task-0141.05, #271 ee5d1e3, decision-0012 | EXEC-01..03, 05..07, 09 on the real worker container (tools/check_worker.py, stack); EXEC-04, 08 in tests/test_execution.py; loosened workers refuse | CargoQuote 11/11 and J-F 12/12 graded in the worker | arms run only through an attested worker (KG_WORKER_JOBS); the 0.7.0 image predates it | Linux with Landlock only, refused elsewhere |
| S2 task-0141.06, #278 7f13676, decision-0014 (#280 bcb6bf7) | SNAP-01..07 hold on Neo4j 5.26 and file-backed rdflib (tools/check_snapshots.py) | the check in the rdflib and stack jobs; comparator incl. D1, D2; neo4j,rdflib,neo4j round trips on both subjects with parts and preload; the 2m memory proof local only | Neo4j loads visible only at commit; StoreChanged, StoreFenced, store.read; refusals (exit 2, MCP error, 503 + Retry-After); projection 409; bounded KG_NEO4J_*, KG_STORE_READ_ATTEMPTS | the begin-to-commit window; transaction memory bounds a unit |
| V1 (throughout) | skip accounting and required backends (E0, the rdflib job, check_worker, check_snapshots) | every package's CI | none | coverage with a denominator; instance/** in stack's paths; job timeouts and cleanup traps; machine-readable outcomes; CI budget overrun |

The record, vendored bytes, deterministic results, schema versions and exit codes are unchanged; every contract change has its CHANGELOG line (0.7.0 and Unreleased).
<!-- SECTION:FINAL_SUMMARY:END -->
