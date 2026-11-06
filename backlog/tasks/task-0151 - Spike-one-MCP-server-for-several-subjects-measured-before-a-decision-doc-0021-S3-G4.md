---
id: TASK-0151
title: >-
  Spike: one MCP server for several subjects, measured before a decision
  (doc-0021 S3, G4)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-05T21:46:00Z'
updated_date: '2026-11-06T04:54:00Z'
labels: []
dependencies:
  - TASK-0146
  - TASK-0148
priority: low
type: spike
ordinal: 158000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Both MCP servers answer for one subject per process (doc-0021 G4, doc-0018 F6), so every new subject means re-registering two servers in every client. Three designs: (a) a child process per call, the page's pattern; (b) a lazy pool, one child per subject; (c) the subject as a value through the harness. The maintainer (2026-11-05): measure first; decide under a decision record; build (doc-0021 B7) only after knowgov 0.7.0, so the reader is not changed under task-0141's H1 and H2.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Latency per call on rdflib and Neo4j for cargo_quote, lines touched and tests moved, for (a), (b) and (c), measured on a spike branch that is never merged
- [x] #2 A proposed decision through the CLI: subject resolved by id under KG_SUBJECTS, never a path, defaulting to KG_SUBJECT so today's clients see no change; (a) if it measures under 1 s per call on Neo4j for CargoQuote, else (c)
- [x] #3 A dated note (a backlog doc) with the numbers; B7 proposed as a task, built only after 0.7.0
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Spike branch spike/task-0151-multi-subject from 1b8fee5: harness/subject_dispatch.py (id under KG_SUBJECTS, never a path; (a) via_child, (b) Pool, with_subject, list_subjects), harness/mcp_child.py, 13 lines in mcp_server.py behind KG_SUBJECT_DISPATCH; spike/task-0151/bench.py. 2. Measure on rdflib and Neo4j 5.26 (tarball, Java 21) for cargo_quote: gate_verdict and register_nodes, cold then 20 warm, median and p95; answers equal across designs. 3. Count lines and tests moved; (c) by import-time bindings. 4. Record: doc-0026, decision-0013 (proposed, rule of AC #2), task-0157 (B7).
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-06: measured on main at 1b8fee5 as it stands (S2, task-0141.06, in build, will change the store's reads). Neo4j, cargo_quote, gate_verdict: (a) 0.433 cold, 0.344 median, 0.439 p95; (b) 0.297 / 0.113 / 0.130; (c) 0.275 / 0.106 / 0.118. Register read: (a) 0.077, (b) and (c) 0.010. rdflib gate_verdict: (a) 0.705 / 0.711 / 0.774; (b) 0.688 / 0.561 / 0.635; (c) 0.633 / 0.551 / 0.619. Answers equal across the three. Lines: (a)/(b) 173 in the prototype (13 in mcp_server.py); 1 of 565 tests moves with the switch on, 0 with it off (run_tests.py 549/565 off). (c): 17 of 32 reachable modules, 235 import-time references; 22 to 29 test files. (a)'s Neo4j p95 0.44 s is outside 30% of 1 s, so no re-measure after S2 is owed. Spike branch spike/task-0151-multi-subject at 410f71b, never merged, no PR; the owner deletes it once decision-0013 is taken. AC1: doc-0026's tables. AC2: decision-0013, proposed, (a) by the rule. AC3: doc-0026 dated; B7 is task-0157, To Do, depending on task-0151 and naming decision-0013, built only once it is accepted (0.7.0 has shipped).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Spike done: three designs for one MCP reader answering for several subjects, measured on rdflib and Neo4j for cargo_quote on a spike branch that is never merged. (a) a child process per call measures 0.34 s median and 0.44 s p95 for gate_verdict on Neo4j, under 1 s, so decision-0013 proposes it by AC #2's rule: subject by id under KG_SUBJECTS, never a path, defaulting to KG_SUBJECT. (b) and (c) are about 0.11 s warm but cost a pool lifecycle or a 17-module rewrite. doc-0026 holds the numbers and method; decision-0013 the fit/gap and SWOT, proposed for the maintainer; task-0157 is B7, To Do. B7 must still settle per-subject stores.
<!-- SECTION:FINAL_SUMMARY:END -->
