---
id: TASK-0165
title: >-
  The worker attests that it cannot open AF_VSOCK or AF_PACKET sockets or reach
  an outside address
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-06T08:25:00Z'
labels:
  - security
  - worker
dependencies:
  - TASK-0161
references:
  - harness/worker.py
  - harness/execution.py
  - tests/test_worker.py
  - tests/test_security.py
  - tools/check_worker.py
documentation:
  - backlog/decisions/decision-0012
  - backlog/decisions/decision-0015
priority: high
type: bug
ordinal: 168000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From the X1 session's review of task-0161 (decision-0015). No network namespace confines AF_VSOCK, and on Docker Desktop the VM's host side (CID 2) answers on it. moby's default seccomp profile refuses socket(AF_VSOCK), so the worker was closed only by the engine's profile, which its attestation did not check. On the maintainer's Mac (Docker Desktop 4.48.0, Engine 28.5.1) a probe in the worker container under compose's settings: AF_VSOCK refused EPERM, AF_PACKET refused EPERM, TCP 1.1.1.1:443 ENETUNREACH. A new key, so the record says what was proven; decision-0012 and decision-0015 are narrowed by nothing, so no new decision.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 attest() carries no_socket_escape: socket(AF_VSOCK, SOCK_STREAM) and socket(AF_PACKET, SOCK_RAW) must raise, and a connect to 192.0.2.1:9 (TEST-NET-1) must end in ENETUNREACH, EPERM or EACCES; connected, a timeout, ECONNREFUSED or EHOSTUNREACH count as reached; the connect's timeout is at most 2 s
- [ ] #2 The attestation carries each probe's outcome under sockets; execution.ATTEST_CHECKS includes no_socket_escape, so the app refuses jobs without it
- [ ] #3 tests/test_worker.py: all refused passes (the Mac's EPERM, EPERM, ENETUNREACH; EAFNOSUPPORT); either family opening, a connection, a timeout, ECONNREFUSED or EHOSTUNREACH fails
- [ ] #4 tests/test_security.py admits import socket in harness/worker.py only while it carries OUTSIDE = ("192.0.2.1", 9), and holds its socket use by AST to the two families and one create_connection to OUTSIDE: no bind, listen, accept, send, receive or name lookup
- [ ] #5 tools/check_worker.py EXEC-10 on the real worker: the attestation's probes all refused, and a job opens neither family; demo.yml runs a loosened worker with seccomp=unconfined and asserts it refuses when AF_VSOCK opens, or says the runner refuses every probe
- [ ] #6 docs/security.md names the probes in the attestation and in the network row, and says the supported-platform sentence was fail-closed design until the maintainer's Mac gave the first evidence on Docker Desktop
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. worker.sockets() and the key in attest(); execution.ATTEST_CHECKS. 2. tests/test_worker.py with stand-in sockets. 3. tests/test_security.py PROBES exception and the AST guard, shown failing on four mutations. 4. check_worker EXEC-10; demo.yml seccomp=unconfined worker. 5. docs/security.md, CHANGELOG. 6. In the same PR: task-0161 Done, the X1 session's Q2 note on task-0162, decision-0015's opportunity canvas and advice.
<!-- SECTION:PLAN:END -->
