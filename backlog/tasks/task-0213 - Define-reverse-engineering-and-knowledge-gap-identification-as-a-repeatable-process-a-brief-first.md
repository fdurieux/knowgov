---
id: TASK-0213
title: >-
  Define reverse engineering and knowledge-gap identification as a repeatable
  process (a brief first)
status: Done
assignee: []
created_date: '2026-11-07T09:25:00Z'
updated_date: '2026-11-08T11:18:00Z'
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
- [x] #1 A backlog doc defines the process step by step (scope at a named commit; reverse-engineer into a kit with each statement observed, inferred or intended; gather the existing artefacts; lint both; load as a subject so lint findings, code quirks and missing documentation become gaps routed to owners; address; re-run on change), each step mapped to the tool or record that exists and the gaps named
- [x] #2 The doc carries the four parts (opportunity canvas, fit/gap, SWOT, advice) and states how decision-0011 relates to it and where H7's drift question fits
- [x] #3 The maintainer's decision on the process is recorded before any task builds a step of it
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-07, sequencing: the brief drafted now, as a document only (doc-0032). The coordinating session decided it under the maintainer's delegation of 23:51 UTC ("opportunity, swot, fit/gap => decide"), and the testing-class session drafted it on that dispatch. The four parts:
- Canvas: the decision gets lead time while the tranche runs, and F2 (task-0199) is shaped by what the process needs from it (doc-0032 §6) before it is dispatched.
- Fit/gap: no code overlap with the tranche, since the brief changes nothing in harness/, tools/ or subjects/. The risk of going stale is mitigated by marking every step that depends on F2, F4, F5, F6 or F8 as provisional.
- SWOT: the strengths are an idle session and a subject close to its doc-0031 work. The weakness is the provisional steps. The opportunity is that the brief feeds F2. The threats are staleness and drift against the tranche as it lands.
- Advice: draft now, document only; no task minted, no step built before the maintainer's decision on the process (AC #3).

2026-11-08, the maintainer's decision: "Do them now. include in 0.9." (answering doc-0032 §11's eight questions as recommended). Recorded as decision-0018 (accepted), with its four parts; decision-0011 gains amendment A7 and stays proposed. The builds are tasks 0214 to 0220; the three contract changes (0214, 0215, 0216) gather for 0.9.0 under doc-0028 G9-12. The same day the maintainer chose to bind attestations to versions in 0.9.0 (decision-0019, task-0221, G9-13) and to build the stage-2 idempotent close (task-0222).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The brief (doc-0032, #340) defines the reverse-engineering process in eight steps, each mapped to its tool or record and its gap, with the four parts and eight questions. The maintainer answered all eight on 2026-11-08; decision-0018 records the process and the answers before any step is built (AC #3), decision-0011 is amended (A7), and the build is tasks 0214 to 0220. Follow-ups: the first instance (task-0220) waits on the maintainer for the J-F commit, the route to its private code and what may be published.
<!-- SECTION:FINAL_SUMMARY:END -->
