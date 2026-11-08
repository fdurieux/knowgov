---
id: TASK-0188
title: >-
  key check: a model listing that answers without the key reads unchecked, never
  accepted (doc-0023)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-06T23:05:00Z'
updated_date: '2026-11-06T23:54:00Z'
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
- [x] #1 A listing that answers 2xx without the key gives the verdict unchecked, with the reason, whatever it answers with the key
- [x] #2 A listing that refuses without the key and accepts with it reads accepted, and one that refuses with it reads refused, as today
- [x] #3 Tests on scripted OpenRouter-, Mistral- and Ollama-shaped listings hold the three; no new field in the page's answer
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. key_check.probe: the listing read first with a placeholder bearer that is no key; a 2xx there reads unchecked, the reason that the listing answers without a key; unreachable stays unreachable; otherwise the keyed listing as today.
2. The reason kept in the cache entry, never a new field in the page's answer.
3. Tests: loopback stand-ins shaped as OpenRouter (200 to any bearer), Mistral (401 without the key, 200 with it, 401 for a wrong one) and Ollama (200 to any bearer).
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-06. key_check.probe reads the listing first with NO_KEY ("knowgov-key-check-no-key"), a bearer no provider issues: a 2xx reads unchecked with the cache entry's "open" (the reason, never a verdict field), the key never sent; no answer reads unreachable; otherwise the keyed listing (_listing, the one OpenAI(...) call the AST test pins) as before. _why gives the reason "the endpoint lists its models without a key, so the listing says nothing of the key in VAR". Tests: real client on a loopback listing in three shapes: Mistral (401 to NO_KEY, 200 to the key: accepted; another key: refused 401), 403 and 404 to both (refused, unchecked), OpenRouter and Ollama (200 to any bearer: unchecked after one request, the key never sent); the cache verdict for an open listing carries the same fields as before. demo/README.md and docs/security.md say so in their key-check paragraphs. Two requests at most per row: the page waits WAIT_S (8 s) for checks, each request bounded by TIMEOUT_S (6 s), so a slow endpoint may still be running when the page first answers, as before.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The key check no longer reads a key as accepted on a listing open to anyone. probe() asks the endpoint first with a placeholder that is no key: a 2xx there reads unchecked, with the reason, and the key is not sent; otherwise the keyed listing decides as before (accepted, refused, unchecked). No field is added to the page's answer; the reason rides in the cache. Verified on the real model client against loopback listings shaped as OpenRouter, Mistral and Ollama; tests/run_tests.py green both ways. A row whose endpoint is open (OpenRouter, Ollama) now reads unchecked, not accepted.
<!-- SECTION:FINAL_SUMMARY:END -->
