---
id: TASK-0088
title: >-
  The register-cites saved query joins directory artefacts as
  register_node_statements does
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T01:31:00Z'
updated_date: '2026-11-04T02:25:00Z'
labels:
  - register
  - impact
milestone: m-6
dependencies:
  - TASK-0077
priority: low
ordinal: 92000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by task-0077: register-cites still joins citations to artefacts by exact path, so for directory artefacts (J-F's contracts/, uml/) with <file>: locators its digest comparison means nothing.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 register-cites matches directory artefacts by locator, as the fixed join does
- [x] #2 check_saved_queries.py and a stdlib test cover a J-F directory citation
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. REGISTER_CITES in store_neo4j: the artefact join of _NODE_STATEMENTS; a directory part matched by its fragments' '<file>:' locators, its version named with the directory and the fragment count (the version digest is the bundle's, so no comparison); a file artefact compared by digest as before.
2. check_saved_queries.py: every cited document the subject loads has a version; a directory part is never compared by digest; counts printed.
3. demo.yml: check_saved_queries on J-F C after check_node_statements, the counts pinned.
4. Stdlib test on J-F's register citations and the check's verdicts; prove on Neo4j 5.26 both subjects.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
rdflib has no console (console_query is Neo4j's only), so the saved query is proven on Neo4j 5.26.0 community (tarball, Java 21): J-F C register-cites 15 documents, 1 file artefact (requirements.json same as tag), 13 files of a directory artefact (contracts/chain.md: v1 in contracts/, 31 fragments), README.md not loaded; CargoQuote S6 8 file artefacts, contract/decision_table.md v1 same as tag, v2 differs, unchanged. check_node_statements J-F ENT-0009 28 / 707 unchanged. tests/run_tests.py 247/247 plain and with KG_SUBJECT=subjects/jef_data_load. Found on the way: the old query's comment line held a ';', which check_saved_queries splits on; the new text holds none (tested).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
register-cites now joins as register_node_statements does: the file artefact of the cited path, or the file's fragments in a directory artefact by their '<file>:' locators. A directory part's version is named with its directory and fragment count, since its digest is the whole bundle's; only a file artefact's digest is compared with the register's. check_saved_queries.py fails when a cited document the subject loads finds no version or a directory part is compared by digest; demo.yml runs it on J-F C (15 documents: 1 file artefact, 13 directory parts, README.md not loaded); a stdlib test covers J-F's directory citations and the check's verdicts. Proven on Neo4j 5.26 both subjects; rdflib has no console. Follow-up, not started: a per-file digest on a directory artefact's Version would let a part be compared too.
<!-- SECTION:FINAL_SUMMARY:END -->
