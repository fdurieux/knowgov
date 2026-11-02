---
id: TASK-0030
title: 'Spike: Gemini and Claude rows through a gateway'
status: To Do
assignee: []
created_date: '2026-11-02T13:32:00Z'
labels:
  - arms
milestone: m-3
dependencies:
  - TASK-0029
documentation:
  - >-
    backlog/docs/doc-0005 -
    Model-and-effort-drop-down-subject-drop-down-opportunity-canvases-and-SWOTs.md
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
- [ ] #1 A note in the backlog with, per provider: the usage fields that arrived (prompt, cached, completion tokens), the effort mapping the gateway applied, whether JSON mode held for the one-reply arm and tool calls for the agent loop, and the tokens spent
- [ ] #2 A decision recorded in the note: a Claude row is a gateway row, or waits; the same for a Gemini row
<!-- AC:END -->
