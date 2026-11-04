---
id: TASK-0122
title: >-
  A register change invalidates: deprecated nodes and withdrawn links mark what
  rests on them stale or suspect
status: To Do
assignee: []
created_date: '2026-11-04T18:33:00Z'
labels:
  - register
  - gate
milestone: m-8
dependencies: []
priority: medium
type: feature
ordinal: 122000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From the doc-0011 fit-gap (2026-11-04): a register change re-projects but invalidates nothing, so the gate never sees it (doc-0011 §4, 'Change propagation'). A source-document change reaches the gate today (S6); a register change does not. register_impact (task-0111) reports what retiring a node would touch, read-only; nothing records it when it happens. At a re-vendor (or an instance's register update), compare the register with the previous vendored tag; for every node that became deprecated or retired and every link withdrawn, mark the statements resting on it stale (reason: the register's decision record) and the derived outputs that used them suspect; surface them as gate findings the way a source change does. 'Resting on' follows the map rows plus the register's walk under ieam-register decision 0016 (descent below a withdrawn node, start never counted, the walk named). Depends on 0016 being approved and tagged (v0.2.9).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A fixture register change (CAP-0001 deprecated with its children moved, one link withdrawn) marks the statements on the affected keys stale with the decision as reason, and the S1 derived output suspect; the gate reports them as findings and exits 1
- [ ] #2 A register update with no state change invalidates nothing; the record and the comparator are unchanged
- [ ] #3 Both adapters agree; the Turtle round trip carries the new staleness; the CHANGELOG names it under Unreleased
<!-- AC:END -->
