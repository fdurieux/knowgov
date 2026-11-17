---
id: TASK-0356
title: >-
  plantuml_realises: document the footer, or read a realises comment (run
  finding 2)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-16T04:37:00Z'
updated_date: '2026-11-17T09:04:00Z'
labels:
  - finding
  - reverse-engineering
  - 0.10.0
dependencies: []
type: bug
ordinal: 346000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found 2026-11-16 by the first private reverse-engineering runs (decision-0018's process on a private demonstration case, task-0220): kits written to subjects/README.md by a clean-room extraction session, then loaded by the instance tooling. The maintainer, 2026-11-16: "mint tasks for the five knowgov findings".

extract_plantuml_realises reads the realised requirements only from the diagram's footer line (a footer ... realises: list). Both runs' kits wrote the links as a comment line (' realises: REQ-001, ...) beside the ' claim: comment line the guide does document, so every diagram-to-requirement link the kits state was silently not loaded. subjects/README.md documents the claim comment for this mapper but not the footer form of realises.

Placement: documenting the footer form and warning on a ' realises comment line are fixes (0.9.x); reading the comment form too is additive (1.1.0).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 subjects/README.md shows the footer form plantuml_realises reads, with an example
- [x] #2 check_subject.py warns on a ' realises: comment line that the mapper does not read, naming the diagram
- [x] #3 A test holds the warning; the scored record is unchanged
- [x] #4 Reader extension (0.10.0): plantuml_realises also reads a ' realises: comment line, with the footer still read, recorded in subjects/README.md and the CHANGELOG under contract changes
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. extract_plantuml_realises reads ' realises: comment lines after the footer, an id both name cited once, the footer's fragment and value unchanged (_realises_lines). 2. convention_warnings: a realises line (comment or footer) naming no id, or an id-shaped token with the document's prefix the pattern does not read; check_subject rule citation (warning), read without the mapper so it holds without pumllint. 3. README with example; tests; both comparators.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
The maintainer, 2026-11-16: "Yes" to these joining 0.10.0 (decision-0047 point 4): the soak they waited for restarts with 0.10.0 anyway.

Evidence (PR #579, merged 75ed913, whole green with stack): subjects/README.md shows the footer and the ' realises: comment forms with a PlantUML example. With #4 the mapper reads comment lines (_realises_lines; an id both name cited once, the footer's fragment and value unchanged), so #2's warning narrows, as the brief set, to a realises line the mapper reads past: one naming no id, or an id-shaped token with the document's prefix the pattern does not read; check_subject's citation warning names the diagram. tests/test_kit_mapper_findings.py holds the comment form, the footer unchanged and the warnings. The change moved no record: no public kit carries a realises comment, CargoQuote and J-F unchanged by it (J-F's re-record is task-0357's).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
plantuml_realises reads ' realises: comment lines beside the footer; check_subject warns only on a malformed realises line, naming the diagram; README shows both forms with an example. Merged in #579; no record moved by it.
<!-- SECTION:FINAL_SUMMARY:END -->
