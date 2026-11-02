---
id: TASK-0031
title: >-
  One stack per subject by compose alone: ports as variables, a project name per
  subject
status: To Do
assignee: []
created_date: '2026-11-02T13:32:00Z'
labels:
  - subject
  - instance
milestone: m-2
dependencies: []
references:
  - demo/docker-compose.yml
  - demo/docker-compose.instance.yml
  - demo/README.md
documentation:
  - >-
    backlog/docs/doc-0005 -
    Model-and-effort-drop-down-subject-drop-down-opportunity-canvases-and-SWOTs.md
priority: medium
type: chore
ordinal: 41000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The page shows one subject, the one KG_SUBJECT named when the container started; the maintainer wants to switch between J-F's data load and the demo on screen. doc-0005 chose a per-request switch as a story (the page serves every subject of its root) and this chore as the zero-code route today: the three published ports become variables with today's defaults, so a second stack with another project name and another KG_SUBJECT stands beside the default one. Two app containers must not share one Neo4j (the Runner's lock is per process and a load would race), so a stack is the whole pair, 1 GB of heap each.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Two stacks run side by side on one machine on different ports with different KG_SUBJECT values; the default command and its ports are unchanged
- [ ] #2 The README's instance section shows the second project name beside the default stack, in the adopter register
<!-- AC:END -->
