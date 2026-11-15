---
id: TASK-0345
title: Neo4j Desktop as a documented, probed target (decision-0042)
status: To Do
assignee: []
created_date: '2026-11-15T09:29:00Z'
labels:
  - neo4j
  - docs
  - probe
dependencies: []
references:
  - backlog/decisions/decision-0042
priority: medium
ordinal: 337000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0042 (accepted 2026-11-15) keeps neo4j:5.26-community as the record's and CI's store and adds Neo4j Desktop as a target for the maintainer's exploration. knowgov already reaches any Neo4j through KG_NEO4J_URI, KG_NEO4J_USER and KG_NEO4J_PASSWORD, so this is documentation plus one proving run of the existing checks. Desktop runs on the maintainer's own machine, which no cloud session reaches, so the run is theirs; the runbook is proven first against a 5.26 Community tarball started directly (CLAUDE.md, 'Against Neo4j'). D1 (the edition's constraint measurement) may differ under Desktop's Enterprise features and is reported apart, never against the record's (task-0004).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 instance/README.md gains a section, in the adopter register, on running knowgov against a Neo4j outside the stack (Desktop): the KG_NEO4J_* settings, the host address seen from the stack's containers, the memory and privilege caveats, and that the record and CI stay on the 5.26 container
- [ ] #2 A runbook of existing commands only (tools/check_snapshots.py, the deterministic run with demo/tools/compare_deterministic.py, demo/tools/check_saved_queries.py), with what each proves and how to read D1 apart, is proven end to end against a 5.26 Community tarball in a session
- [ ] #3 The maintainer's Desktop run is recorded in the task's notes: the Neo4j version and edition, each check's result, D1's accepted and refused constraints, and any difference from the 5.26 container's
- [ ] #4 No contract moves: no new KG_* setting, schema or exit; the record, the compose image and the stack job are unchanged
<!-- AC:END -->
