---
id: TASK-0137
title: >-
  The mid-run refusal covers register_impact and proposal_impact when they read
  key levels (doc-0016 F2, task-0128 follow-up)
status: To Do
assignee: []
created_date: '2026-11-05T00:06:00Z'
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
- [ ] #1 With a live run.json for the server's subject, register_impact and proposal_impact refuse on any call that reads key levels from the store, naming the run; with nothing held, or a stale heartbeat, they answer as before
- [ ] #2 Tests on rdflib cover both tools, live and stale, and another subject's run (no refusal)
- [ ] #3 instance/README.md's tool table and the CHANGELOG line (Unreleased, contract changes) say so
<!-- AC:END -->
