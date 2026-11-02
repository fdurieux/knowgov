---
id: TASK-0029
title: A models table and the Arms call drop-down of its rows, with no price column
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-02T13:32:00Z'
updated_date: '2026-11-02T14:51:00Z'
labels:
  - arms
  - page
  - instance
milestone: m-3
dependencies:
  - TASK-0027
  - TASK-0028
references:
  - harness/arms.py
  - demo/app/server.py
  - demo/app/index.html
  - demo/docker-compose.instance.yml
documentation:
  - >-
    backlog/docs/doc-0005 -
    Model-and-effort-drop-down-subject-drop-down-opportunity-canvases-and-SWOTs.md
priority: medium
type: feature
ordinal: 39000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The Arms call box takes a free-text model name matched by a pattern and sent as KG_ARMS_MODEL; the maintainer asked for a drop-down of models and efforts from several providers "defined in a config file with API tokens". doc-0005 answers: rows the operator writes in a TOML table (provider, base URL, model, the efforts it accepts, the name of the environment variable holding the key, the arm kinds served), never a file of tokens, since a key in a file is a key in a repository, a mount and a backup; keys stay in the environment, as task-0005 and task-0013 settled, and a row whose variable is empty is listed greyed with "set VAR". No price and no read date on a row: the maintainer dropped prices (the prices-out task) because they go stale. The record's row comes first and keeps the red deviation marking of a run that is not like-for-like.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 KG_MODELS names a TOML table of rows (id, label, provider, base URL, model, efforts, key variable name, arm kinds served), default demo/models.toml with the record's row first; a row carries no key and no price
- [ ] #2 /api/scenarios lists the rows with key_set per row and never a key value; a row whose variable is empty is listed, greyed, with "set VAR", and refused by /api/run
- [ ] #3 The Arms call box is a drop-down of rows plus an effort control filled from the row; /api/run takes a row id and an effort, the server resolves them, and a browser can send no URL; the three KG_MODEL_* variables remain as the custom row
- [ ] #4 The record's row is first and greyed with "the record ran no arm" on a subject with no record model; the stack job reads the rows and finds no key; the page-string and glossary tests pass on the new labels
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. demo/models.toml: the operator rows (OpenAI gpt-5.5 and gpt-5.1; a commented Gemini row waiting on task-0030), no key, no price. 2. demo/app/models.py: load_table() refuses unknown fields, a key_var that is not a variable name, bad ids; rows() adds the record row first (greyed "the record ran no arm" without a record model) and the instance row when the KG_MODEL_* variables differ from the defaults, with key_set, serves, available, why; resolve() checks row and effort and returns the four harness variables and the deviation (host, model or effort). 3. server.py: model_rows() and arms_enabled() in /api/scenarios; Runner.start takes row and effort, refuses before running, sets the env from the row; the run record names row, host, model, effort. 4. index.html: two drop-downs, the reason line, the chip and the Arms button hint from the rows, the run posts row and effort. 5. Compose KG_MODELS; README section rewritten; stack job asserts the rows carry no key. 6. Tests; a browser look.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented. Suite 93/93. Served locally on rdflib three ways and read in Chromium: no key, every row greyed with "set OPENAI_API_KEY", the chip and the Arms button name the variable; with a key on CargoQuote the record row is like-for-like and picking gpt-5.5 offers five efforts and says deviation; on J-F the record row is greyed "the record ran no arm" and gpt-5.5 is picked. /api/run refused an unavailable row, an effort the row does not list and an unknown row; a base_url in the body is ignored. No key value in the /api/scenarios payload.
<!-- SECTION:NOTES:END -->
