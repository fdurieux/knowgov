---
id: decision-0021
title: >-
  An execution verification is not bound to the code the suite last passed on
  before 1.0: a stated 1.0 limit, proposed at m-8 with the lighthouse's instance
date: '2026-11-08T16:22:00Z'
status: accepted
---
## Context

task-0219 (decision-0018 point 8; #366, `281125d`) probed the process's re-run step with two mutants on temporary copies of the public J-F rebuild, pre-registered first. Every cell came out as pre-registered (`subjects/jef_data_load/probes/h7/RESULTS.md`): R-STALE invalidates nothing, trace `drift` (minor) flags both mutants alike, and only the suite separates them (258, 256 and 239 of 258). The gate on scenario C reads PROCEED with each variant as the reference code. The probe put one question to the maintainer: should a verification's execution evidence be compared with the code as it now stands?

What the code does today:
- `harness/load.py` `load_verifications` writes an execution verification for each key the subject's `[verification] map` (or `derive_execution`) names. Its `evidence_sha256` is `sha256(SUBJECT.reference_code())`: the reference code's digest as it is at load.
- The suite does not run at load. The oracle runs in CI on the reference rebuild (`harness.yml`).
- Nothing records the digest of the code the oracle last passed on, so there is nothing to compare against. A changed reference code loads with its own digest and reads verified.
- The guard today is `harness/trace.py check --fail-on minor`, which reports `drift` on any changed registered file. `docs/reverse-engineering.md` step 8 names the flag (#366).

## Options

- **(a) Not in 0.9.** A stated 1.0 limit, with the binding proposed at m-8 against the lighthouse's instance.
- **(b) In 0.9.** The oracle's run records the digest of the code it passed on (in its evidence or the manifest). The load compares, and a mismatch withholds the execution verification and raises a `stale` gate finding naming the code. A contract change: a G9 row, and 0.9.0 waits for it.
- **(c) Run the suite at load.** Out: the load is not an execution environment, and contained execution is the worker's (decision-0012).

## Decision

**Accepted: (a)**, on the maintainer's word (2026-11-08: "Agreed", to the coordinator's advice that it stay out of 0.9, be recorded as a 1.0 limit and be proposed with the lighthouse's instance). Drafted by the coordinator. Not a contract change. doc-0028 §10 names it K21, a 1.0 limit. task-0225 proposes the binding at m-8.

## Opportunity canvas

For the binding deferred, (b):

| Element | Content |
|---|---|
| Problem | A passing execution verification keeps vouching after the code changes: H7's two mutants read PROCEED |
| Users | An adopter whose pipeline gates code changes on knowgov; the process's re-run step (decision-0018 step 8) |
| Proposal | The oracle's run records the digest of the code it passed on; the load compares; a mismatch is a `stale` finding naming the code |
| Unique value | Binds the last act not bound to content, after decision-0019 bound attestations to the versions they attest |
| Cost | A passed-on digest in the oracle's evidence or the manifest; a load comparison; a gate finding (contract); the record's digest stated for the reference rebuild |
| Risk | Every code edit stales the key until the suite runs again, a comment edit included |

## Fit/gap

| Must satisfy | (a) | (b) | Evidence |
|---|---|---|---|
| The scored record unchanged | Fit | Fit, once the record states the reference rebuild's digest | `load.py` `smoke_digest` |
| decision-0016: contract changes gather for 0.9.0, then freeze | Fit: no change | **Gap**: a new G9 row, and 0.9.0 waits | doc-0028 §4 |
| A pipeline stops on a changed file | Fit through `trace check --fail-on minor` | Fit, in the gate | #366; the guide's step 8 |
| The gate sees a change in behaviour | **Gap** | **Gap**: a digest sees a change, not a change in behaviour; only the suite does | `RESULTS.md` |
| Sized against an instance | Fit: at m-8, with the lighthouse's | **Gap**: no instance yet | decision-0019's measurement; doc-0028 §5 |

## SWOT

| | Helpful | Harmful |
|---|---|---|
| **Internal** | **S (a):** 0.9.0's freeze list does not grow; the guard exists and the guide names it | **W (a):** the gate reads PROCEED on changed code; a pipeline must read two tools |
| **External** | **O:** the lighthouse's instance shows where an oracle's evidence is kept; task-0212's generated cases could re-run on a stale finding alone | **T:** a reader takes PROCEED as covering the code as it stands. After 0.9.0, the binding is a 0.10.0 contract change that restarts the freeze. That was the maintainer's reason on decision-0019, weighed here and not taken |

## Advice

(a):
- trace's `drift` already gives the signal a digest would give, and the guide names the flag that stops on it. The gate would move the signal, not add to it.
- A digest cannot see behaviour, so the binding's worth turns on how an instance keeps its oracle's evidence, which the lighthouse's instance will show.
- Deferring costs a 0.10.0 contract change, which decision-0016 allows.

## Consequences

- doc-0028 §10 gains **K21**: an execution verification is not bound to the code the suite passed on. It is a 1.0 limit by this decision.
- **task-0225** (m-8, low) drafts the binding's decision against the lighthouse's instance, measured on the H7 probe: both mutants stale, the control not. No build before that decision is accepted.
- No CHANGELOG line: nothing changes for an adopter now, and 1.0's Known limits carry K21 at its release.
