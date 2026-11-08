---
id: TASK-0225
title: >-
  Propose binding an execution verification to the code the suite passed on,
  sized with the lighthouse's instance (decision-0021)
status: To Do
assignee: []
created_date: '2026-11-08T16:22:00Z'
labels:
  - gate
  - verification
  - decision
milestone: m-8
dependencies: []
references:
  - backlog/decisions/decision-0021
  - subjects/jef_data_load/probes/h7/RESULTS.md
priority: low
type: feature
ordinal: 225000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0021 (accepted 2026-11-08, the maintainer: "Agreed") keeps an execution verification unbound to the code before 1.0, a stated 1.0 limit (doc-0028 K21), and asks for the binding to be proposed at m-8 with the lighthouse's instance.

Today harness/load.py load_verifications writes an execution verification for each key the subject's [verification] map (or derive_execution) names, with evidence_sha256 = sha256(SUBJECT.reference_code()): the reference code's digest at load. Nothing records the digest of the code the oracle last passed on, so a changed reference code loads with its own digest and reads verified. task-0219's H7 probe (#366, subjects/jef_data_load/probes/h7/RESULTS.md) measured it: the gate reads PROCEED on both mutants, trace drift (minor) flags both alike, only the suite separates them (256 and 239 of 258). The guard today is trace check --fail-on minor (docs/reverse-engineering.md step 8).

This task drafts the decision, not the build: how the lighthouse's instance keeps its oracle's evidence decides where the passed-on digest lives (the oracle's evidence, the manifest, the worker's job record) and what a mismatch reads (a stale finding, the verification withheld). No code changes before that decision is accepted.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A proposed decision record carries the four parts (opportunity canvas, fit/gap, SWOT, advice), sized against the lighthouse's instance: where its oracle's evidence is kept and how often its code changes between suite runs
- [ ] #2 The proposal is measured on the H7 probe (tools/check_h7_probe.py): under the proposed binding both mutants read stale and the control does not, run on a branch and reported, nothing merged
- [ ] #3 The proposal states the contract change it would be (0.10.0 after the 0.9.0 cut, per decision-0016) and the record's stated digest for the reference rebuild, so the scored record stays equal
<!-- AC:END -->
