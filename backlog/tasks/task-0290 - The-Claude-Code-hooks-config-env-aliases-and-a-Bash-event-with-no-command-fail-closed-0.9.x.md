---
id: TASK-0290
title: >-
  The Claude Code hooks: --config-env aliases and a Bash event with no command
  fail closed (0.9.x)
status: To Do
assignee: []
created_date: '2026-11-09T15:37:00Z'
labels:
  - validation
  - correctness
dependencies: []
references:
  - backlog/decisions/decision-0032
  - task-0256
priority: medium
ordinal: 283000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Remaining after task-0268, found by group 1's re-probe at main 9861953 (decision-0032 point 4, task-0256). Fix-only.

- N12: `X=push git --config-env=alias.p=X p` gives no transition, though git accepts `--config-env`. (The attached form `-calias…` is rejected by git itself, so it is not a gap.)
- N13: a Bash event with no `command`, or an empty `tool_input`, is allowed. It should fail closed, as other malformed input now does.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `knowgov_hook.py` reads `--config-env=alias.<name>=<VAR>` as an alias whose value comes from the environment variable it names, and an unreadable one fails closed.
- [ ] #2 A Bash event with no `command` or an empty `tool_input` blocks in every profile.
- [ ] #3 Both are tests beside task-0268's.
<!-- AC:END -->
