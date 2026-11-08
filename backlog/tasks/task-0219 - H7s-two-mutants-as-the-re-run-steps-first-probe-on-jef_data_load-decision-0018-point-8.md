---
id: TASK-0219
title: >-
  H7's two mutants as the re-run step's first probe on jef_data_load
  (decision-0018 point 8)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-08T11:18:00Z'
updated_date: '2026-11-08T15:31:00Z'
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
- [x] #1 A pre-registration fixed before the run names the mutants, the code they apply to, the three instruments and the expected table
- [x] #2 The run records, per mutant, what R-STALE, trace drift and the suite report, against the expected table
- [x] #3 Nothing of J-F's private code is read, copied or committed
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Sequence:
- 370b76d: the pre-registration, alone.
- dff0b4f: the probe.
- fa4648b: a setup fix. The first run stopped at trace register (exit 2) before any instrument reported, because the temporary instance had no register/ to check APP-0005 against. The expected table is unchanged.
- The run on fa4648b's tree (CPython 3.12.3, the J-F and record pins; KG_CLOCK=pinned) exited 0, every cell as pre-registered:
  - control: R-STALE 0 invalidated, trace no finding, suite 258/258;
  - m1: 0 / drift / 256/258 (collectors: exactly the two scenarios MUTANTS.md names on the original);
  - m2: 0 / drift / 239/258 (19 across adjustment, collectors, decisions, status and sync; 11 of 178 on the original);
  - the gate on C: PROCEED on all three.
Recorded in subjects/jef_data_load/probes/h7/RESULTS.md, with the deviation.
A known limit found: drift is minor and trace check's default --fail-on is blocker, so it exits 0. A pipeline stops on a changed registered file only with --fail-on minor. Guide step 8 now says so and quotes the probe's result. The CHANGELOG has a line under Unreleased, Changes.
tests/test_h7_probe.py holds three things:
- each edit is exact text the vendored rebuild holds once;
- EXPECTED equals PREREGISTRATION §8's table;
- RESULTS.md names 370b76d.
The probe exits through _outcomes.run (test_outcomes). There is no CI step: the probe runs the suite three times, so it is run by hand and its result kept.
CLAUDE.md layout line (the coordinator's request after closing #365): the guide, the template, their test and the probe.
What was read: the public rebuild, the vendored kit and oracle, pumllint's public openwiki PREREGISTRATION (§3 M9, §4 H7), and the prose of hidden/MUTANTS.md for intent and counts. Nothing of the original's diff it quotes is copied. J-F's repository is never opened. No model call.
Suites:
- pins: 794/795, 1 skip, 0 failed;
- bare 3.13: 750/795, 45 skips, 0 failed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The re-run step's first probe (decision-0018 point 8): H7's two mutants, transposed to the public codex rebuild's sync.py, pre-registered (370b76d) before the probe existed in the repository.
The run was as pre-registered:
- R-STALE flags neither mutant (0 invalidated), since no document changed; the gate on C reads PROCEED throughout.
- trace flags both, as the same minor drift.
- Only the kit's suite separates them: 2 and 19 of 258 failing. m1's two are the scenarios MUTANTS.md names on J-F's original.
A known limit surfaced: trace check exits 0 on drift unless --fail-on minor. docs/reverse-engineering.md step 8 now says so.
Adds:
- subjects/jef_data_load/probes/h7/ (PREREGISTRATION.md and RESULTS.md);
- tools/check_h7_probe.py;
- tests/test_h7_probe.py (the edits still apply once to the vendored rebuild, and the expected table is the frozen one);
- a CHANGELOG line;
- the CLAUDE.md layout line for the guide, the template and the probe.
Public code only: J-F's repository was never opened, nothing of MUTANTS.md's diff was copied, and no model was called.
Both suites pass.
Follow-up for the maintainer, not opened: whether a verification's execution evidence should be compared with the code as it now stands, so the gate sees a behaviour change.
<!-- SECTION:FINAL_SUMMARY:END -->
