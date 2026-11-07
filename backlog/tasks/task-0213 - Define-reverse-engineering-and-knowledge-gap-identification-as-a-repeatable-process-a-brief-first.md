---
id: TASK-0213
title: >-
  Define reverse engineering and knowledge-gap identification as a repeatable
  process (a brief first)
status: To Do
assignee: []
created_date: '2026-11-07T09:25:00Z'
labels:
  - process
  - reverse-engineering
  - gaps
dependencies: []
priority: medium
type: task
ordinal: 213000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer, 2026-11-07: "I want the reverse engineering experiment to be repeatable, as I want to define it as a process. The identification of knowledge gaps/issues is part of this, by running the linter tools on the different reverse-engineered & already available artefacts; quirks in code, missing documentation, etc. will then be identified as knowledge gaps, to be addressed." The experiment so far is a one-off record in pumllint (recreate_experiment/, docs/recreate-experiment.md): the kit and its manifest and precedence rule, the observed/inferred/intended split (method 1.2 and 1.3, pumllint #187), the unrealised-code register (#188), the Dominique lint-attribute-route-resolve-re-lint loop (#193), the degradation test (#207, #208), the OpenWiki comparison (H7, its drift check, not run). knowgov already has the linters per kind (tools/preload_check.py), gaps from a load, owners and routes from the register (questionnaires, reviews), the J-F kit as subject jef_data_load, and decision-0011 (proposed), one application of the method to knowgov's own gate lane. Nothing chains these into a process that can be run again on a new code base or a new commit. A brief with the four parts comes before any build; the process steps it proposes, and where each step's record lives (knowgov or pumllint), are the maintainer's to decide.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A backlog doc defines the process step by step (scope at a named commit; reverse-engineer into a kit with each statement observed, inferred or intended; gather the existing artefacts; lint both; load as a subject so lint findings, code quirks and missing documentation become gaps routed to owners; address; re-run on change), each step mapped to the tool or record that exists and the gaps named
- [ ] #2 The doc carries the four parts (opportunity canvas, fit/gap, SWOT, advice) and states how decision-0011 relates to it and where H7's drift question fits
- [ ] #3 The maintainer's decision on the process is recorded before any task builds a step of it
<!-- AC:END -->
