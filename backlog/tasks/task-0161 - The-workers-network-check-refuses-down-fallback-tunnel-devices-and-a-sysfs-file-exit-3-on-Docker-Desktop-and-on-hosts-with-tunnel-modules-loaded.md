---
id: TASK-0161
title: >-
  The worker's network check refuses down fallback tunnel devices and a sysfs
  file: exit 3 on Docker Desktop and on hosts with tunnel modules loaded
status: Done
assignee:
  - '@claude'
created_date: '2026-11-06T07:22:00Z'
updated_date: '2026-11-06T08:25:00Z'
labels:
  - security
  - worker
dependencies:
  - TASK-0141.05
references:
  - harness/worker.py
  - tests/test_worker.py
documentation:
  - backlog/decisions/decision-0012
  - backlog/decisions/decision-0015
priority: high
type: bug
ordinal: 166000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The worker (harness/worker.py, task-0141.05, decision-0012) attested loopback_only as sorted(os.listdir('/sys/class/net')) == ['lo']. On the maintainer's Mac (Docker Desktop 4.48.0, Engine 28.5.1, VM kernel 6.10.14-linuxkit) a network_mode none container lists bonding_masters, erspan0, gre0, gretap0, ip6_vti0, ip6gre0, ip6tnl0, ip_vti0, lo, sit0 and tunl0; plain alpine lists the same. The tunnels are the kernel's fallback devices, created down in every new network namespace while ipip, gre, sit or vti are loaded (net.core.fb_tunnels_only_for_init_net defaults to 0); bonding_masters is the bonding driver's control file, not an interface. The worker exited 3 with no network at all, and would on any Linux host with those modules loaded. decision-0015 (a) sets the exact check.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 loopback_only holds when no interface but lo has IFF_UP in /sys/class/net/<if>/flags, no route in /proc/net/route or /proc/net/ipv6_route leaves lo, and CAP_NET_ADMIN is in neither CapEff nor CapBnd of /proc/self/status
- [x] #2 Only a regular file in /sys/class/net is skipped; an entry whose flags cannot be read counts as up, an unreadable route table as a route, an unreadable capability set as holding CAP_NET_ADMIN
- [x] #3 The attestation carries each interface's state, the routes and cap_net_admin; attest() takes the sysfs and procfs roots
- [x] #4 tests/test_worker.py: lo alone, down tunnels beside lo, the Mac's exact listing with bonding_masters, an interface up, a down device with a route, NET_ADMIN effective or bounding, and unreadable roots
- [x] #5 demo.yml's loosened worker (network on) still refuses on loopback_only in the stack job
- [x] #6 docs/security.md states the check and names Docker Desktop for Mac 4.48.0 as without Landlock
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. network(sys_root, proc_root) in harness/worker.py, attest() reads it. 2. tests/test_worker.py on a fake sysfs and procfs. 3. Proof in a real namespace (unshare -rnm, setpriv without capabilities). 4. decision-0015 (a); docs/security.md; CHANGELOG Changes. 5. The maintainer's Mac: loopback_only true, write_confined false.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Network check implemented in harness/worker.py network(); tests/test_worker.py; proven in a real namespace (unshare -rnm, setpriv without capabilities): down veths pass, one up fails, NET_ADMIN kept fails, SIOCSIFFLAGS from the capless process EPERM. bonding_masters found on the maintainer's Mac and skipped as a regular file. The worker behind the arms profile per decision-0015 (b), demo.yml's stack job passing it. Suite: 568/585 passed, 17 skipped, 0 failed.

Evidence: #284 (https://github.com/fdurieux/knowgov/pull/284) merged as 60ea8ac. CI on its head 193e0ed: stack success (run 42182862189; the loosened worker with network on refused and EXEC-01..09 ran with --profile arms), tests success, rdflib success, knowgov gate success. The maintainer's Mac on 37dc4c0 (Docker Desktop 4.48.0, kernel 6.10.14-linuxkit): the default up --wait green without the worker; --profile arms --attest-only gave loopback_only true, nine tunnels down, lo up, bonding_masters skipped, routes [], cap_net_admin false; write_confined false, a kernel built without Landlock (decision-0015).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
loopback_only now reads what a device can do: no interface but lo up, no route leaving lo, no CAP_NET_ADMIN effective or bounding; only a regular file under /sys/class/net is skipped and anything unreadable counts against (harness/worker.py network(), decision-0015 (a)). The worker is behind the compose profile arms (decision-0015 (b)), so the default up is green on Docker Desktop for Mac, whose kernel has no Landlock. Verified by tests/test_worker.py, a real namespace (down veths pass, one up fails, EPERM on SIOCSIFFLAGS), #284's full CI and the maintainer's rerun. Follow-ups: task-0165 (socket probes), task-0162 (arms on macOS).
<!-- SECTION:FINAL_SUMMARY:END -->
