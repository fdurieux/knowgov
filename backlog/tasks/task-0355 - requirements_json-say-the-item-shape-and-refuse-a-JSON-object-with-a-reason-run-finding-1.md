---
id: TASK-0355
title: >-
  requirements_json: say the item shape, and refuse a JSON object with a reason
  (run finding 1)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-16T04:37:00Z'
updated_date: '2026-11-16T21:14:00Z'
labels:
  - finding
  - reverse-engineering
  - 0.10.0
dependencies: []
type: bug
ordinal: 345000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found 2026-11-16 by the first private reverse-engineering runs (decision-0018's process on a private demonstration case, task-0220): kits written to subjects/README.md by a clean-room extraction session, then loaded by the instance tooling. The maintainer, 2026-11-16: "mint tasks for the five knowgov findings".

harness/extract.py extract_requirements_json iterates json.loads(text) as a list of {id, kind, statement, basis}. A kit that wraps its items in an object ({"requirements": [...], ...}) makes it iterate the object's keys and fail with a TypeError, not a refusal naming the file. subjects/README.md (the guide an extraction writes to) names the mapper and its claim field but never the top-level shape, so a careful extractor wrote the object form in both runs. The instance builder worked around it by projecting each kit's list into a vendored file with digests.

Placement: the guide's sentence and a named refusal are fixes (0.9.x); accepting an object with a requirements list is additive (1.1.0) and a separate choice.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 subjects/README.md states requirements_json's input: a top-level JSON list of items, each with id and statement (kind, basis, claim optional)
- [ ] #2 A non-list top level is refused by check_subject.py and by the load with a message naming the file and the expected shape, never a TypeError
- [ ] #3 A test holds the refusal; the scored record is unchanged
- [ ] #4 Reader extension (0.10.0): requirements_json also reads a top-level object whose one list-valued key holds the items (the kits' shape), recorded in subjects/README.md and the CHANGELOG under contract changes
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. extract.requirements_items: a list, or an object's one list-valued key; anything else ShapeRefused (a DocumentUnreadable) naming the file and the shape; extract_all passes it through. 2. check_subject: the existing mapper-failed rule carries it. 3. subjects/README.md 'Where the bundle mappers read citations'; instance/mappers.toml and the generated skill. 4. tests/test_kit_mapper_findings.py; both comparators.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
The maintainer, 2026-11-16: "Yes" to these joining 0.10.0 (decision-0047 point 4): the soak they waited for restarts with 0.10.0 anyway.
<!-- SECTION:NOTES:END -->
