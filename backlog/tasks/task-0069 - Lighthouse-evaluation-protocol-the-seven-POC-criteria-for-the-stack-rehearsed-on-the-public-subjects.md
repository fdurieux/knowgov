---
id: TASK-0069
title: >-
  Lighthouse evaluation protocol: the seven POC criteria for the stack,
  rehearsed on the public subjects
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-03T23:53:00Z'
updated_date: '2026-11-04T00:21:00Z'
labels:
  - lighthouse
milestone: m-8
dependencies:
  - TASK-0056
references:
  - backlog/docs/doc-0013
priority: medium
ordinal: 73000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0013 P3. An evaluator of a governed-context platform asks seven proof-of-concept questions (semantic modelling, traceability, knowledge quality, agent grounding, operational safety, interoperability, performance and cost). knowgov should answer them first on public content, then on the lighthouse pilot (task-0062 for the pilot half).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 One adopter-register document lists the seven criteria with the stack's evidence for each
- [ ] #2 A script collects the public evidence from the example instance (walk, gate, three-valued answer over MCP, invalidation, export manifest) on CargoQuote and the J-F kit
- [ ] #3 The pilot half is a checklist whose evidence stays in the private record
- [ ] #4 Criterion 6 (executing business actions) is stated as out of scope, with the reason; no banking scenario anywhere
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. docs/lighthouse-evaluation.md, adopter register: the seven criteria, each with the stack today, the rehearsal's evidence, the gap, and what the pilot must show; actions out of scope with the reason; the pilot checklist, its evidence private.
2. tools/lighthouse_evidence.py OUT: builds the example instance, collects per subject in a child process (walk, gate, MCP three-valued answer, invalidation, export manifest, cost), digests the instance before and after, writes evidence.json and evidence.md; exit 0/1/2.
3. tests/test_lighthouse.py on the doc and the summary; harness.yml runs the full collection on rdflib; CLAUDE.md layout line.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Full rehearsal on rdflib, 0 failures: CargoQuote S1-S7 verdicts equal to the record, MCP equal to gate_cli on 7 scenarios with all three answers, S6 four invalidated and derived:S1:G:run1 suspect, 10 of 10 export digests; J-F C-D5 equal to the record, MCP equal on 6, 50 of 50 export digests; instance unchanged. J-F's register anchors reach no statements through register_node_statements (CargoQuote's do); the walk itself holds for both. Wall clock about 50 s CargoQuote, 350 s J-F.
<!-- SECTION:NOTES:END -->
