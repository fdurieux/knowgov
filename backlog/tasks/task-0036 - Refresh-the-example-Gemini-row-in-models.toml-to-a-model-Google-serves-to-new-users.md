---
id: TASK-0036
title: >-
  Refresh the example Gemini row in models.toml to a model Google serves to new
  users
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-02T19:58:00Z'
updated_date: '2026-11-02T22:02:00Z'
labels:
  - arms
milestone: m-3
dependencies:
  - TASK-0033
references:
  - demo/models.toml
  - demo/README.md
documentation:
  - >-
    backlog/docs/doc-0006 -
    Spike-Gemini-and-Claude-rows-through-a-gateway-what-arrived.md
priority: low
type: chore
ordinal: 48000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
demo/models.toml carries a commented Gemini row naming gemini-2.5-pro. On 2026-11-02 Google's compatible endpoint answered gemini-2.5-flash with 'no longer available to new users' and pointed to gemini-3.8-flash (doc-0006); the 2.5 rows are listed by the model list but refused. Since task-0033 the Gemini agent arm works directly against Google's endpoint, so the row can become live, not only an example, for an instance whose key reaches it.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The Gemini row names a model the compatible endpoint answers for a new key, checked on the day, with its read date in a comment; its arms list both kinds now that the agent loop carries the thought signature
- [x] #2 The row's key_var names a variable the compose file passes through, and the README's model section says which key a Gemini row needs
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Probe gemini-3.8-flash on Google endpoint with JSON mode at each effort. 2. Replace the commented 2.5 row with a live row: model gemini-3.8-flash, efforts the probe accepted, key_var GEMINI_API_KEY (its own, not the shared KG_MODEL_API_KEY a gateway may use), both arms. 3. Compose passes GEMINI_API_KEY; README says which key the row needs. 4. Tests; one call through the resolved row.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Checked 2026-11-02: JSON mode holds at the API default, low, medium and high; xhigh refused (400). Resolved the row as the server does and called it through arms.call with the proxy supplying the key: gemini-3.8-flash, effort medium, prompt 17, completion 5, total 113, hidden 91, reply parsed. 106/106 both ways.
<!-- SECTION:NOTES:END -->
