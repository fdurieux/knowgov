---
id: TASK-0266
title: >-
  trace register refuses what it cannot rest on, trace check refuses another
  subject's store, and the ledger read is bounded (0.9.x)
status: To Do
assignee: []
created_date: '2026-11-09T09:33:00Z'
updated_date: '2026-11-09T15:38:00Z'
labels:
  - validation
  - correctness
dependencies: []
references:
  - backlog/decisions/decision-0032
  - task-0256
priority: medium
ordinal: 260000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
`trace register` accepts what it should refuse:
- `--assertion <unknown id>` registers with `used:1`: an output resting on nothing, which `check` never finds suspect.
- A repeated `--file` registers twice.
- `--commit ''` is accepted.
- `--repo` and `KG_CODE_REPO` are not checked: `''`, `'../x'` and `':'` all go into the id. Ids can collide: repo a, commit b:c, file d; and repo a, commit b, file c:d.

`trace check` reads a store that holds another subject (163 "absent" blockers for jef_data_load on the cargo store), where `gate --no-load` refuses.

`--ledger /dev/full` is read without a bound, and duplicate ledger entries are read.

These are fix-only. The ledger's version rule is decision-0033 choice 6.

Source: group 1 F7 and F8, and group 3 CB5's duplicates, decision-0032 (task-0256), probed on main 2a8bbeb.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Unknown statement ids, duplicate files, an empty or non-hex commit, and a repo outside a name pattern each exit 2. Ids cannot collide, held by a test with the two colliding forms.
- [ ] #2 `trace check` refuses another subject's store, as `gate --no-load` does.
- [ ] #3 The ledger read is size-capped, and duplicate entries are refused or reported.
- [ ] #4 `check_trace_walkthrough` and the record are unchanged.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Re-probe and spot check at main 9861953 (decision-0032 points 4 and 5, task-0256):
- Group 1: `upward code` exits 2 on a ledger version error, but a ledger whose `tool` is wrong or whose `entries` is not a list returns the leg 'unchecked' with exit 0.
- Group 3: a JSON `null` format reads as missing, and the writer keeps the null. The same holds for the proposal overlay's optional `format` (task-0280).
<!-- SECTION:NOTES:END -->
