---
id: decision-0012
title: >-
  X1's isolation backend: a sibling worker service from the same image, no
  network, no secrets, read-only; execution refused when the worker is
  unavailable
date: '2026-11-06T01:51:00Z'
status: accepted
---
## Context

task-0141.05 (X1), from the 2026-11-05 code and architecture review: every path that executes model output goes through one trusted execution service; an unavailable backend refuses, never falls back to the host. Its AC #1 asks for EXEC-01..EXEC-09 as real worker-boundary tests in CI, not command-construction mocks. Until X1 lands, task-0141.07 (#262) refuses execution beside a mounted instance unless `KG_ALLOW_UNCONTAINED_EXECUTION=1`.

The security session's read-only investigation (2026-11-06, on `main` at `01f7e06`):
- Model code runs in two oracles, both reached only through `measures._smoke`, .07's choke point:
  - CargoQuote's vendored `smoke_test.py`, whose `run_child` runs `subprocess.run([sys.executable, "-I", CHILD, artifact])` and so inherits the whole environment, model keys and `KG_NEO4J_PASSWORD` included, and the host filesystem. It is vendored and cannot be edited.
  - J-F's `subjects/jef_data_load/oracle/jef_suite.py`, our own file, which runs pytest over the sandbox on the host.
- Containment can wrap the oracle call from outside, with no vendored edit.
- Two defects are independent of the backend:
  - `harness/agent.py` `Sandbox.write` follows symlinks (EXEC-04);
  - the agent's deadline is wall-clock time, is not passed into the streamed model call, and has no idle bound (EXEC-08).
- Isolation primitives:
  - `unshare`, `prlimit` and `setpriv` are in util-linux, already in `python:3.12-slim`;
  - unprivileged user namespaces work in a session container;
  - Docker's default seccomp profile blocks them in the app container;
  - Ubuntu 24.04's AppArmor restricts them on GitHub's runners.

The maintainer is asleep under a standing delegation (2026-11-05 23:3x: "proceed independently with the backlog. In case of doubt, create an opportunity canvas, fit/gap, swot, to inform your decision, record the canvas, fit/gap, swot and proceed with the decision"). The standing limit "a new image or pin for X1 goes to the maintainer first" holds; none of the options below needs one. Taken by the coordinating session; the maintainer may supersede it with a later record.

## Options

- **(a) Namespaces inside the app container**: `unshare --user --net --mount --pid`, `prlimit`, an empty environment, a private tmpfs. No new image.
- **(b) A sibling `worker` compose service from the same image digest**: `network_mode: none`, read-only root, tmpfs `/work`, `cap_drop: ALL`, `no-new-privileges`, user 65534, memory, pids and CPU limits, no secret in its environment, only the subjects' oracles and kits mounted read-only, plus a jobs volume. The app, as the trusted supervisor, writes each job (code and spec) to the jobs volume. A small knowgov loop in the worker runs the oracle, with a per-job process-group kill and an output cap, and writes the result back. There is no Docker socket anywhere. The agent's feedback tool goes the same way. An unavailable worker means execution is refused.
- **(c) gVisor or a microVM**: a new runtime.

## Fit/gap

| Need (task-0141.05) | (a) namespaces in the app | (b) sibling worker | (c) gVisor / microVM |
|---|---|---|---|
| No secrets reach model code | empty environment | none in the worker's environment | yes |
| No network | net namespace | `network_mode: none` | yes |
| No host mounts | mount namespace, private tmpfs | read-only root, read-only oracles, a jobs volume | yes |
| Enforced deadlines and limits | `prlimit`; group kill | container limits; group kill | yes |
| EXEC-01..09 real in CI (AC #1) | **gap**: runners' AppArmor blocks userns | stack job (Docker) | **gap**: needs the runtime on runners |
| Does not weaken the protected container | **gap**: `seccomp=unconfined` or a custom profile on the app | yes | yes |
| No new image or pin | yes | yes, same digest | **gap**: a new runtime |
| Refuses when unavailable | yes | yes | yes |
| Outside compose (bare `run.py`) | runs where userns works | **refused** unless .07's opt-in | refused |

## Opportunity canvas (b)

| Box | Content |
|---|---|
| Problem | Code a model writes runs with the app's environment (model keys, the Neo4j password) and the host filesystem, in two oracles, one of them vendored. |
| Solution | One execution path to a sibling worker started from the same image with Docker's own confinement, fed through a jobs volume by the app as supervisor. |
| Measure | EXEC-01..09 pass for real in the stack job. The worker refuses to start unless its own confinement holds. The deterministic record is unchanged. |
| Cost | A compose service, a worker loop, stack-job steps, this record, and a contract change outside compose. |
| Risk | The jobs volume is a channel: results are untrusted input to the app. An instance could loosen the worker's compose settings. |

## SWOT (b)

- **S.** Real isolation from Docker's own mechanisms, with no Docker socket. Testable in CI, which (a) and (c) are not. Same image digest. The app container is not weakened.
- **W.** More moving parts: a worker loop, a jobs volume, a new trusted component. Bare-metal arms runs need the worker or the explicit opt-in.
- **O.** An upgrade path to (c) without changing the protocol: `runtime: runsc` on the worker service alone, when the maintainer chooses a runtime. The same worker can serve the agent's feedback tool and final grading alike.
- **T.** A loosened compose file in an organisation's instance. Mitigation: the worker checks its own confinement at start (no interface but loopback, no secret-shaped variable, a read-only root, uid 65534) and refuses otherwise, and the app refuses jobs without that attestation. A result carrying an attack: results are capped and schema-checked, and the app never executes them.

## Decision

Accepted: **(b)**, with these conditions:
1. **One path.** Every execution of model output goes through the worker: single-reply grading, the agent's feedback suite and the final grading. Nothing executes on the host. The worker missing or unattested means refusal, and .07's `KG_ALLOW_UNCONTAINED_EXECUTION=1` stays the only, explicit escape.
2. **The worker attests its confinement at start**, as listed under T, and the app checks the attestation before each job.
3. **Results are untrusted**: size-capped and schema-checked, never executed by the app.
4. **Independent of the backend**, in the same work: symlink-safe sandbox writes (a directory-fd walk with `O_NOFOLLOW`, no following when collecting; EXEC-04), and one monotonic run deadline passed into the model stream, with idle and total read bounds and cancellation (EXEC-08).
5. **Proof**: EXEC-01..09 run for real in the stack job. The rdflib job never runs arms. The deterministic record and its comparator are unchanged.
6. **Contract change, recorded under CHANGELOG Unreleased**: outside compose, arms execution needs the worker or the opt-in.

Not decided here: (c), a hardened runtime for the worker, which waits for the maintainer, since it is a new runtime. Whether S2 (task-0141.06) comes before X1's build: the security session recommends, and the coordinator orders.

## Consequences

- X1 is built by the security session after H2 (#266) merges, citing this record.
- 0.7.0 is cut before X1, as decided (the cut-off is E0, S1, H1, H2, task-0142 and task-0143). Its known limits say generated code is not yet contained.
- The maintainer may supersede this record. Until X1 merges, nothing is built that cannot be removed.
