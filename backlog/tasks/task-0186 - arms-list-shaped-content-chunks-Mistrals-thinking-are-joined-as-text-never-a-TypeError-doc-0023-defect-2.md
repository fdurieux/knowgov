---
id: TASK-0186
title: >-
  arms: list-shaped content chunks (Mistral's thinking) are joined as text,
  never a TypeError (doc-0023 defect 2)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-06T23:05:00Z'
updated_date: '2026-11-06T23:46:00Z'
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
- [x] #1 A scripted stream with a thinking chunk and then text yields only the text, in arms.call and openai_responder, and a non-streamed list content likewise
- [x] #2 String content and the existing streams give the same results as before
- [x] #3 Tests in task-0033's shape cover both paths
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. arms.text_of(content): a string as it is; a list of content parts by its text parts only (thinking dropped), dicts or SDK objects.
2. arms.call and agent.openai_responder join text_of(delta.content), never the raw list.
3. Tests in task-0033's shape: a stub stream with a thinking part, then a list closing it with text, then strings, on both paths; a non-streamed list content; string streams unchanged.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-06. arms.text_of: a string as it is; a list (or tuple) of parts gives its text parts only, dict or SDK object, the thinking part dropped; None reads "". arms.call and openai_responder join text_of(delta.content). Tests: arms.call on a stub stream [thinking], [closing thinking + text], string; openai_responder on the same in task-0033's shape; text_of on a non-streamed list content and SDK objects; string streams unchanged. Not tried against Mistral's API (task-0190 is the keyed spike).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Content sent as a list of parts (Mistral at reasoning_effort high: a thinking part, then text) is now read as its text in arms.call and agent.openai_responder, through arms.text_of; the thinking is dropped and a string reads as before. Before, "".join raised TypeError on the list. Verified by scripted streams on both paths and a non-streamed list; tests/run_tests.py green both ways. Not verified against Mistral's own API: that is task-0190.
<!-- SECTION:FINAL_SUMMARY:END -->
