---
id: TASK-0179
title: >-
  The Claude row's upstream Anthropic key checked through the gateway at no
  cost, or a recorded reason why not (follow-up to task-0171)
status: To Do
assignee: []
created_date: '2026-11-06T14:01:00Z'
labels:
  - demo
  - security
dependencies: []
priority: low
type: task
ordinal: 180000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
task-0171 checks each row's key by its endpoint's model listing. Behind the LiteLLM gateway (gateway = true) that proves only LITELLM_MASTER_KEY, so the row reads 'gateway key accepted, upstream unchecked', and KG_ANTHROPIC_KEY is first tested by a paid run. LiteLLM's /health is not usable: it sends a real completion. Two candidates, neither yet tried against the pinned image (ghcr.io/berriai/litellm v1.108.0): (a) LiteLLM's /v1/messages/count_tokens, if it forwards to Anthropic's free token-count endpoint with the configured key; (b) a pass-through route in demo/litellm/config.yaml to Anthropic's GET /v1/models with x-api-key from os.environ/KG_ANTHROPIC_KEY, if pass-through routes are available without a licence in that version. Verify first, against the pinned image with a deliberately invalid KG_ANTHROPIC_KEY; then use the one route that is free, reaches Anthropic and returns 401 for a bad key. If neither qualifies, record why in the task and change nothing. Drafted by the task-0171 session; minted by the coordinator under doc-0029, low priority, not started.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Each candidate is tried against the pinned image (compose --profile claude) with an invalid upstream key and with no key; the task records the request, the status and whether Anthropic was reached and billed, read from Anthropic's side (count_tokens and the models listing are documented as free); no valid key is used in CI
- [ ] #2 If a route qualifies, harness/key_check.py gains a second probe for gateway rows, still the model client's own traffic to the row's own base URL; the row's verdict carries an upstream state (accepted, refused, unreachable, unchecked) beside the gateway's; a refused upstream greys the row like a refused key; models.toml documents how a gateway row names its upstream check
- [ ] #3 If no route qualifies, the task's notes say why per candidate and the row keeps 'gateway key accepted, upstream unchecked'; no code changes
- [ ] #4 Tests use stand-in responses only; the stack job, which has no KG_ANTHROPIC_KEY, asserts the upstream state is unchecked and that nothing was sent
- [ ] #5 A CHANGELOG line under Unreleased, and demo/README's gateway paragraph updated, only if behaviour changes
<!-- AC:END -->
