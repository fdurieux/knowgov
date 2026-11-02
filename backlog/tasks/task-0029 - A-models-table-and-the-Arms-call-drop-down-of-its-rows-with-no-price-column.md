---
id: TASK-0029
title: A models table and the Arms call drop-down of its rows, with no price column
status: To Do
assignee: []
created_date: '2026-11-02T13:32:00Z'
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
