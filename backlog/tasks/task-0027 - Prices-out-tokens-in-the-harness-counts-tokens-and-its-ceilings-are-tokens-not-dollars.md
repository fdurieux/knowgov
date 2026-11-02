---
id: TASK-0027
title: >-
  Prices out, tokens in: the harness counts tokens and its ceilings are tokens,
  not dollars
status: Done
assignee:
  - '@claude'
created_date: '2026-11-02T13:32:00Z'
updated_date: '2026-11-02T13:55:00Z'
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
- [x] #1 No price constant and no cost function remain in the harness; per-call and per-arm records and the agent trace carry prompt, cached and completion tokens and no dollar estimate
- [x] #2 The one-reply arm's ceiling and the agent loop's ceiling are token ceilings with the same environment-variable shape as today (a KG_ variable each, a default, the stopped_by text naming tokens), beside the unchanged call and seconds ceilings
- [x] #3 The page shows tokens wherever it showed a dollar estimate, in controlled sentences that pass the glossary test; the vendored record is unchanged and its recorded figures still show as data
- [x] #4 Tests cover a run stopped by the token ceiling, a run under it, and the trace totals; the stdlib suite is green
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. arms.py: drop CEILING_USD, PRICE_*, cost(); add DEFAULT_CEILING_TOKENS, ceiling_tokens() (KG_ARMS_MAX_TOKENS), tokens_of(); the guard, account() and usage() count tokens; call records lose usd_est. 2. agent.py: DEFAULT_CEILING tokens 1,500,000 (KG_AGENT_MAX_TOKENS), the loop stops at prompt+completion >= tokens, no usd in totals, trace or the accounted record. 3. run.py and report.py: usage.json carries tokens; the report prints the record usd_est only as the record own figure when present. 4. views.py sentence: calls, tokens or seconds. 5. README: the agent passage, the modes table, the closing paragraph. 6. tests: test_arms token guard and no cost symbol; test_agent token ceiling and env names. 7. One real call through the proxy to see the fields.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented. Suite 91/91. One real call on gpt-5.5 through the proxy recorded {prompt 25, cached 0, completion 27, seconds 2.5}, no estimate, usage() tokens 52. Defaults: 6,000,000 tokens per process for the one-reply arms (the record 80 calls were about a third), 1,500,000 per agent run. The record frozen usd_est in results/usage.json still prints in report.py, labelled as the record own estimate.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Merged as knowgov #49 on a green matrix. The harness holds no price: tokens_of() and ceiling_tokens() (KG_ARMS_MAX_TOKENS, default 6,000,000 per process) replace cost() and CEILING_USD; the agent loop stops at KG_AGENT_MAX_TOKENS (default 1,500,000) beside calls and seconds; every record and trace carries the token counts and no estimate; the page sentence reads calls, tokens or seconds; the README says why. The vendored record is untouched and report.py prints its frozen usd_est as the record own estimate. Verified by the stdlib suite (token guard, agent token ceiling, env names) and one real call through the proxy.
<!-- SECTION:FINAL_SUMMARY:END -->
