---
id: TASK-0035
title: >-
  A Claude row through a LiteLLM gateway in the demo stack, with a cache mark
  and the upstream model named
status: To Do
assignee: []
created_date: '2026-11-02T19:58:00Z'
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
- [ ] #1 A litellm service in demo/docker-compose.yml, started only when asked (a compose profile), with a pinned image or version, a config that names the upstream Claude model, adds the cache mark, and reads KG_ANTHROPIC_KEY by name; the app reaches it on the compose network
- [ ] #2 A Claude row in demo/models.toml for that gateway, key_var the gateway's key variable, arms reply and agent; its run file names the upstream model, not the alias
- [ ] #3 A Claude agent run through the gateway reports cached tokens above zero after its first turn; the stack job is unchanged when the profile is off
- [ ] #4 The demo README explains the gateway, the key variable and how to start the profile in the adopter register
<!-- AC:END -->
