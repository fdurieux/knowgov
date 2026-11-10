---
id: TASK-0316
title: >-
  The key rule holds wherever a task key enters: task_policy and check_subject
  apply is_key raw-or-NFC; the trace ledger read in NFC (task-0309 re-check N8,
  N9)
status: To Do
assignee: []
created_date: '2026-11-10T00:46:00Z'
labels:
  - contracts
  - keys
  - 0.9.0
dependencies: []
priority: high
ordinal: 309000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Fix-only, pulled ahead of the 0.9.0 cut because N8 can fail open (the coordinator, 2026-11-10). Found by the spot check's re-check of task-0309 (session_01HTAA1R97hqkerDqYvPVLHm, main 9a1df7e); B1-B4 themselves are fixed. The contract does not move.

N8: the runtime applies no key rule to a task class's keys, and check_subject does not apply task-0309 B3's raw rule. `task_policy.problems` checks only for non-empty strings, so gate_cli runs a class whose keys are `nonsense` or `thing\u200b|x` (absent). A class whose block_levels omit `absent` passes over a malformed key, which fails open. `\U0002F800|technology` passes check_subject and runs as `\u4e3d|technology`; `\U000242EE|technology` gets key-syntax with the NFC form named, not the one written. Fix: `key_rule.is_key` under the raw-or-NFC rule, used by task_policy (TaskPolicyError, exit 2) and by check_subject, with messages naming the value as written. Also warn `duplicate` on `[three_valued] keys` equal after NFC, as task classes do.
N9: `trace.read_ledger` echoes an entry's `keys` as written. It should normalise `keys`, `assertions`, `used[].id` and `used[].key` to NFC, so that a pre-0.9 entry with NFD assertion ids still matches its statements and an invalidation still makes it suspect.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 N8: a task class with a key failing the rule raw or after NFC is refused by gate_cli (exit 2, TaskPolicyError, the value as written) and by check_subject (key-syntax, the value as written); a test fails on 9a1df7e
- [ ] #2 N8: [three_valued] keys equal after NFC warn duplicate
- [ ] #3 N9: trace check and code_path report an NFD ledger entry's keys, assertions and used in NFC, and a pre-0.9 entry with NFD ids matches its NFC statements; a test
- [ ] #4 Every public subject, task class and ledger passes as before; the record holds
<!-- AC:END -->
