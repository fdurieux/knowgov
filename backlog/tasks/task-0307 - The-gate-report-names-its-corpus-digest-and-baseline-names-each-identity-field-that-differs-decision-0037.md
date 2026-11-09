---
id: TASK-0307
title: >-
  The gate report names its corpus digest, and --baseline names each identity
  field that differs (decision-0037)
status: To Do
assignee: []
created_date: '2026-11-09T21:39:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0037
  - backlog/decisions/decision-0029
  - backlog/docs/doc-0037
priority: high
ordinal: 300000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Under decision-0037, accepted 2026-11-09 ("§3.3 (a)", doc-0037 §3.3). Found by the functional review, group A (F2, F3), at main f194aac.

- F2: gate-report v3 names `task_profile`, `register` and `knowgov`, but not the corpus. After an in-place edit of decision_table.md (P2's threshold changed from 1244 to 1300), all four are identical to the pristine S1 report's; only the verdict, why, findings and levels differ.
- F3: take the S1 report and edit its `task_profile` to 0×64, `register.tag` to v0.1.0, `knowgov.version` to 0.5.0 and `as_of` to 2020-01-01. `gate_cli.py --scenario S1 --as-of record --baseline that.json` then gives "no regression", exit 0, and says nothing.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The gate report's identity carries `corpus`: sha256 over the loaded document Versions' digests in a stated, deterministic order. The gate-report schema and decision-0029's documentation describe it, and it is equal on both stores and through the round trip.
- [ ] #2 `--baseline FILE` and `--baseline record` name on stderr each identity field that differs from the baseline's (`task_profile`, `register`, `knowgov`, `corpus`, `as_of`). The exit is unchanged; a baseline without a field reads that field as unknown, never as different.
- [ ] #3 F3's repro prints each changed field; F2's edit changes `corpus`; the pristine run's `corpus` is stable across runs and stores.
- [ ] #4 `check_round_trip` and `check_mcp_server` hold the field; the comparator ignores it; the record does not move.
- [ ] #5 A CHANGELOG line names it under Contract changes.
<!-- AC:END -->
