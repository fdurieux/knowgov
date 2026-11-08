---
id: TASK-0185
title: >-
  arms: a call whose prompt the server cut is marked on the run, never scored
  (doc-0023 defect 1)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-06T23:05:00Z'
updated_date: '2026-11-06T23:46:00Z'
labels:
  - arms
dependencies: []
references:
  - harness/arms.py
  - harness/agent.py
priority: medium
type: bug
ordinal: 185000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer accepted doc-0023's advice on 2026-11-06 ("accept the advice on all three"): fixes 1 to 4 now, as fixes, not bound by decision-0016's freeze. Ollama at its defaults (context 4096) cut an 11,877-token prompt to 2,050 tokens, answered HTTP 200 and gave a wrong reply; with OLLAMA_CONTEXT_LENGTH=32768 the whole prompt arrived. The OpenAI API carries no context-length field, so only the server can set it, and the harness sees the cut only in a low prompt_tokens. The arms' prompts are 6k to 16k tokens (CargoQuote S2: 6,213 baseline, 16,123 governed) and a J-F agent run grows to about 200k, so a private row at a server's defaults would score both arms on cut documents. The probe's ratio was 4.7 characters per token for the whole prompt and 27 for the cut one; doc-0023 proposes a mark above about 10. This guard is the precondition of the private endpoint's row.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A call in arms.call or agent.openai_responder whose reported prompt_tokens implies more characters per token than the guard's threshold is marked on the run file and shown by the page as cut, never scored as an answer
- [x] #2 A test with a scripted usage below the sent size catches it on both paths, and a whole prompt passes
- [x] #3 The deterministic record and the comparator are unchanged
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. arms.prompt_cut(chars, usage): characters sent over the larger of prompt and cached tokens; above CUT_CHARS_PER_TOKEN (10) a mark with chars, tokens, ratio and the reason; no mark when no prompt tokens are reported.
2. arms.call: the mark on the usage record (per_call), then PromptCut raised, never parsed; run.py records the cell as api_error with prompt_cut, unscored.
3. agent.run: characters of messages and tools against each turn's usage, so every responder (openai_responder included) is guarded; a cut turn stops the run, its trace says why, the result carries prompt_cut; run.py one_agent records the cell unscored.
4. The page: _run_view passes prompt_cut; the decision cell reads "prompt cut".
5. Tests: scripted usage below the sent size on arms.call (stub client) and agent.run (scripted responder); a whole prompt passes; the deterministic comparator untouched.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-06. arms.prompt_cut: characters sent over max(prompt_tokens, cached_tokens); marked above CUT_CHARS_PER_TOKEN = 10 and from CUT_MIN_CHARS = 4,000 characters (added when an existing test, a 1,619-character turn at 100 scripted tokens, read as a cut: on a small prompt the ratio is tokenizer overhead). arms.call puts the mark on its usage record (counted, in per_call) and raises PromptCut; run.py one() records an api_error cell with prompt_cut and the usage, unscored. agent.run checks every turn via sent_chars (messages, tool calls, tool definitions), so any responder is guarded; a cut turn stops the run before its tool calls run, the trace ends with the reason, the result carries prompt_cut; run.py one_agent skips the oracle and records the cell with unscored() measures. views._run_view passes prompt_cut; the run table reads "prompt cut" (expression evaluated in node: prompt cut | api error | generate | —). Real path: local Ollama 0.40.14 at its defaults, qwen3.5:0.8b, the probe's 56,093-character prompt: PromptCut, 2,050 tokens, 27.4 characters per token. A transcript or route (c) call that is cut raises from arms.call, so no proposal is made from it. Deterministic record: KG_STORE=rdflib run.py --deterministic, compare_deterministic.py: 0 differing leaves over 7 scenarios.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
A call the endpoint read short is now marked and never scored. arms.prompt_cut compares the characters sent with the prompt tokens reported (more than 10 characters per token, on 4,000 characters or more). arms.call records the mark on the call's usage and raises PromptCut; agent.run checks every turn and stops a cut run before acting on it. run.py records either as an api_error cell carrying prompt_cut, with no decision, no code and no grade, and the page's run table reads "prompt cut". Verified: scripted usage below the sent size on both paths, a whole prompt passing, the real Ollama cut caught locally, the deterministic comparator at 0 differing leaves, tests/run_tests.py 685/686 plain and 684/686 on J-F. Limit: the guard sees a cut, it cannot set the server's context length.
<!-- SECTION:FINAL_SUMMARY:END -->
