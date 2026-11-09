---
id: TASK-0280
title: >-
  decision-0023's version rule extended to the trace ledger and the proposal
  overlay (decision-0033 choice 6)
status: To Do
assignee: []
created_date: '2026-11-09T10:10:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0033
  - task-0256
priority: high
ordinal: 273000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The trace ledger (`KG_LEDGER`) writes `schema_version: 1` but never reads it, so a ledger at 99 is read. The proposal overlay has no version, and a top-level `format` is refused as an unknown field. decision-0023's rule (a missing version reads as 1; a newer one is refused, exit 2, naming the file and both versions) covers neither.

Under decision-0033 (accepted 2026-11-09, "all as advised") choice 6(a), both are versioned: the ledger by its `schema_version`, and the overlay by an optional top-level `format`.

Source: validation-pass group 3 CB5, task-0256.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The ledger's `schema_version` is read through `harness/formats.py`: missing reads as 1, and a higher version is refused (`FormatTooNew`, exit 2) by `trace check` and `code_path`.
- [ ] #2 The overlay accepts an optional top-level `format`: missing reads as 1, and a higher one is refused (exit 2 on the CLI, an `isError` on the MCP), naming the file and both versions.
- [ ] #3 `instance/templates/proposal.toml` and the overlay's documentation name `format`, and `tests/test_proposal_template.py` passes.
- [ ] #4 `tests/test_formats.py` covers both, and the record does not move.
- [ ] #5 `CHANGELOG.md`'s Unreleased section names the change under Contract changes.
<!-- AC:END -->
