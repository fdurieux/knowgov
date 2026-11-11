---
id: decision-0039
title: >-
  Before the freeze: an instance reads its own register, the identity names the
  subject's configuration, register_impact walks the thread, execution's at is
  the load time, and the suite digest binds its declared files (doc-0038 §3)
date: '2026-11-11T22:52:00Z'
status: accepted
---

## Context

doc-0038 is the 0.9.0 release candidate's state of affairs, redone at `main` `e5a5158` by three fresh read-only reviewers after every doc-0037 decision had been built. It raised five findings that bear on contracts freezing at 0.9.0: §3.1 to §3.4, and §3.5 from group A's re-check of task-0330. Each section there carries the options, the opportunity canvas, the fit/gap, the SWOT and the advice in full; this record restates them in brief and records the choice.

The maintainer's word, 2026-11-11: "go with recommendations".

## Options and choice

### §3.1 Which register an instance's gate, CI, hook and capture read (C-N1; FR-10, FR-12, FR-05)

Today `cadence.register_root` and `capture.register_root` fall back to `demo/register`, knowgov's public register, when `KG_REGISTER` is unset. `knowgov-gate.sh` and the hook never set it. So a client's verdicts, review cadence and accepted givers follow the public register.

- (a) fail closed: on a subject outside the checkout with `KG_REGISTER` unset, every register-reading tool refuses with exit 2 and names the setting. The CI template and the hook pass `<instance>/register` unless one is set, and the guide says so;
- (b) default to `<instance>/register` by inference from `KG_SUBJECT`;
- (c) a warning only.

**Chosen: (a).** It fails closed with no guessing, uses the existing exit-2 "cannot run" contract, and leaves the record unmoved, because subjects inside the checkout keep `demo/register`. It moves a contract setting's effective default, which is why it is decided before the freeze.

### §3.2 The identity's remaining inputs (A-N2, B-N1; FR-03, FR-08, U5)

`register_map.toml`, `scenarios.toml` and `subject.toml`'s other tables decide the verdict but sit in no digest. The trace report's gate block lacks the gate report's `corpus`, `attestations` and `captures`.

- (a) one additive `configuration` identity field: a sha256 per subject configuration file the load read, recorded at load through decision-0038 N2's `record_inputs` and `inputs`, and named by `differs`. The trace gate block gains `corpus`, `attestations`, `captures` and `configuration`;
- (b) narrow the claim and list it in Known limits until 0.10.0;
- (c) the gate report only.

**Chosen: (a).** It makes decision-0038's "names every input that decided it" true, through one proven mechanism. It is additive with no version change.

### §3.3 A `thread` walk in `register_impact` (B-D7; FR-06)

- (a) add `thread` to `register_impact`'s walk, using the register's `THREAD` walk as `proposal_impact` already loads it, with the same answer shape;
- (b) list it in Known limits and narrow FR-06.

**Chosen: (a).** It reuses existing code, adds no new semantics, and makes FR-06 true as written. An enum value added after the freeze would be a contract change.

### §3.4 What an execution verification's `at` means (A-N3; FR-01, U5)

- (a) an optional `on` date in the subject format;
- (b) document it: `at` is when the load recorded the attestation, and the run is identified by its digests (decision-0038 N-b), not by a date.

**Chosen: (b).** A date the attester writes, which knowgov cannot check, adds no assurance the digests do not already give. The guide, the field's description and Known limits name it.

### §3.5 What the `suite` digest binds (group A's re-check of task-0330, N-2; FR-01, U5)

`Subject.code_parts` takes the suite as the `[oracle] script`'s own bytes. CargoQuote's expectations live in the acceptance module the script imports, which no digest covers. An honest suite change therefore leaves the digest unchanged, and a wrong edit to the expectations moves nothing.

- (a) an optional `[oracle] suite` list of files, each digested into `suite`. It is additive in the subject format; when missing, the suite digest is the script alone, as now. CargoQuote's manifest lists its acceptance module;
- (b) name the limit and bind more in 0.10.0;
- (c) follow the script's local imports automatically, which is refused as fragile.

**Chosen: (a).** It makes decision-0038 N-b's "the suite it ran" true as written, and it is explicit, with no import guessing. If a vendored file's digest would move the record, fall back to (b) for the record and keep (a) for instances.

## Opportunity canvas

- Problem: five places where a frozen 0.9.0 would encode a fail-open default or an audit gap: §3.1 the register, §3.2 the configuration, §3.5 the suite expectations; or a claimed requirement that is unmet: §3.3 FR-06, §3.4 the meaning of `at`.
- Users: every instance (U1, U2), its CI and assistants (U4), and its auditors (U5).
- Cost:
  - three small contract builds: §3.1, §3.2, §3.5;
  - one narrow one: §3.3;
  - one documentation change: §3.4.
- Value: the frozen contracts mean what the release says.

## Fit/gap

- (a) for §3.1, §3.2, §3.3 and §3.5 closes FR-03, FR-05, FR-06, FR-08, FR-10 and FR-12 as doc-0038 §2 grades them.
- (b) for §3.4 states the truth instead of adding an uncheckable field.
- Every alternative left a known gap frozen for at least a minor version.

## SWOT

- Strengths: each choice reuses an existing mechanism or exit contract, and fails closed where it changes behaviour.
- Weaknesses:
  - an adopter sets one more variable by hand (§3.1);
  - comparators learn one more identity field (§3.2);
  - CargoQuote's execution lists move (§3.5).
- Opportunities:
  - `check_instance` can name a register mismatch;
  - `differs` names the configuration that changed;
  - J-F's oracle can declare its own suite.
- Threats:
  - a local workflow that relied on the public register breaks; that workflow was wrong;
  - the record moving under §3.5, which is covered by its fallback.

## Advice

The coordinator advised (a), (a), (a), (b) and (a), for the reasons in each section above and in doc-0038 §3. The maintainer took all five.

## Decision

Accepted 2026-11-11 by the maintainer: §3.1 (a), §3.2 (a), §3.3 (a), §3.4 (b), §3.5 (a). The builds are task-0334 to task-0338. Each is re-checked by a fresh reviewer before the cut.
