---
id: TASK-0185
title: >-
  arms: a call whose prompt the server cut is marked on the run, never scored
  (doc-0023 defect 1)
status: To Do
assignee: []
created_date: '2026-11-06T23:05:00Z'
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
- [ ] #1 A call in arms.call or agent.openai_responder whose reported prompt_tokens implies more characters per token than the guard's threshold is marked on the run file and shown by the page as cut, never scored as an answer
- [ ] #2 A test with a scripted usage below the sent size catches it on both paths, and a whole prompt passes
- [ ] #3 The deterministic record and the comparator are unchanged
<!-- AC:END -->
