---
id: TASK-0211
title: Pre-register the generated-test-case study on CargoQuote (doc-0031 step 2)
status: To Do
assignee: []
created_date: '2026-11-07T08:46:00Z'
labels:
  - evidence
  - tests
  - subjects
milestone: m-8
dependencies:
  - TASK-0210
references:
  - TASK-0057
documentation:
  - >-
    backlog/docs/doc-0031 -
    Generated-test-cases-on-a-green-kit-validated-against-the-records-code-a-test-task-class-a-deterministic-deriver-a-pre-registered-study.-Sense-and-nonsense-opportunity-canvas-fit-gap-SWOT-advice.md
priority: low
type: spike
ordinal: 211000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From doc-0031 (step 2). Generated test cases are worth something only if they catch faulty code and pass correct code, and the record already holds a labelled corpus to measure that on: `reference_impl.py`, which the oracle passes, and the 50 graded code samples of `vendor/kg_experiment/results` (70 run slots, 20 without code), 31 passing the frozen 11-scenario oracle and 19 failing it, with their per-scenario labels. The corpus is thin: 16 of the 19 faulty samples carry a single fault (10 `screening_down_hold` in S2 and S5, 6 `accept_boundary_41` in S3), so mutants of `reference_impl.py` are needed beyond those two faults. A deriver written while looking at the corpus it is graded on measures nothing, and the full governed bundle names every oracle scenario (79 mentions in `S1/bundle_G.txt`), so the generator's input must be fixed before the deriver exists. The record's PREREGISTRATION.md is what made the proof of concept citable; task-0057 does the same for the lighthouse outcome. This task fixes the study's design only; nothing is derived or executed here.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A pre-registration is committed under docs/ before any generated case runs against code: hypotheses, each stated so that it can fail, and a null result named as an outcome the study reports
- [ ] #2 The corpus is fixed by digest before the deriver exists: reference_impl.py, the record's 50 graded samples with the oracle's per-scenario labels, and the mutants of reference_impl.py, specified one per key family (bound, band edge, pricing threshold and order, dependency failure)
- [ ] #3 Each measure and its computation is stated: pass rate on the reference, detection of the 19 faulty samples, agreement with the oracle on the 31 passing ones with the rule that settles a disagreement against the cited keys, coverage of the points oracle_overlap.md lists as not revealed, mutant kill rate, and the cases marked suspect after S6's change
- [ ] #4 The generator's input is fixed so that no verification scope, suite scenario name or file of the frozen suite reaches it (the compact bundle form of task-0140, or an equivalent), and the check that proves it is named
- [ ] #5 The case families the deriver may derive are listed, so step 3 is held to them and a family added later is reported as such
<!-- AC:END -->
