---
id: TASK-0279
title: >-
  A register named explicitly that cannot be read exits 2 (decision-0033 choice
  5)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-09T10:10:00Z'
updated_date: '2026-11-09T13:52:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0033
  - task-0256
priority: high
ordinal: 272000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
`check_subject --register DIR` with a DIR that does not exist, or a bad `KG_REGISTER`, gives one "unchecked" note and exits 0, as documented. A typo silently drops the register check.

Under decision-0033 (accepted 2026-11-09, "all as advised") choice 5(a), a register that is named (by a flag or by `KG_REGISTER`) and cannot be read exits 2, naming it. "Unchecked" stays for the case where no register is named.

Source: validation-pass group 1 C8, task-0256.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `check_subject` exits 2 naming the path when a named register cannot be read, and keeps the unchecked note when none is named. The documentation says so.
- [x] #2 The task lists every other reader that takes a register (`register_nodes`, `upward`, `proposal_impact`, `gate_cli --register-previous`, the MCP reader), and each follows the same rule, or the task records why not.
- [x] #3 The record does not move.
- [x] #4 `CHANGELOG.md`'s Unreleased section names the change under Contract changes.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/register_impact.py: unreadable(root, tools), named(), require(root, by, tools), require_named(); RegisterUnreadable, an ImpactError.
2. check_subject: --register or KG_REGISTER unreadable exits 2 naming it; none named keeps the unchecked note.
3. The other readers: register_nodes, upward, proposal_impact (and --register-branch), gate_cli (KG_REGISTER, --register-previous) exit 2 before a store opens; the MCP reader refuses to start. New branches in helpers, so the complexity ratchet holds.
4. Docs: instance/README.md, subjects/README.md, check_subject's docstring and --register help. tests/test_named_register.py. CHANGELOG Unreleased › Contract changes.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
register_impact.unreadable(root, tools) treats a register as readable when it is a directory whose metamodel/types.toml names its taxonomies and, when tools is set, holds tools/register.py (the register's loader, which the walks load). require names who named the register and the path; require_named applies only when KG_REGISTER is set. RegisterUnreadable is an ImpactError.
The readers (AC #2):
- check_subject: --register DIR or KG_REGISTER unreadable exits 2 naming it (tools not required; it reads only the metamodel and the nodes). With neither, demo/register is read, and the rows are unchecked only when it cannot be read, as before.
- register_nodes, upward and proposal_impact: an unreadable register, named or default, exits 2 naming it. Before, each crashed with exit 1. proposal_impact's --register-branch DIR is checked the same way.
- gate_cli: a KG_REGISTER that cannot be read is a CannotRun, exit 2, before the store opens. Before, the report carried register null and exited 0. --register-previous DIR is checked before the load, unless --no-load refuses the flag first.
- The MCP reader refuses to start, exit 2, on a KG_REGISTER it cannot read. Before, it started and answered per call.
- Not changed: check_instance reads its instance's own register/ by layout, which is not a register named by a flag or KG_REGISTER, so its absence keeps the layout check's own handling. The page, trace, capture and run read KG_REGISTER through cadence.register_root: not named in the task's list, and left for the re-probe.
Docs: instance/README.md (after the check_subject command), subjects/README.md 'Checking a subject', check_subject's docstring and --register help. The new branches sit in helpers (gate_cli._require_registers, proposal_impact._require_registers), so no function's complexity rises.
tests/test_named_register.py holds the readability rule, check_subject both ways, every reader's exit 2 naming the path, no store opened, and a readable named register read.
Checks at 4bb2a59, on main ada71ce: run_tests 1002/1003 (1 skipped) on the pins and 943/1003 (60 skipped) bare. Comparators: CargoQuote 0 differing leaves over 7 scenarios, J-F 0 over 6. check_round_trip --chain rdflib,rdflib on CargoQuote, and on J-F C,D3 with --expect-parts: every answer survives. check_mcp_server (rdflib) on CargoQuote S1,S2,S6 and J-F C,D3: every check holds. check_review_walkthrough, check_one_clock, check_subject on both subjects: OK. tools/complexity.py --check holds (1752 functions, 181 in the baseline).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
A register that is named, by a flag or by KG_REGISTER, and cannot be read now exits 2, naming who named it, the path and what is missing, before any store opens. That covers check_subject, register_nodes, upward, proposal_impact (and its --register-branch), and gate_cli (KG_REGISTER and --register-previous); the MCP reader refuses to start. Before, check_subject gave an unchecked note and exit 0, register_nodes, upward and proposal_impact crashed with exit 1, gate_cli reported register null with exit 0, and the MCP reader started anyway. 'Unchecked' stays for check_subject when no register is named and the default cannot be read. check_instance's own register/ and the page, trace, capture and run are recorded as not changed, with the reason. The docs say so. The record did not move: both comparators show 0 differences, and the round trips and check_mcp_server hold. CHANGELOG: Unreleased › Contract changes.
<!-- SECTION:FINAL_SUMMARY:END -->
