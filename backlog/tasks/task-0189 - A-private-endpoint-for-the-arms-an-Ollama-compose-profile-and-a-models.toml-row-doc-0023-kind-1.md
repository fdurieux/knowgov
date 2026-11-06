---
id: TASK-0189
title: >-
  A private endpoint for the arms: an Ollama compose profile and a models.toml
  row (doc-0023 kind 1)
status: To Do
assignee: []
created_date: '2026-11-06T23:05:00Z'
labels:
  - arms
  - models
  - contract
dependencies:
  - TASK-0185
references:
  - demo/models.toml
  - docs/security.md
priority: low
type: feature
ordinal: 189000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer accepted doc-0023's advice on 2026-11-06 ("accept the advice on all three"): offer endpoint kinds, not vendor rows, and kind 1 first: a private endpoint (Ollama, or vLLM where a GPU host serves several users) serving open weights (Qwen, Mistral Small 4, gpt-oss). It is the only kind that keeps an instance's content inside its network (task-0013), and the only one doc-0023 measured with both arm kinds through the harness's own code. docs/security.md's endpoint table asserts the private row; it was never run before that probe. Accepted conditions: task-0185's guard first; the server's context length named in the profile and the README; the efforts each model accepts listed in its row; a GPU host stated as the operator's (CPU thinking took 116 to 444 s per reply); and no doc calls the route proven before a vLLM probe on a GPU host, thinking across tool turns included. A row and the profile change demo/models.toml and the page's /api/* lists: under decision-0016 they join the 0.9.0 gathering only if built before doc-0028's G9 is met, never holding 0.9.0 for them, else 0.10.0.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A compose profile serves the private endpoint with OLLAMA_CONTEXT_LENGTH set, and a demo/models.toml row names it with the efforts its model accepts
- [ ] #2 instance/README.md and docs/security.md name the context length, state the GPU host as the operator's, and say the route is not proven before a vLLM probe
- [ ] #3 A run through the row on a public subject is marked a deviation, and task-0185's guard marks a cut prompt there
- [ ] #4 Its release follows decision-0016: the 0.9.0 gathering if built before G9 is met, else 0.10.0
<!-- AC:END -->
