---
id: TASK-0173
title: >-
  The Known limits pass: each limit of 0.7.0, 0.8.0 and Unreleased closed,
  tasked, or proposed as a 1.0 limit (doc-0028 P3, G9-6; doc-0029)
status: To Do
assignee: []
created_date: '2026-11-06T13:03:00Z'
labels:
  - contracts
  - docs
dependencies: []
priority: medium
ordinal: 174000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0028 §9 P3, minted by doc-0029 advice 3. CHANGELOG.md's Known limits (0.7.0 lists fourteen, 0.8.0 adds Landlock and Docker Desktop, Neo4j's single generation, the killed-writer window, transaction memory, TERMINATE, the cached parse, the CRLF file digest) are read one by one against the code and the backlog. Each is marked closed (with the PR that closed it), tasked (with a task id, minting a task where none exists, e.g. response sizes uncapped, the Neo4j window between raising the counter and committing, transaction memory bounding a unit), or proposed as a named 1.0 limit. A limit is only proposed; declaring it a 1.0 limit is the maintainer's word (decision-0016 open). Backlog and docs only: no released CHANGELOG section is edited.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A table in doc-0028 §10 (or a new doc linked from it) lists every Known limit of 0.7.0, 0.8.0 and Unreleased with its state: closed (PR), tasked (task id) or proposed 1.0 limit, each with its source line
- [ ] #2 Every limit without a task gets one, minted through the CLI, or is proposed as a 1.0 limit with a sentence why
- [ ] #3 No released CHANGELOG section is edited; nothing is declared a 1.0 limit without the maintainer
<!-- AC:END -->
