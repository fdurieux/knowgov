---
id: TASK-0295
title: >-
  Scenario ids match [A-Za-z0-9][A-Za-z0-9_-]{0,31} and are unique within a
  subject, refused by check_subject and the Subject loader (decision-0034 choice
  2)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-09T16:51:00Z'
updated_date: '2026-11-09T17:22:00Z'
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
ordinal: 288000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Under decision-0034 (accepted 2026-11-09, "N7, D1, D3 as advised") choice 2(a). Found by the spot check (CS-3) at 9861953.

- Duplicate ids pass `check_subject`, and `Subject` keeps the last one silently.
- `id = ""` and `id = "../x"` pass, and the runtime gates them: `gate_cli` reports `"scenario": "../x"`.
- `run.py` writes `out_root / sc` (`harness/run.py` `_run_all`), so `../x` leaves `--out`.

Every public scenario id matches (S0 to S7, C, D1 to D5). `[[scenario.sources]]` ids and `stage2.derived` ids are not scenario ids and are unchanged. task-0265's duplicate-scenario-id item moves here.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A scenario id outside `[A-Za-z0-9][A-Za-z0-9_-]{0,31}`, a duplicate id within a subject, and a scenario with no id are each an error in `check_subject` (exit 1) and in the MCP `subject_check`, naming the id and the rule.
- [x] #2 The `Subject` loader refuses the same manifests, so `gate_cli`, `run.py`, the page and the MCP servers exit 2 or refuse naming the id, before anything is written.
- [x] #3 The public subjects, the example instance and the record are unchanged.
- [x] #4 Each form in the description is a test.
- [x] #5 `CHANGELOG.md`'s Unreleased section names the rule under Contract changes.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/scenario_ids.py: PATTERN [A-Za-z0-9][A-Za-z0-9_-]{0,31}; problems (code scenario-id: no id, outside the pattern, a duplicate) and check (ScenarioIdError, a ValueError, naming the file and the id).
2. harness/subject.py's loader runs check before it builds the scenarios, so every command refuses: gate_cli and run.py through their exits (ScenarioIdError in cli_exit's OWN), the MCP reader at start (import subject in its start-up try), the page through cli_exit.guard when run as a script.
3. tools/check_subject.py _scenario_ids reports each breach; the subject-check schema gains scenario-id; tests/test_subject_check_rules.py reads scenario_ids.py's codes.
4. tests/test_scenario_ids.py; subjects/README.md; CHANGELOG Unreleased › Contract changes.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
harness/scenario_ids.py holds the rule: an id of [A-Za-z0-9][A-Za-z0-9_-]{0,31} (ASCII), one per scenario, every scenario carrying one. problems lists each breach in file order as {code: scenario-id, id, where, message, hint}; check raises ScenarioIdError on the first, naming scenarios.toml's path and the id.
Subject.__init__ runs check before it builds self.scenarios, so the last of two duplicates is never silently kept, and every reader refuses before it writes anything:
- gate_cli exits 2 ('the subject does not load: ... scenario id '../x' is not ...');
- run.py exits 2 and writes nothing inside or beside --out, so out_root / sc can no longer leave it;
- the MCP reader exits 2 at start: it now imports subject in its start-up try, where before the error read as an as_of failure;
- the page exits 2 with its cause in one line, through cli_exit.guard('kg demo') when run as a script, where before it gave a traceback and exit 1.
knowgov-runs (mcp_runs) loads no subject; its runs go to the page, which refuses at start.
check_subject._scenario_ids reports every breach (exit 1, rule scenario-id, where 'scenarios.toml [[scenario]] #n'), and so does the MCP subject_check. The subject-check schema's finding.rule gains scenario-id, and tests/test_subject_check_rules.py now reads codes from harness/scenario_ids.py beside task_policy.py.
[[scenario.sources]] ids and a stage-2 derived id are not read; a test holds that. Every public scenario id matches (S0 to S7, C, D1 to D5), and check_subject finds none on the public subjects.
tests/test_scenario_ids.py covers each form (duplicate, '', '../x', no id, a space, a leading '-', 33 characters, a number) on the rule, the checker, the MCP subject_check, gate_cli, the MCP reader and the page, and run.py writing nothing (pins).
Checks at a72dd82 on main 34076aa: deterministic comparators CargoQuote 0 differing leaves over 7 scenarios, J-F 0 over 6; check_round_trip --chain rdflib,rdflib on CargoQuote, and on J-F C,D3 with --expect-parts, every answer survives; check_mcp_server (rdflib) on CargoQuote S1,S2,S6 and J-F C,D3, every check holds; check_review_walkthrough, check_one_clock and check_subject on both subjects, OK. The suites' one failure there was tests/test_subject.py's guard on the hint's examples (a public scenario id in harness/), fixed in cc03efd. tools/complexity.py --check holds.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
A scenario id is now [A-Za-z0-9][A-Za-z0-9_-]{0,31}, one per scenario, as decision-0034 choice 2(a) chose. harness/scenario_ids.py holds the rule. check_subject and the MCP subject_check report a scenario with no id, a duplicate id or one outside the pattern (exit 1, rule scenario-id, which the subject-check schema adds). The Subject loader refuses the same, so gate_cli, run.py, the MCP reader and the page exit 2 naming the id before they write anything. run.py's ../x no longer leaves --out, and the last of two duplicates is no longer kept silently. Sources and stage-2 derived ids are unchanged. The public ids all match and the record did not move: both comparators show 0 differences, and the round trips and check_mcp_server hold. CHANGELOG: Unreleased › Contract changes.
<!-- SECTION:FINAL_SUMMARY:END -->
