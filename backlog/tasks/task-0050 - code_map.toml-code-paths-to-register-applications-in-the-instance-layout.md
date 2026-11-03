---
id: TASK-0050
title: 'code_map.toml: code paths to register applications, in the instance layout'
status: To Do
assignee: []
created_date: '2026-11-03T22:40:00Z'
labels:
  - instance
  - traceability
milestone: m-7
dependencies:
  - TASK-0045
priority: medium
type: feature
ordinal: 62000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0011 follow-up 6: nothing maps a code path to the register application or module it implements, so a code change cannot reach the knowledge. An instance file maps path globs to APP ids, checked by tools/check_instance.py. It may later yield to a register implemented_by link, which would be the register's decision.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The instance layout documents code_map.toml (globs → APP id); the example instance carries one for CargoQuote's reference code
- [ ] #2 check_instance.py refuses an unknown APP id or an overlapping glob and lists unmapped code paths
<!-- AC:END -->
