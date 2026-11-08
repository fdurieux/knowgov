---
id: TASK-0203
title: >-
  Worker job isolation and the run-folder lifecycle (doc-0030 F8: R2, R3, R4,
  R7, R10)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-07T07:15:00Z'
updated_date: '2026-11-08T11:36:00Z'
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
- [ ] #1 After each job no process of uid 65534 but the worker remains, within a time bound, by a probe with a deep setsid chain
- [ ] #2 worker_job.py is non-dumpable and its output is closed at exit, so the forge probe fails; write_confined is attested only at Landlock ABI 3 or later
- [ ] #3 A job-stage error becomes the kind's failed cell, and summary.json, usage.json and SHA256SUMS are still written
- [ ] #4 A fresh cell clears its sandbox, usage.json merges only under --resume, and stage 2's derived input is an explicit flag
- [ ] #5 The scored record (S1 to S7), the deterministic run and the comparator stay equal
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
