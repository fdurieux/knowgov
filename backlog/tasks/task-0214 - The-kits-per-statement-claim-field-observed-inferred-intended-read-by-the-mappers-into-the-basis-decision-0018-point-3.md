---
id: TASK-0214
title: >-
  The kit's per-statement claim field (observed, inferred, intended) read by the
  mappers into the basis (decision-0018 point 3)
status: To Do
assignee: []
created_date: '2026-11-08T11:17:00Z'
labels:
  - process
  - reverse-engineering
  - contract
  - mappers
dependencies: []
references:
  - >-
    backlog/decisions/decision-0018 -
    Reverse-engineering-and-knowledge-gap-identification-is-an-eight-step-process-knowgov-routes-and-re-finds-its-gaps-and-its-three-contract-changes-land-in-0.9.0.md
documentation:
  - >-
    backlog/docs/doc-0032 -
    Reverse-engineering-and-knowledge-gap-identification-as-a-repeatable-process-eight-steps-with-their-tools-and-gaps-the-bases-decision-0011-H7-and-what-F2-must-bind.-Opportunity-canvas-fit-gap-SWOT-advice.md
priority: high
type: feature
ordinal: 214000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0018 point 3 (the maintainer, 2026-11-08, answering doc-0032 §11 question 3; doc-0032 §3). A kit statement carries an optional claim: observed (what the pinned original does), inferred (a proposed explanation or generalised rule) or intended (accepted by the responsible authority). The five bundle mappers (requirements_json, contracts_markdown, dmn_decisions, plantuml_realises, gherkin_tagged) read it into the basis: observed to extracted, inferred to inferred (never above proposed, harness/policy.md rule 2; a ruling refuses to approve it since task-0199 I4), intended to authored (approved only under an attestation, decision-0009 and decision-0019). A statement without claim loads as today (extracted), so the vendored kits and the scored record do not move. A contract change (the kit format), for 0.9.0 (doc-0028 G9-12).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Each of the five mappers reads claim when present and maps observed, inferred and intended to extracted, inferred and authored; a statement without claim loads as today
- [ ] #2 An inferred statement never rises above proposed on either store, and a ruling approving it is refused (task-0199 I4), shown by a probe kit
- [ ] #3 subjects/README.md and instance/mappers.toml document the field per mapper, and tools/check_subject.py refuses an unknown claim value
- [ ] #4 CHANGELOG.md carries the line under Unreleased's contract heading
- [ ] #5 The scored record (S1 to S7), the deterministic run and the comparator stay equal
<!-- AC:END -->
