---
id: TASK-0280
title: >-
  decision-0023's version rule extended to the trace ledger and the proposal
  overlay (decision-0033 choice 6)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-09T10:10:00Z'
updated_date: '2026-11-09T10:58:00Z'
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
- [x] #1 The ledger's `schema_version` is read through `harness/formats.py`: missing reads as 1, and a higher version is refused (`FormatTooNew`, exit 2) by `trace check` and `code_path`.
- [x] #2 The overlay accepts an optional top-level `format`: missing reads as 1, and a higher one is refused (exit 2 on the CLI, an `isError` on the MCP), naming the file and both versions.
- [x] #3 `instance/templates/proposal.toml` and the overlay's documentation name `format`, and `tests/test_proposal_template.py` passes.
- [x] #4 `tests/test_formats.py` covers both, and the record does not move.
- [x] #5 `CHANGELOG.md`'s Unreleased section names the change under Contract changes.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/formats.py: kinds ledger (version as schema_version, formats.KEY) and proposal. 2. trace.read_ledger reads the ledger's version by the rule; upward._ledger refuses a newer one (UpwardError). 3. proposal_impact: an optional top-level format, checked in _check_format (the file named by read_proposal), refused as ProposalError. 4. Template, docstrings, MCP description, demo/README and instance/README name it. 5. tests/test_formats.py for both; comparator; CHANGELOG under Contract changes.
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
decision-0023's rule now covers the trace ledger and the proposal overlay (harness/formats.py kinds ledger, its version written as schema_version via formats.KEY, and proposal). trace.read_ledger reads the ledger's schema_version: missing reads as 1, a newer one raises FormatTooNew naming the file and both versions, exit 2 from trace check and register (cli_exit); a new ledger is written at formats.CURRENT. upward.code_path refuses a newer ledger (UpwardError: upward.py exit 2, an isError answer from the MCP code_path) instead of reading the leg unchecked. The overlay accepts an optional top-level format (until now an unknown field): missing reads as 1, a newer or malformed one is ProposalError, the CLI naming the file (read_proposal) and both versions with exit 2, the MCP proposal_impact an isError. instance/templates/proposal.toml writes format = 1; the proposal_impact docstring, the MCP proposal description, demo/README and instance/README's Format versions name it; tests/test_proposal_template.py passes with format in the reader's accepted set. tests/test_formats.py: test_the_trace_ledger_reads_its_schema_version_by_the_rule and test_a_proposal_overlay_takes_an_optional_format_by_the_rule, both failing on main; test_a_missing_version_stays_1_when_a_kind_moves_to_2 builds each kind with its own key. The record does not move: CargoQuote S1-S7 comparator 0 differing leaves on rdflib. Complexity ratchet holds (the format check in _check_format). CHANGELOG under Unreleased > Contract changes. run_tests: bare venv without PyYAML 881/938 (57 skipped), pins 936/938 (2 skipped), 0 failed.
<!-- SECTION:FINAL_SUMMARY:END -->
