---
id: TASK-0305
title: >-
  withdrawn means deprecated or retired only; every edge not followed is
  not_followed (decision-0035 B3)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-09T21:29:00Z'
updated_date: '2026-11-09T22:44:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0035
  - backlog/docs/doc-0037
priority: high
ordinal: 298000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Under decision-0035, accepted 2026-11-09 ("Option (A)", doc-0037 §3.4). Found by the functional review, group B, at main f194aac.

"withdrawn" means two things. In `register_change` and the gate it means deprecated or retired. In proposal-impact's `slices.map[].withdrawn` and `keys.behind_withdrawn`, in `register_impact`'s "flagged withdrawn" and in the page's "no, withdrawn", it means any edge not followed, a proposed one included.

Repro: `harness/proposal_impact.py --scope JRN-0001 --as-of record -f json` gives `slices.map[JRN-0003].withdrawn[0] = {to: PROC-0005, state: "proposed"}`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Every field, finding and text that lists edges not followed says `not_followed` (and `behind_not_followed` where a key sits behind one), with the edge's state; `withdrawn` stays only where an edge or node is deprecated or retired.
- [x] #2 The proposal-impact schema, `register_impact`'s output, the page's impact text and the docs use the one vocabulary, and a test holds that no not-followed list is named `withdrawn`.
- [x] #3 `check_proposal_branch`, `check_mcp_server` and the proposal fixture's outputs are updated; the record does not move.
- [x] #4 A CHANGELOG line names the rename under Contract changes.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Rename every list of edges or descendants a walk does not follow to not_followed (behind_not_followed for keys behind one), each with its state: proposal_impact slices.map and keys, register_impact children and landed-row flag (landed_rows' parameter), step_grid, register_change's descent, mcp_server's descriptions.
2. Page and saved queries: "no, not followed" and why (the link's state, or a far node deprecated or retired).
3. Schemas: proposal-impact, register-impact, step-grid; proposal-impact and step-grid to schema_version 2 (a rename is not additive, the schema's own rule).
4. Docs (guide, demo README, instance README), lighthouse_evidence, check_mcp_server; a vocabulary test; CHANGELOG.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Evidence (e3470b0, then merged with main e79db23): the review's reproduction (proposal_impact --scope JRN-0001) gives slices.map[JRN-0003].not_followed = [{to: PROC-0005, state: proposed}] and no withdrawn key anywhere. tests/test_not_followed_vocabulary.py, 6 tests: schemas, the reproduction, the worked example, register_impact, the page and the saved queries; 5 fail on the old code. Record unmoved: comparator 0 diffs on CargoQuote S1-S7 and J-F (6); check_round_trip --chain rdflib,rdflib on both subjects; check_mcp_server on both; check_proposal_branch holds; check_saved_queries against Neo4j 5.26: every saved query ran; complexity holds. Suites: bare 1005/1067, J-F bare 1004/1067, pinned 1065/1067, J-F pinned 1062/1067, 0 failed. The guide keeps the vendored register tool's own summary line, which says withdrawn for an edge not followed, with a note.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Every list of edges or descendants a walk does not follow is now not_followed, with the edge's state: proposal-impact's slices.map[].not_followed and keys.behind_not_followed, register_impact's children[].not_followed and the landed keys' flag, step-grid's behind_not_followed and register_change's descent; the page and the saved queries say "no, not followed" and why. withdrawn means deprecated or retired alone. proposal-impact and step-grid move to schema_version 2, the rename not being additive; a test holds that no not-followed list is named withdrawn. The record does not move.
<!-- SECTION:FINAL_SUMMARY:END -->
