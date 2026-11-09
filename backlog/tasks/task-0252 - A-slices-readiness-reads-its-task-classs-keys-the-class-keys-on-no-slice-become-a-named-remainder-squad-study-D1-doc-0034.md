---
id: TASK-0252
title: >-
  A slice's readiness reads its task class's keys: the class keys on no slice
  become a named remainder (squad study D1, doc-0034)
status: Done
assignee: []
created_date: '2026-11-09T07:32:00Z'
updated_date: '2026-11-09T07:58:00Z'
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
- [x] #1 With a store, every slice's keys under --task T (CLI and the MCP tool) are T's keys among the rows landing on its thread; T's keys landing on no slice are listed in a named remainder with the count of T's keys as denominator; a test on CargoQuote under design holds the S2 slice verdicts equal to what the subject's design gate reads for those keys, and REQ-06|text in the remainder or its slice
- [x] #2 Under codegen the CargoQuote slices, verdicts and counts are unchanged; task-0191 AC #2's equality with register_impact holds for codegen, and register_impact's documentation states it reports every mapped key a change reaches, not a class's readiness
- [x] #3 harness/schemas/proposal-impact.schema.json names the remainder additively; the deterministic comparator and the round trip pass with the record unchanged; CHANGELOG Unreleased › Contract changes names it
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Built on claude/task-0252-slice-class-keys (PR #402). proposal_impact.slice_keys keeps a slice's rows to [tasks.T].keys; key_remainder gives slices.task_keys (group on_no_slice; key, owner, anchor, via [], mapped, nodes; denominator, in_slices, on_no_slice; gate and cells with a scenario held, read by with_levels as the slices are). evaluate/evaluate_branch take task (DEFAULT_TASK: the command's default class, codegen where declared; None reads every map key); with_levels refuses a report read under another class. register_impact unchanged; its docstring and MCP description call its keys the reach, not a class's readiness; MCP proposal_impact description and intake instructions follow. Schema additive (slices.task_keys required, keys.task, $defs/unsliced_key). Tests: tests/test_proposal_impact.py's three task-0252 tests (class filter and remainder, codegen no-move with landed_rows equality, design levels over MCP against the design gate and the cross-class refusal); JF tests read task=None (the in-process subject's classes are CargoQuote's). tools/check_mcp_server.py check_slice_classes on a real store, every class: slice keys inside the class at the class gate's levels, verdicts gate_verdict's, every class key in one slice or on no slice. Measured on S2 rdflib: design slices JRN-0002 8/36, JRN-0003 9/36, both BLOCKED on QuoteAPI|on_screening_outage; task_keys 25, BLOCKED on REQ-06|text (absent, mapped false); together the subject's design gate. Codegen: slices 22/36 each as before, the four S-* screening-band keys on no slice. Local (rdflib, CPython 3.13): run_tests 857/906, 49 skipped, 0 failed; check_mcp_server CQ S1,S2 and J-F C clean; check_proposal_branch holds; check_round_trip --chain rdflib,rdflib equal; CQ comparator 0 differing leaves. Neo4j left to the stack job.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
A slice's readiness now reads its task class's keys: proposal_impact (CLI --task, MCP task, codegen by default) keeps each slice's keys to [tasks.<class>].keys among the register-map rows on its thread, and slices.task_keys names the class's keys on no slice with the class's key count as denominator, levelled and gated with a scenario held. On CargoQuote S2 under design the slices block on QuoteAPI|on_screening_outage and REQ-06|text (absent, unmapped) sits in task_keys, together the subject's design gate; under codegen the slices, verdicts and counts are unchanged. register_impact keeps its reach and says so. Schema additive; CHANGELOG Unreleased > Contract changes. Verified locally on rdflib (tests, check_mcp_server CQ S1,S2 and J-F C, branch, round trip, comparator); Neo4j by the stack job.
<!-- SECTION:FINAL_SUMMARY:END -->
