---
id: TASK-0084
title: >-
  Keep the CI jobs short: a J-F scenario subset where the round trip and the
  rehearsal run
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-04T00:44:00Z'
updated_date: '2026-11-04T02:09:00Z'
labels:
  - ci
milestone: m-6
dependencies: []
priority: low
ordinal: 88000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The Turtle round trip (task-0070) added about 7 minutes to stack and the lighthouse rehearsal (task-0069) about 7 to rdflib, most of it J-F. Every PR waits on these jobs.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 stack and rdflib each run under a stated budget with J-F on a named subset, the full set kept in a scheduled or release run
- [ ] #2 The subset and the full run are both named in harness.yml/demo.yml and in CLAUDE.md
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Time J-F per scenario: about 80 s round trip and 65 s MCP each on rdflib, all six alike, so two of six is a third of the time.
2. One value, KG_JF_SCENARIOS=C,D3 (control PROCEED; every layer wrong QUALIFIED), set at job level in harness.yml and demo.yml on pull_request, empty otherwise; the J-F round trip and MCP checks pass it.
3. Full set: push to main, a nightly schedule (03:17 UTC), workflow_dispatch; a release is cut from main. The J-F record comparison and oracle stay full.
4. Budget: 12 minutes for rdflib and stack on a PR, in both workflow headers and CLAUDE.md; tests/test_ci_subset.py holds it.
5. The lighthouse rehearsal (task-0069, #124) is not on main yet: once it lands, its J-F part takes the subset too (a follow-up if it lands after this PR).
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Lighthouse (task-0069, #124) landed during #133's run: its step took 291 s and passed only because the composite action's setup writes KG_TODAY to GITHUB_ENV earlier in the job. Follow-up PR: lighthouse_evidence pins each child to its subject's record date, takes --only SUBJECT=IDS, the rdflib job passes the J-F subset; tests/test_clock.py now scans every tool, not only check_*.
<!-- SECTION:NOTES:END -->
