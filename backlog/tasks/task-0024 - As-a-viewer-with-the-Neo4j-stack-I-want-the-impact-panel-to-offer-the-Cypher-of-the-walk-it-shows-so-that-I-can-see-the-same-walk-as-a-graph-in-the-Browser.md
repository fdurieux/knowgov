---
id: TASK-0024
title: >-
  As a viewer with the Neo4j stack, I want the impact panel to offer the Cypher
  of the walk it shows, so that I can see the same walk as a graph in the
  Browser
status: To Do
assignee: []
created_date: '2026-11-02T07:35:00Z'
updated_date: '2026-11-02T07:35:00Z'
labels:
  - story
  - register
  - page
  - store
milestone: m-3
dependencies:
  - TASK-0023
references:
  - demo/app/register_view.py
  - demo/app/index.html
  - demo/app/server.py
priority: low
type: story
ordinal: 32000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The impact panel lists the edges walked and the nodes reached as a table (register_view.impact(), the panel's table and Reached list). The Browser can draw the same walk as a graph only from a query that matches it, which the shipped register-impact does not (TASK-0023). Once it does, the adapter holds the query with one literal start; this story shows that query where the walk is, with the typed id substituted, the needs chip the saved queries already carry, and a copy button; the page executes nothing and writes nothing to the register. Limits recorded by the investigation of 2026-11-02: a run wipes the projection (the chip says 'wiped by a run'; a pasted query in an open Browser tab does not); the rdflib store has no console and no Browser, so the panel shows nothing there, as the Cypher list is hidden today; a parameterised query cannot pass check_saved_queries.py, so the listed text carries a literal start, which should be the register view's impact_default rather than one subject's id. The Browser manual documents ?cmd=edit&arg=<query> to pre-fill the editor without running, and ?connectURL= which the page already uses; combining them in one link is untested.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The impact panel shows the walk's Cypher, both the rows form and the path form, with the typed id, a copy button and the needs chip, when the store is Neo4j, and nothing when it is not
- [ ] #2 A link beside the copy button opens the Browser with the query pre-filled and nothing run, verified in the stack job
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
From the second investigation run: the Browser's own bundle (lib/neo4j-browser-5.26.0.jar, populateEditorFromUrlEpic) reads cmd and arg, and edit sets the editor's content without running it, composable with connectURL; untested through a GUI. The Browser's Connect result nodes setting (autoComplete, on by default) draws every relationship among the shown nodes, so a REG_PARENT edge can appear in the picture that the walk never followed: the panel's sentence beside the link should say so. A comparator in the stack job (a demo/tools/check_impact_cypher.py over console_query for every RegNode) is the stronger gate than a row-count assertion; TASK-0023's test covers the simulation, the comparator would cover the live store.
<!-- SECTION:NOTES:END -->
