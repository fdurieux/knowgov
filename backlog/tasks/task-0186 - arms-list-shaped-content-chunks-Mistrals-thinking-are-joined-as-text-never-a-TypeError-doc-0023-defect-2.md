---
id: TASK-0186
title: >-
  arms: list-shaped content chunks (Mistral's thinking) are joined as text,
  never a TypeError (doc-0023 defect 2)
status: To Do
assignee: []
created_date: '2026-11-06T23:05:00Z'
labels:
  - arms
dependencies: []
references:
  - harness/arms.py
  - harness/agent.py
priority: medium
type: bug
ordinal: 186000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer accepted doc-0023's advice on 2026-11-06 ("accept the advice on all three"). Mistral documents that at reasoning_effort high message.content is a list (a thinking chunk, then a text chunk), and that streamed delta.content is a list during the thinking, then a string. The pinned openai SDK keeps the list, so "".join(parts) raises TypeError at harness/arms.py:176 and :193 and harness/agent.py:215 and :238 (at 8f5edd5): in arms.call the exception reaches run.py, and in openai_responder it ends the agent run as api error. Reproduced against the SDK, not Mistral's API (the keyed spike verifies it there).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A scripted stream with a thinking chunk and then text yields only the text, in arms.call and openai_responder, and a non-streamed list content likewise
- [ ] #2 String content and the existing streams give the same results as before
- [ ] #3 Tests in task-0033's shape cover both paths
<!-- AC:END -->
