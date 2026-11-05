---
id: TASK-0145
title: >-
  C5 spike: a claim's value checked against the cited statement's value,
  mechanically (doc-0019 C5, unparked)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-05T21:11:00Z'
updated_date: '2026-11-05T22:10:00Z'
labels: []
dependencies: []
documentation:
  - >-
    backlog/docs/doc-0019 -
    GraphRAG-read-against-knowgov-the-paper-verified-against-its-tables-fit-gap-opportunity-canvas-SWOT-candidates.md
priority: low
type: spike
ordinal: 151000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
M5 counts a reply's refs that resolve, not whether the value the reply uses matches the cited statement. task-0140 measured the blind spot (doc-0019 §7): on S3 the compact bundle lost the planted accept_boundary_41 in 3 of 5 runs while every failing run cited the right boundary keys, so M5 stayed 1.0 with the wrong value in the code. Claims and assumptions are prose with a ref (A:dt:S-accept|max@v1); the value may sit in the text, in the generated code, or nowhere, so what counts as "the claim's value" is part of the spike. Unparked by the maintainer on 2026-11-05.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Before any measurement, the hypothesis and the bar are recorded in this task through the CLI: recall, every governed run whose M4 fails a planted value target while citing that target's key is flagged; precision, no flag on any of the record's 35 governed replies (S1-S7, five runs) whose M4 targets pass; a claim that states no value is counted unvalued, never matched
- [x] #2 The check reads replies, generated code and the store's statements as a measurement outside the record: no field added to the record's run files, the comparator and the deterministic results unchanged, value normalisation (numbers, units, booleans, enumerations) documented
- [x] #3 Measured on the record's governed replies and on a compact-form S3 re-run labelled a deviation (n = 5, effort as task-0140, raw outputs outside the repository), with the per-run table
- [x] #4 A dated doc-0019 entry gives the outcome against the bar and the decision: fold it into the measures (and where: M5, a new measure, or trace's check on hand-written code), or park it with the reason
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Record the hypothesis and AC #1's bar (this edit), before any measurement.
2. tools/claim_values.py: the check, outside the record; per cited key, the claim's text and the code's bindings against the store's statements (run.deterministic, then run.stage2 where the scenario has one).
3. Measure the record's governed replies (S1-S7, five runs each).
4. Deviation: S3 compact, n = 5, gpt-5.5 at effort low, render_bundle bound to compact as task-0140 did; full-form S3 n = 5 as a control; raw outputs in the session's scratch only; 10 calls.
5. A dated doc-0019 entry: the per-run table, the outcome against the bar, the decision (fold in, and where, or park).
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Hypothesis and bar, recorded 2026-11-05 before any measurement (no run of the check on any reply yet).

Fact established from the store before measuring: S3's plant removed every exact boundary. No statement of the S3 store holds 41, 42, 66 or 67, and neither does the prompt. The cited A:dt:S-accept|max@v1 holds 'risk index clearly low — below the low forties'; A:seq:S-accept|max@v1 holds the undefined symbol ACCEPT_MAX. A right and a wrong boundary are both values the store does not state.

The check, defined: per cited key, the key's value is the cited statement's normalised value, else the values of the key's other statements, a symbol valued only where some statement defines it. The claim's value is the values of that type in the claim's text, the code's the literal bound to a symbol the key's statements or the citing texts name, else for a number or an enumeration whether the value is among the code's literals. Verdicts: mismatch (another value stated or bound), absent (valued key, code written, value nowhere in it), unsupported (unvalued key, a number the store states nowhere in the text or bound in the code), matched, unvalued (a claim stating no value is unvalued, never matched). A flag is mismatch, absent or unsupported. Normalisation in the tool's docstring.

Bar (AC #1, unchanged): recall, every governed run whose M4 fails a planted value target while citing one of that target's keys (tools/claim_values.py TARGET_KEYS) is flagged on one of them; precision, no flag on any key of any of the record's 35 governed replies whose M4 targets pass (all true, or none run); recall population, the record's and the deviation's runs.

Expected (falsifiable): the bar is not met on S3. P1: the mismatch tier alone flags no S3 target, record or deviation. P2: the unsupported tier flags S3 runs whose code binds a boundary number, failing and passing alike, so the record's S3 run 4 (all targets pass) breaks precision. P3: on keys the store values (DT-P, the validation limits, the statuses), the passing runs (S1, S6) carry no mismatch or absent flag; any such flag is a normalisation false positive and is reported as one.

Measured 2026-11-05 (doc-0019 §8). Record, as registered: recall 4/6, precision 12/31 flagged. After three corrections to the check (a symbol binds a key only as a statement value; enumerations one token; booleans never decided), named in the tool and §8: recall 4/6, precision 10/31 flagged; mismatch tier 0/31 flagged and 0/7 recall. Deviation (gpt-5.5, effort low, 10 calls, 133,067 tokens, raw outputs in scratch): compact S3 fails accept_boundary_41 in 1 of 5 (§7: 3 of 5), caught as unsupported; full 0 of 5, all five flagged unsupported. P1 and P2 held; P3 did not hold as registered. The record's S3 target failures are NotImplementedError stubs, not wrong values; compact run 3 (exclusive 40) is the only wrong boundary value in the three sets.

Merging main put task-0139's C1 entry at doc-0019 §8; the C5 entry is §9. The note above that says §8 means §9.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
C5 measured and parked again. tools/claim_values.py checks each governed reply's claims and generated code against the store's statements, outside the record (no run file, comparator or deterministic result touched). The bar is not met under any tier: S3's store states no exact boundary, so a right guess and a wrong one get the same verdict (unsupported), and where the store values a key the mismatch tier is clean but has no recall population. doc-0019 §9 has the per-run table, the corrections, a correction to §7's claim that C5 would have caught S3's miss, the decision and what would reopen it.
<!-- SECTION:FINAL_SUMMARY:END -->
