---
id: TASK-0217
title: >-
  Step 4's checks in preload_check: pumllint trace --features, the glossary
  check, the DMN gap check (decision-0018 point 1)
status: To Do
assignee: []
created_date: '2026-11-08T11:18:00Z'
labels:
  - process
  - reverse-engineering
  - preload
dependencies:
  - TASK-0216
references:
  - >-
    backlog/decisions/decision-0018 -
    Reverse-engineering-and-knowledge-gap-identification-is-an-eight-step-process-knowgov-routes-and-re-finds-its-gaps-and-its-three-contract-changes-land-in-0.9.0.md
documentation:
  - >-
    backlog/docs/doc-0032 -
    Reverse-engineering-and-knowledge-gap-identification-as-a-repeatable-process-eight-steps-with-their-tools-and-gaps-the-bases-decision-0011-H7-and-what-F2-must-bind.-Opportunity-canvas-fit-gap-SWOT-advice.md
priority: medium
type: feature
ordinal: 217000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0018 point 1, step 4 (doc-0032 §2 step 4 and §10 item 3). pumllint's trace --features, the lab's glossary check and its DMN gap check (gaps, overlaps, untyped outputs; pumllint recreate_experiment/harness/glossary_check.py and dmn_check.py) find what the experiment found, but they do not run in tools/preload_check.py. Port or call them so the lint step runs them on a kit and the gathered artefacts, under the gate contract's exit codes, their findings feeding task-0216's routed gaps. Provisional on F6 (task-0200, the uniform exit wrapper): use today's exit handling and say what F6 will change. pumllint is a released library knowgov installs; nothing is copied from pumllint's lab without its licence and a SOURCE note, and pumllint imports nothing from here.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 preload_check runs the three checks on an instance's documents of the kinds they read, each finding in the preload report with its tool
- [ ] #2 A kind whose check cannot run here is listed as unchecked, as today
- [ ] #3 tools/check_preload_linters.py proves each check finds its planted defect
- [ ] #4 The scored record (S1 to S7), the deterministic run and the comparator stay equal
<!-- AC:END -->
