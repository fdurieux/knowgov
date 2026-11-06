---
id: TASK-0159
title: >-
  V1 completion: coverage with a declared denominator, instance/** in demo.yml's
  path filter, job timeouts and cleanup traps, machine-readable outcomes
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-06T06:18:00Z'
updated_date: '2026-11-06T07:11:00Z'
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

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. AC #2: instance/** in demo.yml's pull_request and push path filters.
2. AC #3: timeout-minutes on every job of harness.yml, demo.yml and tests.yml, each above the job's observed worst execution (GitHub API, first attempts, 2026-11-04..06): tests 2.9 min (its long run spans were queueing) -> 20; rdflib 71.8 min (push, the full J-F set) -> 120; stack 25.4 min (push) -> 60; publish 0.9 min -> 30. Cleanup: the compose stack's teardown is if: always() already; the docker run workers are --rm in the foreground; tools/check_mcp_server.py's servers are killed after a bounded wait when they do not exit. A test holds every job's timeout above the recorded worst case, the path filter and the teardown.
3. AC #4: tests/run_tests.py writes a JSON outcome file (KG_TEST_REPORT): every test pass, fail or skip with the skip's reason and seconds. The check tools record their outcomes through one helper (tools/_outcomes.py: the tool, argv, exit code, duration, and per-check pass/fail/skip where the tool reports them) when KG_OUTCOMES names a file. Kept as a CI artifact: needs actions/upload-artifact pinned by digest (a new pin; the coordinator's decision).
4. AC #1: statement and branch coverage, standard library only (sys.monitoring, CPython 3.12+; no new dependency): a tool runs the suite under it, the denominator declared (modules counted by name, those left out and why), branches from the bytecode's conditional jumps; in-process only, so no integration coverage claimed; figures recorded with their scope.
5. AC #5: measured (GitHub API): stack within budget uncontended (7.0-10.6 min with at most one other run active); rdflib over (27.4 min in the one quiet sample; median 24.9 of 128 PR runs). A proposal to split or trim that never subsets the record, with its fit/gap, to the coordinator; stop there.
<!-- SECTION:PLAN:END -->
