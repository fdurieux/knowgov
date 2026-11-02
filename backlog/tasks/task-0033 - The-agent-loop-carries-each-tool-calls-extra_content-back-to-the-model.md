---
id: TASK-0033
title: The agent loop carries each tool call's extra_content back to the model
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-02T19:19:00Z'
updated_date: '2026-11-02T19:22:00Z'
labels:
  - arms
  - harness
milestone: m-3
dependencies:
  - TASK-0030
references:
  - harness/agent.py
  - tests/test_agent.py
documentation:
  - >-
    backlog/docs/doc-0006 -
    Spike-Gemini-and-Claude-rows-through-a-gateway-what-arrived.md
priority: medium
type: bug
ordinal: 45000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The gateway spike (task-0030, doc-0006) found that Gemini 3 attaches a thought signature to every tool call, as extra_content.google.thought_signature on the streamed tool-call delta, and refuses the next turn when the assistant message sent back lacks it: 400 Function call is missing a thought_signature. harness/agent.py openai_responder() rebuilds each tool call from id, name and arguments only, so the Gemini agent arm stops at turn 2 on every scenario. Passing the field back was shown to fix it. The field is opaque provider data: the loop keeps it as received and returns it unchanged, which other providers ignore.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 openai_responder() keeps each streamed tool call's extra_content as received, and the loop sends it back unchanged on the assistant turn it rebuilds; a call without it is sent as before
- [ ] #2 A test drives the loop with a scripted responder that refuses a second turn whose tool calls lack the extra_content it returned, and a test feeds openai_responder() a stubbed stream carrying the field
- [ ] #3 A Gemini agent run through Google's compatible endpoint gets past turn 2 on a J-F scenario; the stdlib suite is green
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. openai_responder(): keep each tool call extra_content (attribute or model_extra) as received. 2. The loop sends it back unchanged on the rebuilt assistant turn; a call without it is rebuilt as before. 3. Tests: a scripted responder that refuses a second turn without the field; a stubbed stream for the responder. 4. Live: a Gemini agent run on J-F C through Google compatible endpoint.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Live run 1 (signature only): arm B passed turn 2 and ran 6 calls to the ceiling; arm G stopped at turn 2 again for a second reason: Gemini streams parallel tool calls whole, each with its own id and index None, and the responder grouped deltas by index, so five read_document calls were glued into one (name read_documentread_document..., arguments not JSON). Fixed in the same change: a new id under the same key starts a new call; OpenAI sends the id only on a call first piece, so its grouping is unchanged. Only the first parallel call carries the signature. Live run 2: both arms 6 calls to the ceiling, 0 errors, read_document and run_suite used, 95,042 tokens. Suite 95/95.
<!-- SECTION:NOTES:END -->
