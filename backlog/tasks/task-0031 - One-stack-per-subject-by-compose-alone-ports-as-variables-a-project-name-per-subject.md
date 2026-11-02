---
id: TASK-0031
title: >-
  One stack per subject by compose alone: ports as variables, a project name per
  subject
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-02T13:32:00Z'
updated_date: '2026-11-02T13:51:00Z'
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

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. docker-compose.yml: the three published ports as ${KG_PORT_APP:-8080}, ${KG_PORT_BROWSER:-7474}, ${KG_PORT_BOLT:-7687}; the header documents them and the second-stack command. 2. README: a "Two subjects side by side" passage under One register per organisation, adopter register, with the paste command and a plain-English walkthrough. 3. test_compose_files_agree holds the three variables and the README command. 4. Verify with docker compose config for both stacks.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
docker compose config renders the default stack (knowgov; 8080, 7474, 7687) and the second (-p knowgov-jef with the README variables; 8081, 7475, 7688; KG_SUBJECT jef_data_load; its own volumes knowgov-jef_neo4j-data and knowgov-jef_demo-runs). No Docker daemon in the hosted session, so the two stacks were not started here: the live side-by-side start is the maintainer Mac check; nothing in the Python changed, suite 91/91.
<!-- SECTION:NOTES:END -->
