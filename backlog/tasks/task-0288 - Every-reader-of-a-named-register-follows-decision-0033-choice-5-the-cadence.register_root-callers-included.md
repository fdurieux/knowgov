---
id: TASK-0288
title: >-
  Every reader of a named register follows decision-0033 choice 5, the
  cadence.register_root callers included
status: Done
assignee:
  - '@claude'
created_date: '2026-11-09T15:37:00Z'
updated_date: '2026-11-09T16:12:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0032
  - task-0256
  - backlog/decisions/decision-0033
priority: high
ordinal: 281000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
task-0279 left the readers that go through `cadence.register_root` unchanged. Choice 5 covers every reader that takes a register. With `KG_REGISTER` set to a missing directory:
- capture ingest skips the issued-handle check (N11): `ans-handle_unknown.toml`, from `employee-99`, is refused with the good register, but here it exits 0 and writes `2026-11-09-ORG-0002-employee-99.toml`, a weaker policy;
- capture questionnaire and review exit 2, but with a raw FileNotFoundError;
- capture due exits 0;
- trace check falls back to 12 review months without saying so;
- `run.py --deterministic` exits 0;
- the page starts, and `/api/register` answers 404 with the full path in the error.

Fix-only, the same check (N10): `check_subject`'s test of a readable register differs from the others'. A directory with only `metamodel/types.toml` gives exit 1 with 187 errors where the others give 2, and one without `tools/register.py` gives 0 where the others give 2.

Source: the bounded re-probe (decision-0032 point 4, task-0256), group 1 at main 9861953 (§8, N10, N11).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A named register that cannot be read is refused with exit 2 naming it, by the one check `register_impact.require` uses, at capture ingest, questionnaire, review and due, trace check and register, and `run.py`. An unnamed register keeps today's behaviour.
- [x] #2 The page refuses at start, or answers `/api/register` with a message that does not leak the path.
- [x] #3 `check_subject` uses the same readable-register test as the other tools.
- [x] #4 Every reproduction in the description is a test. The record does not move.
- [x] #5 `CHANGELOG.md`'s Unreleased section names the change under Contract changes.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/cli_exit.py run(main, tool, register=True): register_impact.require_named() before main (RegisterUnreadable in OWN); capture, run, trace and transcript pass it; -h/--help pass the check (asks_help).
2. step_grid: register_impact.require() in its existing try. The page: register_impact.require_named() in main's existing start-up try, so it refuses to start, exit 2, and no path reaches an HTTP client.
3. check_subject (N10): register_impact.unreadable(register), the readers' one test, tools/register.py included.
4. tests/test_named_register.py: each reproduction; tests/test_execution_guard.py's run.py case mounts a readable register. Docs and CHANGELOG Unreleased › Contract changes.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
cli_exit.run(main, tool, register=True) runs register_impact.require_named() before main, unless -h or --help is among the arguments (cli_exit.asks_help, before any --). RegisterUnreadable is in OWN, so the line reads '<tool>: cannot run: KG_REGISTER <path> is not a readable register: <why>'. capture (ingest, questionnaire, review, due), run, trace (check, register) and transcript pass register=True. step_grid calls register_impact.require() inside its existing try, and the page calls require_named() in main's existing start-up try, refusing to start, exit 2, so no path reaches an HTTP client. check_subject (N10) uses register_impact.unreadable(register), tools/register.py included: a folder with only metamodel/types.toml, or a register copy without tools/, is exit 2, where before it was exit 1 with every row's node unknown, or exit 0. An unnamed register reads as before.
tests/test_named_register.py:
- test_the_readers_through_register_root_refuse_it_too: capture due, ingest, questionnaire and review; trace check and register; transcript; step_grid; the page. Each exits 2 naming KG_REGISTER and the path, and nothing is written and no store opened. The probe's ans-handle_unknown.toml is not in the repository; the ingest case shows the same thing, refused before the capture folder is written.
- test_run_refuses_it_too (pins): run.py --deterministic exits 2 and writes no --out; run.py --help prints the usage.
- test_check_subject_reads_a_register_as_the_others_do: N10's two folders.
- test_help_passes_the_check_so_the_usage_can_be_read.
tests/test_execution_guard.py's run.py case mounted /instance/register, which does not exist here; run.py now refuses that before main, so the case mounts a copy of the public register outside the checkout, and still asserts the X1 refusal.
Docs: instance/README.md lists every command and the page and says what counts as a register; subjects/README.md and check_subject's docstring name the one test. They name the register's loader without a repository path, which the docs gate holds to files.
Checks at beccc66 (code identical to the head): run_tests 1017/1018 (1 skipped) on the pins and 957/1018 (61 skipped) bare. At a61b47c, whose code differs only by the --help skip: comparators CargoQuote 0 differing leaves over 7 scenarios, J-F 0 over 6; check_round_trip --chain rdflib,rdflib on CargoQuote, and on J-F C,D3 with --expect-parts, every answer survives; check_mcp_server (rdflib) on CargoQuote S1,S2,S6 and J-F C,D3, every check holds; check_review_walkthrough, check_one_clock and check_subject on both subjects, OK. tools/complexity.py --check holds (1755 functions, 180 in the baseline).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Every command that reads a register now refuses a named one it cannot read, by the one check register_impact.require uses, as decision-0033 choice 5 asks. capture (ingest, questionnaire, review, due), run, trace (check, register) and transcript do it through cli_exit.run(register=True) and step_grid through its own call, each exiting 2 naming KG_REGISTER, the path and what is missing, before reading or writing anything. -h and --help still print the usage. The page refuses to start, so /api/register never answers with the path. Before, capture ingest skipped the issued-handle check and wrote a capture the register would refuse; capture due, trace check and run.py went on with exit 0; and the page started. check_subject uses the same test as the other readers (N10). An unnamed register reads as before. Every reproduction is a test. The record did not move: both comparators show 0 differences, and the round trips and check_mcp_server hold. CHANGELOG: Unreleased › Contract changes.
<!-- SECTION:FINAL_SUMMARY:END -->
