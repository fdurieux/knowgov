---
id: TASK-0159
title: >-
  V1 completion: coverage with a declared denominator, instance/** in demo.yml's
  path filter, job timeouts and cleanup traps, machine-readable outcomes
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-06T06:18:00Z'
updated_date: '2026-11-06T07:42:00Z'
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
- [x] #5 rdflib and stack are measured on an uncontended runner against task-0084's 12-minute budget; if over, a proposal to split or trim that never subsets the record
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. AC #2: instance/** in demo.yml's pull_request and push path filters.
2. AC #3: timeout-minutes on every job of harness.yml, demo.yml and tests.yml, each above the job's observed worst execution (GitHub API, first attempts, 2026-11-04..06): tests 2.9 min (its long run spans were queueing) -> 20; rdflib 71.8 min (push, the full J-F set) -> 120; stack 25.4 min (push) -> 60; publish 0.9 min -> 30. Cleanup: the compose stack's teardown is if: always() already; the docker run workers are --rm in the foreground; tools/check_mcp_server.py's servers are killed after a bounded wait when they do not exit. A test holds every job's timeout above the recorded worst case, the path filter and the teardown.
3. AC #4: tests/run_tests.py writes a JSON outcome file (KG_TEST_REPORT): every test pass, fail or skip with the skip's reason and seconds. The check tools record their outcomes through one helper (tools/_outcomes.py: the tool, argv, exit code, duration, and per-check pass/fail/skip where the tool reports them) when KG_OUTCOMES names a file. Kept as a CI artifact: needs actions/upload-artifact pinned by digest (a new pin; the coordinator's decision).
4. AC #1: statement and branch coverage, standard library only (sys.monitoring, CPython 3.12+; no new dependency): a tool runs the suite under it, the denominator declared (modules counted by name, those left out and why), branches from the bytecode's conditional jumps; in-process only, so no integration coverage claimed; figures recorded with their scope.
5. AC #5: measured (GitHub API): stack within budget uncontended (7.0-10.6 min with at most one other run active); rdflib over (27.4 min in the one quiet sample; median 24.9 of 128 PR runs). A proposal to split or trim that never subsets the record, with its fit/gap, to the coordinator; stop there.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-06 evidence. AC #1 coverage (tools/coverage_stdlib.py, sys.monitoring, no new dependency): denominator 89 files counted (harness/, demo/app/, tools/, demo/tools/, instance/, .claude/hooks/), left out by named rule (tests/; subjects/*/vendor, demo/model, demo/register vendored and pinned by digest; subjects/*/oracle run only in child processes), a test holding every .py of the repository counted or left out; statements are line-table lines, branches the two outcomes of each POP_JUMP_IF_* and FOR_ITER; in-process only, no integration coverage claimed. Figures 18461 statements, 15762 branch outcomes: CargoQuote with the pins 67.6% statements, 47.2% branches; J-F with the pins 65.4%, 45.4%; CargoQuote stdlib (3.13) 60.8%, 43.2%. By folder (CargoQuote, pins): demo/app 93.9%/68.6%, harness 74.9%/52.9%, demo/tools 63.6%/46.8%, tools 45.1%/29.0%, instance 30.7%/13.6%, .claude 48.0%/10.9%; the modules at 0% (run.py, worker_job.py, the check tools, _outcomes.py) run only as child processes. The review's 71.0%/66.0% was another scope (a local unit-plus-CargoQuote sample) and is not comparable. AC #2: instance/** in demo.yml's pull_request and push filters; tests/test_ci_hygiene.py. AC #3: timeouts tests 20, rdflib 120, stack 60, publish 30 against job execution worst cases tests 2.9, rdflib 71.8 (push, full J-F), stack 25.4 (push), publish 0.9 (GitHub API, first attempts, 2026-11-04..06; run spans include up to ~20 min of queueing, which a job timeout does not count); the compose teardown is if: always() already, the docker run workers --rm in the foreground, check_mcp_server's servers now killed after a bounded wait; tests/test_ci_hygiene.py holds each timeout >= max(1.5 x worst, worst + 10) and > 12. AC #4: KG_TEST_REPORT (the runner's JSON) and KG_OUTCOMES (tools/_outcomes.py, every check tool exits through it; per-check outcomes from check_worker and check_snapshots, the SNAP-07 skip with its reason); each job's summary (tools/outcomes_summary.py); tests/test_outcomes.py. The CI artifact upload waits on the coordinator's decision (actions/upload-artifact would be a new pin). Suite four ways, 0 failed: CargoQuote pins 584/585, stdlib 568/585; J-F pins 583/585, stdlib 567/585.

AC #5, measured 2026-11-06 (GitHub API, pull-request jobs, first attempts; concurrency = other workflow runs active during the job):
- stack within task-0084's 12 minutes uncontended: 7.0-10.6 min in the 14 runs with at most one other run active; median 10.6 over 128 PR runs, max 17.7.
- rdflib over: 27.4 min in the one quiet run (one other active); fastest of 128 PR runs 15.6, median 24.9, max 36.7; on push to main (the full J-F set) 64.7-71.8.
- Where rdflib's time goes (median of the 8 latest PR jobs): MCP server step 8.3 min, round trip 5.1, lighthouse 2.6, suite 1.7, J-F record 1.7, SNAP 1.4, oracle 1.0, citations 0.8, gate 0.8, review 0.7, the rest under 0.5 each.
Proposal, none of which subsets the record:
(A) split rdflib into two parallel jobs, the record and its round trip, and the readers (MCP, lighthouse, SNAP, review, capture, transcript); each half ~12-14 min; a second runner per PR; it gates only once the maintainer adds the new job to the ruleset's required checks.
(B) trim the MCP step through task-0097 (rescoped: a per-process cache of rdflib's parsed snapshot); no change to what runs. Expected to remove much of the MCP step's 8.3 min but not all: the ~4 s per J-F call measured by task-0095 is the parse, an estimated 3-5 min; rdflib then ~20-22 min, still over.
(C) the lighthouse step (2.6 min, evidence, not the record) on push and nightly only: changes what a PR runs.
(D) restate rdflib's budget.
Coordinator's decision (2026-11-06, under the delegation): B now (task-0097, another session); A to the maintainer as its own task, measured after B; C and D not taken.
<!-- SECTION:NOTES:END -->
