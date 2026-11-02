---
id: TASK-0030
title: 'Spike: Gemini and Claude rows through a gateway'
status: Done
assignee:
  - '@claude'
created_date: '2026-11-02T13:32:00Z'
updated_date: '2026-11-02T19:03:00Z'
labels:
  - arms
milestone: m-3
dependencies:
  - TASK-0029
documentation:
  - >-
    backlog/docs/doc-0006 -
    Spike-Gemini-and-Claude-rows-through-a-gateway-what-arrived.md
priority: low
type: spike
ordinal: 40000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0005 (docs read 2026-11-02): Google's OpenAI-compatible endpoint maps reasoning_effort to thinking levels with xhigh and max unmapped and JSON mode undocumented; Anthropic's compatibility layer ignores effort, refuses json_object (the one-reply arm's mode), returns no cached-token count, and its own page calls the layer test-and-compare only. So a Claude row either goes through a gateway that translates effort per provider and holds keys server-side (LiteLLM was the candidate read), or waits. This spike runs that gateway in front of the unchanged loop, one row for each provider, both arms on one scenario with an effort set, and records what arrives. No code is merged; the session's network must reach the providers, which the hosted sessions' proxy does not, so it runs where keys and network exist.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A note in the backlog with, per provider: the usage fields that arrived (prompt, cached, completion tokens), the effort mapping the gateway applied, whether JSON mode held for the one-reply arm and tool calls for the agent loop, and the tokens spent
- [x] #2 A decision recorded in the note: a Claude row is a gateway row, or waits; the same for a Gemini row
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Ran 2026-11-02 in the hosted environment: LiteLLM 1.106.6 on localhost:4000, claude-sonnet-5-5 (KG_ANTHROPIC_KEY) and gemini-3.8-flash (network secret). Findings and the two decisions in doc-0006. Reply arms: both providers 11/11 on CargoQuote S1. Agent arm on J-F C: Claude works (no caching: 201k prompt tokens, 0 cached); Gemini fails at turn 2 on a missing thought signature, fixed when the loop passes extra_content back (shown). Decision: Gemini a direct row after that fix; Claude a gateway row with a cache mark and the upstream model named. About 370k tokens spent.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Spike done; no code merged. The note is doc-0006: per provider the usage fields that arrived, the effort mapping (LiteLLM: adaptive thinking plus output_config.effort for Claude; reasoning_effort passed through to Gemini), JSON mode (enforced on Gemini, accepted but not enforced for Claude), tool calls (Claude works; Gemini needs the thought signature carried back), tokens spent. Decisions: Gemini is a direct row once harness/agent.py carries tool-call extra_content; Claude is a gateway row, honest only with a cache mark and the upstream model named. Four follow-ups proposed in the doc, none created.
<!-- SECTION:FINAL_SUMMARY:END -->
