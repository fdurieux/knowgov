---
id: TASK-0225
title: >-
  Propose binding an execution verification to the code the suite passed on,
  sized with the lighthouse's instance (decision-0021)
status: Done
assignee: []
created_date: '2026-11-08T16:22:00Z'
updated_date: '2026-11-15T10:31:00Z'
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-15, superseded before it was drafted. decision-0038 N-b (reviewer A's re-check of task-0306: "Editing reference_impl.py keeps every execution verification and PROCEED, and nothing is named") chose option (a), "[verification] execution lists the digest of the code it ran on", and task-0320 built it before the 0.9.0 cut rather than at m-8: [verification] execution's implementation and suite, compared by load.execution_code, a mismatch or a missing list verifying nothing by execution, named by the gate's attestation finding. decision-0039 §3.5 (task-0338, task-0340) extended the suite digest to the files [oracle] suite declares; decision-0040 (task-0341) put the code and suite compared into the report's identity. What this task asked to decide (where the passed-on digest lives, what a mismatch reads) is therefore decided: in the subject's attestation, and a mismatch verifies nothing. docs/lighthouse-evaluation.md's Knowledge-quality gap was rewritten the same day to say so, with H7 kept as the dated record of the code it ran on (2026-11-08, before the binding landed on 2026-11-11). Remaining limit, not this task's: no oracle runs at load, so a listed digest asserts a result, never a fresh run (docs/guide.md §9).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Closed as superseded by decision-0038 N-b and task-0320, which bound an execution verification to the code and suite it ran on before the 0.9.0 cut; decision-0039 §3.5 and decision-0040 completed the binding and its report identity. No proposal was drafted and no acceptance criterion is checked: AC #1-#3 asked for a decision record, an H7 measurement and a 0.10.0 sizing for a binding that already exists, so none is met and none is needed. Nothing built here. Follow-up, not opened: a fresh-run receipt (a verification issued only by the run that passed) is a contract addition, 1.1.0 at the earliest (decision-0041), and sits with knowgov-bench's XR-05 if the maintainer wants it.
<!-- SECTION:FINAL_SUMMARY:END -->
