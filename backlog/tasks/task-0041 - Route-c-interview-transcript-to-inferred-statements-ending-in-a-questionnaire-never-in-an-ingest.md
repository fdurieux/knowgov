---
id: TASK-0041
title: >-
  Route (c): interview transcript to inferred statements, ending in a
  questionnaire, never in an ingest
status: Done
assignee:
  - '@claude'
created_date: '2026-11-02T23:22:00Z'
updated_date: '2026-11-04T00:07:00Z'
labels:
  - capture
milestone: m-5
dependencies:
  - TASK-0009
documentation:
  - >-
    backlog/docs/doc-0007 -
    Capturing-an-employees-knowledge-to-resolve-a-non-conformity-the-John-Doe-walkthrough.md
priority: low
type: feature
ordinal: 53000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0007 §6: a model reading a transcript of a conversation with a person may propose statements; they load as basis inferred, proposed, never promoted (as S5's machine note does), and the questionnaire already lists such candidates in `known` (seen on S5). What is missing is the step from a transcript to inferred statements. The transcript is never the record (doc-0001 §0); only the person's answer to the questionnaire becomes elicited. The model endpoint is instance configuration (harness/arms.py endpoint()).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A command turns a transcript into inferred, proposed statements on required keys, attributed to the model, and writes no capture
- [x] #2 The questionnaire generated afterwards lists those candidates in `known`, and the person confirms by answering
- [x] #3 The transcript is not copied into the store, the captures or the register
- [x] #4 With no model key configured the command refuses to run (exit 2), as the arms do
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/transcript.py: refuse exit 2 without a model key (arms.endpoint); load the scenario, take the keys at absent or declared_gap, ask the model (arms.call), keep proposals on those keys only; write <capture dir>/inferred/<date>-<sha12>.toml with the digest, model, date, never the text.
2. load.load_inferred_proposals inside load_captures: basis inferred, proposed, attributed to the model, version transcript (pairs with no document), no candidate_for (both adapters take None).
3. tools/check_transcript_route.py with a fixture transcript and a stub model, on both stores; harness.yml and demo.yml.
4. Unit tests; instance/README.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Proven locally on rdflib and on Neo4j 5.26 (tarball, Java 21): check_transcript_route OK; comparator 0 differing leaves on both. Proposals restricted to keys at absent or declared_gap: decision-0004 exempts only elicited statements, so a model's candidate beside a validated document statement would lower the key.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Route (c): transcript.py turns a transcript into a model's candidates on the required keys the store holds nothing on. It refuses (exit 2) without a model key. The candidates are written to <capture dir>/inferred/ with the transcript's SHA-256, the model and the date, never its text, and every load reads them as inferred, proposed and attributed to the model. The next questionnaire lists them in known, and the person confirms by answering. No capture is written. tools/check_transcript_route.py proves this with a fixture transcript and a stub model on rdflib and Neo4j, and runs in both CI jobs.
<!-- SECTION:FINAL_SUMMARY:END -->
