---
id: TASK-0027
title: >-
  Prices out, tokens in: the harness counts tokens and its ceilings are tokens,
  not dollars
status: To Do
assignee: []
created_date: '2026-11-02T13:32:00Z'
labels:
  - arms
  - harness
milestone: m-3
dependencies: []
references:
  - harness/arms.py
  - harness/agent.py
  - demo/app/views.py
documentation:
  - >-
    backlog/docs/doc-0005 -
    Model-and-effort-drop-down-subject-drop-down-opportunity-canvases-and-SWOTs.md
priority: medium
type: task
ordinal: 37000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The harness prices every model at one pair of constants in harness/arms.py (the record model's list price read 2026-10-30, cached at a tenth), and cost() applies it to any model: doc-0005 found the default other model, gpt-5.5, listed at four times the input and three times the output rate, so every usd_est and both dollar ceilings (CEILING_USD in arms.py, KG_AGENT_MAX_USD in agent.py) are off by that much. The maintainer decided (2026-11-02) not to keep a price table at all, because any price goes stale and nobody refreshes it: the harness counts what the API returns (prompt, cached and completion tokens) and bounds a run by tokens, calls and seconds; the operator multiplies by what they pay, and the provider's bill is the record of cost. The record's own frozen figures (the CargoQuote pre-registration, the vendored results) are data and are not recomputed.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 No price constant and no cost function remain in the harness; per-call and per-arm records and the agent trace carry prompt, cached and completion tokens and no dollar estimate
- [ ] #2 The one-reply arm's ceiling and the agent loop's ceiling are token ceilings with the same environment-variable shape as today (a KG_ variable each, a default, the stopped_by text naming tokens), beside the unchanged call and seconds ceilings
- [ ] #3 The page shows tokens wherever it showed a dollar estimate, in controlled sentences that pass the glossary test; the vendored record is unchanged and its recorded figures still show as data
- [ ] #4 Tests cover a run stopped by the token ceiling, a run under it, and the trace totals; the stdlib suite is green
<!-- AC:END -->
