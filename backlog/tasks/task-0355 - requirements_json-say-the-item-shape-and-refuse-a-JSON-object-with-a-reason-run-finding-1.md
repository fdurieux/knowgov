---
id: TASK-0355
title: >-
  requirements_json: say the item shape, and refuse a JSON object with a reason
  (run finding 1)
status: To Do
assignee: []
created_date: '2026-11-16T04:37:00Z'
labels:
  - finding
  - reverse-engineering
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
<!-- AC:END -->
