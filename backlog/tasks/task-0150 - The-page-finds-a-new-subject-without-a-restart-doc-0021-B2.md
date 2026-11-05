---
id: TASK-0150
title: The page finds a new subject without a restart (doc-0021 B2)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-05T21:46:00Z'
updated_date: '2026-11-05T22:56:00Z'
labels: []
dependencies: []
priority: medium
type: bug
ordinal: 157000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
demo/app/server.py lists the subjects under KG_SUBJECTS once, at import (doc-0021 G3), so a subject added to an instance answers 404 until the page restarts: a restart doc-0021 counts in every onboarding. Maintainer's go, 2026-11-05. task-0141 H1/H2 change the same file's request handling; this change stays in the subject listing.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A subject added under KG_SUBJECTS after start is served on its first request (a rescan on an unknown id, or by modification time), and a removed one stops being listed
- [x] #2 A test adds a subject to a temporary instance after the server starts and reads it without a restart; the stack job's page checks hold
- [x] #3 task-0148's prompt drops its restart step in the same PR if 0148 has landed; instance/README.md says so
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
PR fdurieux/knowgov#249: refresh_subjects() by the manifests' paths and mtimes, inside the subject listing only. AC #3: task-0148 has not landed; its restart step drops in #245.

Merged as fdurieux/knowgov#249 on a fully green matrix (tests, rdflib, stack). Evidence: tests/test_page_subject.py's new live test (added after start: listed and served; broken manifest left out; removed: unlisted, 404). AC #3: task-0148 had not landed; its restart step leaves in #245, and instance/README.md says the page lists a new subject without a restart.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The page keeps its subject list current: `refresh_subjects()` in `demo/app/server.py`'s listing compares the manifests' paths and mtimes under `KG_SUBJECTS` on each request and rebuilds only what was added or edited; a removed subject is no longer listed, a manifest that does not load is left out and logged. Merged as #249.
<!-- SECTION:FINAL_SUMMARY:END -->
