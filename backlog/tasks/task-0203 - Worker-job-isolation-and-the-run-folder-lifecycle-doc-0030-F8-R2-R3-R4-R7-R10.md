---
id: TASK-0203
title: >-
  Worker job isolation and the run-folder lifecycle (doc-0030 F8: R2, R3, R4,
  R7, R10)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-07T07:15:00Z'
updated_date: '2026-11-08T12:14:00Z'
labels:
  - review
  - worker
  - runs
dependencies: []
priority: medium
type: bug
ordinal: 203000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer accepted doc-0030's advice on 2026-11-07 ("accept the advise on all four"): the hardening tranche before 0.9.0's cut, in the order F7; F1 with the check_instance guard, H7 and M3; F3, F4 and F2; F5 and F8. The ids below are doc-0030's (the code review at 8d80b2b); each finding there quotes its lines and its probe.

R4: the reaper kills one level of escaped descendants per round for 50 rounds (worker.py:298-317); a 70-deep setsid chain leaves 21 processes alive, never killed. R7: model code can forge the job result through the parent's stdout during the 5 s drain. R10: write_confined is attested at Landlock ABI 1 though truncation is denied only from ABI 3. R2: a worker-reported timeout or kill raises and aborts the whole run (execution.py:282), where the host records a failed cell. R3: a reused --out folder carries an earlier attempt's sandbox, usage and stage-2 input into the record. Fixes.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 After each job no process of uid 65534 but the worker remains, within a time bound, by a probe with a deep setsid chain
- [x] #2 worker_job.py is non-dumpable and its output is closed at exit, so the forge probe fails; write_confined is attested only at Landlock ABI 3 or later
- [x] #3 A job-stage error becomes the kind's failed cell, and summary.json, usage.json and SHA256SUMS are still written
- [x] #4 A fresh cell clears its sandbox, usage.json merges only under --resume, and stage 2's derived input is an explicit flag
- [x] #5 The scored record (S1 to S7), the deterministic run and the comparator stay equal
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. R4. worker._reap_orphans kills every descendant of the worker (the subreaper), at any depth at once, each round, reaping the dead, until none is left or REAP_S (10 s) passes. It no longer kills one level a round for 50 rounds. Descendants of the worker, not every uid-65534 process, so the compose healthcheck (worker.py --attest-only as uid 65534 in the same container) is never killed.
2. R7. worker_job.py is made non-dumpable (prctl PR_SET_DUMPABLE 0). Its stdout moves to a private descriptor, close-on-exec, and fd 1 points at /dev/null; the one answer line is written there and the descriptor closed.
3. R10. write_confined requires landlock_abi() >= 3, and the attestation carries landlock_abi. execution.attested's refusal names the ABI, and the page's worker chip shows 'Landlock ABI N, 3 needed'. The docs' platform floor moves from Linux 5.13 to 6.2.
4. R2. execution.run maps a job-stage error the model output caused (timeout, killed, output, harness_error) to execution.failed_cell(kind), so the run goes on. A job the app wrote wrong ('job' stage) and ExecutionRefused still raise.
5. R3. run.py one_agent empties its sandbox before a fresh cell. _write_usage merges an earlier usage.json only under --resume. Stage 2's derived input comes from --stage2-derived, else the file this invocation wrote (WRITTEN), else, under --resume, the earlier attempt's; never a reused --out's leftover (run.stage2_derived).
6. Probes in tools/worker_probes.py: a 70-deep setsid chain with a survivors count, and a forge through /proc. tests/test_worker_isolation.py runs them on a worker process as uid 65534 under its real Landlock domain (as root), and check_worker.py adds EXEC-11 to EXEC-13 and the R10 attestation check for the stack. Each fails on the old code first.
7. Docs (demo README, compose comment, docs/security.md) and CHANGELOG: the attestation field and --stage2-derived under Contract changes, the fixes under Changes. Suites (pins, bare stdlib, J-F), the comparator on S1-S7 and J-F, and the round trip on both subjects.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-08 evidence.
- Where each probe ran. This container has Landlock ABI 7 and root, but no Docker daemon. tests/test_worker_isolation.py starts worker.serve in its own process, dropped to uid 65534 when the tests run as root, with its real Landlock domain (run_job confine=True). Only the attestation is stood in. The same probes (tools/worker_probes.py) are EXEC-11 to EXEC-13 in tools/check_worker.py, which the stack runs on the real worker container under --profile arms (demo.yml step 'The contained worker ... EXEC-01 to EXEC-13'). Run here against the uid-65534 worker, EXEC-11/12/13 held; EXEC-03 and J-F's EXEC-09 need the container (its network namespace; the image's pandas).
- Each probe fails on the old code first (worktree at main 6b656ed, same tests):
  - R4: '20 of the 70-deep chain outlived its job';
  - R7: the result carried the forged line ('{"stdout": "FORGED"}');
  - R2: 'RuntimeError: the worker could not run the job: the job exceeded its 4 s';
  - R10: KeyError 'landlock_abi';
  - R3: no stage2_derived.
- AC #1. On the new code a 70-deep setsid chain leaves 0 marked and 0 other uid-65534 processes outside the job's ancestry and the health check, the job and its reaping in 0.3 s. The bound is worker.REAP_S, 10 s. The sweep takes the worker's descendants, not every uid-65534 process, so the compose healthcheck (worker.py --attest-only, uid 65534, same container) is never killed; every escapee is a descendant, because the worker is their subreaper.
- AC #2:
  - the forge opens 0 of the runner's descriptors, and the answer is the job's own;
  - attest() gives write_confined True only at ABI 3 or above (tested at 0, 1, 2, 3 and 7) and carries landlock_abi;
  - execution.attested's refusal names the ABI, and the page's worker chip reads 'Landlock ABI N, 3 needed'.
- AC #3. execution.run maps the stages timeout, killed, output and harness_error to failed_cell(kind). A suite that hangs past its time returns {ran: True, passed: 0, total: 11, stage: timeout, error}, and the arm's cell is recorded like any other. A job the app wrote wrong (stage 'job') and ExecutionRefused still raise.
- AC #4. run.stage2_derived resolves --stage2-derived, else the file this invocation wrote (run.WRITTEN), else, under --resume, the earlier attempt's, and never a leftover. _write_usage merges usage.json only with resume=True. one_agent rmtree's its sandbox before agent.run.
- AC #5. Deterministic record on rdflib: CQ 0 differing leaves over 7 scenarios, J-F 0 over 6. Round trips rdflib,rdflib on CQ and on J-F with --expect-parts: every answer survives.
- Suites, all 0 failed: bare stdlib with no yaml, CQ 717/755 and J-F 717/755; pins with KG_TEST_REQUIRE=rdflib,node, 754/755. test_r3 skips under 'rdflib' without the pins.
- Contract: the attestation's landlock_abi and run.py --stage2-derived go under Unreleased › Contract changes, the rest under Changes. The platform floor for arms moves from Linux 5.13 to 6.2 (ABI 3). decision-0015's text names 5.13; it is flagged to the coordinator under DECIDE and not edited here.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
F8 hardens the worker's job isolation and the run folder's lifecycle.
- R4: after each job the worker kills every process below it, at any depth at once, within 10 s; a 70-deep setsid chain left 20 alive before, and none now.
- R7: worker_job.py is non-dumpable and answers on a private descriptor no child inherits, so model code cannot forge its answer.
- R10: write_confined is attested only at Landlock ABI 3 or later, with the ABI reported and named on the page's worker chip.
- R2: a job the model's code timed out, overran or broke is the kind's failed cell, as on the host, and the run goes on.
- R3: a fresh agent cell empties its sandbox, usage.json merges only under --resume, and stage 2's derived input is --stage2-derived or this run's own file.
The probes (tools/worker_probes.py) run on a uid-65534 worker under Landlock in tests/test_worker_isolation.py and on the real container as check_worker.py EXEC-11 to EXEC-13, and each fails on the old code. The record, the deterministic runs and the round trips are unchanged. Contract: the attestation's landlock_abi and run.py --stage2-derived. Platform: arms now need Linux 6.2.
<!-- SECTION:FINAL_SUMMARY:END -->
