---
id: TASK-0293
title: >-
  schema_check reads patterns as JSON Schema does (ASCII \d), and add_artefact
  refuses a backtick (0.9.x)
status: To Do
assignee: []
created_date: '2026-11-09T15:43:00Z'
labels:
  - validation
  - correctness
dependencies: []
references:
  - backlog/decisions/decision-0032
  - task-0256
priority: low
ordinal: 286000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Fix-only. Source: the bounded re-probe (decision-0032 point 4, task-0256), group 2 at main 9861953 (N3, N4).

N3: `harness/schema_check.py` compiles `pattern` with Python's `\d`, which matches any Unicode digit; JSON Schema's ECMA-262 `\d` is ASCII only. `node: "CAP-٠٠٠١"` (Arabic-Indic digits) passes the schema check and is refused later by the tool ("no such node"), not with -32602; `owner` is the same.

N4: the `add_artefact` prompt's `file` accepts a backtick (`a`b.md`), and the prompt wraps the value in a code span, which breaks.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `schema_check` compiles every pattern with `re.ASCII`, and a test holds `CAP-٠٠٠١` to -32602.
- [ ] #2 `add_artefact`'s `file` refuses a backtick, named, held by a test.
<!-- AC:END -->
