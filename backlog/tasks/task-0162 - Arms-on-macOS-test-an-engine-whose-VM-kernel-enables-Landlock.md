---
id: TASK-0162
title: 'Arms on macOS: test an engine whose VM kernel enables Landlock'
status: Done
assignee: []
created_date: '2026-11-06T07:22:00Z'
updated_date: '2026-11-06T12:50:00Z'
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
- [x] #1 On a named macOS engine and version, the worker service started with --profile arms attests every check true, or the attestation that fails is recorded with the engine's version and kernel
- [x] #2 docs/security.md and demo/README.md name only engines whose attestation was recorded on a real machine
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Record Docker Desktop for Mac 4.48.0's self-check (AC #1's first evidence).
2. Maintainer tries Colima (Lima, vz) on the Intel Mac; record its self-check JSON, engine version, uname -r in the VM, verdict.
3. If Colima fails write_confined, try EC2 Ubuntu 24.04 with docker.io; record the same.
4. Name in demo/README.md and docs/security.md only hosts whose attestation was recorded on a real machine (AC #2); CHANGELOG line under Unreleased if the README route is added.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-06, the maintainer's Mac: Docker Desktop 4.48.0's kernel 6.10.14-linuxkit is built without Landlock: /proc/config.gz reads '# CONFIG_SECURITY_LANDLOCK is not set', CONFIG_LSM="yama,loadpin,safesetid,integrity,bpf"; landlock_create_ruleset answers ENOSYS (38) with Docker's seccomp profile and with seccomp=unconfined. No setting on that engine enables it; another engine's VM kernel is what this task tests.

The X1 session's view (session_01HTAA1UsSVF25SBM7XfjnqP, 2026-11-06), advice only. Separate uids for the worker (A) and the job (B) is the one alternative it would call equivalent to Landlock for the forging threat, and only with all of: (i) the worker keeps CAP_SETUID/SETGID and drops every capability before exec, with no-new-privs, so B holds none; (ii) /jobs not writable by B at all: mode 0770 with a group shared by the app and A only, not 1777 (the sticky bit stops replacing A's files, not creating new entries); (iii) B's only writable path is its own job folder; (iv) write_confined attested by trying, as B, to create, rename and replace a file in /jobs and a job folder, all failing; (v) the forging tests (tests/test_execution.py, result.json and attest.json) pass under that mode. Costs: cap_drop ALL becomes cap_drop ALL plus cap_add SETUID, SETGID; uid_65534 becomes a pair; the worker gains privilege, so the attestation also checks the job's CapEff empty after the drop. A per-job read-only mount needs mount privileges and a container per job the engine socket; decision-0012 rejected both. Its advice: Landlock where the kernel has it; separate uids only if built to (i)-(v); otherwise unsupported without Landlock. Not built.

2026-11-06, the maintainer's Mac (Intel MacBook Pro), Docker Desktop for Mac 4.48.0, kernel 6.10.14-linuxkit: `docker compose --profile arms run --rm --no-deps worker python harness/worker.py --attest-only` gave "ok": false. Every check true except write_confined: false (no Landlock). loopback_only true with the tunnel devices down; AF_VSOCK and AF_PACKET refused EPERM; outside ENETUNREACH; read_only_root, uid_65534, no_docker_socket, no_secret_variables true. Verdict: refused; arms runs are refused on this engine (decision-0015).

2026-11-06, the maintainer's EC2 instance in eu-west-1 (t3.large, 2 vCPU, 8 GiB; Ubuntu Server 24.04 LTS x86_64 AMI, /etc/os-release 'Ubuntu 24.04.5 LTS'), docker.io 29.1.3-0ubuntu3~24.04.2 with docker-compose-v2 2.40.3, kernel 7.0.0-1014-aws, /sys/kernel/security/lsm 'lockdown,capability,landlock,yama,apparmor,ima,evm'; knowgov main cloned that day. `docker compose --profile arms run --rm --no-deps worker python harness/worker.py --attest-only` gave "ok": true, every check true: loopback_only (interfaces lo up only, no routes, cap_net_admin false), no_secret_variables (secret_names empty), read_only_root, uid_65534, no_docker_socket, write_confined, no_socket_escape (AF_VSOCK and AF_PACKET refused EPERM, outside ENETUNREACH). Verdict: attested; the first real machine on which the worker serves outside CI. Compose's 'buildx isn't installed' warning is harmless (the classic builder built the image).

The EC2 attestation was taken at knowgov main 5ce8262 (PR #301's merge).

2026-11-06, the same EC2 instance, the stack up with --profile claude --profile arms (all services healthy after the root volume was raised from 8 to 30 GiB; on 8 GiB Neo4j exited out of disk), the page reached over an SSH tunnel: an S1 arms run on the Claude row (through the LiteLLM gateway) completed, the maintainer reports. The OpenAI row's runs failed with a 401 because OPENAI_API_KEY held a value that was not an OpenAI secret key (the first attempt an Anthropic key, the second a value not starting sk-); configuration, not the worker. The Gemini row was not offered, for want of GEMINI_API_KEY. Checking keys before a run is session_01HTAA1V5hRxxogbYzNaHL2a's task.

2026-11-06, the same EC2 instance, after a new OpenAI key (the models listing answered 200): demo run 2026-11-06-1248, S1 arms on the record's model gpt-5.1-2025-11-13, effort the API default, finished in 73 s. B: decisions ['generate_with_assumptions'], code [True], suite [11], flagged [False]; G: decisions ['generate'], code [True], suite [11], flagged [False]; usage 2 calls, 32882 tokens. The oracle's suite ran in the attested worker on both arms' code, 11/11 each, as the record's S1; the gate's report identical to results/S1 on all 122 fields, timestamps aside.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Two hosts attested on real machines on 2026-11-06. Docker Desktop for Mac 4.48.0 (kernel 6.10.14-linuxkit) fails only write_confined, for lack of Landlock, so arms runs stay refused there. EC2 t3.large on Ubuntu 24.04 LTS (docker.io 29.1.3, kernel 7.0.0-1014-aws) attests every check true. demo/README.md adds 'The Arms mode on an EC2 instance': the default 127.0.0.1 bind and an SSH tunnel. docs/security.md names that host and no other, and the Mac quick start points to it. A CHANGELOG line sits under Unreleased. python tests/run_tests.py: 598/619 passed, 21 skipped. Colima on the Intel Mac is parked, untested. Whether a full arms run completes on the instance is reported separately.
<!-- SECTION:FINAL_SUMMARY:END -->
