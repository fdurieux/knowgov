---
id: decision-0015
title: >-
  The worker on engines without Landlock: an exact network check, and the worker
  behind an arms compose profile
date: '2026-11-06T07:21:00Z'
status: accepted
---
## Context

task-0161, from the maintainer's first `docker compose --profile claude up -d --build --wait` after #271 (task-0141.05, X1). The worker (`harness/worker.py`) exited 3; `--wait` failed although app, neo4j and litellm were healthy. The worker attests six checks at start and refuses to serve when one fails (decision-0012, threat T).

Evidence, on the maintainer's Mac: Docker Desktop 4.48.0 (207573), Engine 28.5.1, runc 1.2.5, darwin/amd64, VM kernel 6.10.14-linuxkit.
- `docker compose logs worker`: `worker: refusing to serve, not confined: loopback_only, write_confined`. The other four checks held.
- `/sys/class/net` in the `network_mode: none` worker, and the same in plain `alpine --network none`: `bonding_masters`, `erspan0`, `gre0`, `gretap0`, `ip6_vti0`, `ip6gre0`, `ip6tnl0`, `ip_vti0`, `lo`, `sit0`, `tunl0`.
- `landlock_abi()` 0. The kernel is built without Landlock: `/proc/config.gz` reads `# CONFIG_SECURITY_LANDLOCK is not set` and `CONFIG_LSM="yama,loadpin,safesetid,integrity,bpf"`, and `landlock_create_ruleset` answers ENOSYS (38) under Docker's seccomp profile and under `seccomp=unconfined` alike. Neither seccomp nor a boot parameter is the cause.
- Why it appeared overnight: the previous checkout (`33fdfde`) had no `worker` service; #271 (task-0141.05) added it, and the maintainer's `git pull` brought it in. Neo4j and litellm were not recreated.

Two findings, of different kinds.
- **The network check was too literal: a defect.** It required `/sys/class/net == ["lo"]`. The tunnels are the kernel's fallback devices, created down in every new network namespace while `ipip`, `ip_gre`, `sit`, `ip6_tunnel`, `ip_vti` or `ip6_vti` are loaded (`net.core.fb_tunnels_only_for_init_net` defaults to 0). `bonding_masters` is the bonding driver's control file, a regular file, not an interface. A report on Docker Desktop for Mac 4.92.0, arm64, names `tunl0`, `gre0` and `ip_vti0` in a `network=none` container (docker/desktop-feedback discussion #708). A Linux host with those modules loaded refuses for the same reason, with Landlock present.
- **No Landlock: a platform gap.** Without it a job can write the jobs folder, and so forge `result.json` or `attest.json`: the hole Landlock closes (decision-0012). A mode without it is refused.

## Options

**(a) The network check.**
1. Keep `== ["lo"]`. Refuses every engine that loads tunnel modules, with no network reachable.
2. An allowlist of fallback device names. Brittle: the set follows the modules loaded, and the names prove nothing about state.
3. **What a device can do**: no interface but lo up, no route leaving lo, and no capability that could bring one up.

**(b) `docker compose up --wait` where the worker cannot attest.** An unhealthy container fails `--wait` as an exited one does.
- (i) **The worker behind a compose profile, `arms`.** The default `up` does not start it; an arms run without a served worker is refused app-side, as now.
- (ii) Keep it in the default set, and document `--wait` failing on such engines.
- (iii) The worker exits 0 on refusal, or stays up while refusing. The first is untested against `--wait`; the second reports a refusing worker as running.

## Decision

Accepted by the coordinating session under the maintainer's overnight delegation (2026-11-05: 'In case of doubt, create an opportunity canvas, fit/gap, swot, to inform your decision, record the canvas, fit/gap, swot and proceed with the decision'); the maintainer may supersede it. It supersedes decision-0012's loopback clause ("no interface but loopback", threat T) and nothing else of decision-0012.

**(a) `loopback_only` holds when all of these hold** (`harness/worker.py` `network()`):
- no entry of `/sys/class/net` other than `lo` has `IFF_UP` (0x1) in its `flags`;
- no route in `/proc/net/route` or `/proc/net/ipv6_route` leaves `lo` (no `ipv6_route` is a kernel without IPv6: no route);
- `CAP_NET_ADMIN` (bit 12) is in neither `CapEff` nor `CapBnd` of `/proc/self/status`.

Only a regular file in `/sys/class/net` is skipped; an interface entry is a symlink or a directory. Whatever cannot be read counts against the check: unread flags as up, an unread route table as a route, an unread capability set as holding `CAP_NET_ADMIN`. The attestation keeps the key `loopback_only`, and carries each interface's state, the routes and `cap_net_admin`.

`CapBnd` beside `CapEff` attests the precondition itself: with `CAP_NET_ADMIN` outside the bounding set, no process in the container can regain it, whether or not no-new-privileges holds. A down device stays down.

**(b) Option (i).** The `worker` service in `demo/docker-compose.yml` moves behind the profile `arms`. Nothing about the refusal changes: an arms run without a fresh attestation is refused by `harness/execution.py`. The stack job in `demo.yml` starts the stack with `--profile arms`, so EXEC-01..09 and the loosened workers still run.

## Consequences

- On Docker Desktop for Mac 4.48.0 the default `docker compose up -d --build --wait` succeeds. App, neo4j, and litellm with `--profile claude`, start green; the worker is not started; every arms run is refused.
- With `--profile arms` on that engine, whose kernel is built without Landlock, the worker attests `loopback_only` true and `write_confined` false, refuses to serve, and exits 3. That is by design. A later Docker Desktop may differ; unverified (task-0162).
- An adopter's default `up` no longer starts the worker: a contract change (CHANGELOG, Unreleased). To run arms: `--profile arms`, on Linux with Landlock (kernel 5.13 or later, enabled). Arms need a paid key anyway, so they were already opt-in.
- The limit: an engine that brings a non-lo interface up in a `network_mode: none` container still refuses, by design.
- Not decided here: arms on macOS (task-0162), and a write confinement without Landlock, which would be a redesign.

## Proof

- `tests/test_worker.py`, on a fake sysfs and procfs:
  - pass: lo alone; down tunnels beside lo; the Mac's exact listing with `bonding_masters`;
  - fail: an interface up; a down device with a route; `CAP_NET_ADMIN` effective or bounding; unreadable roots.
- A real network namespace (`unshare -rnm`, sysfs remounted, `setpriv` with no capabilities and no-new-privs):
  - lo plus a down veth pair: `ok: true`;
  - one end up: `ok: false`;
  - `CAP_NET_ADMIN` kept: `ok: false`;
  - the capless process's `SIOCSIFFLAGS IFF_UP` on the down device: `EPERM`.
- The stack job: the loosened worker (network on) still refuses on `loopback_only`.
- The maintainer's Mac on the PR's branch: `loopback_only` true, `write_confined` false, and the default `up --wait` succeeds without the worker.

## Fit/gap

| Need | (a)3 with (b)(i) | Gap |
|---|---|---|
| A worker with no network attests so on every engine | the check reads state, routes and capability, not names | an engine that brings an extra interface up refuses (by design) |
| Nothing lost against decision-0012's threat T | no up device, no route, no way to bring one up; unreadable counts against | none found |
| The default demo starts green everywhere | the worker is opt-in | an adopter used to the worker starting by default must add `--profile arms` |
| Arms refused without confinement | unchanged: `harness/execution.py` reads the attestation | none |
| Arms on Docker Desktop for Mac | not met | no Landlock there; task-0162 |

## Opportunity canvas

- **Problem:** the worker exited 3 on Docker Desktop for Mac with no network reachable, so the default `docker compose up --wait` failed for everyone on that engine, although the page, the store and the gate were healthy.
- **Who:** the maintainer and any adopter running the demo on Docker Desktop for Mac; any Linux host with tunnel or bonding modules loaded; CI, which must still prove the worker's confinement.
- **Solution:** (a) a network check that reads interface state, routes and `CAP_NET_ADMIN` instead of interface names; (b) the worker behind the compose profile `arms`.
- **Measures:**
  - `tests/test_worker.py` and the real-namespace proof;
  - the stack job's EXEC-01..09 and its loosened workers with `--profile arms`;
  - the maintainer's Mac: the default `up --wait` green, and with `--profile arms` `loopback_only` true and `write_confined` false.
- **Cost:**
  - one function in `harness/worker.py` and its tests;
  - one compose key, the profile flag on three `demo.yml` lines, one README paragraph;
  - an adopter adds `--profile arms` to run arms.
- **Risk:**
  - an adopter expecting the worker by default sees arms refused (the refusal names the missing attestation; the README names the profile);
  - an attestation that reads state must read it right, so anything unreadable counts against it.

## SWOT

- **Strengths.** The check states what the threat needs: no path out, and no way to make one. The precondition is attested, not assumed from compose. The default stack no longer depends on the engine's kernel. No weaker mode.
- **Weaknesses.** One more flag for arms. The attestation's shape grows: `interfaces` is now a map of names to states.
- **Opportunities.** The same check holds on Linux hosts with tunnel modules loaded, and on any later engine that adds Landlock. task-0162 can test a macOS engine against an exact attestation.
- **Threats.** An adopter who expects the worker by default sees arms refused; the refusal names the missing attestation, and the README names the profile. A future kernel could add another regular file under `/sys/class/net`: it is skipped, as it cannot be an interface.

## Advice

Take (a)3 with (b)(i), as decided.
- (a)3 states what decision-0012's threat T needs, not a proxy for it: no path out, and no way to make one. It holds on every engine that confines the worker, whatever modules its kernel loads, and it fails closed.
- (b)(i) keeps the refusal where it already is, app-side from the attestation, and stops one engine's missing kernel feature from failing the whole demo.
- Reject (b)(iii) and any mode without Landlock: both would report a worker that cannot confine its jobs as healthy.
- Next: task-0165 adds the socket probes the netns does not cover (AF_VSOCK); task-0162 tests arms on a macOS engine whose VM kernel enables Landlock.

## Note (2026-11-08): the platform floor since task-0203

A consequence of the accepted R10 fix (doc-0030 F8, task-0203, #353), not a change to what this record chooses. The backend, the exact network check and the `arms` compose profile are unchanged. `write_confined` is now attested only at Landlock ABI 3 or later, the first ABI that also denies truncation. So "Linux with Landlock (kernel 5.13 or later)" in Consequences now reads **Landlock ABI 3, Linux 6.2 or later**. Below that floor:
- the worker refuses to start;
- the page's worker chip reads "worker: not attested · Landlock ABI N, 3 needed";
- every Arms run is refused, while Replay and Deterministic work as before.

The adopter docs (`demo/README.md`, `docs/security.md`) and CHANGELOG's Unreleased known limit say the same. GitHub's runners and the maintainer's EC2 host are above the floor.
