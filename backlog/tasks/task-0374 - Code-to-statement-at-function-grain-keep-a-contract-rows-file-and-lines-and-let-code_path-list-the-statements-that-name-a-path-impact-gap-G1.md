---
id: TASK-0374
title: >-
  Code to statement at function grain: keep a contract row's file and lines, and
  let code_path list the statements that name a path (impact gap G1)
status: To Do
assignee: []
created_date: '2026-11-18T07:35:00Z'
updated_date: '2026-11-18T07:36:00Z'
labels:
  - impact
  - reverse-engineering
  - contract
dependencies: []
priority: medium
ordinal: 363000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Source: a private instance's impact and traversal study (2026-11-17), gap G1.

A reverse-engineered kit names each function's file and lines in its contracts, but the contracts mapper keeps only elaborated_by, so that join never reaches the store. Code that cannot carry a header citation (code the instance may not write to) then reaches every key of its application through `code_map.toml`. Today `code_map.toml` maps paths by glob and `harness/citation.py` reads a header comment line: neither parses the code.

Placement: a contract change (decision-0016), so 0.10.0 before its cut or 1.1.0 after it; the maintainer's word. Minted on the maintainer's word, 2026-11-18: "yes, mint the six knowgov tasks".
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 the contracts mapper keeps a row's file and line range as a fragment of the statements it cites
- [ ] #2 code_path (and upward.py code) lists the statements whose fragments name the path, with the ranges, beside the cited keys
- [ ] #3 who_knows --path may scope by those statements (with the G5 task)
- [ ] #4 a test on a public fixture; the scored records unchanged or re-recorded with every moved leaf accounted for; CHANGELOG line under Contract changes
<!-- AC:END -->
