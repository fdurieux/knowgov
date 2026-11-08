---
id: TASK-0233
title: Probe whether a hostile job can outlast the worker's reaper
status: Done
assignee:
  - '@claude'
created_date: '2026-11-08T20:55:00Z'
updated_date: '2026-11-08T23:47:00Z'
labels:
  - worker
  - containment
dependencies: []
priority: high
type: bug
ordinal: 229000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The containment question behind EXEC-11 (task-0232): can a job's processes outlast harness/worker.py _reap_orphans within REAP_S? A fork chain whose processes each live a few ms, started by a double fork that takes its own session, probed in the container emulated as for task-0232 (the worker as pid 1 of its own pid namespace, uid 65534). _reap_orphans returns at the first /proc scan that finds no live descendant, and one scan can miss a fast fork chain (task-0232). If it can be outlasted, the fix is proposed to the coordinator before it is built; if not, the probe becomes the next EXEC check the stack runs.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The hostile job is run in the emulated container, with the outcome measured from outside the namespace over several lifetimes and with and without a new session per generation
- [x] #2 If the reaper can be outlasted, the fix is proposed under DECIDE with what the worker container would need for each option, before any change
- [x] #3 If it cannot, the probe is the next EXEC check in tools/check_worker.py, run by the stack
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Probe (main 615fa36, the container emulated: the worker as pid 1 of its own pid namespace, uid 65534; the witness the namespace's ns_last_pid over the second after the job's answer, read by nsenter; control without the reaper, zombies still reaped: every chain survived, 280-800 pids/s):
- idle machine: 0 of 160 (life 0, 1, 3, 10 ms, with and without setsid per generation) and 0 of 40 (a branching swarm, life 0 and 1 ms);
- under load (6 busy loops on 4 cores): 1 of 260 jobs left a chain alive, 121 pids/s, life 1 ms with setsid per generation; the job took 0.5 s, so the reaper returned early, not at REAP_S.
Cause: _reap_orphans returns at the first /proc scan with no live descendant, and a /proc listing is no snapshot: a member that forks and exits between the listing and its read leaves a child never listed. Options sent to the coordinator under DECIDE before any change: (A) quiescence by the namespace's ns_last_pid around an empty scan, (A') fail closed at REAP_S, (B) cgroup.kill, (C) freeze then kill, (D) a pid namespace per job; B to D change decision-0012/0015's container settings.

Fix (A), the coordinator's call, no container change: _reap_orphans takes an empty scan only when the pid namespace's counter (/proc/sys/kernel/ns_last_pid, read by the worker as its namespace's pid 1, no privilege) did not move across it; elsewhere QUIET_SCANS (5) empty scans in a row, the weaker test-path rule stated in docs/security.md. (A') in its own commit, held for the maintainer: past REAP_S the reaper raises ReapIncomplete and the worker stops serving (the job a failed cell, the attestation withdrawn, exit 4).
Evidence:
- tests/test_reaper_quiescence.py: a scan made to miss a listed process (deterministic) and a namespace counter that moved across an empty scan; both fail on main 44ef5c8 (the reaper returned after one scan, the process alive), pass here; plus the counter rule's guard and (A')'s test.
- The emulated container under load (6 busy loops on 4 cores): main's reaper let 1 of 260 hostile chains outlive its job; this one 0 of 260 (life 0, 1, 1, 2 ms, setsid per generation).
- EXEC-14 (tools/check_worker.py, the stack): five hostile chains, the next job's witness the namespace's pid counter (at most 5 pids in the second after) and no marked process, and the worker its namespace's init; holds in the emulated container. NSpid was first used to detect the namespace and is wrong under a /proc mounted inside it (it shows one level, as Docker's does): the worker being pid 1 is the test.
- run_tests: no yaml 823/878 (55 skipped), pins 877/878 (1 skipped), 0 failed.

EXEC-14's witness fixed (main's stack job at ec4e693, job 128882506686: round 5 allocated 6 pids against QUIET_PIDS 5, marked 0, init 1; the healthcheck's docker exec, not a chain). ns_quiet now reads two consecutive one-second windows; a round fails when both allocate more than QUIET_PIDS (20) or any process carries the chain's mark (check_worker.quiet_round, its reasoning in check_worker.py): a surviving chain forks 121 to 800 a second in every window, a healthcheck runs once in ten seconds and lands in at most one. The reaper is unchanged. Emulated container, five rounds each: the new witness beside a healthcheck entered by nsenter back to back holds (17 to 20 a window); main's fails; the new witness with the reaper disabled fails (677 to 3214 a window, marked 2). tests/test_reaper_quiescence.py's quiet_round test fails on main 6cc4ee1, passes here.

(A') decided: the maintainer, 2026-11-08, "(A') yes" (recorded in #389's body, after the coordinator set out what it implies). #389 merged as ec4e693 with (A') as built: past REAP_S the job fails, the attestation is withdrawn and the worker exits (code 4), ending every process in its namespace; arms runs are refused until a worker attests again; recovery is a manual restart, the worker having no restart policy (an automatic restart would be a container setting, decision-0015, a separate question). EXEC-14 held in the real worker container on #389's stack job. (B) to (D) go to the maintainer as a 1.0 question.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
A hostile job could outlast the worker's reaper: _reap_orphans returned at the first /proc scan with no live descendant, and a listing is no snapshot, so under load a fast fork chain slipped between a listing and its reads (1 of 260 hostile jobs in the emulated container). Now, in its container (the init of its own pid namespace), the reaper takes an empty scan only when the namespace's pid counter did not move across it, which closes the race; on a host it takes five empty scans in a row. EXEC-14 runs the hostile chain against the real worker container (#389; its witness made blind to a healthcheck and strict for a chain in #391). (A'), the worker stopping at the bound, was decided by the maintainer on 2026-11-08 ("(A') yes") and merged in #389: past REAP_S the job fails, the attestation is withdrawn and the worker exits with code 4, so recovery is a manual restart, named as the 1.0 limit K22 (doc-0028 §10). (B) to (D), cgroup and namespace options that change decision-0012/0015's container settings, and an automatic restart, are parked as task-0238 for a decision after the lighthouse.
<!-- SECTION:FINAL_SUMMARY:END -->
