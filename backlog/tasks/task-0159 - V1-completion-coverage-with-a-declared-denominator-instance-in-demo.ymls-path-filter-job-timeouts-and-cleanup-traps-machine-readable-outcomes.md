---
id: TASK-0159
title: >-
  V1 completion: coverage with a declared denominator, instance/** in demo.yml's
  path filter, job timeouts and cleanup traps, machine-readable outcomes
status: To Do
assignee: []
created_date: '2026-11-06T06:18:00Z'
labels:
  - ci
  - security
dependencies:
  - TASK-0141
priority: medium
ordinal: 165000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The 2026-11-05 code and architecture review's plan (task-0141) runs a cross-cutting package, V1, through every work package. task-0141 closed with E0's skip accounting (tests/_skip.py, KG_TEST_REQUIRE) and with security checks that fail without their real backend (tools/check_worker.py, tools/check_snapshots.py). Four of V1's items were not done, and no AC of task-0141 named them. Its CI budget (task-0084, 12 minutes per pull request for rdflib and for stack on an uncontended runner) was also overrun while task-0141 landed: on #278 the rdflib job took about 20 minutes and stack 10 to 17. Known limits, not ACs here: H2 (task-0141.04) bounds request bodies, connections and admitted work but not response size; on Neo4j a writer killed between raising the sequence lock's begin and committing makes reads wait KG_NEO4J_READ_WAIT, then refuse, until the next writer takes the lease (decision-0014). Neither has a task of its own.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Statement and branch coverage is measured with a declared denominator (the modules counted and those left out, by name), subprocesses instrumented where integration coverage is claimed, and the figures recorded with the scope they cover
- [ ] #2 demo.yml's pull_request and push path filters include instance/**, so a change to the instance template runs the stack job
- [ ] #3 Every job in harness.yml, demo.yml and tests.yml has a timeout-minutes, and every step that starts containers or servers tears them down on failure as well as on success
- [ ] #4 The test runner and the check tools write machine-readable outcomes (pass, fail and skip per test or check, with the skip's reason), kept as a CI artifact
- [ ] #5 rdflib and stack are measured on an uncontended runner against task-0084's 12-minute budget; if over, a proposal to split or trim that never subsets the record
<!-- AC:END -->
