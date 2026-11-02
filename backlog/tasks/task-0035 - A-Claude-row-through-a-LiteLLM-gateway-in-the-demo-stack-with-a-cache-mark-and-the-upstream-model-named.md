---
id: TASK-0035
title: >-
  A Claude row through a LiteLLM gateway in the demo stack, with a cache mark
  and the upstream model named
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-02T19:58:00Z'
updated_date: '2026-11-02T22:13:00Z'
labels:
  - arms
  - instance
milestone: m-3
dependencies:
  - TASK-0030
references:
  - demo/docker-compose.yml
  - demo/models.toml
  - demo/README.md
documentation:
  - >-
    backlog/docs/doc-0006 -
    Spike-Gemini-and-Claude-rows-through-a-gateway-what-arrived.md
priority: low
type: feature
ordinal: 47000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0006 decided a Claude row is a gateway row: Anthropic's own OpenAI-compatible layer ignores effort and refuses json_object, while LiteLLM maps reasoning_effort to adaptive thinking plus output_config.effort and served both arm kinds. Two conditions make it honest. Caching: nothing is cached unless the request is marked, so a J-F agent run sent 201,028 prompt tokens with 0 cached; with an ephemeral mark a repeated 11.5k-token prompt read 11,508 from cache, and LiteLLM can add the mark itself (cache_control_injection_points). Provenance: the run file names the gateway alias (claude), not the model behind it. The key stays an environment variable, KG_ANTHROPIC_KEY, never ANTHROPIC_API_KEY, which a Claude Code session itself reads. JSON mode is accepted but not enforced for Claude; the harness's own system prompt held it on every reply in the spike.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A litellm service in demo/docker-compose.yml, started only when asked (a compose profile), with a pinned image or version, a config that names the upstream Claude model, adds the cache mark, and reads KG_ANTHROPIC_KEY by name; the app reaches it on the compose network
- [x] #2 A Claude row in demo/models.toml for that gateway, key_var the gateway's key variable, arms reply and agent; its run file names the upstream model, not the alias
- [x] #3 A Claude agent run through the gateway reports cached tokens above zero after its first turn; the stack job is unchanged when the profile is off
- [x] #4 The demo README explains the gateway, the key variable and how to start the profile in the adopter register
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Pin the LiteLLM image the spike ran (v1.106.6, by tag and digest). 2. demo/litellm/config.yaml: alias = the upstream model name, cache marks on the system prompt and the newest message, KG_ANTHROPIC_KEY and LITELLM_MASTER_KEY read by name. 3. Compose service behind the profile claude, app not depending on it; app receives LITELLM_MASTER_KEY. 4. Row in models.toml at http://litellm:4000/v1. 5. README passage with the two keys and the profile command. 6. Test; a live J-F agent run through the same config.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Ran the committed config through LiteLLM 1.106.6 locally (no Docker here): the gateway lists claude-sonnet-5-5, refuses a call without its key; a J-F agent run on scenario C, 4 calls per arm, recorded model claude-sonnet-5-5 and read each turn after the first from the cache: arm B (prompt, cached) 1906/0, 3514/1902, 6164/3512, 8674/6162; arm G 7530/0, 12089/7526. 41,329 tokens. The compose service itself is checked by docker compose config with and without the profile; its live start is the maintainer check on the Mac. Incident: rendering the profile config printed the session KG_ANTHROPIC_KEY value into the tool output (not into any file or commit); the maintainer was told to revoke and replace that key.
<!-- SECTION:NOTES:END -->
