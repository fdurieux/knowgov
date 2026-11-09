---
id: TASK-0252
title: >-
  A slice's readiness reads its task class's keys: the class keys on no slice
  become a named remainder (squad study D1, doc-0034)
status: To Do
assignee: []
created_date: '2026-11-09T07:32:00Z'
labels:
  - proposal
  - slices
  - contracts
  - correctness
dependencies: []
priority: high
ordinal: 246000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The squad study (doc-0034, D1) found that harness/proposal_impact.py with_levels gates each slice over the register map's rows landing on it (spec = dict(TASKS[task], keys=<slice rows>), lines 937 and 947), not over the class's [tasks.<class>].keys. Under codegen the two coincide on the public subjects; under design they do not: on CargoQuote S2 the slices block on response|hold_presence, which design does not require, and miss REQ-06|text, which blocks the subject's own design gate; 21 of design's 36 keys are in no register-map row and land on no slice. The maintainer, 2026-11-09: "(a), fix it in 0.9.0". A slice's keys become the class's keys among the rows landing on its thread; the class's keys on no slice are a named remainder with the denominator (as slices already place every overlay element); register_impact keeps its reach semantics (what a change touches, all mapped keys) and says so. A contract change to the proposal-impact output, additive in the schema, gathered for 0.9.0.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 With a store, every slice's keys under --task T (CLI and the MCP tool) are T's keys among the rows landing on its thread; T's keys landing on no slice are listed in a named remainder with the count of T's keys as denominator; a test on CargoQuote under design holds the S2 slice verdicts equal to what the subject's design gate reads for those keys, and REQ-06|text in the remainder or its slice
- [ ] #2 Under codegen the CargoQuote slices, verdicts and counts are unchanged; task-0191 AC #2's equality with register_impact holds for codegen, and register_impact's documentation states it reports every mapped key a change reaches, not a class's readiness
- [ ] #3 harness/schemas/proposal-impact.schema.json names the remainder additively; the deterministic comparator and the round trip pass with the record unchanged; CHANGELOG Unreleased › Contract changes names it
<!-- AC:END -->
