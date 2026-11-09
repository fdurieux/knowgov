---
id: TASK-0253
title: >-
  How knowgov's facts feed a team's prioritisation method: the inputs recipe for
  WSJF, cost of delay and RICE (squad study, doc-0034)
status: To Do
assignee: []
created_date: '2026-11-09T07:33:00Z'
labels:
  - docs
  - prioritisation
dependencies: []
priority: low
ordinal: 247000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From doc-0034 (the squad study, advice 3). knowgov supplies inputs to a prioritisation method a team already uses, and no score: time criticality (lapses before a date with --as-of; the existing products and journeys a change reaches), risk reduction and opportunity enablement (absent, declared-gap and disputed keys; required_not_reached enablers), a job-size proxy (new against reused elements, gaps, owners and handoffs per slice), dependencies (the realisers chain, node before link approval, both owners across domains). It supplies nothing on value, user reach, confidence in value or effort, and key levels are confidence in knowledge, not in value. A section in instance/README.md, in the adopter register, with the commands that produce each input on the example instance. Documentation only: a 0.9.x patch under decision-0016 point 2.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 instance/README.md gains a section naming each input, the command or MCP tool that yields it, and what knowgov does not supply, in plain English
- [ ] #2 tests/test_adopter_docs.py's flag and command checks hold the new section's commands to real options
<!-- AC:END -->
