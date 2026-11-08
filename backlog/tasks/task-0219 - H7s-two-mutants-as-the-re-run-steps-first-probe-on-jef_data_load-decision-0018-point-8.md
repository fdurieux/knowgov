---
id: TASK-0219
title: >-
  H7's two mutants as the re-run step's first probe on jef_data_load
  (decision-0018 point 8)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-08T11:18:00Z'
updated_date: '2026-11-08T14:51:00Z'
labels:
  - process
  - reverse-engineering
  - drift
  - jef
dependencies:
  - TASK-0218
references:
  - >-
    backlog/decisions/decision-0018 -
    Reverse-engineering-and-knowledge-gap-identification-is-an-eight-step-process-knowgov-routes-and-re-finds-its-gaps-and-its-three-contract-changes-land-in-0.9.0.md
documentation:
  - >-
    backlog/docs/doc-0032 -
    Reverse-engineering-and-knowledge-gap-identification-as-a-repeatable-process-eight-steps-with-their-tools-and-gaps-the-bases-decision-0011-H7-and-what-F2-must-bind.-Opportunity-canvas-fit-gap-SWOT-advice.md
priority: medium
type: task
ordinal: 219000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0018 point 8 (doc-0032 §5). H7 (pumllint openwiki-2026-10-27/PREREGISTRATION.md §4, not run, M9): m2 edits a guard a claim cites and is flagged stale; m1 reorders two calls without changing a cited line and is not flagged. In knowgov, R-STALE sees a changed document fragment (neither mutant), trace drift a changed registered file (both), and only the subject's suite sees behaviour (m1 2 failures, m2 11; pumllint recreate_experiment/hidden/MUTANTS.md). Pre-register the probe with task-0218's template, then run it on jef_data_load, recording which instrument caught which change. The mutants apply to public code only (the vendored codex rebuild), never to J-F's private code; if MUTANTS.md describes J-F's original, the probe states the transposition. No paid model calls.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A pre-registration fixed before the run names the mutants, the code they apply to, the three instruments and the expected table
- [ ] #2 The run records, per mutant, what R-STALE, trace drift and the suite report, against the expected table
- [ ] #3 Nothing of J-F's private code is read, copied or committed
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Pre-register with task-0218's template: subjects/jef_data_load/probes/h7/PREREGISTRATION.md, committed alone (370b76d) before any mutant or instrument runs. It names the mutants, the code they apply to (the public codex rebuild, temporary copies), the three instruments and the expected table.
2. tools/check_h7_probe.py: m1 and m2 as exact-text edits of the rebuild's sync.py, refused if the text is not there once, plus an unmutated control. On each of the three:
   - R-STALE: C loaded on rdflib, then apply_change over each of the five documents, counting invalidated statements; the gate's verdict on C recorded beside it.
   - trace drift: a temporary instance whose code_map maps jef/** to APP-0005; C published to a file store; sync.py registered from the control, then check --changed on each variant.
   - the suite: oracle/jef_suite.py under the J-F pins on CPython 3.12.
   Writes results.json; exits 1 on any cell against expectation.
3. Run it under the pins; write RESULTS.md beside the pre-registration, with each cell against the table, the suite's failing cases by feature and the gate's verdicts.
4. Tests and CI as the existing check tools need (test_clock's pinned rule; rdflib split if a CI step is added). J-F's private code is never read.
<!-- SECTION:PLAN:END -->
