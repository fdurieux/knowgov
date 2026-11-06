---
id: TASK-0173
title: >-
  The Known limits pass: each limit of 0.7.0, 0.8.0 and Unreleased closed,
  tasked, or proposed as a 1.0 limit (doc-0028 P3, G9-6; doc-0029)
status: Done
assignee: []
created_date: '2026-11-06T13:03:00Z'
updated_date: '2026-11-06T13:26:00Z'
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
- [x] #1 A table in doc-0028 §10 (or a new doc linked from it) lists every Known limit of 0.7.0, 0.8.0 and Unreleased with its state: closed (PR), tasked (task id) or proposed 1.0 limit, each with its source line
- [x] #2 Every limit without a task gets one, minted through the CLI, or is proposed as a 1.0 limit with a sentence why
- [x] #3 No released CHANGELOG section is edited; nothing is declared a 1.0 limit without the maintainer
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Drafted by the v1.0 session (session_01HTAA1TThDg3TA2qJHCemaG) at main 38ae719, filed verbatim by the coordinating session under doc-0029. The table is doc-0028 §10: 25 entries, 2 closed (#271, #278), 6 tasked (0162, 0160, 0148 AC#5, 0063, 0108, 0164), 4 minted (task-0175 T-a abandoned Neo4j publication; task-0176 T-b heap a load needs; task-0177 T-c response sizes bounded; task-0178 T-d register panel shows withdrawals), 13 proposed as 1.0 limits for the maintainer. No released CHANGELOG section edited; nothing declared a 1.0 limit.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The Known limits pass (doc-0028 P3, G9-6) is done: every limit of 0.7.0, 0.8.0 and Unreleased is classed in doc-0028 §10 against the code at 38ae719. The four with no owner are minted as task-0175..0178; thirteen are proposed as named 1.0 limits, each with its reason, and wait for the maintainer's word under decision-0016. Docs and backlog only.
<!-- SECTION:FINAL_SUMMARY:END -->
