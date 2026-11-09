---
id: TASK-0251
title: >-
  A complexity ratchet in the test suite: new functions stay under the
  threshold, today's hotspots may only shrink (doc-0033)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-09T07:10:00Z'
updated_date: '2026-11-09T09:37:00Z'
labels:
  - quality
  - tests
  - tooling
dependencies: []
priority: medium
ordinal: 245000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer, 2026-11-09: "yes, mint and dispatch both", on the coordinator's advice (doc-0033, Answered): the everyday control that keeps debt from growing between the per-release scans. A standard-library test (tests/test_complexity.py, with a small tools/complexity.py to measure and regenerate) computes each function's cognitive complexity by AST, following Sonar's published rules closely enough that the numbers read alike (documented). It covers harness, demo/app, tools (fixtures excluded) and instance/ci. A function not in the baseline must be at or under the threshold, 15 as in Sonar's default. A function in the baseline (today's hotspots, about 185 at Sonar's count) may not exceed its recorded value; a lower value lowers the baseline in the same pull request; a raised value is accepted only with a stated reason in the baseline entry, reviewed in the PR, so an urgent fix is never blocked. It runs in seconds in the tests job, with no dependency and no server. Not a cut condition.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 tests/test_complexity.py fails a new function over the threshold and a baseline function above its recorded value, and passes on main as committed
- [x] #2 tools/complexity.py measures and regenerates the baseline; a raised entry needs a reason field, and the test reports stale entries (a function gone or lowered) so the baseline tightens
- [x] #3 The measure is documented beside Sonar's (what it counts, where it differs), and the suite stays standard-library only and within the tests job's budget
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. tools/complexity.py: cognitive complexity by AST (Sonar's rules, documented with where it differs) over harness, demo/app, tools (fixtures excluded) and instance/ci; --check, --update (tighten; a raise or a new hotspot only with --reason KEY=TEXT), --init.
2. tools/complexity_baseline.json: today's functions over 15, each {value, floor, reason?}.
3. tests/test_complexity.py: the ratchet holds as committed; Sonar's worked examples; a new hotspot, a raise, a stale entry and an unexplained raise each fail; the baseline is well formed; standard library; seconds.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Measured on main 6dcfe92 (after #398): 1657 functions, 186 over 15 (the brief's 'about 185 at Sonar's count'); the worst harness/review.py::check at 148. The measure: if (+nesting), elif and else (+1), conditional expressions, loops and except (+nesting), a loop's else (+1), match (+nesting), each boolean-operator sequence (+1), direct recursion (+1); nesting from those and from nested functions, lambdas and classes, whose complexity counts to the function around them. Differs from Sonar: comprehension clauses not counted, no labelled jumps, no indirect recursion, module and class-level code unscored; documented in the tool's docstring. The ratchet: value is the recorded score, floor the lowest ever recorded; a function above value fails; below value, at or under 15, or gone is stale and fails until --update tightens it; value above floor needs a reason, which --update writes only from --reason. No product code changed; no CHANGELOG line (maintainer tooling). The measure runs in under a second. Local: run_tests stdlib 860/909, bare venv without yaml 853/909, pins 908/909, each 0 failed (each suite run alone: three worker-probe tests count processes and fail when two suites run side by side).

Regenerated on main 73ff4d4 (after #400, #402, #404, #406): 188 functions over 15 of 1668, largest harness/review.py::check at 148; against 6dcfe92: new proposal_impact.with_levels 17, task_policy.problems 34; raised mcp_server Server._tools 23->25, proposal_impact.render_text 57->64, slices 129->132, rules.compatible 17->21; lowered gate.resolve_spec 42->39, check_subject.check_manifest 85->77; none left. Stdlib suite on the merge 875/925, 0 failed.

Regenerated again on main 2b585d2 (after #405, #408, #401): 188 functions over 15 of 1689, largest harness/review.py::check at 148; the one move against 73ff4d4: tools/coverage_stdlib.py::main raised 17->20 (#401).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
A standard-library complexity ratchet. tools/complexity.py scores each function's cognitive complexity by AST, following Sonar's published rules (documented, with where it differs), over harness, demo/app, tools (fixtures excluded) and instance/ci; tools/complexity_baseline.json records the 186 functions over 15 on main 6dcfe92. tests/test_complexity.py fails a new function over 15, a baseline function above its recorded value, a stale entry (lowered, at or under 15, or gone) until --update tightens the baseline, and a value above its floor without a reason; --update admits a raise or a new hotspot only with --reason, so an urgent fix is never blocked and never silent. It runs in under a second; no product code changed.
<!-- SECTION:FINAL_SUMMARY:END -->
