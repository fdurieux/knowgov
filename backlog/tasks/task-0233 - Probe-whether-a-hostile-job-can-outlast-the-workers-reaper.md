---
id: TASK-0233
title: Probe whether a hostile job can outlast the worker's reaper
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-08T20:55:00Z'
updated_date: '2026-11-08T21:17:00Z'
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
- [ ] #1 The hostile job is run in the emulated container, with the outcome measured from outside the namespace over several lifetimes and with and without a new session per generation
- [ ] #2 If the reaper can be outlasted, the fix is proposed under DECIDE with what the worker container would need for each option, before any change
- [ ] #3 If it cannot, the probe is the next EXEC check in tools/check_worker.py, run by the stack
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Probe (main 615fa36, the container emulated: the worker as pid 1 of its own pid namespace, uid 65534; the witness the namespace's ns_last_pid over the second after the job's answer, read by nsenter; control without the reaper, zombies still reaped: every chain survived, 280-800 pids/s):
- idle machine: 0 of 160 (life 0, 1, 3, 10 ms, with and without setsid per generation) and 0 of 40 (a branching swarm, life 0 and 1 ms);
- under load (6 busy loops on 4 cores): 1 of 260 jobs left a chain alive, 121 pids/s, life 1 ms with setsid per generation; the job took 0.5 s, so the reaper returned early, not at REAP_S.
Cause: _reap_orphans returns at the first /proc scan with no live descendant, and a /proc listing is no snapshot: a member that forks and exits between the listing and its read leaves a child never listed. Options sent to the coordinator under DECIDE before any change: (A) quiescence by the namespace's ns_last_pid around an empty scan, (A') fail closed at REAP_S, (B) cgroup.kill, (C) freeze then kill, (D) a pid namespace per job; B to D change decision-0012/0015's container settings.
<!-- SECTION:NOTES:END -->
