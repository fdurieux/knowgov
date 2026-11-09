---
id: TASK-0299
title: >-
  gate_cli: --baseline record runs task-0286's checks, and a record with empty
  gate_keys is refused (0.9.x)
status: To Do
assignee: []
created_date: '2026-11-09T19:01:00Z'
labels:
  - validation
  - correctness
dependencies: []
references:
  - backlog/decisions/decision-0032
  - task-0256
priority: low
ordinal: 292000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Source: the re-check of the pass's second-round fixes (decision-0032 point 4, task-0256), group 3 at main 95af205, confirmed by group 1 at c94dfa5. Fix-only.

- `_baseline('record')` calls `_read_baseline(p)` with no `run`, so the shape, identity and level checks task-0286 added are skipped on that path. With the subject's own record edited, an off-ladder level gives "the store did not answer: ValueError", a `D6_gate` verdict `FOO` the same, an empty `gate_keys` exit 0 with no key ratchet, and a record whose `scenario` says S2 is accepted for S1. Reachable only by editing the vendored, digest-tested record bytes.
- A record with `gate_keys: {}` passes `_record_shape` on the FILE path too (exit 0), so a keyless record silently disables the key ratchet.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The `record` branch passes `run` and `record_dir` to the same checks as a named file; each form above exits 2 naming the field.
- [ ] #2 A record with an empty `gate_keys` is refused, naming it.
- [ ] #3 `--baseline record` on the public subjects is unchanged, and the record does not move.
<!-- AC:END -->
