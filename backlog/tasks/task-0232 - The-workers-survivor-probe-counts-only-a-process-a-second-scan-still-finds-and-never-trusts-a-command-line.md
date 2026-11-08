---
id: TASK-0232
title: >-
  The worker's survivor probe counts only a process a second scan still finds,
  and never trusts a command line
status: Done
assignee:
  - '@claude'
created_date: '2026-11-08T20:30:00Z'
updated_date: '2026-11-08T20:50:00Z'
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
The stack's EXEC-11 (task-0203, R4) went red once on #383 at 6c7f7b0 (survivors others ['0','1']; the same code green at b8f7a56). Not a survivor: marked was 0, and the worker kills, waits for, settles and reaps a job's processes before it claims the next. The probe counted the Docker healthcheck (worker.py --attest-only, uid 65534, every 10 s) in the instant it exits: its cmdline reads empty before it is a zombie, so the --attest-only exclusion misses it (reproduced: 7 of 300 probes beside a stand-in healthcheck, 0 without). That exclusion is also spoofable: a job may carry --attest-only in its own argv and drop out of the count.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 survivors() counts an 'other' only when a second full scan about a second later also finds one (any pid, not Z or X), so an exiting process drops out and a fork chain or a lingerer is still counted
- [x] #2 No command-line exclusion: the healthcheck is excluded by what a job cannot forge, a parent outside the container's pid namespace (ppid 0), since every job process descends from the worker, the container's init
- [x] #3 Each counted other is printed with pid, ppid, state and cmdline; EXEC-11 and the R4 test parse the counts line
- [x] #4 Tests fail on main first: an exiting process is not counted, a lingerer with --attest-only in its argv is; a short-lived fork chain is counted; EXEC-11 stays strict; no pin changes
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. survivors(): two windows of scans (a quarter second, every 20 ms, so a fast fork chain is not missed between a /proc listing and its reads), the second a second after the first; an other counts only when the second window finds one, whichever pid.
2. No command-line exclusion: a process with ppid 0 (entered from outside the pid namespace: docker exec, the healthcheck) is not the job's; every job process descends from the worker, the container's init.
3. Each counted other printed as OTHER pid ppid state cmdline; EXEC-11 and the R4 test read the counts line, EXEC-11 strict.
4. tests/test_survivor_probe.py; the container emulated with unshare and nsenter for the healthcheck.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Evidence (no Docker daemon here; KG_CLOCK pinned, no model call):
- The container emulated: the worker as pid 1 of its own pid namespace (unshare --pid --fork --mount-proc, uid 65534), the healthcheck worker.py --attest-only entered by nsenter (ppid 0 inside, as docker exec) in a tight loop, 300 survivors probes each: main's probe counted another process 3 times ('0 1', the CI red), this one 0.
- Healthcheck caught exiting, outside a namespace: 7 of 300 of main's probes counted it (state R, cmdline empty), 0 without the healthcheck.
- A single /proc scan misses a fast fork chain (each process forks the next and exits after 50 ms): 3 of 5 runs read '0 0' with one scan per phase; with a quarter-second window of scans per phase, 10 of 10 counted it, and 5 of 5 under four busy CPUs.
- tests/test_survivor_probe.py: all 4 fail on main fea8942 (an exiting process counted; a lingerer with --attest-only dropped; no OTHER line for the chain; the source holds --attest-only), all pass here.
- run_tests: no yaml 806/860 (54 skipped), pins 859/860 (1 skipped), 0 failed; test_release passes.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The worker's survivor probe (tools/worker_probes.py survivors, read by EXEC-11 and the R4 test) counts a process of the worker's user only when a second window of scans, a second after the first, also finds one, whichever pid: a process caught exiting drops out, a lingerer or a fork chain does not. Each window is a quarter second of scans, since one /proc scan can miss a fast fork chain. The --attest-only command-line exclusion, which a job could copy, is gone: a process whose parent is outside the pid namespace (ppid 0: docker exec, the healthcheck) is not the job's, since every job process descends from the worker, the container's init. Each counted process is printed with pid, ppid, state and cmdline. EXEC-11 stays strict. Proven on the container emulated with unshare and nsenter (main's probe 3 of 300 false counts, this one 0) and by tests/test_survivor_probe.py, failing on main first. No pin changes.
<!-- SECTION:FINAL_SUMMARY:END -->
