---
id: TASK-0157
title: >-
  B7: subject on every reader and knowgov-runs tool, and list_subjects, per
  decision-0013 (doc-0021 G4)
status: To Do
assignee: []
created_date: '2026-11-06T04:53:00Z'
labels:
  - mcp
  - subject
dependencies:
  - TASK-0151
documentation:
  - >-
    backlog/decisions/decision-0013 -
    One-MCP-reader-for-several-subjects-the-subject-named-by-id-under-KG_SUBJECTS-defaulting-to-KG_SUBJECT-served-by-a-child-process-per-call.md
  - >-
    backlog/docs/doc-0026 -
    Spike-task-0151-one-MCP-reader-for-several-subjects-measured-doc-0021-S3-G4-2026-11-06.md
priority: low
type: feature
ordinal: 164000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0021 G4: both MCP servers answer for one subject per process, so n subjects mean 2n client registrations. task-0151's spike measured three designs (doc-0026); decision-0013, proposed, chooses (a), a child process per call, by AC #2's rule. Build only once decision-0013 is accepted by the maintainer, and after 0.7.0 (shipped). Scope as the decision states: an optional subject id on every tool of both servers, resolved under KG_SUBJECTS, never a path; none named answers as today, from KG_SUBJECT; list_subjects; a named subject other than the process's own runs in a child process with KG_SUBJECT set. If S2 (task-0141.06) moves the Neo4j number of (a) above 0.7 s, re-measure before building.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Every tool of the reader and of knowgov-runs takes an optional subject, an id under KG_SUBJECTS; a path, an unknown id or one outside KG_SUBJECTS is refused; none named answers exactly as today
- [ ] #2 list_subjects names every subject under KG_SUBJECTS and the default (KG_SUBJECT)
- [ ] #3 A call naming another subject is answered by a child process with that subject's KG_SUBJECT, equal to what a server started on that subject answers; check_mcp_server.py holds it over stdio and HTTP
- [ ] #4 Additive tool-schema change: CHANGELOG under Contract changes; instance/README's one-subject-per-process note updated
<!-- AC:END -->
