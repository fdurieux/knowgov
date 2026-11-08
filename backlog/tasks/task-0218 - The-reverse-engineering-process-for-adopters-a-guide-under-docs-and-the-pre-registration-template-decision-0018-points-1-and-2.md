---
id: TASK-0218
title: >-
  The reverse-engineering process for adopters: a guide under docs/ and the
  pre-registration template (decision-0018 points 1 and 2)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-08T11:18:00Z'
updated_date: '2026-11-08T14:20:00Z'
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
1. docs/reverse-engineering.md, adopter register (CLAUDE.md Registers): name each concept before use (a glossary table first), then the eight steps of doc-0032 as decision-0018 points 1 and 2 fix them. Each step gives its tool as it runs today, its record and where the record lives (the run's folder, the instance). The roles stay apart (method 1.3: extraction reads everything allowed, recreation gets the frozen bundle only). The bars are fixed before measurement (method 1.2: no percentage of all tacit knowledge). The claim (task-0214), the intended bar (task-0215) and lint gaps with --previous (task-0216) are as merged; step 4's glossary and DMN gap checks are named as not yet in preload_check (task-0217).
2. docs/reverse-engineering-preregistration.md: the template's ten fields:
   - code base and commit; the lane's file set; the roles;
   - what extraction may read (the clean-room parameter: J-F's full clean room, decision-0011 A1's none for the author); what recreation receives (the bundle);
   - the bars (gates or reported); the bounded inventories; expectations; what the run never does; frozen.
   J-F's first run (pumllint recreate_experiment/PREREGISTRATION.md) is the worked example.
3. tests/test_reverse_engineering_guide.py, AC 3 (knowgov has no test_docs_flags.py):
   - every option a fenced command passes is one its program's argparse accepts (run with --help);
   - every --flag the prose names is real;
   - every repository path named exists;
   - the eight steps each name a tool, a record and a place;
   - the template's headings are the ten fields, and the example cites J-F's numbers.
4. README links both. Run both suites.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
The guide follows the merged task-0214, 0215 and 0216:
- step 4's report is written to the instance's root, where the load reads it (harness/preload.py);
- a lint finding is a lint gap with its owner and route, and moves no key's level;
- step 6 resolves one by [[resolves]] (choice, exception, open; a slip is a new version), and re-lints with preload_check --previous FIRST, whose delta sorts each finding as new, gone (a slip when the bytes changed) or kept, at the same tool versions only;
- step 8's gate re-run uses --baseline and trace.py check, not --stage 2, which replays only a subject's planted change.
The template's clean-room field names both settings: J-F's full clean room, and decision-0011 A1's none for the kit's author, with the rebuilder still on a bundle only.
AC 3: knowgov has no test_docs_flags.py, so tests/test_reverse_engineering_guide.py holds the guide's and the template's flags. Each fenced command's options are checked against its program's --help, each --flag in the prose is checked to be real, and each repository path named is checked to exist.
README links both pages.
Checks on c24a85f plus this change:
- tests/run_tests.py with the pins: 790/791, 1 skip (hook-live), 0 failed;
- bare 3.13: 746/791, 45 skips, 0 failed. The extra skip, test_r3, comes from main's #353.
- The guide's five tests pass bare and with the pins.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Adds the reverse-engineering process for adopters (decision-0018 points 1 and 2).
- docs/reverse-engineering.md walks doc-0032's eight steps in the adopter register: a glossary first, then for each step the tool as it runs today, the record it leaves and where that lives. The roles stay apart, the bars are fixed before measurement, and no percentage of tacit knowledge is given.
- docs/reverse-engineering-preregistration.md is step 1's template: ten fields, including the clean-room parameter and the bundle. J-F's first run (pumllint recreate_experiment/PREREGISTRATION.md: J-F 8f6d6b0, pumllint 5c1fa55, 157 artefacts, 158 requirements) is the worked example.
- tests/test_reverse_engineering_guide.py holds every command option, prose flag and repository path the two pages name to a real one.
- The README links both.
Checks: both suites pass (790/791 with the pins, 746/791 bare).
Follow-ups:
- step 4's glossary and DMN gap checks are named as not yet in preload_check (task-0217);
- step 8 names task-0219 as its first probe.
<!-- SECTION:FINAL_SUMMARY:END -->
