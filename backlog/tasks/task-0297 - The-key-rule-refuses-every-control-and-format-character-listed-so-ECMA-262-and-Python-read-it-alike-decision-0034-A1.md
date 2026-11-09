---
id: TASK-0297
title: >-
  The key rule refuses every control and format character, listed so ECMA-262
  and Python read it alike (decision-0034 A1)
status: To Do
assignee: []
created_date: '2026-11-09T19:01:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0034
  - task-0296
  - task-0256
priority: high
ordinal: 290000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Under decision-0034 Amendment A1, accepted 2026-11-09 ("K1 (a) as advised"). Found by the spot check's re-check of task-0296 at main 946c72e, and confirmed by the coordinator.

- K1: these pass `harness/key_rule.py` on every surface (`gate_verdict`, `evidence_bundle`, `check_subject`) and read as absent at the gate: U+200E (LRM), U+202E (RLO, a bidi override), U+00AD (soft hyphen), U+2061, U+180E and NUL.
- K2: Python's str `\s` matches U+001C to U+001F and U+0085, but ECMA-262's does not. So a JavaScript client validating the inputSchema accepts `thing\x1c|property`, which the server refuses with -32602.

The rule: each side of the `|` is non-empty and holds no `|`, no whitespace and no character of general category Cc or Cf, every class listed as `\uXXXX` ranges with no `\s`, `\d` or `\w`. Combining marks (Mn, such as U+034F) stay allowed.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `SIDE` refuses `|`, every whitespace character and every Cc and Cf code point, listed explicitly; `PATTERN` holds no `\s`, `\d` or `\w`.
- [ ] #2 A test generates every Cc and Cf code point and every whitespace character from `unicodedata` and holds the pattern to refuse each, and holds a combining mark accepted.
- [ ] #3 `gate_verdict` and `evidence_bundle` answer -32602 for an RLO key over stdio and HTTP, held by `check_mcp_server`; `check_subject` reports it as `key-syntax`.
- [ ] #4 `DESCRIPTION` and the docstring state the rule; every public key still matches, and the record does not move.
- [ ] #5 `CHANGELOG.md`'s Unreleased section names the widened rule under Contract changes.
<!-- AC:END -->
