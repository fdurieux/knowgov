---
id: TASK-0162
title: 'Arms on macOS: test an engine whose VM kernel enables Landlock'
status: To Do
assignee: []
created_date: '2026-11-06T07:22:00Z'
updated_date: '2026-11-06T07:26:00Z'
labels:
  - worker
  - security
dependencies:
  - TASK-0161
documentation:
  - backlog/decisions/decision-0015
priority: low
type: task
ordinal: 167000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Docker Desktop for Mac 4.48.0 (kernel 6.10.14-linuxkit) gives a container no Landlock (landlock_abi() 0), so the worker refuses to serve there and every arms run is refused (decision-0015). Whether another engine on macOS, such as Colima or Lima with a distro kernel, gives a container Landlock is untested; nothing here claims it does. A write confinement without Landlock (separate uids for the worker and the job) is a security redesign, out of scope here. The X1 session's view on alternatives is attached as a note when it arrives.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 On a named macOS engine and version, the worker service started with --profile arms attests every check true, or the attestation that fails is recorded with the engine's version and kernel
- [ ] #2 docs/security.md and demo/README.md name only engines whose attestation was recorded on a real machine
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-06, the maintainer's Mac: Docker Desktop 4.48.0's kernel 6.10.14-linuxkit is built without Landlock: /proc/config.gz reads '# CONFIG_SECURITY_LANDLOCK is not set', CONFIG_LSM="yama,loadpin,safesetid,integrity,bpf"; landlock_create_ruleset answers ENOSYS (38) with Docker's seccomp profile and with seccomp=unconfined. No setting on that engine enables it; another engine's VM kernel is what this task tests.
<!-- SECTION:NOTES:END -->
