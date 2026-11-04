---
id: TASK-0084
title: >-
  Keep the CI jobs short: a J-F scenario subset where the round trip and the
  rehearsal run
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-04T00:44:00Z'
updated_date: '2026-11-04T02:27:00Z'
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
- [x] #2 The subset and the full run are both named in harness.yml/demo.yml and in CLAUDE.md
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

Measured on pull-request heads. stack: 12.5 min before, 7.7 min (#133) and 8.0 min (#134) after. rdflib: 16.4 min before (982 s, without the rehearsal). After: 14.0 min on #133's head, with the rehearsal still full at 291 s. #134's head took 16.8 min with the rehearsal on the subset at 193 s, but every step ran about 1.5x slower there than on #133's runner (round trip 117 -> 182 s, J-F record comparison 80 -> 135 s, both unchanged). Scaled to #133's runner it is about 11 min. The 12-minute budget holds for stack. It holds for rdflib only at #133's runner speed, so AC #1 stays unchecked until a typical run shows it. The remaining time is CargoQuote's full round trip, MCP and rehearsal, plus the full J-F record comparison and oracle.
<!-- SECTION:NOTES:END -->
