---
id: TASK-0105
title: Dogfood the fail-closed hook on knowgov's own protected paths
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T10:46:00Z'
updated_date: '2026-11-04T11:16:00Z'
labels:
  - ci
  - security
milestone: m-8
dependencies:
  - TASK-0099
priority: medium
type: task
ordinal: 108000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Maintainer's decision 2026-11-04, recorded in doc-0014 §11 (#170). This repository gains a .claude/ with two hooks on its own protected paths: (1) a vendored file or its SOURCE.md edited by hand; (2) a backlog markdown file written other than through the backlog CLI. The hooks reuse task-0099's script and exit mapping and call nothing else. The knowledge gate is not wired to this repository's commits: no subject describes the repository. No recipe, README or release note claims an outcome from the 20-of-20 figure (doc-0014).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A test feeds each hook a hand edit to a vendored file and to a backlog file and sees both blocked; a CLI-written backlog change and an unprotected edit both pass
- [x] #2 The hooks use task-0099's script and its exit mapping, with no copy of it
- [x] #3 CLAUDE.md names the hooks in one line and states what they guard
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. .claude/hooks/protected_paths.py: two checks (vendored, backlog) on PreToolUse Edit|Write|MultiEdit|NotebookEdit; vendored trees read from the vendor tools' DEST and each subject's [vendor] dest; outcome mapped by importing decide() from instance/ci/claude/knowgov_hook.py (no copy).
2. .claude/settings.json: two hook entries, onFailure block.
3. tests/test_dogfood_hooks.py: both blocked by hand edits, CLI-written backlog change and unprotected edit pass, no copy of the mapping.
4. CLAUDE.md one line.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
tests/test_dogfood_hooks.py: Edit/Write/MultiEdit on demo/register, demo/model, subjects/{cargo_quote,jef_data_load}/vendor (files and SOURCE.md) block under 'vendored'; backlog/**/*.md (and NotebookEdit) block under 'backlog'; Bash events (the backlog CLI, the vendor tools) and edits to unprotected files (incl. subjects/jef_data_load/record/SOURCE.md, a run's output, not vendored) pass; unreadable events block fail-closed. Vendored trees come from the vendor tools' DEST and vendor_subject.spec_for. Mapping: decide/emit imported from instance/ci/claude/knowgov_hook.py; the test holds the source free of a copy. Settings use a command string with $CLAUDE_PROJECT_DIR and onFailure block. Limit: a Bash write (sed -i, redirection) to a protected path is not seen; the task scopes Edit and Write. Both suites 314/314.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
.claude/settings.json wires two fail-closed PreToolUse hooks (.claude/hooks/protected_paths.py vendored|backlog) on the write tools; each answers under the gate contract and task-0099's decide maps it (1 and 2 block). The knowledge gate is not wired to this repository. CLAUDE.md names them. Follow-up proposed to the coordinator: Bash writes to protected paths; a decide() unavailable-route parameter (its route text speaks of the gate).
<!-- SECTION:FINAL_SUMMARY:END -->
