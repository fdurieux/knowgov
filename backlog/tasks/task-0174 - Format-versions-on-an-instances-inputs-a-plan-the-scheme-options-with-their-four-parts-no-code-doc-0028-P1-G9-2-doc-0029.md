---
id: TASK-0174
title: >-
  Format versions on an instance's inputs: a plan, the scheme options with their
  four parts, no code (doc-0028 P1, G9-2; doc-0029)
status: To Do
assignee: []
created_date: '2026-11-06T13:03:00Z'
labels:
  - contracts
  - instance
dependencies: []
priority: medium
ordinal: 175000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0028 §9 P1, minted by doc-0029 advice 4 as a plan only. subject.toml, register_map.toml, code_map.toml, connectors.toml, the captures and the review files carry no format version today, so a change to any of them cannot be told from an old file. Plan, in this task's implementation plan: the files in scope (from instance/kinds.toml and instance/README.md), two or three schemes (e.g. a format = N key per file; one instance-level version; a schema URI), each with an opportunity canvas, a fit/gap (decision-0003 contracts, decision-0016 point 3, check_instance.py, the loaders, backward reading of a file without a version as current until 1.0), a SWOT and the drafter's advice. No code until the maintainer has read the plan: the scheme is a contract choice.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The implementation plan names every input file in scope with its reader (module and function)
- [ ] #2 Two or three schemes, each with an opportunity canvas, a fit/gap, a SWOT and advice; a recommendation
- [ ] #3 No code change; the task stays To Do with the plan, for the maintainer
<!-- AC:END -->
