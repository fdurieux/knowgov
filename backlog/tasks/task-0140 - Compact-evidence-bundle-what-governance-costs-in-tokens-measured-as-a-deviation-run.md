---
id: TASK-0140
title: >-
  Compact evidence bundle: what governance costs in tokens, measured as a
  deviation run
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-05T17:21:00Z'
updated_date: '2026-11-05T20:37:00Z'
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

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. AC #1: render_bundle/render_key form='full'|'compact', full the default; tests: compact = full less the text, evidence, verification and approval lines; full pinned by a golden; full renders S1-S7 byte for byte as the pre-change renderer (done, 8692cb4).
2. AC #2: commit the hypothesis below, in this task and in the PR body, before any call.
3. AC #3: deviation run, governed arm only, CargoQuote S1-S7, n = 5 per form, one model (gpt-5.5, API default effort), KG_STORE=rdflib, as of the record date; a scratch driver outside the repository wraps harness/run.py's deterministic, stage2 and arm_runs with render_bundle bound to the form; raw outputs in the session scratch directory, never results/ or runs/.
4. AC #4: dated entry in doc-0019 with the per-scenario table and the decision on an evidence_bundle option; the option itself only if the hypothesis holds, as a separate additive change with a CHANGELOG line.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
HYPOTHESIS, committed 2026-11-05 before any model call (doc-0019 C3, as the task states it). Run: governed arm only, CargoQuote S1-S7, 5 runs per form (full, compact), one model, gpt-5.5 at the API's default effort, labelled a deviation (record model gpt-5.1-2025-11-13), never written into results/. Operationalised, per scenario:
H1 (M1 unchanged): no compact run returns code where the gate is BLOCKED, and the compact form's modal M1 decision equals the full form's.
H2 (M4, M5): the compact form's median M4 (suite passed) and median M5 (resolved share of refs) each lie within the full form's [min, max] over its five runs.
H3 (tokens): the compact form's mean prompt tokens are at most 40 % of the full form's.
The hypothesis holds if H1-H3 hold on all seven scenarios; a miss is reported per scenario, not averaged away. Known before the run from doc-0019 §2's character count: S7's compact bundle is 51 % of its full bundle, so H3 is at risk on S7. Decision rule for AC #4: offer compact as an evidence_bundle option only if the hypothesis holds; otherwise record why and leave the option out.

AMENDMENT to the run design, 2026-11-05, before any scored reply (the five S1 calls at the API's default effort all failed, no reply): the session proxy answers 502 'upstream request failed' when the upstream sends no byte for 30 s, and gpt-5.5 at its default effort sends none for longer on a 58 kB prompt (two probes, 30.3 s and 30.4 s). Probes at effort none and low streamed at once (first byte 1.3 s and 2.5 s; 17,466 prompt tokens either way). The run uses gpt-5.5 at effort low for both forms. H1-H3 and the decision rule are unchanged.
<!-- SECTION:NOTES:END -->
