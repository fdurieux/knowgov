---
id: TASK-0268
title: The two Claude Code hooks fail closed on every form they cannot read (0.9.x)
status: To Do
assignee: []
created_date: '2026-11-09T09:33:00Z'
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
- [ ] #1 Each command form named reads as its transition or fails closed (blocks), in `transition()`'s tests.
- [ ] #2 A command or tool name that is not a string blocks.
- [ ] #3 `KG_HOME` and `--knowgov` are resolved to absolute paths before use. `--timeout` must be finite and positive. A repeated `--task-for` stage is refused.
- [ ] #4 `attestation_paths` runs its content checks for every write tool, and compares names case-folded.
- [ ] #5 The settings snippets are unchanged, unless a test shows they must move.
<!-- AC:END -->
