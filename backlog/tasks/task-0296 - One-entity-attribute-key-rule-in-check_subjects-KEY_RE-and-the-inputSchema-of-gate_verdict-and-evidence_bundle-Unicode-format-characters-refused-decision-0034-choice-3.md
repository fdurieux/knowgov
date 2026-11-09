---
id: TASK-0296
title: >-
  One entity|attribute key rule in check_subject's KEY_RE and the inputSchema of
  gate_verdict and evidence_bundle, Unicode format characters refused
  (decision-0034 choice 3)
status: To Do
assignee: []
created_date: '2026-11-09T16:51:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0034
  - backlog/decisions/decision-0032
  - task-0256
priority: high
ordinal: 289000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Under decision-0034 (accepted 2026-11-09, "N7, D1, D3 as advised") choice 3(a). Found by the spot check (GV-1, CS-4) at 9861953.

- `gate_verdict {"keys":["nonsense"]}` is answered as BLOCKED, "nonsense (absent)", though the description says `entity|attribute` and `check_subject`'s `KEY_RE` refuses it. `keys:[""]` is already refused.
- `evidence_bundle` takes `keys` the same way.
- `KEY_RE`'s `\s` misses a zero-width space: `thing\u200b|property` passes the checker and reads absent at the gate.

One rule: each side of the `|` is non-empty and holds no `|`, no whitespace and no format character (`\u200b` to `\u200d`, `\u2060`, `\ufeff`). task-0265's CS-4 item moves here.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `tools/check_subject.py`'s `KEY_RE` and the `keys` items of `gate_verdict` and `evidence_bundle` carry the same pattern, held equal by a test.
- [ ] #2 `gate_verdict` and `evidence_bundle` answer -32602 for a key outside it, over stdio and HTTP, in both eras; `check_mcp_server.py` holds one such call.
- [ ] #3 A key holding a zero-width space or another listed format character is an error in `check_subject` and -32602 on the wire.
- [ ] #4 Every key in the public subjects and the record matches, and the record does not move.
- [ ] #5 `CHANGELOG.md`'s Unreleased section names the pattern under Contract changes.
<!-- AC:END -->
