---
id: doc-0023
title: >-
  Model endpoints for the arms: self-hosted, Mistral, OpenRouter, Jev; two
  harness defects. A probe, fit/gap, opportunity canvas, SWOT, proposals
type: specification
created_date: '2026-11-05T23:02:00Z'
updated_date: '2026-11-06T17:44:00Z'
tags:
  - arms
  - models
  - spike
  - security
  - canvas
  - swot
  - fit-gap
---
*2026-11-05. Maintainer register. The study the maintainer asked for: which other models should be offered to run the arms (Mistral, Qwen, Jev named), and where else in knowgov such models could serve. One local probe through the harness's own code, desk research against primary sources where they exist; no hosted model call and no valid key; public model listings read without a key or with an invalid bearer, at no cost (OpenRouter's, the inventory and the fourth finding; Mistral's and Alibaba's international endpoint's, both 401); nothing under `results/` or `runs/`, raw outputs in the session's scratch directory. Every run on a model other than the record's is a deviation. Nothing is built; no task, no models.toml row, no harness change. Every follow-up is a proposal.*

*Revised 2026-11-06: the four parts the record now asks of a decision put to the maintainer (fit/gap, opportunity canvas, SWOT, advice); what decision-0016's freeze means for the advice; one key-check finding, measured on two public model listings with an invalid bearer and no cost. Code references re-read at `8f5edd5`.*

## Verdict

**Offer three endpoint kinds, not one row per vendor, and fix two defects first.** (1) A private endpoint, Ollama or vLLM inside the instance's network, serving open weights (Qwen, Mistral Small 4, gpt-oss): the only kind a bank's instance can point at its own content, asserted by the private-endpoint row of `docs/security.md`'s endpoint table and never run until this probe. (2) Mistral's API, the hosted EU option. (3) OpenRouter, for the maintainer's cross-family study on the public subjects only. Qwen fits kind (1) as open weights better than Alibaba's cloud. **Jev (TypeSafe AI) cannot serve the arms**: it generates no text, code or tool call; it is a candidate for typed classification elsewhere, US-hosted. The two defects: Ollama cuts a prompt beyond its context silently (HTTP 200, a wrong answer), and a Mistral reply at `reasoning_effort` high would raise TypeError in `arms.call` and `agent.openai_responder`. Both are fixes, outside decision-0016's freeze; adding endpoint kinds to `demo/models.toml` is treated here as a contract change, so it gathers for 0.9.0 or waits for 0.10.0.

## What the arms need from an endpoint

From `harness/arms.py` and `harness/agent.py`, probed at `506b9a5` and re-read at `8f5edd5`: OpenAI chat completions, streamed with `stream_options.include_usage`; `response_format: json_object` (one-reply arm); `tools` with `tool_choice: auto` over many turns (agent arm); `reasoning_effort` only when a row names one; `delta.content` a string, concatenated by `"".join(parts)`. A row lists the efforts its model accepts (`demo/models.toml`). The session proxy cuts a reply silent for 30 s (task-0140's amendment). Since task-0141.05 (X1, decision-0012) the agent arm's `run_suite` executes model-written code only in the no-network worker; the model call stays in the app, so a private endpoint is reached from the app's network, not the worker's.

## Probe: the private endpoint, through the harness's own code

Set-up: Ollama 0.40.14 on CPU (4 cores, no GPU) in the session container; `arms.call()` and `agent.run()` imported unchanged from `harness/`, openai 3.41.0 as pinned; `KG_MODEL_BASE_URL=http://127.0.0.1:11434/v1`, a placeholder key; toy prompts (a one-line document, a four-tool task over a temporary sandbox whose suite only reads the written file; no model-written code executed). Models: `qwen3.5:2b`, `qwen3.5:0.8b`, `ministral-3:3b`.

| | qwen3.5:2b | ministral-3:3b |
|---|---|---|
| one-reply, JSON mode | parsed at effort "", none, low, high | parsed at "" and none; high: `400 "ministral-3:3b" does not support thinking` |
| streamed usage | arrives; thinking counted in `completion_tokens` (2,182 to 2,596 with thinking on, 27 at none), `hidden_tokens` 0; `cached_tokens` reported (82 to 84) | arrives |
| effort | none turns thinking off; low and high changed little (2,182 against 2,534) | none accepted |
| agent loop (effort none) | read_document, write_file, run_suite, finish: 4 turns, finished | the same 4 turns, finished |
| time | thinking on: 116 to 144 s per reply (0.8b: 444 s); none: 1.5 to 1.7 s | 2 to 6 s |

The probe ran `arms.call()` and `agent.run()` directly, outside the worker: its toy suite read the written file and executed nothing.

Not run: thinking on across a multi-turn agent run (stopped: minutes per turn on CPU), gpt-oss (13 GB), the public subjects' arms, any model call to a hosted Mistral, Qwen or OpenRouter endpoint (no valid key, no go).

## Defect 1: Ollama cuts a long prompt silently

Reproduction: Ollama at its defaults (`ollama ps` showed CONTEXT 4096); `arms.call()` with a 56,145-character prompt (the fact first, then filler), effort none, `qwen3.5:0.8b`. The server logged `msg="truncating input prompt" limit=2050 prompt=11877 keep=4 new=2050`, answered HTTP 200, usage `prompt_tokens` 2,050, reply `{"valid": true}`: the system prompt and the fact were cut. Restarted with `OLLAMA_CONTEXT_LENGTH=32768`: `prompt_tokens` 11,877, reply `{"decision": "generate", "minutes": "30"}`.

Why it matters: the arms' prompts are 6k to 16k tokens (CargoQuote S2: 6,213 baseline, 16,123 governed) and a J-F agent run grows to about 200k. An Ollama row at its defaults would score both arms on cut documents, and the run file would show nothing but a low `prompt_tokens`. The OpenAI API carries no context-length field, so the harness cannot set it; only the server can.

Proposed: a guard in `arms.call` and `openai_responder` that marks a call whose reported `prompt_tokens` is far below what was sent (characters per token above about 10; here 4.7 whole, 27 cut), recorded on the run and shown by the page, never scored silently; and `OLLAMA_CONTEXT_LENGTH` named wherever a private row is documented.

## Defect 2: Mistral's thinking chunks break the string join

Mistral's reasoning page: at `reasoning_effort` high, `message.content` is a list (a `thinking` chunk, then a `text` chunk), and streamed `delta.content` is a list during the thinking, then a string. The lines, at `8f5edd5`: `harness/arms.py:176` and `:193`, `harness/agent.py:215` and `:238`. Reproduction against the pinned SDK, no API call: `openai._models.construct_type` on a chunk whose `delta.content` is `[{"type": "thinking", ...}]` keeps the list; `"".join([that, "{}"])` raises `TypeError: sequence item 0: expected str instance, list found`. In `arms.call` the join follows the stream and the exception reaches `run.py`; in `openai_responder` it ends the agent run as `api error`. At effort none Mistral documents a plain string. Not verified against Mistral's API.

Proposed: keep the text chunks and drop the thinking ones before the join (about ten lines and a scripted-stream test, in the shape of task-0033), or a Mistral row limited to effort none.

## A third finding, smaller

`arms.call` retries every exception four times with 5, 10 and 15 s waits: the 400 for an effort the model refuses cost 30 s and four requests. Proposed: retry 429, 5xx and network errors only.

## A fourth finding: a model listing that accepts any key

The page's key check (task-0171, `harness/key_check.py` `probe`) reads `GET {base_url}/models` and calls any 2xx `accepted`. Measured 2026-11-06 with an invalid bearer and no cost: `https://openrouter.ai/api/v1/models` answered 200, so an OpenRouter row would read "key accepted" whatever its key; `https://api.mistral.ai/v1/models` answered 401, so a Mistral row's check holds; Ollama's `/v1/models` answered 200 with any bearer, which is right for a server that holds no keys, and proves reachability only. Proposed: probe the listing once without the key; a 200 there means the listing says nothing of the key, and the verdict reads `unchecked`. A fix in `key_check.py`, no new field.

## The endpoint kinds

| Kind | Models (read 2026-11-05) | Fit with the loop | Before a row is honest |
|---|---|---|---|
| **1. Private: Ollama or vLLM in the network** | Qwen 3.6 and 3.8 27B-class open weights; Mistral Small 4 (Apache 2.0); gpt-oss-120b and 20b (Apache 2.0) | shown above for both arm kinds | defect 1's guard and the server's context length; efforts per model; a GPU host (thinking on CPU costs minutes per call, and `KG_AGENT_MAX_SECONDS` 1500 ends a run in a few turns); a compose profile like `claude`, which turns the private-endpoint row of `docs/security.md` from a practice into evidence; the page's key check (task-0171) reads the endpoint's model listing, not tried against Ollama here |
| **2. Mistral API, `api.mistral.ai/v1`** | `mistral-medium-3-5` and `mistral-small-2603` (effort none or high only), `mistral-large-4-0` (low, medium, high); the same platform serves `zai-glm-5-3` and DeepSeek V4.1 Flash | JSON mode, tools and streamed usage documented; effort high breaks the join (defect 2) | defect 2's fix or effort none only; a spike with a key in doc-0006's shape; data terms read from Mistral's own DPA (EU processing by default and about 30 days' retention are reported by third parties only) |
| **3. OpenRouter, the maintainer's study only** | deepseek-v4.1-flash, glm-5.3, kimi-k3, qwen3.8-max, mistral-large-4-0 | its public model list marks tools, `response_format` and reasoning for each | public subjects only: it routes to upstream providers an instance does not choose; `thinking_uncounted` measured as task-0034 did for LiteLLM |
| Qwen through Alibaba Model Studio, Frankfurt (`{WorkspaceId}.eu-central-1.maas.aliyuncs.com/compatible-mode/v1`) | `qwen3.8-max`, `qwen3.8-flash`, `qwen3.8-27b` | `reasoning_effort` documented for the qwen3.8 family (not together with `thinking_budget`); thinking in `reasoning_content`, which the harness ignores; older Qwen switches thinking only by `enable_thinking`, which the harness never sends; no forced tool choice in thinking mode (the loop uses auto) | region-bound keys and model lists; JSON mode with thinking on undocumented; a bank's vendor review. Ranked below kind 1 for Qwen |

Not worth a row: Devstral (retired from Mistral's API on 2026-07-31), Codestral 25.08 (a completion model), Llama (the newest on OpenRouter's list is Llama 4, 2025-04).

## Jev, TypeSafe AI

Read against TypeSafe's own site, docs, models page, request rules, privacy policy, terms and enterprise page; no call (an early-access key is needed) and no local run (no weights).

| Question | Finding |
|---|---|
| Weights | None published; the terms license the site only; Ollama or vLLM cannot serve it. The enterprise FAQ asks about VPC and on-premises; no answer shows. "OpenJev" (Qwen3.5-4B) is a community imitation, not affiliated |
| API | Not OpenAI-compatible: `POST https://api.typesafe.ai/v1/systemone`, a `state` and typed questions (`choice`, `score`, `noul`, `box`), typed answers with probabilities and confidence; streaming undocumented; 70 to 500 ms, so the 30 s cut is moot |
| Effort and output | No effort setting, no thinking output. "It does not generate text, write code, or hold a conversation"; "not a drop-in replacement for the LLM behind Claude Code" |
| Context | `jev-1.14.0` (from 2026-10-14, `jev-latest`): 64k per request, 32k per question, 262k with a long-context header |
| Hosting and data use | "The Services are hosted in the United States", EEA data transferred there; "We will not train or fine tune any … models on your prompts" (policy updated 2025-11-19); retention "as long as reasonably necessary"; zero data retention for enterprise customers on request; SOC 2 Type II; Delaware law; no EU region and no DPA stated |

Verdict: not an arm. Where it could serve, each at info, never a gate input (decision-0002): doc-0019 C2's pairwise contradiction search (TypeSafe's citation-check recipe is that shape: `choice` over supports, contradicts, says nothing); a yes/no screen before route (c) spends an LLM call on a key; ranking doc-0017 candidate 4's link pairs, kept `inferred`. Each adds a second model client and host, which `tests/test_security.py::test_nothing_reaches_the_network_but_the_model_client_and_the_store_driver` forbids today, so each is a decision; none for a bank's content while the service is US-hosted. Not verified: the FAQ answers on VPC and data location, whether early access takes new sign-ups (a third party says not), an EU region, a DPA, streaming.

## Fit/gap per requirement

M measured in this session; R read (the source in the endpoint kinds and Jev sections); — neither.

| Requirement (`arms.py`, `agent.py`, the page) | 1. Private (Ollama; vLLM not probed) | 2. Mistral API | 3. OpenRouter | Jev |
|---|---|---|---|---|
| OpenAI chat completions | **Fit**, M | Fit, R | Fit, R | **Gap**, R: its own `POST /v1/systemone` |
| Streamed, usage in the last chunk | **Fit**, M | Streaming R; usage in the stream — | — ; cached tokens returned (doc-0005, R) | Gap: no stream documented; moot at 70 to 500 ms |
| `json_object` (one-reply arm) | **Fit**, M, both families at every accepted effort | Documented, R; with effort high — | `response_format` listed for every candidate, R | **Gap**: typed answers only |
| Tools, `tool_choice: auto`, many turns (agent arm) | **Fit**, M, 4 turns at effort none; thinking on across turns — | Documented, R | `tools` listed, R | **Gap**, R: "does none of that" |
| Efforts the row lists | Partial, M: none turns thinking off; low and high alike on Qwen; high refused (400) on a non-thinking model | Partial, R: Small 4 and Medium 3.5 none or high; Large 4 low, medium, high | `reasoning` listed, R | n/a: no setting |
| `delta.content` a string | **Fit**, M: thinking kept out of `content` | **Gap** at high (defect 2: SDK reproduced, API not); fit at none, R | — | n/a |
| The whole prompt reaches the model (6k to 16k; a J-F agent run about 200k) | **Gap** at defaults, fit with `OLLAMA_CONTEXT_LENGTH` (defect 1, M) | 262k (Small 4, Medium 3.5), 1M (Large 4), R | 262k to 1M by model, R | 64k per request, 32k per question, R |
| Thinking counted against the ceilings (task-0034) | **Fit**, M: in `completion_tokens`, `hidden_tokens` 0 | — | — ; LiteLLM undercounted (task-0034) | n/a: input and output tokens reported, R |
| Key check by model listing (task-0171) | Reachability only, M: 200 with any bearer, no keys held | **Fit**, M: 401 on an invalid bearer | **Gap**, M: 200 on an invalid bearer | Gap: no OpenAI listing; its own list-models endpoint, R |
| Content goes only where the instance allows (task-0013) | **Fit** inside the network (`docs/security.md`'s private row; practice: confirm what it forwards) | Partial: EU processing by default and about 30 days' retention per third parties; Mistral's DPA not read | **Gap**: routes to providers the instance does not choose | **Gap**, R: US-hosted, no EU region or DPA stated |
| A call without the maintainer's go | Fit: no per-call cost | Gap: a key and a go | Gap: a key and a go | Gap: an early-access key |
| An agent run within `KG_AGENT_MAX_SECONDS` 1500 | **Gap** on CPU, M: 116 to 444 s per thinking reply; 1.5 to 6 s at none | — | — | moot |

## Other uses of these models in knowgov

1. **Cross-family replication of the record** (kinds 1 to 3): does the gate's effect hold beyond one vendor, and does an in-house model still abstain under BLOCKED. Pre-registered as task-0140 was: hypothesis committed first, n = 5, deviation-labelled, raw outputs outside `results/`; M1 per family the headline.
2. **Route (c) over a document, reopened**: task-0139 is parked at precision 0.56 against a bar of 0.9, and doc-0019 reopens it with "a model or prompt that clears 0.9 with the tool unchanged"; `tools/route_c_documents.py` over several rows is that, with no code. Its `LANGUAGE` parameter admits the French and German documents an EU instance holds.
3. **The transcript route on the private endpoint**: `harness/transcript.py` sends a person's own words, the most sensitive payload knowgov sends; `instance/README.md` could name kind 1 as its recommended setting.
4. **task-0104, the eval recipe** (parked): it reruns governed tasks when the model row changes; a second row is the trigger it waits for, with a baseline per row.
5. **Volume work for a cheap local model**, both parked behind measured preconditions: doc-0017 candidate 4 (model-proposed links, `inferred`, never above `proposed`) and doc-0019 C2 (pairwise contradiction search, info only).
6. **Other agents as consumers**: the MCP server is client-neutral, but only Claude Code and Claude Desktop are documented (task-0117: the Desktop recipe not run), and the fail-closed hook is Claude Code's protocol (doc-0014 names the coupling). One non-Anthropic MCP client on kind 1 consulting `gate_verdict` shows a governed in-house model end to end, nothing leaving the network.

Kept out by the record's own rules: an LLM judge, text-to-Cypher and embeddings (doc-0019 C7); a model that verifies, approves or chooses keys (decision-0002, doc-0018 §3); a model in CI (`docs/security.md`, the no-key row).

## Opportunity canvas: kind 1 first

| Block | Content |
|---|---|
| Users and customers | The operator of a private instance choosing which model answers, or none (task-0013); the maintainer measuring the gate's effect beyond one vendor; a lighthouse reviewer asking what leaves the network (`docs/security.md`) |
| Problem | Every row in `demo/models.toml` sends content outside the organisation (OpenAI, Google, Anthropic through LiteLLM). The private route is asserted in `docs/security.md` and was never run; at Ollama's defaults it scores the arms on cut prompts and says nothing (defect 1) |
| Solution | A compose profile serving open weights (Ollama; vLLM where a GPU host serves several users), the server's context length set; a row naming the efforts its model accepts; defect 1's guard, so a cut prompt is marked, never scored; defects 2 to 4 fixed beside it |
| Value | The arms, the transcript route and route (c) runnable on an instance's content with nothing leaving the network; the security description's private row backed by a run; a cross-family replication with no per-call cost |
| Metrics | Calls the guard marks (target none at a set context length); M1 per family on CargoQuote S1 to S7, each a deviation beside the record; the share of a pilot's arm calls on the private row |
| Channels | The row and the profile; `instance/README.md` naming the private row for the transcript route; `docs/security.md`'s endpoint table |
| Cost | Each defect fix about ten lines with a scripted test; the profile a compose service, a row and README lines; the GPU host the operator's, outside knowgov |
| Risks | A small open model abstains where the record's model generated (`ministral-3:3b` abstained on a stated value in the probe); CPU timings mislead; a context length set too low brings defect 1 back |
| Unfair advantage | The gate, the oracle and the measures are model-neutral: any family is graded by the same suite and compared with the record as a marked deviation |

## SWOT: kind 1 first

- **Strengths.** Both arm kinds ran through the harness's own code with no change (probe). The key-variable rule, the deviation marking and the models table already carry a row. Since task-0141.05 (X1) the model's code runs in the no-network worker, so a private endpoint changes only where the call goes.
- **Weaknesses.** Defect 1 is silent at Ollama's defaults. Thinking on CPU costs minutes per call. Effort means on or off for Qwen under Ollama, not a level. vLLM was not probed; thinking across tool turns was not measured. *Response:* the guard before the row; a GPU host named as the operator's; a vLLM probe before the docs call it proven.
- **Opportunities.** Route (c)'s reopening condition, a model that clears 0.9 with the tool unchanged, can be tried on many open models at no per-call cost. The transcript route's payload, a person's words, stays inside. A non-Anthropic MCP client on the same host shows an in-house model governed end to end.
- **Threats.** Open-weight churn: Devstral 2 retired on 2026-07-31 and Mistral Large 3 deprecated on 2026-10-31, within months of release. An organisation's policy on model origin may exclude some families' weights. Under decision-0016 a row or field added after 0.9.0 is 0.10.0 and restarts the freeze. *Response:* rows dated and re-read as `demo/models.toml`'s comments already are; families chosen by the operator; the row in the 0.9.0 gathering if it is ready before G9 is met.

## Proposed follow-ups (not created)

In order. 1 to 4 are fixes and are not bound by decision-0016's freeze; 5 is treated as a contract change. doc-0028 §3 does not list `demo/models.toml` among the contract surfaces; a new field in it, such as a context length, changes the table's format, and the page's `/api/*` lists its rows. Under decision-0016 point 2, contract changes after 0.8.0 gather for 0.9.0, cut when G9-1 to G9-10 are met; after 0.9.0 any contract change is 0.10.0 and restarts the freeze.
1. **Defect 1**: the prompt-integrity guard in `arms.call` and `openai_responder`, with a test on a scripted usage below the sent size.
2. **Defect 2**: content-chunk normalisation, with a scripted-stream test carrying a thinking chunk.
3. **Retries**: 429, 5xx and network errors only.
4. **The key check on a public listing**: a listing that answers without the key reads `unchecked`.
5. **Decide the endpoint kinds**: kind 1 first, as a compose profile with `OLLAMA_CONTEXT_LENGTH` and a row; kind 2 after a keyed spike; kind 3 for the maintainer's study only. In the 0.9.0 gathering if ready before G9 is met, else 0.10.0.
6. **A Mistral spike with a key**, in doc-0006's shape, after 2.
7. **A vLLM probe on a GPU host**, thinking on across tool turns included, before the docs call the private route proven.
8. **The cross-family replication**, pre-registered, on the public subjects, once 1 to 5 stand.

## For the maintainer

- **Which endpoint kinds to add.** Recommendation: kind 1 first; kind 2 after its spike and defect 2's fix; kind 3 for your study on the public subjects only, after the key-check fix; neither Jev nor Alibaba's cloud. Reasons: kind 1 is the only one that keeps an instance's content inside (task-0013) and the only one measured with both arm kinds; kind 2 is documented but breaks the join at effort high; kind 3 routes to providers an instance does not choose, and its listing accepts any key; Jev generates no reply; Qwen serves better as open weights under kind 1.
- **When the row lands, against the freeze.** Recommendation: fixes 1 to 4 now, as fixes; the row and the profile in the 0.9.0 gathering only if built before G9 is met, never holding 0.9.0 for them, else 0.10.0. Reasons: decision-0016 restarts the freeze on any contract change after 0.9.0, and the fixes make a private row honest whenever it lands.
- **What the self-hosted route needs.** Recommendation: defect 1's guard as a precondition of the row; the server's context length named in the profile and the README; the efforts listed per model; a GPU host stated as the operator's; a vLLM probe before the docs call the route proven. Reasons: the probe's cut prompt answered HTTP 200; CPU thinking took 116 to 444 s per reply; vLLM and thinking across turns are unmeasured.
- **Whether to spend on keyed calls.** Recommendation: one Mistral spike after defect 2's fix; OpenRouter only for the replication. Reasons: no hosted model call has been made; defect 2 is reproduced against the SDK only.
- **Jev as a second model client.** Recommendation: not now. Reasons: `tests/test_security.py` lets nothing reach the network but the model client and the store driver; the service is US-hosted with no DPA stated; its fits (doc-0019 C2, a screen before route (c), doc-0017 candidate 4) are parked behind measured preconditions.

## What was read

- knowgov at `506b9a5` (the probe), the defect lines and `docs/security.md` re-read at `8f5edd5`: `harness/arms.py`, `harness/agent.py`, `harness/transcript.py`, `tools/route_c_documents.py`, `demo/models.toml`, `demo/litellm/config.yaml`, `docs/security.md`, doc-0005, doc-0006, doc-0019, task-0013, task-0104, task-0139, task-0140.
- Mistral, 2026-11-05: docs.mistral.ai/studio/conversations/reasoning; docs.mistral.ai/getting-started/models.
- Alibaba Model Studio, 2026-11-05: alibabacloud.com/help/en/model-studio/deep-thinking; alibabacloud.com/help/en/model-studio/qwen-api-via-openai-chat-completions.
- OpenRouter's public model list, openrouter.ai/api/v1/models, 2026-11-05.
- TypeSafe AI, 2026-11-05: typesafe.ai; typesafe.ai/blog/introducing-system-one-models-and-jev; docs.typesafe.ai introduction, quickstart, models, api/errors, introduction/coding-agents, cookbooks/citation_check; typesafe.ai/legal/privacy-policy, /legal/terms, /enterprise.
- Third-party, weaker, named where used: on Mistral's data terms (waimakers.com, requesty.ai) and on open-weight rankings (mindstudio.ai, kilo.ai; vendor-reported and conflicting).
