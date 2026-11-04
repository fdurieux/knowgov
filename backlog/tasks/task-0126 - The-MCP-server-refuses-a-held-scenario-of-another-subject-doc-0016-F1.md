---
id: TASK-0126
title: The MCP server refuses a held scenario of another subject (doc-0016 F1)
status: To Do
assignee: []
created_date: '2026-11-04T20:09:00Z'
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
- [ ] #1 store_status on a store holding another subject's scenario reports scenario null and names the foreign scenario in held_by_other_subject
- [ ] #2 gate_verdict, three_valued_answer, evidence_bundle and register_impact (where it reads a scenario) refuse with isError on such a store, with or without a scenario argument, naming the held scenario and the server's subject
- [ ] #3 A test on a stub store holding J-F's C under the CargoQuote subject covers both, and the existing MCP tests and tools/check_mcp_server.py pass unchanged on a store of the server's own subject
- [ ] #4 CHANGELOG line under Unreleased; instance/README.md's tool table says what a foreign held scenario reads as
<!-- AC:END -->
