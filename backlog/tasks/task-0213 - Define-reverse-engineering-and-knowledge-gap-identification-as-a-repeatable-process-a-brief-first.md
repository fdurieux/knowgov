---
id: TASK-0213
title: >-
  Define reverse engineering and knowledge-gap identification as a repeatable
  process (a brief first)
status: To Do
assignee: []
created_date: '2026-11-07T09:25:00Z'
updated_date: '2026-11-07T23:59:00Z'
labels:
  - process
  - reverse-engineering
  - gaps
dependencies: []
documentation:
  - >-
    backlog/docs/doc-0032 -
    Reverse-engineering-and-knowledge-gap-identification-as-a-repeatable-process-eight-steps-with-their-tools-and-gaps-the-bases-decision-0011-H7-and-what-F2-must-bind.-Opportunity-canvas-fit-gap-SWOT-advice.md
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-07, sequencing: the brief drafted now, as a document only (doc-0032). The coordinating session decided it under the maintainer's delegation of 23:51 UTC ("opportunity, swot, fit/gap => decide"), and the testing-class session drafted it on that dispatch. The four parts:
- Canvas: the decision gets lead time while the tranche runs, and F2 (task-0199) is shaped by what the process needs from it (doc-0032 §6) before it is dispatched.
- Fit/gap: no code overlap with the tranche, since the brief changes nothing in harness/, tools/ or subjects/. The risk of going stale is mitigated by marking every step that depends on F2, F4, F5, F6 or F8 as provisional.
- SWOT: the strengths are an idle session and a subject close to its doc-0031 work. The weakness is the provisional steps. The opportunity is that the brief feeds F2. The threats are staleness and drift against the tranche as it lands.
- Advice: draft now, document only; no task minted, no step built before the maintainer's decision on the process (AC #3).
<!-- SECTION:NOTES:END -->
