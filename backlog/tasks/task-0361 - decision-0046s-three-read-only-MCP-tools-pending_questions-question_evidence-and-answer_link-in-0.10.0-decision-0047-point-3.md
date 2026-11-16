---
id: TASK-0361
title: >-
  decision-0046's three read-only MCP tools: pending_questions,
  question_evidence and answer_link (in 0.10.0, decision-0047 point 3)
status: To Do
assignee: []
created_date: '2026-11-16T19:16:00Z'
labels:
  - contract
  - 0.10.0
  - mcp
dependencies: []
references:
  - backlog/decisions/decision-0046
  - backlog/decisions/decision-0047
priority: high
ordinal: 351000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0046 point 2 names a channel-neutral bridge as three read-only MCP tools; decision-0047 point 3 brings them into 0.10.0 beside who_knows, amending decision-0046's point 4 (the pilot gate). Their schemas follow the issue form already built in a pilot instance: its fields (key, subject, scenario, owner unit, evidence, verdict, statement, note) and its four verdicts. Any MCP client can then walk a person through their questions and hand them the link; the person submits in GitHub. The server gains no write tool.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 pending_questions(handle) lists a handle's open items from the questionnaires and the captures already ingested, refusing a handle that is not issued
- [ ] #2 question_evidence(key) returns one item's evidence as the instance generated it, or a not-found reason
- [ ] #3 answer_link(key, verdict, statement) returns the prefilled issue-form URL computed from the instance's form template, writing nothing; a verdict outside the form's four is refused
- [ ] #4 Schemas for the three, both transports, check_mcp_server.py holding each, CHANGELOG Unreleased under contract changes
<!-- AC:END -->
