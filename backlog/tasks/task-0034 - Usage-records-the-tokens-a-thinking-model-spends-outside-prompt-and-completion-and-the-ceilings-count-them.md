---
id: TASK-0034
title: >-
  Usage records the tokens a thinking model spends outside prompt and
  completion, and the ceilings count them
status: Done
assignee:
  - '@claude'
created_date: '2026-11-02T19:58:00Z'
updated_date: '2026-11-02T21:24:00Z'
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
- [x] #1 Every call record and agent turn carries total_tokens and the hidden remainder (total minus prompt minus completion) when the endpoint reports a total; the ceilings count total_tokens when present, prompt plus completion otherwise
- [x] #2 Where streamed usage omits the thinking, the record says so in a field the page shows, rather than a number that reads as complete; the README states the limit in the adopter register
- [x] #3 Tests cover a usage with a hidden remainder, one without a total, and a ceiling reached through hidden tokens; the stdlib suite is green
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. arms.usage_fields(): prompt, cached, completion, total when reported, hidden remainder, and the declared thinking_uncounted flag; tokens_of() counts the total when present. 2. arms.call and the agent responder use it; the agent loop accumulates hidden and counted tokens and stops on counted; trace and run usage carry them. 3. Page: other tokens column in the run and trace tables, a sentence explaining it, a sentence when thinking is uncounted; the leftover est. $ column of task-0027 removed. 4. models.toml optional thinking_uncounted per row, passed as KG_THINKING_UNCOUNTED. 5. README passage; doc-0006 correction. 6. Tests; live calls.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented. 106/106 both ways. Live, direct and streamed: gemini-3.8-flash prompt 41 completion 8 total 391 (hidden 342) at high, 45/8/246 at low, 45/8/168 at medium; gpt-5.5 at high 46/63/109, hidden 0 (OpenAI counts reasoning in completion). This overturned the spike reading that streamed Gemini omits thinking: that was LiteLLM rebuilding the total. So the flag is a model row declaration, not a host rule, and doc-0006 carries a dated correction. Also removed the est. $ column task-0027 left on agent run tables (it read 0 for every new run).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Merged as knowgov #61 on a green matrix. Usage records total and hidden tokens; the ceilings count the total; the page shows other tokens and says when a row declares thinking uncounted; the est. $ column task-0027 left is gone. Live calls showed Google streamed usage does count Gemini thinking in its total (391 against 49 at high), so the spike reading was a LiteLLM artefact: the flag is a model row declaration, and doc-0006 carries a dated correction. 106/106 both ways.
<!-- SECTION:FINAL_SUMMARY:END -->
