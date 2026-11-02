---
id: TASK-0023
title: Saved query register-impact draws a smaller walk than the panel reports
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-02T07:35:00Z'
updated_date: '2026-11-02T09:28:00Z'
labels:
  - register
  - store
milestone: m-3
dependencies: []
references:
  - harness/store_neo4j.py
  - demo/register/tools/impact.py
  - tests/test_register_view.py
  - demo/tools/check_saved_queries.py
priority: medium
type: bug
ordinal: 31000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The page lists a saved Cypher query, register-impact in harness/store_neo4j.py, titled as the impact walk. It follows REG_SUPPORTS|REG_IS_SUPPORTED_BY|REG_DELIVERS*1..4 forward only with no state filter, so it follows is_supported_by from step to process (the wrong way for a walk leaving a process), omits realizes and concerns, and ignores the stop at a deprecated or retired node that demo/register/tools/impact.py walk() applies. Measured at ieam-register v0.2.1 (investigation of 2026-11-02, the simulation script and a live run against a projected Neo4j): APP-0002 3 of the walk's 5 edges, APP-0005 5 of 9, PROC-0006 2 of 6, disagreement on 24 of 56 nodes; no journey step is ever reached, while demo.yml asserts the walk reaches JRN-0002; from a journey step the query over-reaches (JRN-0002: walk 0 edges, query reaches PROC-0002). tests/test_register_view.py test_projection_is_wired_and_named pins the wrong literal in place; demo/tools/check_saved_queries.py proves the text parses, not that it says what the panel says. The walk's rules: applications follow supports; processes follow delivers, realizes, and is_supported_by backwards; journeys follow concerns; any link state; a deprecated or retired node is reached, not expanded; no parent climb; depth three. A fixed-stage pattern (eight chains in a CALL { } UNION, intermediate nodes filtered on state, end node unfiltered) reproduces the walk on 56 of 56 nodes in simulation over register_project.rows() and in a live run. Precedent: TASK-0020, the saved query that had never run.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 register-impact is the fixed-stage pattern, with the intermediate-state filter and the inverse is_supported_by stage, and its title says it is the walk impact.py makes
- [ ] #2 A test in tests/test_register_view.py simulates the pattern over register_project.rows() and asserts its distinct edge set equals impact.walk()'s for every node of the register copy
- [ ] #3 check_saved_queries.py still runs the query in the stack job, and the job asserts the row count the walk gives for its start node
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Replace register-impact in harness/store_neo4j.py with the fixed-stage pattern (eight chains in CALL { } UNION, start and intermediate nodes filtered on state, end node unfiltered, is_supported_by inverse stage), as module constants IMPACT_START, IMPACT_WALK, IMPACT_ROWS and IMPACT_PATHS so later tasks can substitute the start and surface both forms; the title says it is the walk impact.py makes.
2. In tests/test_register_view.py, parse the adapter's text (the CALL block's branches: typed relationship sets, directions, taxonomy and state filters) and simulate it over register_project.rows(); assert the distinct edge set (from, relationship, to, link) equals impact.walk() for every node of demo/register, and for a small fixture register with a deprecated intermediate node, which no vendored node exercises.
3. Update test_projection_is_wired_and_named, which pinned the wrong literal.
4. demo.yml: the saved-queries step keeps running check_saved_queries.py and asserts register-impact's row count equals the edge count GET /api/register/impact gives for the same start.
5. python tests/run_tests.py; verify against a live Neo4j 5.26 if the tarball can be fetched; PR, green matrix, merge.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Second investigation run (2026-11-02, live Neo4j 5.26.0 in the session, register projected at v0.2.1): a quantified-path-pattern form of the same rules also equals the walk on 56 of 56 nodes, in the rows form with evidence joined from RegLink (evidence sits on the RegLink node, register_project.py lines 80-81, not on the typed relationship) and in the graph form; the shipped query equals the walk on 32 of 56. Caveat for the test: no node in the vendored register exercises the stop at a deprecated intermediate node (JRN-0008 has no outgoing concerns link), so the equivalence test needs a small fixture register with one, beside the real copy.

Implementation (branch claude/impact-cypher): harness/store_neo4j.py holds IMPACT_START ('APP-0002'), IMPACT_WALK (the MATCH and the eight-branch CALL { } UNION), IMPACT_ROWS (one row per edge, evidence joined from RegLink, ORDER BY link; the saved query register-impact) and IMPACT_PATHS (OPTIONAL CALL, RETURN a, p: a start with no edge still draws itself). The title names tools/impact.py. tests/test_register_view.py parses the CALL block's branches from the adapter's text (typed relationship sets, directions, taxonomy and state filters) and simulates them over register_project.rows(): equal to impact.walk() on every node of demo/register at v0.2.1, and on a fixture register with a deprecated intermediate process, a retired journey step, a deprecated start, two links of one type on one pair and a parent. The test also pins the register's kinds that bound every chain to three steps. test_projection_is_wired_and_named no longer pins the old literal. demo.yml's saved-query step tees the checker's output and asserts register-impact's row count equals the edge count of GET /api/register/impact/<start> for the start the listed text names.

Live verification in the session: Neo4j 5.26.0 community started from the tarball (Java 21), the register projected through register_project.project, both forms run through console_query for all 56 nodes: rows equal walk() on 56 of 56 (from, relationship, to, link state, owner, evidence), the paths form's distinct relationships count equal on 56 of 56 and every start returned itself. check_saved_queries.py: every saved query ran, register-impact 5 rows; the stack job's new assertion passed against the local server (5 rows, 5 edges). python tests/run_tests.py: 84 of 84.
<!-- SECTION:NOTES:END -->
