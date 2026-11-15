---
id: TASK-0345
title: Neo4j Desktop as a documented, probed target (decision-0042)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-15T09:29:00Z'
updated_date: '2026-11-15T11:30:00Z'
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
- [x] #1 instance/README.md gains a section, in the adopter register, on running knowgov against a Neo4j outside the stack (Desktop): the KG_NEO4J_* settings, the host address seen from the stack's containers, the memory and privilege caveats, and that the record and CI stay on the 5.26 container
- [x] #2 A runbook of existing commands only (tools/check_snapshots.py, the deterministic run with demo/tools/compare_deterministic.py, demo/tools/check_saved_queries.py), with what each proves and how to read D1 apart, is proven end to end against a 5.26 Community tarball in a session
- [ ] #3 The maintainer's Desktop run is recorded in the task's notes: the Neo4j version and edition, each check's result, D1's accepted and refused constraints, and any difference from the 5.26 container's
- [x] #4 No contract moves: no new KG_* setting, schema or exit; the record, the compose image and the stack job are unchanged
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Add 'Running against a Neo4j outside the stack' to instance/README.md. 2. Prove the runbook on a 5.26.0 Community tarball (Java 21), empty database. 3. CHANGELOG Unreleased line. 4. Run the suite.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Tarball proof, Neo4j 5.26.0 Community, Java 21.0.12, empty database, pinned venv (CPython 3.13 here, not the image's 3.12): (1) tools/check_snapshots.py --disposable: exit 0, 60 ok lines SNAP-01..11, 'snapshots (neo4j): every check holds', 3m54s. (2) harness/run.py --deterministic --out <dir>: exit 0, S1 PROCEED, S2 BLOCKED, S3 QUALIFIED, S4 BLOCKED, S5 BLOCKED, S6 PROCEED, S7 BLOCKED, 0 model calls, 7s. (3) demo/tools/compare_deterministic.py <dir>: exit 0, 7 scenarios, 0 differing leaves ('OK: 0 differing leaf/leaves over 7 scenario(s)'). (4) demo/tools/check_saved_queries.py: exit 0, 22 ok lines, 'every saved query ran'. D1 on Community 5.26.0: 6 uniqueness constraints accepted; assertion_status (existence), fragment_key (node key), version_sha (property type) refused. The URI row left as is: not proven that other schemes are accepted.

PR #550 head bb0eed7: tests, rdflib, rdflib-readers, stack all green. AC #3 awaits the maintainer's Desktop run.
<!-- SECTION:NOTES:END -->
