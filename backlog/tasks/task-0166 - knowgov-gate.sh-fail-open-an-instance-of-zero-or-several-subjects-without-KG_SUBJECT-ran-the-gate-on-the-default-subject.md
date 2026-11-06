---
id: TASK-0166
title: >-
  knowgov-gate.sh fail-open: an instance of zero or several subjects without
  KG_SUBJECT ran the gate on the default subject
status: Done
assignee:
  - '@claude'
created_date: '2026-11-06T09:42:00Z'
updated_date: '2026-11-06T09:46:00Z'
labels:
  - security
  - ci
dependencies: []
priority: high
type: bug
ordinal: 169000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
instance/ci/knowgov-gate.sh: subject() refused with exit 2 inside $(subject) (lines 128 and 138), which ends only the subshell, and an unmatched glob counted as one subject; with KG_SUBJECT unset, an instance with zero or several subjects fell through to gate_cli/trace with an empty --subject, i.e. the harness's default subject, and could exit 0. test_ci_wrappers passed in CI only because no store is reachable there. Found during task-0157; 0.7.0 and earlier affected.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 An instance with zero or several subjects and no KG_SUBJECT exits 2 for gate, trace-check and trace-register, with nothing run
- [x] #2 An empty subjects/ glob counts 0 subjects
- [x] #3 A test in tests/test_ci_wrappers.py, independent of whether a store is reachable, fails on today's script and passes on the fix
- [x] #4 CHANGELOG line under Unreleased / Changes naming 0.7.0 as affected
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. subject(): count only files the glob matched; return 2, never exit, from inside $(...).
2. Each call site: S=$(subject) || exit 2.
3. Test with a stub interpreter recording argv; CHANGELOG under Unreleased / Changes.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
tests/test_ci_wrappers.py test_without_kg_subject_an_instance_of_zero_or_several_subjects_runs_nothing_and_exits_2: a stub PYTHON answers the version probe and records every other call, exiting 0; zero and two subjects exit 2 for gate, trace-check and trace-register with nothing recorded ("holds 0"/"holds 2"); one subject runs gate_cli with --subject on it. On origin/main's script it fails (exit 0, "holds 1 subject(s)" for an empty folder); on the fix it passes, with no store involved.
Suites: stdlib 586/606, pinned 605/606, 0 failed; tools/check_ci_wrappers.py on rdflib holds.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
knowgov-gate.sh fails closed: with KG_SUBJECT unset, an instance of zero or several subjects exits 2 for gate and trace-* with nothing run (the refusal no longer dies in a subshell; an empty glob counts 0). Store-independent test; CHANGELOG names 0.7.0 as affected.
<!-- SECTION:FINAL_SUMMARY:END -->
