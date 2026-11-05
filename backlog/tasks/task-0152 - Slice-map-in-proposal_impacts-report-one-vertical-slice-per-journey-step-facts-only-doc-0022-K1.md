---
id: TASK-0152
title: >-
  Slice map in proposal_impact's report: one vertical slice per journey step,
  facts only (doc-0022 K1)
status: To Do
assignee: []
created_date: '2026-11-05T22:38:00Z'
labels: []
dependencies: []
priority: medium
type: feature
ordinal: 159000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0022 (initiative slicing): knowgov reads an initiative and gates the board; it does not hold the backlog, the ranking or the estimates. proposal_impact already gives the intake read of a proposed addition; grouping its report into slices makes it the story map's backbone: per journey step, the thread step → process → capability → application → entity, from the register's own walks. It waits on doc-0022 K2, the register's thread walk and product–journey alignment rule (an ieam-register decision), being approved and vendored, so knowgov composes no second walk semantics. Maintainer's go, 2026-11-05: K1 after K2 is vendored, below task-0141 and the lighthouse prerequisites; slices by journey step, by end-to-end process for a product no journey concerns; facts only.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 After the ieam-register tag carrying doc-0022 K2 is vendored, proposal_impact's report gains a slices section built from the register's thread walk: one slice per journey step, or per end-to-end process for a product no journey concerns
- [ ] #2 Every overlay element appears in exactly one slice or in a named remainder (for example a capability the product requires that no step reaches, an enabler), with the denominator shown
- [ ] #3 Facts only: no planning label (walking skeleton, MVP, priority), no estimate, no rank; additive schema change, CHANGELOG Unreleased carries the line
- [ ] #4 Tested on doc-0017's worked example and on the approved register (PRD-0002's CAP-0003 reached by no step; PRD-0005 with no journey)
<!-- AC:END -->
