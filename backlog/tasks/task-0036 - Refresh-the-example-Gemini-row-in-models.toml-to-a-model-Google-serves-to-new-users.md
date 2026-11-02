---
id: TASK-0036
title: >-
  Refresh the example Gemini row in models.toml to a model Google serves to new
  users
status: To Do
assignee: []
created_date: '2026-11-02T19:58:00Z'
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
- [ ] #1 The Gemini row names a model the compatible endpoint answers for a new key, checked on the day, with its read date in a comment; its arms list both kinds now that the agent loop carries the thought signature
- [ ] #2 The row's key_var names a variable the compose file passes through, and the README's model section says which key a Gemini row needs
<!-- AC:END -->
