---
id: TASK-0268
title: The two Claude Code hooks fail closed on every form they cannot read (0.9.x)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-09T09:33:00Z'
updated_date: '2026-11-09T10:59:00Z'
labels:
  - validation
  - security
dependencies: []
references:
  - backlog/decisions/decision-0032
  - task-0256
priority: high
ordinal: 262000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
`knowgov_hook` misses pushes written as:
- backticks: the tokenising path ignores the backtick that the fallback regex lists;
- `git -c alias.ship=push ship`, and repository aliases;
- `bash -c 'git${IFS}push'`;
- `x=git; $x push`.

Other `knowgov_hook` gaps:
- A `tool_input.command` or `tool_name` given as a list yields no transition, and the hook allows it. task-0200 P8 promises a refusal on anything unreadable.
- A relative `--knowgov` or `KG_HOME` passes the check, then fails from the instance's cwd, so the hook blocks but names the wrong cause.
- `--timeout` nan or inf blocks through an exception.
- A repeated `--task-for` stage silently takes the last.

`attestation_paths` gaps:
- It returns CLEAR for a NotebookEdit naming `subject.toml`, or any `.toml`, before its content checks run.
- It compares names case-sensitively, so `Preload-Baseline.json`, `Register/` and `Captures/` pass. On macOS's case-insensitive default filesystem that is a bypass.

These are fix-only: the fixes restore the fail-closed contract.

Source: group 1 F11 and F12, decision-0032 (task-0256), probed on main 2a8bbeb.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Each command form named reads as its transition or fails closed (blocks), in `transition()`'s tests.
- [x] #2 A command or tool name that is not a string blocks.
- [x] #3 `KG_HOME` and `--knowgov` are resolved to absolute paths before use. `--timeout` must be finite and positive. A repeated `--task-for` stage is refused.
- [x] #4 `attestation_paths` runs its content checks for every write tool, and compares names case-folded.
- [x] #5 The settings snippets are unchanged, unless a test shows they must move.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. knowgov_hook transition: backticks as separators, inline and configured aliases expanded (the call kept), a variable where git or its subcommand would be failing closed, non-string fields refused. 2. main: --knowgov/KG_HOME absolute, --timeout finite and above 0, a repeated --task-for stage refused. 3. attestation_paths: NotebookEdit through the content checks, names case-folded. 4. One test per form, failing on main; settings unchanged. 5. Under the complexity ratchet: the parsers split into helpers.
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
knowgov_hook.py: git is read with the backtick as a separator (shlex punctuation); an alias is read as what it runs, set inline (git -c alias.X=push X) or in git's configuration (git config --get-regexp ^alias. in the event's cwd), shell aliases and chains included, the call itself always kept, so an alias named like a builtin never hides it; a word holding a variable where git or its subcommand would be (git${IFS}push, x=git; $x push, git $x, eval "$x push") fails closed to push or spec by what the command names; a non-string tool_name, tool_input, command or cwd raises and is refused in every profile (task-0200 P8); a repeated --task-for stage is refused; --timeout takes only a finite number above 0 (argparse exit 2, no traceback); --knowgov and KG_HOME are resolved to absolute paths where the hook starts. attestation_paths.py: NotebookEdit runs the content checks (new_source as a review or capture; on subject.toml it cannot tell and blocks; a real .ipynb skipped); every name is compared case-folded (the instance, register/, captures/, [capture] dir, verification map, preload-baseline.json, subject.toml). Four tests, one per form, each failing on main; the settings snippets unchanged; test_dogfood_hooks passes; the record does not move. Under the complexity ratchet the parsers are split into helpers, every score at or under its baseline (188 entries to 185). run_tests: bare venv without PyYAML 883/940 (57 skipped), pins 938/940 (2 skipped), 0 failed.
<!-- SECTION:FINAL_SUMMARY:END -->
