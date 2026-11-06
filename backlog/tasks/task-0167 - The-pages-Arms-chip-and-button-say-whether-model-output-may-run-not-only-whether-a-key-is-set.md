---
id: TASK-0167
title: >-
  The page's Arms chip and button say whether model output may run, not only
  whether a key is set
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-06T11:20:00Z'
labels:
  - demo
  - security
dependencies: []
priority: medium
ordinal: 170000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
On the maintainer's Mac (Docker Desktop 4.48.0, started without --profile arms), the chip read 'arms enabled (5 of 5 model rows)' and the Arms button was live. Pressing it was refused because the worker had not attested its confinement. demo/app/server.py arms_enabled() counts model rows with a key and the oracle only. harness/execution.py refusal() already says whether model output may run (the instance guard, the backend, the worker's attestation). The page shows its answer beside the key count. Queued on the maintainer's go ('yes, queue the badge fix'), relayed by the coordinating session.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The status JSON (/api/scenarios) gains an additive field execution: {ok, why}, from execution.refusal() (called, never copied); arms_enabled is unchanged; demo/README names the field where it documents the page's HTTP surface
- [ ] #2 The chip reads 'arms enabled (n of m model rows)' only when a key and execution are both there; a key without a contained worker is a warn chip, 'arms: no contained worker', with the refusal and an adopter hint (--profile arms, Linux with Landlock, demo/README) in its title; the key-missing chip otherwise
- [ ] #3 The Arms button is disabled with the same reason; Replay and Deterministic are unaffected
- [ ] #4 Stdlib tests prove the chip and the button each way: no attest.json gives execution.ok false and a 'has not attested' reason, a fresh valid attestation ok, a stale one the stale reason; the stack job asserts the status its worker gives
- [ ] #5 demo/README's Mac note, in the adopter register, gives the one-command self-check (docker compose --profile arms run --rm --no-deps worker python harness/worker.py --attest-only) and what write_confined: false means
<!-- AC:END -->
