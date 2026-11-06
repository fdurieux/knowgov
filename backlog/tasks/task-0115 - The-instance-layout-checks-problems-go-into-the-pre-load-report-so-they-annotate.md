---
id: TASK-0115
title: >-
  The instance layout check's problems go into the pre-load report, so they
  annotate
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T14:55:00Z'
updated_date: '2026-11-06T04:59:00Z'
labels:
  - ci
  - preload
milestone: m-8
dependencies: []
priority: low
type: task
ordinal: 115000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Proposed by task-0106; chosen by the maintainer 2026-11-04. The layout check's problems reach only the job log; the pre-load report should carry them so KG_ANNOTATE shows them as annotations.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A layout problem in the example instance appears in the pre-load report and as a GitHub annotation and a GitLab code-quality entry
- [x] #2 The preload report schema change is additive; the exit code is unchanged
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. tools/preload_check.py --layout: tools/check_instance.check on the same instance, its problems as the report's optional layout block (holds, exit_code, problems: severity, kind, path, message, fails); the report's exit_code stays the lint's.
2. Problems: layout errors blocker and fails (path from the error's prefix: the file, or the subject's subject.toml); check_subject warnings minor and notes info at the subject's subject.toml; absent minor at the file; unread info at the file; code_map unmapped minor, unmatched info at code_map.toml.
3. harness/annotate.py: the layout problems among a pre-load report's findings (kind layout:<kind>); a non-failing one never an error.
4. instance/ci/preload-check.sh: --layout when KG_REPORT is set; check_instance.py still sets the layout exit. Schema additive (layout optional).
5. Proof: harness.yml's action preload step and tools/check_ci_wrappers.py (GitLab) on an unread document committed beside the broken diagram; tests; CHANGELOG new Unreleased.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Evidence. AC1: with an unread story (artefacts/user-stories/orphan.md) committed before the broken diagram, harness.yml's action preload step greps ::warning ... title=knowgov layout absent (minor) and ::notice ... title=knowgov layout unread (info) on it from annotate.py's GitHub output, and asserts the report's layout block; tools/check_ci_wrappers.py asserts the GitLab code-quality entries knowgov-layout:absent (minor) and knowgov-layout:unread (info) on it; tests/test_preload_layout.py adds a layout error (a blocker, an error annotation at the subject's subject.toml or with no file, GitLab '.') and non-failing problems never an error at --fail-on info, on GitHub, GitLab and SARIF. AC2: the layout block is optional (only with --layout), the rest of the report unchanged (test), schema version 1; the report's exit_code stays the lint's and preload-check.sh's exit is unchanged (check_instance.py still sets the layout's). Merged in #273 (2f633a0) on a full green matrix with stack.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The layout check's problems now ride in the pre-load report: tools/preload_check.py --layout runs tools/check_instance.py on the same instance and adds an optional layout block (holds, exit_code, problems with severity, kind, file and fails); instance/ci/preload-check.sh passes it with KG_REPORT, so KG_ANNOTATE shows them through harness/annotate.py, a layout error as an error and absent, unread, warning, note, unmapped and unmatched problems as warnings or notices only. Additive schema change (version 1); exit codes unchanged. Proven in harness.yml's action preload step (GitHub annotations) and tools/check_ci_wrappers.py (GitLab code quality) on an unread story; tests/test_preload_layout.py. Merged in #273. Follow-up: none.
<!-- SECTION:FINAL_SUMMARY:END -->
