---
id: TASK-0218
title: >-
  The reverse-engineering process for adopters: a guide under docs/ and the
  pre-registration template (decision-0018 points 1 and 2)
status: To Do
assignee: []
created_date: '2026-11-08T11:18:00Z'
labels:
  - process
  - reverse-engineering
  - docs
dependencies: []
references:
  - >-
    backlog/decisions/decision-0018 -
    Reverse-engineering-and-knowledge-gap-identification-is-an-eight-step-process-knowgov-routes-and-re-finds-its-gaps-and-its-three-contract-changes-land-in-0.9.0.md
documentation:
  - >-
    backlog/docs/doc-0032 -
    Reverse-engineering-and-knowledge-gap-identification-as-a-repeatable-process-eight-steps-with-their-tools-and-gaps-the-bases-decision-0011-H7-and-what-F2-must-bind.-Opportunity-canvas-fit-gap-SWOT-advice.md
priority: medium
type: task
ordinal: 218000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0018 points 1 and 2. The process definition lives in knowgov: doc-0032 is the maintainer's brief; adopters need a guide in the adopter register (CLAUDE.md, Registers: name a concept before using it, say what a command does and what the reader gets back, a plain-English walkthrough beside any command sequence). The guide walks the eight steps with the tools each runs today, the records each leaves and where they live (each run's record with its instance), the roles kept apart (extraction may read everything; recreation gets the frozen package only, method 1.3), and the bars fixed before measurement (method 1.2: no percentage of all tacit knowledge). Step 1's pre-registration template: the code base and its commit, the lane's file set, the roles, the clean-room parameter (J-F used a full clean room; decision-0011 A1 none for the author), the bars, the bounded inventories, the bundle's contents.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 docs/reverse-engineering.md walks the eight steps in the adopter register, each with its tool, its record and where the record lives
- [ ] #2 A pre-registration template carries every field step 1 names, with J-F's first run as the worked example
- [ ] #3 tests/test_docs_flags.py (or knowgov's equivalent) holds every flag the guide names to a real option
<!-- AC:END -->
