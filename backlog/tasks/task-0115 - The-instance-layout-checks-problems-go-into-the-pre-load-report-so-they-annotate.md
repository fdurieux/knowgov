---
id: TASK-0115
title: >-
  The instance layout check's problems go into the pre-load report, so they
  annotate
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-04T14:55:00Z'
updated_date: '2026-11-06T03:17:00Z'
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
- [ ] #1 A layout problem in the example instance appears in the pre-load report and as a GitHub annotation and a GitLab code-quality entry
- [ ] #2 The preload report schema change is additive; the exit code is unchanged
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. tools/preload_check.py --layout: tools/check_instance.check on the same instance, its problems as the report's optional layout block (holds, exit_code, problems: severity, kind, path, message, fails); the report's exit_code stays the lint's.
2. Problems: layout errors blocker and fails (path from the error's prefix: the file, or the subject's subject.toml); check_subject warnings minor and notes info at the subject's subject.toml; absent minor at the file; unread info at the file; code_map unmapped minor, unmatched info at code_map.toml.
3. harness/annotate.py: the layout problems among a pre-load report's findings (kind layout:<kind>); a non-failing one never an error.
4. instance/ci/preload-check.sh: --layout when KG_REPORT is set; check_instance.py still sets the layout exit. Schema additive (layout optional).
5. Proof: harness.yml's action preload step and tools/check_ci_wrappers.py (GitLab) on an unread document committed beside the broken diagram; tests; CHANGELOG new Unreleased.
<!-- SECTION:PLAN:END -->
