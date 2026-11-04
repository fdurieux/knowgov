---
id: TASK-0077
title: J-F register anchors reach no statements through register_node_statements
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-04T00:44:00Z'
updated_date: '2026-11-04T01:08:00Z'
labels:
  - register
  - impact
milestone: m-6
dependencies: []
priority: medium
ordinal: 81000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by the task-0071 session: register_node_statements (task-0046) returns statements for CargoQuote's anchored citations but none for J-F's. Either J-F's citations carry no anchors the store can match, or the join misses its fragment ids.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The cause is named in the task notes with the measured counts per subject
- [ ] #2 Either the join is fixed and a J-F node reaches its statements in CI, or the missing anchors are listed as a proposal to ieam-register
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Measure per subject: approved citations with the subject's prefix, anchored, projected as REG_CITES, reaching statements.
2. Fix the cause in knowgov: the projection's prefix and the join to directory artefacts, in both adapters and the saved queries that share the join.
3. tools/check_node_statements.py: the measurement as a check, pinned per subject; run in harness.yml (rdflib) and demo.yml (Neo4j).
4. Prove locally on rdflib and Neo4j 5.26; tests plain and with KG_SUBJECT=subjects/jef_data_load.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Cause: in knowgov, not the register. Two faults, then a third the fix exposed.
1. demo/app/register_project.rows built cites only for evidence starting 'kit:' (and _doc_key stripped only that); J-F's evidence is 'jef_kit:', so the projection carried no REG_CITES for it. Now the subject's prefix, register_view._ps().sys.
2. The join matched Artefact.id = RegDocument.path only. J-F's contracts/, contracts/dmn/ and uml/ are directory artefacts whose fragments are '<file>:<path>' (chain.md:row/15), so contracts/chain.md matched nothing. Both adapters now take the file artefact of the path or the file's fragments in a directory artefact, the anchor read after '<file>:' (_NODE_STATEMENTS, shared by the port and the saved query register-node-statements; MODULE_STORE, the same join at document grain).
3. rdflib keyed rows by statement; the Cypher groups by statement and document. A J-F statement two cited documents support (A:con:JDL-043|elaborated_by@v1: leg.md and store.md) gave 705 rows on rdflib against 707 on Neo4j. rdflib now keys by (statement, document); the port's docstring says so.
Measured (approved links, evidence with the subject's prefix; reaching = at least one statement from either endpoint):
- CargoQuote S6, before and after: 21 citations, 11 anchored, 21 projected, 21 reaching (11 anchored); 17 nodes, all reaching; ENT-0004 13.
- J-F C before: 80 citations, 47 anchored, 0 projected, 0 reaching; ENT-0004 0, every node 0.
- J-F C after: 80, 47, 80 projected, 74 reaching (all 47 anchored); 28 nodes, 24 reaching. The 6 others are jef_kit:README.md (REL-09004..09009 from ORG-0003): in the export manifest, loaded by no J-F artefact; listed, not failed. No anchor is missing from the register, so no ieam-register proposal.
Proof: tools/check_node_statements.py (fails on a short projection or a loaded document reaching nothing; --node/--expect, --total over every register node). harness.yml (rdflib) and demo.yml (Neo4j) run CargoQuote ENT-0004 13 / total 392 on S6 and J-F ENT-0009 28 / total 707 on C (ENT-0009: contracts/store.md, contracts/dmn/actions_gate.dmn, requirements.json#JDL-040/044/086/089). Locally on rdflib and Neo4j 5.26.0 community (tarball, Java 21): register_node_statements for every register node of both subjects identical across the adapters; check_saved_queries ok; the page's impact panel for J-F ENT-0009 shows 28. tests/run_tests.py 220/220 plain and with KG_SUBJECT=subjects/jef_data_load. PR #126.
Left: the register-cites saved query still joins by exact path; its register digest against the version digest has no meaning for a directory artefact.
<!-- SECTION:NOTES:END -->
