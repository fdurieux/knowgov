---
id: TASK-0171
title: >-
  Model keys checked before the Arms drop-down offers a row: the provider's
  model listing, no tokens spent
status: Done
assignee:
  - '@claude'
created_date: '2026-11-06T12:42:00Z'
updated_date: '2026-11-06T13:01:00Z'
labels:
  - demo
  - security
dependencies:
  - TASK-0167
  - TASK-0168
priority: medium
ordinal: 172000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
On 2026-11-06 the maintainer's S1 arms run on an EC2 stack ran 93 s and failed with OpenAI's 401 'Incorrect API key': an Anthropic key had gone into OPENAI_API_KEY. A second attempt failed on the OpenAI row again while the Claude row ran. demo/app/models.py rows() marks a row available when its key variable holds a value; nothing tests the key. Maintainer's ask (2026-11-06, relayed by the coordinating session): check the keys upfront, before the drop-down offers the rows.

Design. A key check that spends no tokens: the provider's model listing, GET {base_url}/models (OpenAI-compatible; OpenAI, Google's compatible endpoint and LiteLLM all serve it), sent by the model client itself (the openai library's models.list(), max_retries=0, a short timeout) from a new harness/key_check.py, so the only outbound traffic stays the model client's to the row's own endpoint (docs/security.md, tests/test_security.py). Results: accepted (2xx), refused (401, 403), unreachable (no connection, a timeout), unchecked (no key, the check off or not yet run, any other status such as 404 or 429). The verdict carries the HTTP status and the time, never the provider's message: OpenAI's 401 body quotes part of the key. Cached per endpoint and key under a non-reversible fingerprint (HMAC-SHA256 under a per-process random secret, so it is not comparable across processes and the key is never held by the cache); rows sharing an endpoint and a key are checked once. The checks start with the page (server.main()), so the first page load usually finds them done; a page load waits a bounded time for any still in flight. POST /api/models/check re-checks, behind the page's write guard. KG_KEY_CHECK=off turns the check off (an endpoint that serves no listing, an air-gapped instance): every row reads unchecked and behaves as before.

The drop-down marks each row's verdict; a refused row is unavailable with the reason (the status and the key variable to fix), so the server refuses a run on it at once (models.resolve), and the chip counts only usable rows. An Arms run on a row not yet checked is checked first. knowgov-runs' run_options passes each row's key_check through.

The Claude row goes through the LiteLLM gateway, and the app holds only LITELLM_MASTER_KEY. The gateway's listing proves the master key only. LiteLLM's /health sends a real, paid completion upstream, so it is not used. No free check of the upstream Anthropic key through the gateway is used here: candidates (LiteLLM's /v1/messages/count_tokens forwarding to Anthropic's free token count; a pass-through route to Anthropic's GET /v1/models) are unverified against the pinned image v1.108.0 and would add configuration. The row is declared gateway = true in models.toml and reads 'gateway key accepted, upstream unchecked'.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 harness/key_check.py checks a row's key by the model client's models.list() against the row's base_url: accepted, refused (401/403), unreachable, unchecked, with the HTTP status; cached per endpoint and key by a non-reversible fingerprint, once per key, re-checkable; the key and the provider's message never logged, shown, returned or written
- [x] #2 demo/app/models.py: rows carry key_check; a refused row is unavailable with the status and the key variable to fix, so models.resolve refuses a run on it before anything runs; an optional row field gateway marks a row whose listing proves the gateway's key only, read 'gateway key accepted, upstream unchecked'; demo/models.toml's Claude row declares it
- [x] #3 demo/app/server.py starts the checks at start, a page load waits a bounded time for them, an Arms run on an unchecked row is checked first, POST /api/models/check re-checks behind the write guard; KG_KEY_CHECK=off leaves every row unchecked and as before
- [x] #4 The page's drop-down marks each row's verdict and offers a re-check; knowgov-runs run_options passes key_check through, named in the tool's description
- [x] #5 docs/security.md names the check as the model client's own traffic to the row's endpoint; tests/test_security.py's client list adds harness/key_check.py and holds that it calls models.list only
- [x] #6 Stdlib tests with stand-in responses only (no paid call, no real key): each verdict, the cache once per key and its fingerprint, re-check, a refused row refused at run start, the gateway row, the key absent from every output; with openai installed, the real client against a loopback stand-in for 200, 401, 403 and 404; harness.yml's rdflib job requires openai so it cannot skip unseen
- [x] #7 A CHANGELOG line under Unreleased; demo/README names the check, the verdicts, KG_KEY_CHECK and the gateway's limit
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/key_check.py: probe via openai models.list (lazy import), classify, Checker with fingerprint cache, ensure(parallel, bounded wait), recheck, KG_KEY_CHECK.
2. models.py: optional gateway field; rows(check=) attaches key_check, refused -> unavailable; public() carries key_check.
3. server.py: model_rows ensures then reads; main() enables and warms; start() checks the chosen row first; POST /api/models/check.
4. index.html: verdict in option and #am-why; re-check link. mcp_runs: key_check in model_rows, description.
5. docs/security.md, test_security CLIENTS; tests/test_key_check.py; harness.yml KG_TEST_REQUIRE openai; _skip doc.
6. models.toml gateway = true on the Claude row; demo/README; CHANGELOG.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-06 evidence.
- AC1: harness/key_check.py probe() is openai's models.list() (max_retries=0, 6 s); APIStatusError 401/403 refused, other statuses unchecked with the status, connection or timeout unreachable; the exception's text is never kept. Checker caches by (base_url, HMAC-SHA256 of the key under a per-process secret); in-flight checks are joined; recheck; KG_KEY_CHECK=off. tests/test_key_check.py: verdicts, once per endpoint and key, re-check, a changed key re-checked, the fingerprint is not a plain digest, no key in the cache.
- AC2: models.rows(check=) attaches key_check; refused means unavailable, with the status and the variable; resolve(check=) refuses. Optional field gateway; the Claude row in demo/models.toml declares it. Test: the record's row and both OpenAI rows on one refused key give one request, all three unavailable; Gemini accepted; Claude gateway-scoped.
- AC3: server.main() enables the checker and starts the checks without waiting; model_rows() waits at most 8 s for checks in flight; Runner.start checks before resolve, and the test proves the 401 refusal comes before any run folder exists; POST /api/models/check is behind write_guard, like every POST. Without main(), every row reads unchecked and behaves as before (test).
- AC4: index.html marks each available option (key accepted / gateway key accepted, upstream unchecked / endpoint unreachable), greys a refused one with the reason, adds a status line and a 're-check keys' button. mcp_runs run_options passes key_check; the description and the docstring name it. Live on a local page (rdflib, loopback stand-in endpoints: 200, 401 and a gateway row) with Playwright: the options as described, the refused row disabled, the re-check sent one GET per endpoint and stamped a new time. The key appears in neither log.
- AC5: docs/security.md has a new flows row and the outbound row names the check; tests/test_security.py CLIENTS adds harness/key_check.py; test_the_check_is_the_model_clients_listing_and_nothing_else holds models.list as the only client call, no retry, no print or logging, no /health.
- AC6: the real openai 3.41.0 client against a loopback stand-in: 200 accepted, 401 and 403 refused, 404 unchecked, a closed port unreachable; exactly one GET /v1/models each, the key as a bearer token, and nothing of the key or of the provider's message in the verdict. Prerequisite openai, added to harness.yml rdflib's KG_TEST_REQUIRE. Suite: stdlib 609/631, 22 skipped, 0 failed; with the pins (rdflib, pyshacl, pumllint, openai) and KG_TEST_REQUIRE=rdflib,node,openai, 630/631, 1 skipped (hook-live), 0 failed.
- AC7: CHANGELOG Unreleased > Changes line; demo/README 'Which model the Arms mode calls' and the HTTP-surface paragraph; compose passes KG_KEY_CHECK (default on) and documents it.
- Gateway: no free upstream check is used. LiteLLM /health makes a paid completion. LiteLLM's /v1/messages/count_tokens (Anthropic's free token count) and a configured pass-through to Anthropic's GET /v1/models are untested against image v1.108.0. They are a possible follow-up, not built.

2026-11-06, relayed by the coordinator: on the maintainer's EC2 stack, the value in OPENAI_API_KEY was not an OpenAI secret key at all (no sk- prefix). A prefix-shape warning was suggested; it was not added. The listing check refuses such a key at start, at no cost; a prefix rule would read the key's text and keep provider-specific shapes (Google's and LiteLLM's keys have no fixed prefix).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The page now checks each model row's key before the Arms drop-down offers the row, and spends no tokens doing it. When the page starts, harness/key_check.py asks each row's endpoint for its model listing through the model client (openai models.list(), no retry). Each endpoint and key is asked once, cached under a per-process HMAC fingerprint. The verdicts are accepted, refused (401/403), unreachable, or unchecked; only the verdict, the HTTP status and the time are kept. A refused row is greyed with the status and the key variable, and an Arms run on it is refused at once by models.resolve, before any run folder exists. This is the 2026-11-06 failure: a wrong OPENAI_API_KEY cost a 93 s run that ended in a 401. A 're-check keys' button (POST /api/models/check, behind the write guard) asks again. KG_KEY_CHECK=off sends nothing. knowgov-runs' run_options carries each row's key_check. The Claude row, gateway = true, reads 'gateway key accepted, upstream unchecked'. The listing proves LITELLM_MASTER_KEY only; /health would be a paid call, so the Anthropic key is first tested by a run. docs/security.md and tests/test_security.py name the check as the model client's own traffic to the row's endpoint. Tests use stand-ins only: a stand-in probe, and the real client against a loopback listing, which harness.yml's rdflib job now requires. Follow-up candidate, not built: a free upstream check through LiteLLM (count_tokens or a pass-through), once verified against the pinned image.
<!-- SECTION:FINAL_SUMMARY:END -->
