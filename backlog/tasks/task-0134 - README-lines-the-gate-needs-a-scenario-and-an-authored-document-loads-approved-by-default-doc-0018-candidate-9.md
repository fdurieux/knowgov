---
id: TASK-0134
title: >-
  README lines: the gate needs a scenario, and an authored document loads
  approved by default (doc-0018 candidate 9)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T22:40:00Z'
updated_date: '2026-11-04T23:15:00Z'
labels:
  - docs
  - subject
milestone: m-8
dependencies: []
priority: medium
type: docs
ordinal: 134000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0018 §6 candidate 9, on the maintainer's go of 2026-11-04. Two facts an adopter meets today, documented now while their fixes come: (1) the gate needs at least one scenario: `subjects/README.md` lists `scenarios.toml` as not required, yet `gate_cli.py` exits 2 on a subject with none (doc-0018 F3); an instance subject declares at least the pristine scenario `subjects/minimal/` declares (`S0`). (2) Until the F1 decision (decision-0009, proposed) lands, a document a mapper reads as `authored` loads verified and approved by the subject's default human agent, `agent:maintainer`, whether or not the manifest declares `[verification]` (doc-0018 F1): an adopter who drafts a requirements file with an assistant gets it read as approved. Adopter register in `instance/README.md`, maintainer register in `subjects/README.md`; flags named are real flags (`tests/test_docs_flags.py` style guards where they exist).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 subjects/README.md says the gate needs at least one scenario and shows the minimal S0 pattern
- [x] #2 instance/README.md says, in plain words, what an authored document reads as today and that declaring [verification] and [provenance] names who attests; it points to decision-0009 as proposed
- [x] #3 Both suites pass; no code changes
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. subjects/README.md: scenarios.toml's required column and a scenarios.toml paragraph with the pristine S0 pattern minimal follows. 2. instance/README.md: a 'Who vouches for a document' section, adopter register, before 'Capturing what people know': what an authored document reads as today, the [provenance]/[verification] declaration, decision-0009. 3. Both suites.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
AC #2 asked for decision-0009 'as proposed'; the maintainer accepted (a) at 23:04 before this landed, so the section names it accepted with task-0136 as its build, and still says what an authored document reads as today. Snippet dates are strings, as the public manifests write them; the attester's id an issued handle (agent:employee-2). task-0135 rewrites the subjects/README.md 'does not catch it yet' clause once its check lands, and task-0136 rewrites the section to the rule.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
subjects/README.md: scenarios.toml is required for the gate (gate_cli.py exits 2 on a subject with a task and none, doc-0018 F3), with the pristine S0 pattern before CargoQuote's S6. instance/README.md: 'Who vouches for a document', in plain words: an authored document loads reviewed and approved by the subject's human agent whether or not anyone read it (agent:maintainer and record 'approval' by default, doc-0018 F1); declare [provenance] human (an issued handle) and [verification] authored and approval in a reviewed pull request; decision-0009, accepted, makes the declaration required (task-0136). Docs only. python tests/run_tests.py 406/406, and 406/406 with KG_SUBJECT=subjects/jef_data_load.
<!-- SECTION:FINAL_SUMMARY:END -->
