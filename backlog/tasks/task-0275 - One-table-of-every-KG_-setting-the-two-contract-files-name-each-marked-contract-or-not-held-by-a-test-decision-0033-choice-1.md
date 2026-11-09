---
id: TASK-0275
title: >-
  One table of every KG_* setting the two contract files name, each marked
  contract or not, held by a test (decision-0033 choice 1)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-09T10:09:00Z'
updated_date: '2026-11-09T11:02:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0033
  - task-0256
priority: high
ordinal: 268000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0016 point 3 made every setting that `instance/README.md` or `docs/security.md` documents a contract. task-0234's README section reads as if only decision-0027's twenty are contracts, and the two files name 75 settings.

Under decision-0033 (accepted 2026-11-09, "all as advised") choice 1(b), one table lists them all, each marked contract or not. decision-0016 point 3 now reads "a setting the table marks as a contract".

The contracts are the settings an instance's CI, compose file or hook sets in order to run. The test clock, demo ports and tuning knobs are marked not a contract. The classification is the maintainer's word row by row: the build proposes it, and the PR is held until the maintainer confirms the table.

Source: validation-pass group 1 C3, task-0256.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `instance/README.md` has one table with one row per `KG_*` setting named in `instance/README.md` or `docs/security.md`. Each row gives the setting, what it does, its group, and whether it is a contract.
- [x] #2 A test fails when either file names a setting the table lacks, or when the table names a setting neither file mentions.
- [x] #3 The README's settings paragraph and the contracts table say that a setting is a contract when the table marks it so, citing decision-0016 point 3 as amended by decision-0033 choice 1.
- [x] #4 The PR is held for the maintainer's confirmation of the rows. The coordinator merges only after it.
- [x] #5 `CHANGELOG.md`'s Unreleased section names the table under Contract changes.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Replace instance/README.md's four settings tables with one table: a row per KG_* setting instance/README.md or docs/security.md names (75), columns setting, group, what it does, default, contract (yes, or no: why).
2. Classify by decision-0033 choice 1(b): a contract is a setting an instance's CI, compose file or hook sets in order to run; the test clock, demo ports, tuning knobs and the uncontained escape not.
3. Reword the section's paragraph, the contracts table's KG_* row and the note under decision-0016's quote: a setting is a contract when the table marks it so (decision-0016 point 3 as amended by decision-0033 choice 1); point the worker paragraph in docs/security.md at the table.
4. tests/test_settings_table.py: a setting either file names without a row fails; a row for a setting named nowhere outside the table (but the TABLE_ONLY settings whose row is their description) or read by no code fails; groups and marks held; decision-0027's twenty contracts.
5. CHANGELOG Unreleased > Contract changes; PR held for the maintainer's confirmation of the rows.

6. On the maintainer's confirmation ("#418 as advised"), KG_CLOCK and KG_TODAY become contracts under the group Clock: 63 contracts, 12 not.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
PR #418, branch claude/task-0275-settings-table. Proposed 61 contracts, 14 not: KG_CLOCK, KG_TODAY (test clock), KG_PORT_APP, KG_PUBLIC_PORT (demo ports), KG_LOAD_MEMORY_MARGIN, KG_NEO4J_LEASE_SECONDS, KG_NEO4J_LOCK_TIMEOUT, KG_NEO4J_READ_WAIT, KG_RDFLIB_LOCK_TIMEOUT, KG_STORE_READ_ATTEMPTS, KG_PAGE_MAX_RESPONSE, KG_PAGE_MAX_RUNS, KG_MCP_MAX_RESPONSE (tuning), KG_ALLOW_UNCONTAINED_EXECUTION (an escape). Stdlib suite 889/939, 50 skipped (pins), 0 failed; the new test fails on a setting added with no row (mutation check). The coordinator advised the maintainer to make KG_CLOCK and KG_TODAY contracts (instance/README.md and docs/guide.md advise both in a pipeline), which would give 63 and 12; the table waits on the maintainer's answer. ACs stay open until the maintainer confirms the rows.

Maintainer, 2026-11-09, relayed by the coordinator: "#418 as advised". The advice taken: KG_CLOCK and KG_TODAY are contracts (group Clock), since instance/README.md and docs/guide.md advise both in a pipeline. Final: 75 rows, 63 contracts, 12 not (KG_PORT_APP, KG_PUBLIC_PORT; six store tuning knobs; KG_PAGE_MAX_RESPONSE, KG_PAGE_MAX_RUNS, KG_MCP_MAX_RESPONSE; KG_ALLOW_UNCONTAINED_EXECUTION). CHANGELOG counts and the test's clock assertions updated; the test also holds 63 of 75. tools/complexity.py --check holds (1689, 188); stdlib suite 889/939, 50 skipped (pins), 0 failed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
instance/README.md's settings section is one table: a row for each of the 75 KG_* settings instance/README.md or docs/security.md names, with its group, what it does, its default and whether it is a contract. 63 are, the settings an instance's CI, compose file or hook sets in order to run (decision-0027's twenty, and the clock the guides advise in a pipeline); 12 are not: two demo ports, nine tuning knobs and the uncontained escape. The section's paragraph, the contracts table's KG_* row and the note under decision-0016's quote say a setting is a contract when the table marks it so (decision-0016 point 3 as amended by decision-0033 choice 1); docs/security.md's worker paragraph points at the table. tests/test_settings_table.py holds the table to both files both ways (an unrowed setting, an invented row, a row no code reads) and the maintainer's 63 of 75. CHANGELOG: Unreleased, Contract changes. The maintainer confirmed the rows ("#418 as advised", 2026-11-09). Checks: complexity --check holds; stdlib suite 889/939, 50 skipped for missing pins, 0 failed. Risk: a row marked wrongly is frozen until 2.0 (decision-0033's SWOT); a new KG_* setting named in either file now needs a row and a decision.
<!-- SECTION:FINAL_SUMMARY:END -->
