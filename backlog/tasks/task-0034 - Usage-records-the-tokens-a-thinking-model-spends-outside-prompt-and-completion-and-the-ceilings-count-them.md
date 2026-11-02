---
id: TASK-0034
title: >-
  Usage records the tokens a thinking model spends outside prompt and
  completion, and the ceilings count them
status: To Do
assignee: []
created_date: '2026-11-02T19:58:00Z'
labels:
  - arms
  - harness
milestone: m-3
dependencies:
  - TASK-0030
references:
  - harness/arms.py
  - harness/agent.py
documentation:
  - >-
    backlog/docs/doc-0006 -
    Spike-Gemini-and-Claude-rows-through-a-gateway-what-arrived.md
priority: medium
type: feature
ordinal: 46000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The gateway spike (doc-0006) measured a gap between what a model bills and what the harness counts. Gemini's non-streamed usage puts its thinking only in total_tokens (37 prompt + 114 completion + 212 hidden on one question at low effort, 372 hidden at high), and its streamed usage, which is how arms.call() and the agent loop call, carries the thinking in no field at all (total 143 against 363 for the same call). Since task-0027 the token ceilings sum prompt and completion tokens only, so a thinking model is undercounted and can run past the ceiling the operator set. Claude via LiteLLM reports completion_tokens_details.reasoning_tokens as 0 and counts thinking inside completion_tokens, so it is not affected the same way.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Every call record and agent turn carries total_tokens and the hidden remainder (total minus prompt minus completion) when the endpoint reports a total; the ceilings count total_tokens when present, prompt plus completion otherwise
- [ ] #2 Where streamed usage omits the thinking, the record says so in a field the page shows, rather than a number that reads as complete; the README states the limit in the adopter register
- [ ] #3 Tests cover a usage with a hidden remainder, one without a total, and a ceiling reached through hidden tokens; the stdlib suite is green
<!-- AC:END -->
