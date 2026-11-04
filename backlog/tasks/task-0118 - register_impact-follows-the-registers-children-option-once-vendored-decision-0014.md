---
id: TASK-0118
title: >-
  register_impact follows the register's children option once vendored (decision
  0014)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-04T15:07:00Z'
updated_date: '2026-11-04T17:03:00Z'
labels:
  - mcp
  - register
milestone: m-8
dependencies: []
priority: low
type: feature
ordinal: 118000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From the 'Connecting agents to knowgov MCP' findings, task C. Depends on task-0111 (register_impact, queued in #188) and on ieam-register approving decision 0014 (PR #23) and tagging it. Then vendor that tag and wire children into register_impact and, if the maintainer wants it, the page's impact panel. tests/test_register_view.py's CAP-0001 expectation changes only if the page adopts the option.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The register is vendored at the tag carrying 0014 and 0015; the record and the comparator are unchanged
- [x] #2 register_impact with children=true on CAP-0001 reaches PRD-0002, PROC-0001, JRN-0001 and the 36 codegen keys; default unchanged
- [x] #3 A CHANGELOG line under Unreleased
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Vendor ieam-register v0.2.8 (f8fb17e) with tools/vendor_register.py; bump the tag pins in tests and demo.yml.
2. Deterministic rdflib run as of 2026-10-30 and the comparator: must stay equal.
3. register_impact.walk(children=False): with children, impact.walk_children; every descendant listed with parent, state, walked, withdrawn; landed_rows also lands on walked descendants. MCP input children (boolean, default false).
4. Page panel: not adopted here (its saved Cypher, guide and Cypher-equals-walk test would all need the descent); proposed to the coordinator.
5. Tests on both subjects, check_mcp_server children check, CHANGELOG line.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Vendored v0.2.8: only tools/impact.py, tools/check_register.py and decisions 0014, 0015 changed; the register's data is the same. rdflib deterministic run against the record: 0 differing leaves over 7 scenarios.
With children on CAP-0001: dependants reaches PRD-0002, PROC-0001, JRN-0001 and lands 31 of the 36 codegen keys (the four response|* keys rest on APP-0002/JRN-0003/JRN-0004/ENT-0003; QuoteAPI|on_notification_failure on CAP-0005, proposed, so withdrawn and not walked). realisers lands all 36, equal to TASKS['codegen'].keys. Without children nothing lands, as before.
The register's walk_children leaves the start out of what is reached; its plain walk counts the start when a cycle leads back to it (13 nodes on dependants). Shown as the register does.
check_mcp_server: S6 (CargoQuote) and C (J-F) exit 0 with the new children check (CAP-0001 31 keys; ENT-0006 154 keys).
Both test runs 339/339.

AC #2 holds across the two walks: dependants with children reaches the three nodes (31 keys), realisers with children lands the 36 codegen keys; tests/test_mcp_server.py holds both and the default unchanged.
<!-- SECTION:NOTES:END -->
