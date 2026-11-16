---
id: TASK-0362
title: >-
  Re-vendor the register at the ieam-register tag that carries decision 0021's
  person field
status: To Do
assignee: []
created_date: '2026-11-16T19:16:00Z'
labels:
  - 0.10.0
  - register
dependencies: []
priority: medium
ordinal: 352000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0047 point 7: who_knows resolves a handle to its holder through the register's person field (ieam-register decision 0021). knowgov vendors the register at a tag; the tag that carries the person field and its check is published by the owner after ieam-register's build merges.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 demo/register is re-vendored with tools/vendor_register.py at that tag, SOURCE.md rewritten, the digest test green
- [ ] #2 who_knows on the example instance shows holder null with why for the synthetic handles, which carry no person
<!-- AC:END -->
