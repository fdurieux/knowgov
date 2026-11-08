---
id: TASK-0218
title: >-
  The reverse-engineering process for adopters: a guide under docs/ and the
  pre-registration template (decision-0018 points 1 and 2)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-08T11:18:00Z'
updated_date: '2026-11-08T14:49:00Z'
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
- [x] #1 docs/reverse-engineering.md walks the eight steps in the adopter register, each with its tool, its record and where the record lives
- [x] #2 A pre-registration template carries every field step 1 names, with J-F's first run as the worked example
- [x] #3 tests/test_docs_flags.py (or knowgov's equivalent) holds every flag the guide names to a real option
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. docs/reverse-engineering.md, adopter register: the words; the eight steps at a glance (tool, record, where it lives); the roles and the bars before measurement; each step with its commands and a plain-English walkthrough; what is not built yet, each with its task.
2. docs/reverse-engineering-preregistration.md: the template's fields (every one step 1 names, plus the question, the oracle, the iteration and budget ceiling, what is never done and what may be published, the record's place, the freeze), each with J-F's first run as the worked example from the vendored PREREGISTRATION.md (no model names), and a skeleton to copy.
3. tests/test_docs_flags.py: every --flag either file names is an option of a script the line or the file names (AST over add_argument, no import), every named script exists, foreign flags listed with their owner; tests/test_preregistration_template.py: the skeleton's fields equal the worked example's and the guide links the template.
4. Point docs/guide.md and CLAUDE.md at the guide; a CHANGELOG line under Unreleased, Changes.
5. python tests/run_tests.py; PR; merge on green; refresh the two pages.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
docs/reverse-engineering.md: the words; the eight steps at a glance (tool, record, place in the instance); the roles kept apart and the bars fixed first; each step with its commands and a plain-English walkthrough; section 5 what is not built yet (steps 1 and 2 no tool, no runner, task-0217's three checks, the code-level lists without format, key alignment manual, step 7's oracle per code base, MCP reads results and runs no step, one run behind it). The run's record: <instance>/reverse-engineering/<run>/, a convention nothing checks; the kit and gathered artefacts under artefacts/<kind>/, reviews under captures/reviews/, step 7's scores under record/<subject>/.
docs/reverse-engineering-preregistration.md: fifteen fields (step 1's seven plus the question, the existing artefacts, the kit, the oracle, the iteration and budget, what is never done and what may be published, the record's place, the freeze), each with what to write and J-F's first run from the vendored PREREGISTRATION.md; no model named; a skeleton to copy.
tests/test_docs_flags.py: a flag after a script on a command is that script's option, any other flag an option of a script the page names, every named script exists, FOREIGN (--features, pumllint trace) still mentioned; options read by AST from add_argument calls, no import. Mutation-checked: a renamed flag, a flag on the wrong script and a misspelt script each fail. Scoped to the two pages: on docs/guide.md and instance/README.md it reports false positives (a cd harness && python run.py form; ieam-register's tools/reconcile.py), so widening it is separate work.
tests/test_preregistration_template.py: fields numbered in order, step 1's seven present, each with What to write and J-F, the skeleton equal to the fields.
docs/guide.md links the guide; CLAUDE.md layout line; CHANGELOG Unreleased, Changes. python tests/run_tests.py: 758/797 passed, 39 skipped, 0 failed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The reverse-engineering process for adopters (decision-0018 points 1 and 2). docs/reverse-engineering.md walks the eight steps in the adopter register, each with the tool that runs it today, the record it leaves and where that lives in the instance, the roles kept apart and the bars fixed before measurement, and lists what is not built yet with its task. docs/reverse-engineering-preregistration.md is step 1's template: fifteen fields, every one step 1 names among them, each with J-F's first run as the worked example, and a skeleton to copy. tests/test_docs_flags.py holds every flag the two pages name to a real option of the script it is passed to, read from the scripts' source; tests/test_preregistration_template.py holds the template's fields. Documentation and tests only: no command, report, schema or record changes. Unblocks task-0219 (H7's probe, pre-registered with this template) and, with 0214 to 0217, task-0220.
<!-- SECTION:FINAL_SUMMARY:END -->
