---
id: TASK-0059
title: Security pack for an enterprise pilot
status: To Do
assignee: []
created_date: '2026-11-03T22:49:00Z'
updated_date: '2026-11-03T23:54:00Z'
labels:
  - lighthouse
  - security
milestone: m-8
dependencies: []
documentation:
  - >-
    backlog/docs/doc-0012 -
    Positioning-the-governed-context-quadrant-the-market-and-the-route-to-the-top-right.md
priority: medium
type: docs
ordinal: 61000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
A regulated organisation's procurement asks for a security description before a pilot touches its systems (doc-0012 §6, OpenAI's review). The facts exist but are spread: the read-only mount, the localhost rule, the model endpoint off by default, the store holding status and provenance never content, the private instance never pushed out. A reviewer must be able to read them in one place and check each against the code.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 One adopter-register document lists the data flows of a private instance (what is read, stored, sent and to where), each with the file or setting that enforces it
- [ ] #2 It states what leaves the client's network under each model-endpoint setting, including none
- [ ] #3 It lists the dependencies and image pins with how they are kept current, and how to report a vulnerability
- [ ] #4 Every claim in it is checked by an existing or new test, or marked as a practice the operator must follow
- [ ] #5 A permission matrix: who may read, propose, approve, close, edit the model, or execute a business action (nobody), per actor (model, agent over MCP, pipeline, person by role, register approver), each enforceable row citing its test (doc-0013 P7)
<!-- AC:END -->
