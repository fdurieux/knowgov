---
id: TASK-0118
title: >-
  register_impact follows the register's children option once vendored (decision
  0014)
status: To Do
assignee: []
created_date: '2026-11-04T15:07:00Z'
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
- [ ] #1 The register is vendored at the tag carrying 0014 and 0015; the record and the comparator are unchanged
- [ ] #2 register_impact with children=true on CAP-0001 reaches PRD-0002, PROC-0001, JRN-0001 and the 36 codegen keys; default unchanged
- [ ] #3 A CHANGELOG line under Unreleased
<!-- AC:END -->
