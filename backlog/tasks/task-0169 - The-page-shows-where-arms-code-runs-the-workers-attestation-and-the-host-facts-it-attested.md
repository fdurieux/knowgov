---
id: TASK-0169
title: >-
  The page shows where arms code runs: the worker's attestation and the host
  facts it attested
status: Done
assignee:
  - '@claude'
created_date: '2026-11-06T12:29:00Z'
updated_date: '2026-11-06T13:09:00Z'
labels:
  - demo
  - security
dependencies: []
priority: medium
ordinal: 172000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Maintainer, 2026-11-06: 'Create a task: visualise on the dashboard that the arms is running in a Docker container on AWS.' Since 0.8.0 (decision-0012, decision-0015) model-written code runs only in the compose worker (--profile arms), which attests its confinement at start (harness/worker.py attest(), /jobs/attest.json; harness/execution.py refuses a job without a fresh attestation). On 2026-11-06 the maintainer ran the stack on an EC2 t3.large (Ubuntu 24.04, docker.io 29.1.3, kernel 7.0.0-1014-aws) and the worker attested every check true (task-0162). The page's chips (store, Arms since task-0167, register) do not say where the worker runs or that it attested. A worker chip does, e.g. 'worker: attested · Docker · Linux 7.0.0-1014-aws (x86_64) · AWS (read from the kernel release)', or that no worker attested. Relayed by the coordinating session.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 attest() carries an additive host block read from inside the container (os.uname(): system, kernel release, machine; the engine from /.dockerenv or /run/.containerenv, else unknown); no check and no ok verdict changes, and the host facts never enter ATTEST_CHECKS
- [x] #2 harness/execution.py gives the worker's place from the same attestation it checks (attested(), called, never copied): attested with the host facts, or not attested with the refusal; the facts are read as untrusted data (strings only, length-capped, printable)
- [x] #3 A cloud is shown only as a reading of an attested fact, labelled as such (a kernel release ending -aws reads AWS 'from the kernel release'), never from an instance metadata service or any new network call; tests/test_security.py's outbound rule unchanged
- [x] #4 /api/scenarios carries an additive worker field beside execution; the page draws a worker chip from it: ok when attested, naming the engine, the kernel and the machine and the cloud reading; warn when no worker attested, with the reason in its title; arms_enabled and execution unchanged
- [x] #5 knowgov-runs run_options passes the page's worker field through (a page without it reads not attested)
- [x] #6 Stdlib tests: the host block from a stand-in uname and root; the worker view attested, absent, stale and malformed; the cloud reading only from the kernel suffix; the chip each way run in node from index.html; the stack job asserts its worker's view
- [x] #7 docs/security.md and demo/README describe the chip and say the cloud is a reading, not a check; a CHANGELOG line under Unreleased
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/worker.py host_facts(uname, root): system, kernel, machine, engine; attest() adds 'host' additively.
2. harness/execution.py placement(env): backend none/host/worker; worker: attested() then sanitised host facts and cloud_reading(kernel) (suffix table: -aws AWS, -azure Azure, -gcp Google Cloud, -oracle Oracle Cloud), else attested false with the refusal.
3. demo/app/server.py worker_view() calls execution.placement(); /api/scenarios gains 'worker'.
4. demo/app/index.html workerChip() between Arms and register.
5. harness/mcp_runs.py run_options passes 'worker' through.
6. tests: test_worker, test_execution (placement), test_arms_execution (chip in node), test_mcp_runs; demo.yml stack asserts worker attested with host facts.
7. docs/security.md, demo/README, CHANGELOG.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented as planned. worker.host_facts(uname, root) beside attest(); execution.placement() calls attested() and reads host facts only from a holding attestation, each a printable string capped at 128 characters (else None); cloud_reading() maps the kernel release's last '-' part through KERNEL_CLOUDS. The page's workerChip() sits between the Arms and register chips: ok when attested, warn when not, bad under the uncontained opt-in. python tests/run_tests.py: 608/629 passed, 21 skipped, 0 failed (node present, so the chip tests ran). AC #6's stack-job assertion (demo.yml: the worker attests with engine docker) is proven only on the PR's stack run; it is left unchecked until that run is green.

tools/check_worker.py (the stack job, on the real worker) also checks the attestation names Linux, a kernel, a machine and engine docker, and that its checks are ATTEST_CHECKS unchanged (coordinator's ask).

AC #6 proven on #304's stack job: the workflow run 42221266746 on 1c6070a was green; demo.yml asserted the worker attested with engine docker and a Linux kernel and machine, and tools/check_worker.py held the same with ATTEST_CHECKS unchanged. Merged as 22125ea.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The page's header has a worker chip saying where Arms code runs, as the worker attested it: 'worker: attested · Docker · Linux <kernel> (<machine>)', plus a cloud only as a labelled reading of the kernel release's suffix (-aws reads AWS 'from the kernel release', not checked). It reads 'worker: not attested' with the reason, or is a red chip under the uncontained opt-in. The worker's attestation gains an additive host block (os.uname() and the engine's marker file); no check and no ok verdict changed. harness/execution.py placement() reads the facts from the same attested() a job is refused by, as capped printable strings. /api/scenarios and knowgov-runs run_options carry it as worker. No metadata service and no network call. Tests: stdlib and node (the page's own workerChip()), with the stack job and tools/check_worker.py on the real worker. Docs: security.md, the demo README, CHANGELOG. PR #304.
<!-- SECTION:FINAL_SUMMARY:END -->
