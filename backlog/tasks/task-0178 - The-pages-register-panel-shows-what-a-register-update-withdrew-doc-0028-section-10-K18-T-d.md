---
id: TASK-0178
title: >-
  The page's register panel shows what a register update withdrew (doc-0028
  section 10 K18, T-d)
status: To Do
assignee: []
created_date: '2026-11-06T13:27:00Z'
labels:
  - register
  - page
dependencies: []
priority: low
type: task
ordinal: 179000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The gate reads a register change only when given the previous register (--register-previous, task-0122). The page's register panel never reads one, so a reviewer on the page cannot see what an update withdrew, deprecated or retired, nor the keys it staled (0.7.0 Known limits; no module under demo/app reads a previous register). When the instance names a previous register, the panel lists those changes as harness/register_change.py computes them. With none, it says the panel shows the current register only. Drafted by the v1.0 session (task-0173), minted under doc-0029.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 With a previous register configured, the panel lists the withdrawn, deprecated and retired nodes and links, and the keys they stale, equal to the gate's register-change block for the same pair, which a test compares
- [ ] #2 With none configured, the panel says so in one line; nothing else changes
- [ ] #3 The setting is read once at start, read-only, and a missing or unreadable path is reported on the page, not raised
- [ ] #4 The Known limit's page half is removed with its CHANGELOG line
<!-- AC:END -->
