---
id: TASK-0139
title: >-
  Route (c) over a document: key-constrained proposals from prose kinds, scored
  against the mappers before any use
status: To Do
assignee: []
created_date: '2026-11-05T17:21:00Z'
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
- [ ] #1 The bar is committed before the first measured run: no value proposed for S2's declared gap, no silent resolution of S3's vague wording, precision at least 0.9 on S1 (the maintainer may change it before the run, never after)
- [ ] #2 The measurement runs the model over the public subjects' mapped documents with the mapper withheld, constrained to the task's required keys the gate holds nothing on, and reports per document the proposals, the matches against the mapper's assertions (`rules.compatible`), precision, recall and inventions, with the model, effort and date; it writes nothing into a subject's capture folder
- [ ] #3 It is off until the key variable (`KG_MODEL_API_KEY_VAR`) holds a value, reads public content only, and its prompt states the language it reads
- [ ] #4 The outcome, either way, is a dated entry in doc-0019 with the decision: build the document route (fragment-named proposals into `<capture dir>/inferred/`, listed in the questionnaire, invalidated on a fragment change) or park it
<!-- AC:END -->
