---
id: TASK-0005
title: >-
  Configurable model endpoint for the arms: OpenAI-compatible base URL, key
  variable, model name
status: To Do
assignee: []
created_date: '2026-11-01T14:27:00Z'
updated_date: '2026-11-01T14:30:00Z'
labels:
  - platform
  - model
milestone: m-1
dependencies:
  - TASK-0001
priority: medium
type: feature
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
arms.py opens the OpenAI client with one key and calls chat completions; the provider is fixed and only the model name is configurable through KG_ARMS_MODEL. Option 1 of the re-evaluation (2026-11-01): one OpenAI-compatible endpoint configured by address covers OpenAI, Google's compatible endpoint and a private model behind vLLM, Ollama, LiteLLM or a gateway. A private instance's content must go only where its configuration says, so arms are off until an endpoint is set.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Base URL, key environment variable name and model name are instance settings; none is hard-coded
- [ ] #2 Arms mode is disabled, and the page says so, when no endpoint or key is configured
- [ ] #3 A run answered by a model other than the record's stays marked as a deviation and names the model on every run
- [ ] #4 The demo README documents the three cases: OpenAI, Google's compatible endpoint, a private model
<!-- AC:END -->
