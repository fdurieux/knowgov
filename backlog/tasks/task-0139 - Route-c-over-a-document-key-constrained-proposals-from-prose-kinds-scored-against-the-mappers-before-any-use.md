---
id: TASK-0139
title: >-
  Route (c) over a document: key-constrained proposals from prose kinds, scored
  against the mappers before any use
status: Done
assignee:
  - '@claude'
created_date: '2026-11-05T17:21:00Z'
updated_date: '2026-11-05T21:10:00Z'
labels:
  - capture
  - arms
milestone: m-6
dependencies: []
references:
  - harness/transcript.py
  - instance/kinds.toml
  - https://aclanthology.org/2025.genaik-1.6.pdf
documentation:
  - >-
    backlog/docs/doc-0019 -
    GraphRAG-read-against-knowgov-the-paper-verified-against-its-tables-fit-gap-opportunity-canvas-SWOT-candidates.md
priority: low
type: spike
ordinal: 139000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0019 C1. Twelve of the twenty kinds in `instance/kinds.toml` have no mapper, so an adopter's ADRs, user stories, glossary and threat-model narratives load as `unmapped` and their keys read `absent`: the gate blocks on knowledge the documents may state. Route (c) (`harness/transcript.py`, task-0041) already turns a transcript into `inferred`/`proposed` candidates for the task's empty keys, never promoted, listed in the owner's questionnaire. Widened to a document, it is FactRAG (Barry et al., GenAIK 2025) constrained to the keys. The paper could not score its extractor; here the deterministic mappers are the ground truth, so the extractor is measured on the public subjects before any adopter relies on it. Structured kinds (schemas, ArchiMate, data models) get a mapper instead; this is for prose.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The bar is committed before the first measured run: no value proposed for S2's declared gap, no silent resolution of S3's vague wording, precision at least 0.9 on S1 (the maintainer may change it before the run, never after)
- [x] #2 The measurement runs the model over the public subjects' mapped documents with the mapper withheld, constrained to the task's required keys the gate holds nothing on, and reports per document the proposals, the matches against the mapper's assertions (`rules.compatible`), precision, recall and inventions, with the model, effort and date; it writes nothing into a subject's capture folder
- [x] #3 It is off until the key variable (`KG_MODEL_API_KEY_VAR`) holds a value, reads public content only, and its prompt states the language it reads
- [x] #4 The outcome, either way, is a dated entry in doc-0019 with the decision: build the document route (fragment-named proposals into `<capture dir>/inferred/`, listed in the questionnaire, invalidated on a fragment change) or park it
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. tools/route_c_documents.py: per scenario and mapped document, load with the document's mapper withheld (single) or every mapper withheld (all), ask the model for the task's required keys at absent/declared_gap, score through rules.compatible against the withheld mapper's assertions; stdlib tests of the pure half.
2. Run on the public subjects only: CargoQuote S1, S2, S3 (codegen and design), J-F C (codegen); model gpt-5.5-2026-04-23, effort medium, KG_MODEL_API_KEY_VAR at a dummy-valued variable (proxy-injected key); raw replies in the session scratch directory, never the repository.
3. Dated entry in doc-0019 with the numbers and build or park.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-05, before any measured run: the bar, confirmed by the maintainer this date and fixed from here on (AC #1). (1) No value proposed for S2's declared gap. (2) No silent resolution of S3's vague wording: a proposal on a key whose mapped text carries S3's vague wording must keep the vagueness (or propose nothing); a definite value read into it is a fail. (3) Precision at least 0.9 on S1 (matches through rules.compatible over proposals, S1's mapped documents, mapper withheld). Missed on any one, the document route parks.

2026-11-05, before the first measured run: how the fixed bar is measured, declared now and not moved after. Model gpt-5.5-2026-04-23 at effort medium through arms.endpoint(). Language English, stated in the prompt. Bar checks (route_c_documents.bar): (1) S2: zero proposals on any key the scenario's own load holds at declared_gap, in both modes (strict: any value on that key fails, a restatement that it is open included). (2) S3: zero silent resolutions in mode all, the only mode that asks the vague threshold keys (single never opens them: other documents state them); a silent resolution is a proposal on a key whose live statements R-VAGUE words vaguely (a subject vague word or an unresolved symbol) that carries none of the vague words and equals none of the document's own values. (3) S1: pooled precision at least 0.9 in mode single (the brief's shape: the document's own mapper withheld, the keys the gate then holds nothing on), over S1's mapped documents and both task classes; mode all reported beside it, not part of the bar. Precision is strict rules.compatible 'equal' against the mapper's value or raw symbol; no normalisation counts. Value forms in the prompt come from shapes only (number, name=value names, NONE, words), never values. J-F C reported, no bar.

2026-11-05, measured: gpt-5.5-2026-04-23, effort medium. S2 held (0 fills, both modes), S3 held (0 silent resolutions, all), S1 single precision 0.56 (19/34), bar missed: parked. Scoring fix after the first all run, before any reading of the bar: the vague-key test matched NONE as a symbol, which load.resolve_symbols excludes; corrected to the recorded definition and every kept reply rescored (--resume), no new call for them. Four calls 502 twice (J-F all contracts/dmn/ and uml/; CargoQuote S2 and S3 all acceptance.feature), reported, unscored. Raw replies in the session scratch directory only.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
tools/route_c_documents.py measures route (c) over a document: per mapped document of the public subjects, the mapper withheld (single) or all mappers withheld (all), the model asked for the task's required keys the gate then holds nothing on, proposals scored against the withheld mapper through rules.compatible (match, wrong, invention; precision, recall; fills of a declared gap; silent resolutions of vague wording). Off without KG_MODEL_API_KEY_VAR; prompt states English; outputs refused inside the repository; nothing ingested. tests/test_route_c_documents.py covers the pure half. Run 2026-11-05 on gpt-5.5-2026-04-23 at medium: S2 and S3 held, S1 precision 0.56 against 0.9, so the document route parks; doc-0019 §7 records the numbers, the miss analysis (citation suffixes and value forms; inventions when asked keys a document does not state) and what would reopen it.
<!-- SECTION:FINAL_SUMMARY:END -->
