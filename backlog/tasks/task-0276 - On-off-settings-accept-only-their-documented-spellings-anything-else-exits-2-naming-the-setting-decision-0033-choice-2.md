---
id: TASK-0276
title: >-
  On/off settings accept only their documented spellings; anything else exits 2
  naming the setting (decision-0033 choice 2)
status: In Progress
assignee: []
created_date: '2026-11-09T10:09:00Z'
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
ordinal: 269000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
`KG_NO_LOAD` and `KG_PUBLISH` act only on exactly `1`, so `true`, `yes` and `on` silently mean off. In `action.yml`, `annotate` and `sarif` are compared case-sensitively in sh, while `publish` is compared in a GitHub expression, which ignores case.

Under decision-0033 (accepted 2026-11-09, "all as advised") choice 2(a): `1` means on; `0`, empty or unset means off; anything else exits 2 naming the setting and the accepted values. A setting whose documentation uses a word (for example `KG_LOAD_MEMORY_CHECK=off`, `KG_KEY_CHECK=off`) keeps that spelling and refuses others. The action's and the GitLab include's boolean inputs take `true` or `false` in any case, and anything else fails.

Source: validation-pass group 1 C4, task-0256.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The task lists every on/off `KG_*` setting with its documented spellings, and one parser reads them all. A value outside a setting's spellings exits 2 naming the setting and the spellings accepted.
- [x] #2 `action.yml`'s and the GitLab include's boolean inputs compare without case. A value other than true or false fails the step, naming the input.
- [x] #3 Every spelling documented today keeps its meaning, and the record does not move.
- [ ] #4 `check_ci_wrappers`, `harness.yml`'s instance/ci steps and `tests/run_tests.py` pass.
- [x] #5 `CHANGELOG.md`'s Unreleased section names the change under Contract changes.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/switches.py: SWITCHES lists every on/off KG_* setting with its spellings; parse/on read them; BadSwitch names the setting and its spellings.
2. Route every reader through it: cli_exit (KG_TRACEBACK), load_memory, key_check, arms, execution_guard, execution, the page's start; knowgov-gate.sh's flag() for KG_NO_LOAD and KG_PUBLISH under the same rule.
3. action.yml: publish, annotate, sarif take true/false in any case, else fail naming the input; the GitLab include's flags go through knowgov-gate.sh.
4. Tests (tests/test_switches.py), docs (instance/README.md 'On and off'), CHANGELOG; the record unmoved.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Built on PR #421 (branch claude/task-0276-0277-switches-and-tags), with task-0277.
The list (harness/switches.py SWITCHES), each with its documented spellings:
- flags, 1 on and 0, empty or unset off: KG_NO_LOAD and KG_PUBLISH (instance/README.md, read by instance/ci/knowgov-gate.sh), KG_ALLOW_UNCONTAINED_EXECUTION (docs/security.md; execution_guard, execution), KG_TRACEBACK (harness/cli_exit.py), KG_THINKING_UNCOUNTED (demo/models.toml's thinking_uncounted; harness/arms.py);
- word settings, off in any case and on, empty or unset leaving the check on: KG_LOAD_MEMORY_CHECK (instance/README.md, docs/security.md; harness/load_memory.py) and KG_KEY_CHECK (demo/README.md, docs/security.md; harness/key_check.py).
Anything else raises BadSwitch, which is in cli_exit's OWN set, so the message is the one line: exit 2 under cli_exit.run. cli_exit.run reads KG_TRACEBACK before main. The page checks every switch at start and exits 2. knowgov-gate.sh's flag() is the same rule in shell.
action.yml: publish, annotate and sarif go through a shell bool(), true/false in any case, else exit 2 naming the input; the sarif upload step's inputs.sarif == 'true' is a GitHub expression, already without case. The GitLab include has no true/false input: its flags, KG_PUBLISH and KG_NO_LOAD, reach knowgov-gate.sh's flag().
Behaviour change, in the CHANGELOG line and the PR body: KG_LOAD_MEMORY_CHECK and KG_KEY_CHECK set to 0, no or false, spellings no document named, turned the check off before and now exit 2; KG_ALLOW_UNCONTAINED_EXECUTION=yes read as not opted in and now raises. Every documented spelling keeps its meaning. tests/test_load_memory.py and tests/test_execution_guard.py are updated to match.
Checks at 9c07512: run_tests 896/946, 0 failed; with the pins 939/940; check_ci_wrappers exit 0; the CargoQuote comparator on rdflib, 0 differing over 7 (the record unmoved); complexity --check holds.
AC #4's harness.yml instance/ci steps (the composite action run for real, publish: "true") run in #421's CI; checked once that is green.
<!-- SECTION:NOTES:END -->
