---
id: TASK-0137
title: >-
  The mid-run refusal covers register_impact and proposal_impact when they read
  key levels (doc-0016 F2, task-0128 follow-up)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-05T00:06:00Z'
updated_date: '2026-11-05T00:38:00Z'
labels:
  - mcp
  - runs
milestone: m-8
dependencies:
  - TASK-0128
priority: medium
type: bug
ordinal: 137000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
task-0128 made gate_verdict, three_valued_answer and evidence_bundle refuse while a live run.json (heartbeat within 120 s) shows a run loading the store of the server's subject. register_impact and proposal_impact also read key levels from the store when a scenario is held, and still answer mid-run: on Neo4j a load is a wipe and steps, so they can return levels read from a partial graph, well-formed and wrong. They take the same refusal on that path, naming the run; their register-only answers (nothing held, or no key levels asked) are unaffected.

Coordinator's decision under the maintainer's night delegation (2026-11-05), canvas: Problem, two of six reading tools can answer from a half-loaded store. Options: (a) extend the refusal to their store-reading path; (b) document the gap; (c) make them read only the register mid-run. Value: one rule for every tool that reads the store. Cost: the same check call, tests. Risk: none new; the rule and its clock reads already exist. Chosen (a): (b) leaves a wrong answer possible, (c) silently changes what the tool returns.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 With a live run.json for the server's subject, register_impact and proposal_impact refuse on any call that reads key levels from the store, naming the run; with nothing held, or a stale heartbeat, they answer as before
- [x] #2 Tests on rdflib cover both tools, live and stale, and another subject's run (no refusal)
- [x] #3 instance/README.md's tool table and the CHANGELOG line (Unreleased, contract changes) say so
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. mcp_server: _not_mid_run() before register_impact's gate_cli.evaluate and proposal_impact's pi.with_levels, the paths that read key levels from the store.
2. Tests: live refuses naming the run, nothing held answers from the register, stale and another subject's run do not refuse; an rdflib-store case.
3. instance/README.md table and refusal paragraph; CHANGELOG.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
The refusal sits after _check_scenario and just before the level read, so another subject's held scenario still refuses as task-0126's, nothing held answers from the register, and a call with no keys landed reads no levels and is not refused. Evidence: tests/test_impact_mid_run.py (4 tests: live, nothing held, stale, another subject's run; and a real rdflib store, run in the rdflib job's interpreter, passing locally in a venv with the pins); both suites 429/429.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
register_impact and proposal_impact now refuse, naming the run, while a run.json of the server's subject reads running with a live heartbeat, on the path where they read key levels from the store; register-only answers are unchanged. One rule for every reading tool. Verified by tests/test_impact_mid_run.py on a stub and on rdflib, both suites 429/429. instance/README.md (table and refusal paragraph) and CHANGELOG updated.
<!-- SECTION:FINAL_SUMMARY:END -->
