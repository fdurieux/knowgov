---
id: TASK-0254
title: >-
  A refinement-plan view: the analysis work that takes a scope's slices to the
  definition of ready, each below-bar key once with its work type, owner,
  closer, route and the slices it blocks (post-1.0, parked)
status: To Do
assignee: []
created_date: '2026-11-09T07:58:00Z'
labels:
  - proposal
  - slices
  - refinement
milestone: m-4
dependencies:
  - TASK-0252
priority: low
ordinal: 248000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From the maintainer's question of 2026-11-09 ("Could knowgov be used for planning refinement: planning the analysis work to get slices in DoR state?") and the coordinator's answer (2/4 today, 3/4 once task-0252 lands; doc-0034). knowgov has every fact but no single view: the per-slice gate findings must be grouped by owner and work type by hand, the questionnaires are per task class not per slice, and a key shared by several slices is not surfaced, though one answer can unblock several. The view, over a scope (JRN-/PRD-) or a proposal and a task class, as of a date: each key below the class's bar listed once with its work type (from its level), owner, closer, route, and the slices it blocks (its leverage); lapses due before the date; per-slice questionnaires. It composes existing reads (proposal_impact's slices and with_levels, gate findings, capture's questionnaire and due), an additive output: a post-1.0 minor (or 0.10.0). Parked until the lighthouse plans a refinement with it.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A decision with the four parts fixes the view's shape and release before any build
- [ ] #2 If built: the view lists every below-bar key of the class once, with work type, owner, closer, route and the slices it blocks, and a test on CargoQuote S2 under design and codegen holds it against the per-slice gate findings
<!-- AC:END -->
