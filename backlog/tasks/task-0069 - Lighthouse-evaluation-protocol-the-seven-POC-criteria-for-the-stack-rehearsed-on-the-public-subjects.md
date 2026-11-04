---
id: TASK-0069
title: >-
  Lighthouse evaluation protocol: the seven POC criteria for the stack,
  rehearsed on the public subjects
status: Done
assignee:
  - '@claude'
created_date: '2026-11-03T23:53:00Z'
updated_date: '2026-11-04T00:43:00Z'
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
- [x] #1 One adopter-register document lists the seven criteria with the stack's evidence for each
- [x] #2 A script collects the public evidence from the example instance (walk, gate, three-valued answer over MCP, invalidation, export manifest) on CargoQuote and the J-F kit
- [x] #3 The pilot half is a checklist whose evidence stays in the private record
- [x] #4 Criterion 6 (executing business actions) is stated as out of scope, with the reason; no banking scenario anywhere
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

After merging main (#115 in): rdflib full run 0 failures, superseded_by named for S6's three stale statements; Neo4j 5.26 full run 0 failures (verdicts, MCP, S6 invalidation and superseded_by identical; CargoQuote 30 s, J-F 63 s). Fixed on the way: register_project.project releases the store it is given, so the anchor read opens a fresh one, as the CI steps do.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
docs/lighthouse-evaluation.md (adopter register) lists doc-0013's seven criteria, each with the stack today, its rehearsal evidence, its gap and what the pilot must show; executing business actions (criterion 6) is out of scope with the reason; the pilot half is a checklist whose evidence stays in the pilot's private record; no banking scenario. tools/lighthouse_evidence.py collects the public evidence: CargoQuote from the example instance and the J-F kit, the walk and statements at each anchor, the gate on every scenario against the record, the MCP verdict and three-valued answers, S6's invalidation with superseded_by, the export manifest's digests, and wall-clock cost; the instance is digested unchanged. 0 failures on rdflib and on Neo4j 5.26; harness.yml runs it on rdflib. Follow-up seen: J-F's register anchors reach no statements through register_node_statements.
<!-- SECTION:FINAL_SUMMARY:END -->
