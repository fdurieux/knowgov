---
id: TASK-0032
title: >-
  As the maintainer, I want the page to serve every subject of its root and a
  drop-down to switch, so that one stack shows J-F's data load and the demo
  without a restart
status: To Do
assignee: []
created_date: '2026-11-02T13:32:00Z'
labels:
  - story
  - subject
  - instance
milestone: m-2
dependencies: []
documentation:
  - >-
    backlog/docs/doc-0005 -
    Model-and-effort-drop-down-subject-drop-down-opportunity-canvases-and-SWOTs.md
priority: medium
type: story
ordinal: 42000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The subject is chosen once, by KG_SUBJECT at process start, and views, register_view and server read it through a module-level global, so one container is one subject. doc-0005 weighed three shapes and chose this one: the server loads every subject.toml under a root list, keeps a Subject per id, every route takes a subject id, runs land under a folder per subject, and a header drop-down lists the ids and names from the manifests. It keeps task-0002 (the list is read from the directory, no id in code) and the read-only instance mount (an instance lists its own subjects and none of the public ones). A restart-on-select was rejected: one viewer's click would change the page for every viewer and kill a run in progress.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 One stack lists both public subjects in a header drop-down and shows either without a restart; an instance started with the instance file lists its own subjects only
<!-- AC:END -->
