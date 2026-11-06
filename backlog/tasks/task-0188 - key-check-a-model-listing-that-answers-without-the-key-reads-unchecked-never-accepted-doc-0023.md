---
id: TASK-0188
title: >-
  key check: a model listing that answers without the key reads unchecked, never
  accepted (doc-0023)
status: To Do
assignee: []
created_date: '2026-11-06T23:05:00Z'
labels:
  - arms
  - page
dependencies: []
references:
  - harness/key_check.py
priority: medium
type: bug
ordinal: 188000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer accepted doc-0023's advice on 2026-11-06 ("accept the advice on all three"). The page's key check (task-0171, harness/key_check.py probe) reads GET {base_url}/models and calls any 2xx accepted. Measured on 2026-11-06 with an invalid bearer, at no cost: https://openrouter.ai/api/v1/models answered 200, so an OpenRouter row would read key accepted whatever its key; https://api.mistral.ai/v1/models answered 401, so a Mistral row's check holds; Ollama's /v1/models answers 200 with any bearer, which proves reachability only. doc-0023 proposes probing the listing once without the key: a 200 there says nothing of the key. A fix in key_check.py, no new field. OpenRouter waits on it for the maintainer's study.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A listing that answers 2xx without the key gives the verdict unchecked, with the reason, whatever it answers with the key
- [ ] #2 A listing that refuses without the key and accepts with it reads accepted, and one that refuses with it reads refused, as today
- [ ] #3 Tests on scripted OpenRouter-, Mistral- and Ollama-shaped listings hold the three; no new field in the page's answer
<!-- AC:END -->
