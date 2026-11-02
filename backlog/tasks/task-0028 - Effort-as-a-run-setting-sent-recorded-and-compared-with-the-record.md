---
id: TASK-0028
title: Effort as a run setting, sent, recorded and compared with the record
status: To Do
assignee: []
created_date: '2026-11-02T13:32:00Z'
labels:
  - arms
  - page
milestone: m-3
dependencies: []
references:
  - harness/arms.py
  - harness/agent.py
  - demo/app/server.py
  - demo/app/index.html
  - subjects/README.md
documentation:
  - >-
    backlog/docs/doc-0005 -
    Model-and-effort-drop-down-subject-drop-down-opportunity-canvases-and-SWOTs.md
priority: medium
type: feature
ordinal: 38000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Effort is not sent, not recorded and not compared today: the pinned client (openai 3.41.0) accepts reasoning_effort on chat.completions.create, and neither arms.call() nor agent.openai_responder() passes it, so a run on the record's model at xhigh passes as like-for-like and the page's red deviation marking, which compares the model only, cannot see it. doc-0005 settles that effort is a second control, filled from the model row, because medium on OpenAI, Gemini and Claude are not the same thing; the record's effort is a subject manifest field (empty: the API default), and the deviation compares host, model and effort.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 KG_ARMS_EFFORT, when set, reaches both arms as reasoning_effort; when unset no parameter is sent
- [ ] #2 The subject manifest may name record_effort (empty: the API default); every run file and trace carries host, model and effort
- [ ] #3 A run at an effort other than the record's is marked in red and names the effort; a run with no effort set matches the record; the J-F subject marks nothing, greyed as now
- [ ] #4 The page's new sentences pass the glossary test; the stdlib suite is green
<!-- AC:END -->
