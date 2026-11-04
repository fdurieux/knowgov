---
id: doc-0015
title: >-
  Out of scope, read again: observed state, simulation and write-back;
  implemented_by; code semantics. Canvas and fit-gap
type: specification
created_date: '2026-11-04T19:05:00Z'
---

*2026-11-04. Maintainer register. Reads again the three items doc-0011 §3–§4 left out of scope, after the doc-0011 fit-gap of the same day (every definition-of-done point met; process mining parked in task-0053; the register-change gap filed as task-0122). Evidence used: knowgov `main` after #199; register v0.2.8 vendored, decision 0016 approved and implemented (ieam-register #25, #26); the ARIS 10.0 round-trip findings recorded in task-0119's notes. Tasks created on the maintainer's go: task-0123, task-0124, task-0125.*

## 1. Observed state, simulation, write-back

| Box | Content |
|---|---|
| Problem | knowgov knows what was decided and documented, not what runs; it cannot simulate a change; it never writes into ARIS or LeanIX. |
| Who | Process owners and operations (declared versus actual); EA (what-if); modellers (ids that survive their tools). |
| Today | Observed state: none, by design (doc-0010 §4.1); a received, flag-only form of process mining is parked in task-0053 on Loop B's trigger. Simulation: structural what-if is built (the impact walk, `register_impact` with `children` and `task`); no dynamic simulation. Write-back: none; the store holds status, provenance and links, never content. |
| Candidates | (a) process-mining verdicts as flagged evidence (task-0053); (b) identity-only write-back: the register id into the tool's id attribute, because ARIS rewrites element ids on BPMN import and only process ids survive (task-0119 notes); (c) dynamic simulation. |
| Value | (b) high and cheap: every later export keeps its identity. (a) medium, gated. (c) low for a governance layer. |
| Cost, risk | (b) one attribute, written by a client-run template; risk: it grows into content write-back, which makes two records. (a) medium; the word "running twin" misleads. |

| Item | Fit/gap |
|---|---|
| Structural what-if | Fit: built |
| Observed state | Out, except task-0053's flagged form, parked |
| Dynamic simulation | Out: the process tools' job |
| Content write-back | Out: the tool stays the author |
| Identity-only write-back | Gap: **task-0123** |

## 2. An `implemented_by` relationship in the register

| Box | Content |
|---|---|
| Problem | Code is outside the governed record: `code_map.toml` (instance, path globs to APP) is unapproved and has no lifecycle. |
| Who | Architects, application owners, auditors: which code implements this capability, and who approved the link. |
| Today | `code_map.toml` (task-0050) feeds `knowgov-trace` (task-0051); APP nodes exist; no APP-to-code link. |
| Candidate | A coarse register link APP to repository (or module), approved and owned; path globs stay in `code_map.toml`. |
| Value | The walk reaches code and its owners; decision 0015 and task-0122 can flag code when an application retires. |
| Cost, risk | A register decision and a node kind; risk of copying tool-owned detail, avoided by the coarse grain. |

| Item | Fit/gap |
|---|---|
| Path-level mapping | Fit: `code_map.toml`, stays |
| Approved APP-to-repository link | Gap: register proposal **task-0125**, at the pilot |

## 3. Code semantics; hand-written code that cites nothing

| Box | Content |
|---|---|
| Problem | knowgov cannot tell whether code does what the statements say; hand-written code maps to an APP but to no statement. |
| Who | Developers and reviewers; the gate, for hand-written modules. |
| Today | Correctness is the tests' and the oracle's (J-F's suite, 258 of 258); `knowgov-trace register` records built files with the statements they used; hand-written files have no such record. |
| Candidates | (a) a citation convention: a header naming the keys a file rests on, `knowgov-trace register --keys`, an optional check; (b) reading code semantics (static analysis or a model). |
| Value | (a) medium-high: hand-written code joins the stale and suspect chain. (b) low and non-deterministic; at most flagged evidence. |
| Cost, risk | (a) small; citations rot, which drift detection and re-registration already cover. |

| Item | Fit/gap |
|---|---|
| Is the code correct | Out: tests and oracle |
| Code contradicting a statement | Out, deterministically; a model's reading at most flagged, not planned |
| Hand-written code citing its keys | Gap: **task-0124** |

## Summary

| Item | Disposition |
|---|---|
| Identity-only write-back of the register id | task-0123, low, after task-0063, verified at the pilot |
| Citations in hand-written code | task-0124, medium, can start now |
| APP-to-repository link | task-0125, register proposal at the pilot |
| Process mining as flagged evidence | task-0053, parked on Loop B |
| Dynamic simulation, content write-back, code semantics | Out |
