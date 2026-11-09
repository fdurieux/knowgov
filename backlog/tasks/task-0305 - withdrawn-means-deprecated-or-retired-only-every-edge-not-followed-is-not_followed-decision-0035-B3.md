---
id: TASK-0305
title: >-
  withdrawn means deprecated or retired only; every edge not followed is
  not_followed (decision-0035 B3)
status: To Do
assignee: []
created_date: '2026-11-09T21:29:00Z'
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
- [ ] #1 Every field, finding and text that lists edges not followed says `not_followed` (and `behind_not_followed` where a key sits behind one), with the edge's state; `withdrawn` stays only where an edge or node is deprecated or retired.
- [ ] #2 The proposal-impact schema, `register_impact`'s output, the page's impact text and the docs use the one vocabulary, and a test holds that no not-followed list is named `withdrawn`.
- [ ] #3 `check_proposal_branch`, `check_mcp_server` and the proposal fixture's outputs are updated; the record does not move.
- [ ] #4 A CHANGELOG line names the rename under Contract changes.
<!-- AC:END -->
