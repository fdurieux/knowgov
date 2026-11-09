---
id: TASK-0301
title: >-
  A key is compared, stored and reported in Unicode NFC wherever it enters
  (decision-0034 A2)
status: To Do
assignee: []
created_date: '2026-11-09T21:13:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0034
  - task-0297
  - task-0256
priority: high
ordinal: 294000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Under decision-0034 Amendment A2, accepted 2026-11-09 ("N3 (a) as advised"). Found by the spot check's re-check of task-0297 at main f194aac (N3), and confirmed by the coordinator: `société|adresse` in NFC and in NFD both pass `key_rule.is_key` and are different keys, so one reads absent against the other. Nothing in knowgov normalises. The decomposed form comes routinely from macOS paths and clipboards, PDF copies and some exports; a Belgian instance will have accented French names throughout.

The rule: `key_rule.normalise` (NFC, not NFKC) applied wherever a key enters, before validation:
- the MCP reader's arguments;
- `check_subject` and the MCP `subject_check`;
- the `Subject` loader;
- the mappers' yielded keys;
- `register_map.toml` rows;
- code-header citations and `trace`;
- captures;
- `proposal_impact`;
- every CLI that takes a key.

The store holds NFC, and every answer echoes NFC.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `key_rule.normalise` is NFC, and every entry point where a key enters applies it before validation; the task's notes list each entry point.
- [ ] #2 A test sends an NFD key through every entry point and finds it matched against the NFC key a document yields, and the reverse, with `société|adresse` and one more name, on a subject copy whose document spells the name in NFD.
- [ ] #3 The store holds NFC and every report and answer echoes NFC; `DESCRIPTION`, the docstring and the adopter docs state that canonically equivalent keys are one key.
- [ ] #4 `instance/README.md` names `git config core.precomposeunicode true` for macOS checkouts. Every public key is unchanged, and the record does not move.
- [ ] #5 `CHANGELOG.md`'s Unreleased section names the rule under Contract changes.
<!-- AC:END -->
