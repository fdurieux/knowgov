---
id: TASK-0206
title: Page and connector single fixes (doc-0030 P3, P10)
status: To Do
assignee: []
created_date: '2026-11-07T07:15:00Z'
labels:
  - review
  - page
dependencies: []
priority: low
type: bug
ordinal: 206000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer accepted doc-0030's advice on 2026-11-07 ("accept the advise on all four"): the hardening tranche before 0.9.0's cut, in the order F7; F1 with the check_instance guard, H7 and M3; F3, F4 and F2; F5 and F8. The ids below are doc-0030's (the code review at 8d80b2b); each finding there quotes its lines and its probe.

P3: the page's rescan rebuilds on a changed mtime, but page_subject.of caches by root forever, so an edited name, listed, tasks or id is never served, scenarios.toml is not watched, and KG_SUBJECTS with nothing loadable serves public CargoQuote. P10: tools/connector.py drops an export file that shares a basename with another. Fixes.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 An edited subject.toml or scenarios.toml is served on the next request; KG_SUBJECTS with nothing loadable serves no public subject
- [ ] #2 connector.py refuses two inputs that map to one relative path
<!-- AC:END -->
