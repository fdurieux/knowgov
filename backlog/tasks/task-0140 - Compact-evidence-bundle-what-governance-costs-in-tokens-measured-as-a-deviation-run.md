---
id: TASK-0140
title: >-
  Compact evidence bundle: what governance costs in tokens, measured as a
  deviation run
status: To Do
assignee: []
created_date: '2026-11-05T17:21:00Z'
labels:
  - arms
  - lighthouse
milestone: m-8
dependencies: []
references:
  - harness/gate.py
  - https://aclanthology.org/2025.genaik-1.6.pdf
documentation:
  - >-
    backlog/docs/doc-0019 -
    GraphRAG-read-against-knowgov-the-paper-verified-against-its-tables-fit-gap-opportunity-canvas-SWOT-candidates.md
priority: low
type: spike
ordinal: 140000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0019 C3. In the CargoQuote record the governed prompt is 2.0 to 2.7 times the baseline's (S2: 16,123 against 6,213 prompt tokens), while GraphRAG is sold on the opposite (Barry et al., GenAIK 2025: concise facts, about 80 % fewer tokens), so a buyer at the lighthouse will raise it. Evidence quotes, text, verification and approval lines are two thirds of the bundle; without them it is 28 to 34 % of its characters on S1 to S6 (51 % on S7), smaller than the documents. `read_knowledge` already serves a key's full section on demand. Whether the arm still abstains and cites without the inline evidence is the question; the record stays frozen.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The bundle renderer gains a compact form that keeps the verdict, the policy, each key's header, each assertion line and the conflict, stale, lapsed and suspect sections, and drops the text, evidence, verification and approval lines; the full form stays the default and the record's bundles still compare equal
- [ ] #2 The hypothesis is committed before the run: M1 unchanged (no code under BLOCKED), M4 and M5 within the full form's range, prompt tokens at most 40 % of the full form's
- [ ] #3 A deviation run on CargoQuote S1 to S7, five runs per form on one current model, labelled as a deviation and never written into `results/`, reports per scenario prompt tokens, M1, M4 and M5 for both forms
- [ ] #4 The outcome, either way, is a dated entry in doc-0019 with the decision on offering the compact form as an `evidence_bundle` option
<!-- AC:END -->
