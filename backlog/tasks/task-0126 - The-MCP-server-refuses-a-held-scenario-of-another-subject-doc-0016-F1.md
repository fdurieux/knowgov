---
id: TASK-0126
title: The MCP server refuses a held scenario of another subject (doc-0016 F1)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T20:09:00Z'
updated_date: '2026-11-04T20:51:00Z'
labels:
  - mcp
  - bug
milestone: m-8
dependencies: []
priority: high
type: bug
ordinal: 126000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0016 §2 F1. One store serves every subject; `harness/mcp_server.py` `_check_scenario` compares the held scenario (`_held`, the first `act:extract:<sc>:<v>`) with the caller's expectation only, never with `SUBJECT.scenarios`. Probed on rdflib: a CargoQuote server with J-F `C` loaded reports `store_status.scenario: C`, and `gate_verdict {}` returns a well-formed BLOCKED that is CargoQuote's codegen keys read against J-F's graph; `evidence_bundle {}` fails with a KeyError. Fix: `_held` yields the scenario only when it is the server's subject's; otherwise `store_status` names it as held by another subject (`held_by_other_subject`) and every scenario-reading tool refuses with a message naming the held scenario and the server's subject. Read-only stays; the tool list and the record are unchanged.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 store_status on a store holding another subject's scenario reports scenario null and names the foreign scenario in held_by_other_subject
- [x] #2 gate_verdict, three_valued_answer, evidence_bundle and register_impact (where it reads a scenario) refuse with isError on such a store, with or without a scenario argument, naming the held scenario and the server's subject
- [x] #3 A test on a stub store holding J-F's C under the CargoQuote subject covers both, and the existing MCP tests and tools/check_mcp_server.py pass unchanged on a store of the server's own subject
- [x] #4 CHANGELOG line under Unreleased; instance/README.md's tool table says what a foreign held scenario reads as
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Split the held read: _held_any (the raw act:extract:<sc> read), _held (only when the scenario is in SUBJECT.scenarios), _foreign (when it is not).
2. store_status: scenario from _held, held_by_other_subject from _foreign; tool description says so.
3. _check_scenario refuses a foreign scenario first, naming it, the server's subject and its scenarios; every scenario-reading tool goes through it, with or without a scenario argument. register_impact keeps its register-only answer when nothing at all is held (_held_any None).
4. Tests: the stub holds the running subject's first scenario (both suites test the server on its own subject); a new test holds J-F's C under CargoQuote (S1 under J-F) across store_status and the four tools.
5. CHANGELOG under Unreleased contract changes; instance/README.md store_status row.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
harness/mcp_server.py: _held_any, _held, _foreign; _check_scenario refuses a foreign scenario before the expectation check, so the refusal is the same with no argument, the foreign scenario or one of the server's own. register_impact's register-only path keys on _held_any, so a foreign store refuses there too. The MCP test stub held CargoQuote's S1 under the J-F suite as well; it now holds the running subject's first scenario (FIRST sentinel), three S1 asserts follow it, and the README's CargoQuote curl example takes the subject's scenario under J-F.
Evidence: both suites 380/380 after merging main; deterministic rdflib run with the comparator, 0 differing leaves over S1-S7; tools/check_mcp_server.py on rdflib, CargoQuote S1,S2,S6 and J-F C,D3, every check holds; live probe (J-F C in an rdflib file, CargoQuote server): store_status scenario null, held_by_other_subject C, gate_verdict, evidence_bundle, three_valued_answer and register_impact refused. PR #210 tests, rdflib, stack green before the main merge.
Limit: the activity id carries no subject, so a scenario id two subjects share would still read as the server's own.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The MCP server reads only its own subject's scenarios (doc-0016 F1). One store serves every subject; a CargoQuote server over J-F's C used to report scenario C and answer gate_verdict on J-F's graph. Now store_status reports scenario null with the foreign one in held_by_other_subject, and gate_verdict, three_valued_answer, evidence_bundle and register_impact (where it reads a scenario) refuse with isError naming the held scenario and the server's subject, with or without a scenario argument. No new tool; read-only; record and comparator unchanged. Tests on a stub holding the other subject's scenario; CHANGELOG under Unreleased contract changes; instance/README.md tool table. Verified by both suites, the comparator, check_mcp_server.py on both subjects and a live rdflib probe. Risk: a scenario id shared by two subjects is indistinguishable, since the extraction activity carries no subject.
<!-- SECTION:FINAL_SUMMARY:END -->
