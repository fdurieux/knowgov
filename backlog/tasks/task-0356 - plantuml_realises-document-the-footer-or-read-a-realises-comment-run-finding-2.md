---
id: TASK-0356
title: >-
  plantuml_realises: document the footer, or read a realises comment (run
  finding 2)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-16T04:37:00Z'
updated_date: '2026-11-16T19:46:00Z'
labels:
  - finding
  - reverse-engineering
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
- [ ] #1 subjects/README.md shows the footer form plantuml_realises reads, with an example
- [ ] #2 check_subject.py warns on a ' realises: comment line that the mapper does not read, naming the diagram
- [ ] #3 A test holds the warning; the scored record is unchanged
- [ ] #4 plantuml_realises also reads a ' realises: comment line, the footer still read; the warning then applies only to a malformed one
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. extract_plantuml_realises reads ' realises: comment lines after the footer, an id both name cited once, the footer's fragment and value unchanged. 2. convention_warnings: a realises line (comment or footer) naming no id, or an id-shaped token with the document's id prefix the pattern does not read; check_subject rule citation (warning). 3. README with example; tests; both comparators.
<!-- SECTION:PLAN:END -->
