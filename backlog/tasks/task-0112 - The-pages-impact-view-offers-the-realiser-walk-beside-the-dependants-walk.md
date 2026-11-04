---
id: TASK-0112
title: The page's impact view offers the realiser walk beside the dependants walk
status: To Do
assignee: []
created_date: '2026-11-04T14:55:00Z'
labels:
  - demo
  - register
milestone: m-8
dependencies: []
priority: medium
type: feature
ordinal: 112000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Proposed by task-0109; chosen by the maintainer 2026-11-04. ieam-register v0.2.7 (decision 0012) adds impact.py --walk realisers: what realises a capability (processes that support it, applications that realise it). The page's impact view shows only the dependants walk. Offer both, in both store adapters, with a saved query and the panel naming which walk it shows.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The impact view switches between dependants and realisers; CAP-0002/3/4 show three distinct realiser answers, as impact.py does
- [ ] #2 Both adapters return the same walk; a saved query for the realiser walk runs in check_saved_queries
- [ ] #3 The record and the comparator are unchanged; a CHANGELOG line under Unreleased
<!-- AC:END -->
