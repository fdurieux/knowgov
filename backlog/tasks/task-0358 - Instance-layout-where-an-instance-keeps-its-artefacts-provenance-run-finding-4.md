---
id: TASK-0358
title: >-
  Instance layout: where an instance keeps its artefacts' provenance (run
  finding 4)
status: To Do
assignee: []
created_date: '2026-11-16T04:37:00Z'
labels:
  - finding
  - reverse-engineering
  - docs
dependencies: []
type: task
ordinal: 348000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found 2026-11-16 by the first private reverse-engineering runs (decision-0018's process on a private demonstration case, task-0220): kits written to subjects/README.md by a clean-room extraction session, then loaded by the instance tooling. The maintainer, 2026-11-16: "mint tasks for the five knowgov findings".

tools/check_instance.py refuses any file at the top of artefacts/ ("files go under a kind folder", by design). A run that copies existing artefacts in as found needs a manifest of where each came from and its digest; it first put SOURCE.md and SOURCE.sha256 at the top of artefacts/ and check_instance.py exited 1 (preload_check.py 2). instance/README.md does not say where such a manifest belongs.

Placement: a documented place is a docs fix (0.9.x); admitting named manifest files at the top of artefacts/ is a layout change (1.1.0).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 instance/README.md names where an instance keeps the provenance of artefacts it copied in (path, source, commit, digests)
- [ ] #2 The refusal message points to that place
<!-- AC:END -->
