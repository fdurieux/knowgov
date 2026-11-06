---
id: TASK-0190
title: One keyed Mistral spike in doc-0006's shape, after defect 2's fix (doc-0023)
status: To Do
assignee: []
created_date: '2026-11-06T23:05:00Z'
labels:
  - arms
  - models
  - spike
dependencies:
  - TASK-0186
priority: low
type: task
ordinal: 190000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer accepted doc-0023's advice on 2026-11-06 ("accept the advice on all three"), including "whether to spend on keyed calls: one Mistral spike after defect 2's fix; OpenRouter only for the replication". It is the one paid spike the acceptance authorises. Defect 2 is reproduced against the SDK only; this verifies it against Mistral's API at reasoning_effort high and reads the hosted EU option (kind 2) before any row is proposed. The key comes from the environment's credential settings, never a file or the chat. The spike runs on the public subjects only, as a deviation, with raw outputs outside results/ and runs/ (doc-0023's constraints).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Defect 2's fix is verified against Mistral's API at reasoning_effort high, with the reply's content shape recorded
- [ ] #2 The arms run once on a public subject in doc-0006's shape, the cost and the tokens recorded, every run a deviation
- [ ] #3 The findings land in a backlog doc with the four parts for kind 2; no models.toml row without the maintainer's word
<!-- AC:END -->
