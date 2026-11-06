---
id: TASK-0157
title: >-
  B7: subject on every reader and knowgov-runs tool, and list_subjects, per
  decision-0013 (doc-0021 G4)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-06T04:53:00Z'
updated_date: '2026-11-06T09:36:00Z'
labels:
  - mcp
  - subject
dependencies:
  - TASK-0151
documentation:
  - >-
    backlog/decisions/decision-0013 -
    One-MCP-reader-for-several-subjects-the-subject-named-by-id-under-KG_SUBJECTS-defaulting-to-KG_SUBJECT-served-by-a-child-process-per-call.md
  - >-
    backlog/docs/doc-0026 -
    Spike-task-0151-one-MCP-reader-for-several-subjects-measured-doc-0021-S3-G4-2026-11-06.md
priority: low
type: feature
ordinal: 164000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0021 G4: both MCP servers answer for one subject per process, so n subjects mean 2n client registrations. task-0151's spike measured three designs (doc-0026); decision-0013, proposed, chooses (a), a child process per call, by AC #2's rule. Build only once decision-0013 is accepted by the maintainer, and after 0.7.0 (shipped). Scope as the decision states: an optional subject id on every tool of both servers, resolved under KG_SUBJECTS, never a path; none named answers as today, from KG_SUBJECT; list_subjects; a named subject other than the process's own runs in a child process with KG_SUBJECT set. If S2 (task-0141.06) moves the Neo4j number of (a) above 0.7 s, re-measure before building.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Every tool of the reader and of knowgov-runs takes an optional subject, an id under KG_SUBJECTS; a path, an unknown id or one outside KG_SUBJECTS is refused; none named answers exactly as today
- [x] #2 list_subjects names every subject under KG_SUBJECTS and the default (KG_SUBJECT)
- [x] #3 A call naming another subject is answered by a child process with that subject's KG_SUBJECT, equal to what a server started on that subject answers; check_mcp_server.py holds it over stdio and HTTP
- [x] #4 Additive tool-schema change: CHANGELOG under Contract changes; instance/README's one-subject-per-process note updated
- [x] #5 A1 (decision-0013, accepted 2026-11-06): every tool is classed as store-backed or not, visible to a client; a store-backed tool naming a subject whose scenario the store does not hold refuses, naming the held subject and scenario and the run to start; list_subjects names each subject's held scenario or none; no load-on-demand (the reader never writes)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Re-measure (a) on Neo4j on main before building (stop above 0.7 s).
2. harness/subject_ids.py: ids under KG_SUBJECTS by the page's rules, never a path.
3. mcp_server: subject on every tool, _meta io.knowgov/storeBacked, list_subjects, a child process per call for another subject (harness/mcp_child.py), A1 refusal naming the held subject and the start_run.
4. mcp_runs: subject forwarded to the page as ?subject=.
5. tests/test_mcp_subjects.py; check_mcp_server.check_subjects over stdio and HTTP.
6. CHANGELOG Contract changes; instance/README and the onboarding skill drop the per-subject relaunch.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Re-measure on main before building (Neo4j, after S2 and task-0097): (a) gate_verdict cold 1.365 s, median 0.421 s, p95 0.506 s (< 0.7 s); register_nodes 0.074 s.
AC1: SUBJECT_ARG on all 16 reader tools and the 3 knowgov-runs tools; subject_ids.resolve refuses a path, a bad shape, ".." and an id outside KG_SUBJECTS (test_a_subject_is_an_id..., test_a_path_or_an_unknown_subject_is_refused_on_every_tool); none named and the own id named answer the same (test_none_named_or_the_own_subject_named...).
AC2/AC5: list_subjects names default, each subject with its held scenario or null, store.held_by/unavailable, store_backed and files_only; every tool carries _meta io.knowgov/storeBacked; a store-backed call for an unheld subject refuses with the held subject and scenario and a start_run {subject, scenario, mode} line; a real rdflib store is byte-identical after the routed calls (test_the_routed_store_backed_refusal...).
AC3: route_to_child runs harness/mcp_child.py with KG_SUBJECT, the session's as_of, KG_INSTANCE/KG_LEDGER; check_mcp_server.check_subjects holds register_nodes and scenario_runs equal to a reader started on the other subject over stdio and HTTP, both ways (KG_STORE=rdflib S1 on cargo_quote; C on jef_data_load), and on Neo4j by hand.
AC4: CHANGELOG Unreleased > Contract changes; instance/README "One registration for every subject"; SKILL.md step 1 is now list_subjects (wizard --check clean; test_wizard updated).
Suites: stdlib 594/615 0 failed; KG_SUBJECT=jef 593/615 0 failed; pinned rdflib 614/615 0 failed once the local Neo4j was stopped.
Found, out of scope: instance/ci/knowgov-gate.sh subject() calls exit 2 inside $(subject), so an instance with no or several subjects falls through to the harness default subject; test_ci_wrappers only passes because no store is reachable in CI (with a local Neo4j up it ran cargo_quote and exited 0). Reported to the coordinator.
<!-- SECTION:NOTES:END -->

## Comments

<!-- COMMENTS:BEGIN -->
created: 2026-11-06T08:20:00Z

---

2026-11-06: decision-0013 accepted by the maintainer with amendment A1 ("approve decision-0013 with amendment A1"). Build is unblocked. Before building, re-measure (a)'s Neo4j p95 after S2 (task-0141.06) and task-0097's snapshot cache; re-measure in full if it exceeds 0.7 s. The shared-store remedy, per-subject read snapshots, is a separate parked task (O3); the port's instance= is a no-op today and is neither relied on nor removed.

---
<!-- COMMENTS:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Both MCP servers answer for every subject under KG_SUBJECTS by id (decision-0013 (a) with A1): an optional subject on every tool, list_subjects, tools classed store-backed or files-only in _meta, another subject answered by a child process equal to a reader started on it, a store-backed call for an unheld subject refused with the held subject and the start_run to load it; the reader never writes. Additive contract change in CHANGELOG; README and onboarding skill no longer relaunch per subject. Neo4j p95 0.506 s re-measured before building.
<!-- SECTION:FINAL_SUMMARY:END -->
