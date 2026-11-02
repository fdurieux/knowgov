---
id: TASK-0028
title: Effort as a run setting, sent, recorded and compared with the record
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-02T13:32:00Z'
updated_date: '2026-11-02T13:54:00Z'
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

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. subject.py: record_effort from the manifest ("" = API default). 2. arms.py: RECORD_EFFORT; endpoint() returns host, effort (KG_ARMS_EFFORT) and record_effort, deviation = model or effort differs when the record ran an arm; effort_kwargs() adds reasoning_effort only when set; call() sends it and records host and effort. 3. agent.py: the responder sends the same; totals carry host and effort; run.py writes them into the agent run usage. 4. views.py: efforts per arm, record_effort, efforts_used, effort_deviation, one controlled sentence. 5. server.py: arms_effort() with EFFORT_RE, is_deviation(model, effort), KG_ARMS_EFFORT per run, effort in the run record and /api/scenarios. 6. index.html: an effort field in the Arms call box, the record radio states the record effort, the run posts effort, the banner and an Effort deviation alert. 7. compose and subjects/README document KG_ARMS_EFFORT and record_effort. 8. Tests in test_arms and test_demo; two real calls at low and medium.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented on top of task-0027. Suite 92/92. Two real calls on gpt-5.5 through the proxy, KG_ARMS_EFFORT low then medium: both accepted, the record carries host api.openai.com and the effort (completion 11 tokens at low, 26 at medium for the same one-line reply), endpoint().deviation true on the CargoQuote subject since the model differs. The page: an effort field under the two radios, the record radio names the record effort (API default for CargoQuote), the banner shows "at effort X" and the red mark reads "not the record model or effort", an Effort deviation alert beside the Model deviation one; J-F marks nothing since its record ran no arm.
<!-- SECTION:NOTES:END -->
