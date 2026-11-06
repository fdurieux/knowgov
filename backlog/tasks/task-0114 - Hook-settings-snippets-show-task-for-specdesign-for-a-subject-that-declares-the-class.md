---
id: TASK-0114
title: >-
  Hook settings snippets show --task-for spec=design for a subject that declares
  the class
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T14:55:00Z'
updated_date: '2026-11-06T03:23:00Z'
labels:
  - ci
  - gate
milestone: m-8
dependencies:
  - TASK-0101
priority: low
type: task
ordinal: 114000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Proposed by task-0101; chosen by the maintainer 2026-11-04. instance/ci/claude/ snippets name --task codegen only; the pilot protocol uses design at the spec commit. Show --task-for spec=design, with a note that it applies only where the subject declares [tasks.design].
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The repository and managed snippets carry --task-for spec=design; the README says when to drop it
- [x] #2 tests/test_claude_hook.py holds the snippets equal to each other
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. instance/ci/claude/settings.json and managed-settings.json: --task-for spec=design after --task codegen (managed keeps --knowgov last). 2. instance/README.md: when to keep it ([tasks.design] in every gated subject) and when to drop it; a subject without the class exits 2 at the spec commit. 3. tests/test_claude_hook.py: both carry it, the same arguments in order, the README note. 4. CHANGELOG Unreleased > Changes.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-06: the advisory fail-open snippet is left as it was (the brief names the repository and managed snippets). A subject without [tasks.design]: gate_cli raises CannotRun 'no task' (exit 2), so the mandatory hook blocks at spec; the README says so. Evidence: tests/test_claude_hook.py test_the_repository_and_managed_snippets_read_the_spec_commit_under_design_and_agree (repo args gate --task codegen --task-for spec=design; managed the same plus --knowgov /opt/knowgov; the README phrases); the existing snippet tests still pass. run_tests.py 534/550 stdlib (16 skipped), 549/550 with rdflib/pyshacl pins and KG_TEST_REQUIRE=rdflib (1 skipped), 0 failed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The hook's repository and managed settings snippets add --task-for spec=design, so the spec commit is read under design as the pilot protocol does; plan and push stay codegen. The instance README says to keep it only where every gated subject declares [tasks.design], since without it the spec commit's gate exits 2 and the mandatory hook blocks, and to drop the two arguments otherwise. A test holds both snippets to the same arguments. The advisory snippet is unchanged. CHANGELOG Unreleased > Changes.
<!-- SECTION:FINAL_SUMMARY:END -->
