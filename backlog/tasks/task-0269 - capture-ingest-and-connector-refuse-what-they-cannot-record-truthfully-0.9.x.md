---
id: TASK-0269
title: capture ingest and connector refuse what they cannot record truthfully (0.9.x)
status: To Do
assignee: []
created_date: '2026-11-09T09:33:00Z'
labels:
  - validation
  - correctness
dependencies: []
references:
  - backlog/decisions/decision-0032
  - task-0256
priority: medium
ordinal: 263000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
`capture ingest` records what it should refuse:
- `nobody_knows` set to "yes" or "false" is read as true: a declared gap under the person's handle.
- An answer of true is written as "True", nan as "nan", and [1,2] as "[1, 2]".
- Two conflicting items for one key are both captured.
- A questionnaire whose owner was edited is accepted: ORG-9999, or `x/../../y`, which reaches the path join.
- Scenario S99 is accepted, and so are 2 to 3 MB answers and bidi control characters.

The load applies a capture stamped with another subject or scenario. That may be intended; it is still to be confirmed.

`connector` accepts:
- a far-future `--exported-on`, which is converted to UTC, so the folder is a day off and every later real export is refused as "before the newest";
- `id_attribute` set to `""` or 5, which `check_instance` flags;
- `system = "aris"` given as a string, which raises TypeError and exits 1.

These are fix-only.

Source: group 1 F19 and F20, and group 3 F7, F8 and F13, decision-0032 (task-0256), probed on main 2a8bbeb.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `ingest` refuses each of these with its reason, under capture's documented refusal code:
- a non-boolean `nobody_knows`;
- a non-string answer;
- two items for one key;
- an owner that owns none of the questionnaire's keys, or is not an ORG id;
- an unknown scenario;
- an answer over a stated bound;
- bidi controls.
- [ ] #2 The load refuses or reports a capture stamped with another subject or scenario, and the task records which it does, with the reference.
- [ ] #3 `connector` refuses a future `--exported-on` and keeps the date as typed. It uses `check_instance`'s validator for `id_attribute`. A malformed system table exits 2.
- [ ] #4 `check_attestation_binding`, `check_act_binding` and `check_capture_pairing` pass.
<!-- AC:END -->
