---
id: doc-0006
title: 'Spike: Gemini and Claude rows through a gateway, what arrived'
type: specification
created_date: '2026-11-02T19:03:00Z'
updated_date: '2026-11-02T21:20:00Z'
---
*2026-11-02. Maintainer register. The note task-0030 asked for: Gemini and Claude rows behind the unchanged loop, both arm kinds, an effort set, what arrives. Probe outputs stay in the session's scratchpad, outside the repository; nothing here was merged as code.*

## Verdict

**Gemini is a direct row, after one fix to the agent loop. Claude is a gateway row.** Gemini needs no gateway: Google's OpenAI-compatible endpoint takes JSON mode, tool calls and `reasoning_effort` as the harness sends them, and the one-reply arm ran clean. Its tool loop breaks on the second turn because the loop drops the thought signature Gemini 3 attaches to each tool call; carrying that one field back fixes it (shown). Claude goes through LiteLLM, which maps effort to Anthropic's adaptive thinking and served both arm kinds, but enforces no JSON mode and adds no cache mark, so a Claude agent run resends its whole history at full price.

## Set-up

- LiteLLM 1.106.6 (`litellm[proxy]`) on `localhost:4000`, local master key, `LITELLM_LOCAL_MODEL_COST_MAP=True`, config: `claude` = `anthropic/claude-sonnet-5-5` with `api_key: os.environ/KG_ANTHROPIC_KEY`; `gemini` = `openai/gemini-3.8-flash` at `https://generativelanguage.googleapis.com/v1beta/openai/` with a placeholder key the session proxy replaces (network secret, `Authorization: Bearer`).
- Keys: Gemini as a network secret on `generativelanguage.googleapis.com`; Claude as the environment variable `KG_ANTHROPIC_KEY` (not `ANTHROPIC_API_KEY`, which the session itself reads), since `api.anthropic.com` is in the proxy's bypass list and a secret there is never applied. No key value was printed or written anywhere.
- Model names from each provider's model list on 2026-11-02: `gemini-2.5-flash` is listed but refused to new users ("no longer available to new users", pointing at `gemini-3.8-flash`); the commented Gemini row in `demo/models.toml` names a 2.5 model and is stale.
- Client: the harness venv's openai 3.41.0, streamed as `arms.call()` and `agent.openai_responder()` stream.

## What arrived, per question

| question | Claude via LiteLLM | Gemini via Google's compatible endpoint (also via LiteLLM, unchanged) |
|---|---|---|
| JSON mode, one-reply arm | accepted, **not enforced**: asked for `{"minutes": n}` it replied in prose with a fenced JSON block, which `json.loads` rejects. With the harness's own system prompt all replies parsed (S1, both arms) | enforced: every reply parsed |
| effort | `reasoning_effort` becomes `thinking: {type: adaptive, display: summarized}` plus `output_config: {effort: low/high}` (gateway debug log) | passed through as `reasoning_effort`; it changes the thinking spent (non-streamed totals 363 at low, 523 at high, same question) |
| tool calls, agent arm | work: J-F C, arm B ran 10 turns and 18 tool calls to the 10-call ceiling; arm G read 2 documents and finished | **break on turn 2**: `400 Function call is missing a thought_signature`. Each tool call carries `extra_content.google.thought_signature`; `openai_responder()` rebuilds the assistant turn without it. Passing it back: the second turn succeeds (shown through the gateway) |
| usage fields | `prompt_tokens`, `completion_tokens`, `completion_tokens_details.reasoning_tokens` (always 0 here), `prompt_tokens_details.cached_tokens`, `cache_write_tokens`; LiteLLM adds a `cost` from its own price map, which task-0027 ignores | non-streamed: thinking appears only in `total_tokens` (e.g. 37 + 114 + 212 hidden); **streamed: the thinking is in no field at all** (total 143 against 363 for the same call), so the token ceilings undercount Gemini runs |
| caching | none unless the request marks it; with an `ephemeral` cache mark the second 11.5k-token call read 11,508 tokens from cache. The harness marks nothing: the J-F B run sent 201,028 prompt tokens with 0 cached | none reported on a repeated 8.9k-token prompt |
| what the run file names | the gateway alias, `claude`, not the model behind it | `gemini` through the gateway; the real name when called directly |

## Harness runs through the gateway (effort low)

| run | Claude | Gemini |
|---|---|---|
| CargoQuote S1, one-reply, `--n 1` | B generate with assumptions, G generate; both 11/11 on the oracle; 2 calls, 42,334 tokens | B and G generate; both 11/11; 2 calls, 32,724 tokens |
| J-F C, agent, ceilings 10 calls / 600k tokens / 600 s | B abstain at the 10-call ceiling (10 calls, 18 tool calls, no file written); G abstain after reading 2 documents; 12 calls, 224,104 tokens | B and G abstain on `api error` at turn 2 (thought signature); 2 calls, 7,487 tokens |

Tokens spent, all probes and runs: about 370,000, most of it the Claude agent run's resent history.

## Decisions recorded

- **Gemini: a direct row**, `base_url` Google's compatible endpoint, `key_var` the network secret's placeholder variable or `KG_MODEL_API_KEY`, current model names, `arms = ["reply", "agent"]` once the loop carries `extra_content`. The gateway adds nothing for Gemini.
- **Claude: a gateway row.** Anthropic's own compatibility layer ignores effort and refuses `json_object` (doc-0005); LiteLLM maps effort and serves both arms. Two conditions before it is honest: the gateway adds the cache mark (LiteLLM's `cache_control_injection_points`), or the page says a Claude agent run is billed uncached; and the row names the upstream model, not the alias, in the run file.

## Follow-ups proposed (not created)

1. **The agent loop carries each tool call's `extra_content` back** (`harness/agent.py`, about ten lines, a test with a scripted responder that requires it). Unblocks the Gemini agent arm; harmless elsewhere.
2. **Usage records `total_tokens` and the hidden remainder** (total minus prompt minus completion), and the token ceilings count it, so a thinking model is not undercounted; note that streamed Gemini usage omits thinking entirely, which only a non-streamed call or Google's native usage can show.
3. **A Claude gateway row**: a `litellm` service in compose (config with the cache mark, `KG_ANTHROPIC_KEY` passed through), the row in `demo/models.toml` naming the upstream model, and the README in the adopter register.
4. **Refresh the commented Gemini row** in `demo/models.toml` to a current model.

## Correction, 2026-11-02, later (task-0034)

The usage row above says Gemini's streamed usage carries the thinking "in no field at all". That holds for the spike's streamed calls, which all went **through LiteLLM**, and not for Google's endpoint itself. Called directly and streamed, as the harness calls it since task-0033, gemini-3.8-flash reported its thinking in `total_tokens` at every effort tried: prompt 41, completion 8, total 391 at high; 45, 8, 246 at low; 45, 8, 168 at medium. So the undercount was LiteLLM rebuilding the streamed total from prompt and completion. Task-0034 therefore counts the endpoint's total against the ceilings, shows the remainder as *other tokens*, and leaves the "thinking uncounted" flag to a model row that declares it (`thinking_uncounted = true`) rather than to Google's host. The rest of this note stands.

## What was read

- LiteLLM's request to Anthropic, from its own `--detailed_debug` log, 2026-11-02.
- Google's error payloads quoted above, 2026-11-02.
- Each provider's model list, 2026-11-02.
