---
id: TASK-0346
title: AuraDB Free as a documented, probed target (decision-0042)
status: To Do
assignee: []
created_date: '2026-11-15T09:29:00Z'
labels:
  - neo4j
  - docs
  - probe
dependencies:
  - TASK-0345
references:
  - backlog/decisions/decision-0042
priority: low
ordinal: 338000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0042 (accepted 2026-11-15) adds AuraDB Free as a shared, cloud-reachable demo target after Neo4j Desktop. It is gated: the maintainer creates the instance, rules on which data may live in a third-party cloud (public subjects only by default; never a client instance), and the session's environment gets the instance's exact host on its allowlist and its credential through the environment's credential form, never in chat. Then the Desktop runbook runs with a neo4j+s:// URI.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The maintainer has created the instance and ruled on which data may live there, recorded in the task's notes
- [ ] #2 The runbook runs against the instance: the snapshot checks, the deterministic run and comparator, and the saved queries, with D1 reported apart; Aura-specific limits (pausing, caps, TERMINATE TRANSACTIONS privilege, the memory-settings read) are measured and recorded
- [ ] #3 instance/README.md's section names Aura's URI form and its measured limits; no contract moves
<!-- AC:END -->
