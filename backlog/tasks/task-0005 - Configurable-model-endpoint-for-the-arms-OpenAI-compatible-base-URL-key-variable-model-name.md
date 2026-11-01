---
id: TASK-0005
title: >-
  Configurable model endpoint for the arms: OpenAI-compatible base URL, key
  variable, model name
status: Done
assignee:
  - '@claude'
created_date: '2026-11-01T14:27:00Z'
updated_date: '2026-11-01T15:46:00Z'
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
- [x] #1 Base URL, key environment variable name and model name are instance settings; none is hard-coded
- [x] #2 Arms mode is disabled, and the page says so, when no endpoint or key is configured
- [x] #3 A run answered by a model other than the record's stays marked as a deviation and names the model on every run
- [x] #4 The demo README documents the three cases: OpenAI, Google's compatible endpoint, a private model
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/arms.py: an endpoint() reading three instance settings, KG_MODEL_BASE_URL (default OpenAI's), KG_MODEL_API_KEY_VAR (the name of the variable holding the key, default OPENAI_API_KEY) and KG_ARMS_MODEL (default the subject's record model); the client is built with base_url and the named key; enabled() is true only when the named key holds a value.
2. demo/app/server.py: arms_enabled from arms.enabled(); the scenarios API carries the endpoint (host, key variable name, model) so the page can say what it would call and why arms are off; the run's environment passes the settings through.
3. docker-compose.yml: the three settings passed through, the key under its default name and under KG_MODEL_API_KEY for a custom one.
4. demo/README.md: the three cases (OpenAI, Google's compatible endpoint, a private model behind a gateway), and that any model other than the record's is a deviation.
5. Tests: endpoint() under each configuration with no network; the page reports arms disabled and names the endpoint; the README names the three cases.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Done as planned (option 1). arms.endpoint() reads KG_MODEL_BASE_URL, KG_MODEL_API_KEY_VAR and KG_ARMS_MODEL at call time; enabled() is true only when the named variable holds a value; the OpenAI client is imported inside call() so the module loads without it (the tests job). The page's /api/scenarios carries model_endpoint (host, key variable name, model, deviation; never the key), the header chip names host and variable, the Arms button's hint names the variable, and a run request without the key is refused naming it. Compose passes the three settings plus OPENAI_API_KEY and KG_MODEL_API_KEY; a custom variable name is added to the app service by the operator (README says so). Proof: 53/53 tests; the page served under three configurations: no key (disabled, api.openai.com named), a gateway with a key (enabled, host gateway.internal:4000, model local-7b, deviation true, the key absent from the JSON), a custom key name unset while OPENAI_API_KEY is set (disabled, the custom name named); an arms run request without the key refused with the variable's name. No model was called.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The model endpoint is three instance settings: KG_MODEL_BASE_URL (default api.openai.com), KG_MODEL_API_KEY_VAR (the name of the variable holding the key, default OPENAI_API_KEY) and KG_ARMS_MODEL (default the record's model). One OpenAI-compatible client covers OpenAI, Google's compatible endpoint and a private model behind a gateway. The arms are enabled only when the named key variable holds a value, so a private instance that sets none sends nothing anywhere; the page says which variable to set, names the endpoint's host and never shows the key; any model other than the record's stays a marked deviation. Verification: 53/53 tests (settings under four configurations, no network); the page served under three configurations with the expected enabled state and endpoint view; the run endpoint refuses arms without the key.
<!-- SECTION:FINAL_SUMMARY:END -->
