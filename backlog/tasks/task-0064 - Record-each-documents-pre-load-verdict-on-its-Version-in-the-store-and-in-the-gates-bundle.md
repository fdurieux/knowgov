---
id: TASK-0064
title: >-
  Record each document's pre-load verdict on its Version in the store and in the
  gate's bundle
status: Done
assignee:
  - '@claude'
created_date: '2026-11-03T23:04:00Z'
updated_date: '2026-11-04T00:17:00Z'
labels:
  - instance
  - gate
  - store
milestone: m-6
dependencies:
  - TASK-0045
references:
  - backlog/docs/doc-0008
priority: low
type: feature
ordinal: 70000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The pre-load check (task-0045) runs on the pull request and its result stays in CI. Once merged, the load reads the document with no memory of whether its form was checked, by which tool, or whether it was left unchecked. A document loaded without a passing check is invisible in the store, in the gate's bundle and on the page. doc-0008 §5 proposed recording "each document's linter verdict (tool, version, digest of the file it judged) on its Version node, so a document loaded without a passing check is visible in the store and in the gate's bundle". The load does not re-run linters: the merge is the check; it only reads the verdict a CI run left.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A load given a preload report (a path or an instance-relative default) records on each document version the tool, its version, the state (clean, findings, unchecked) and the digest of the file judged, through the store port in both adapters
- [x] #2 A version whose bytes do not match the digest judged, or that no report covers, is recorded as unchecked, never as clean
- [x] #3 The gate's bundle and gate_cli.py's JSON list the documents behind the task's keys whose form was unchecked or had findings, as info-level findings that do not change the exit code unless a threshold asks
- [x] #4 The page shows the verdict per document in the ingest stage panel
- [x] #5 The comparator still matches the record for every scenario when no report is given (the field is absent, not empty), and tests cover both adapters
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. tools/preload_check.py records sha256 of the bytes judged per file (schema: optional, additive).
2. harness/preload.py: the report (KG_PRELOAD_REPORT, else <instance>/preload-report.json when the subject sits in an instance), schema-checked; per loaded document, the report row for its instance-relative path; state clean/findings/held as reported when the digest equals sha256 of the text loaded, else unchecked with the reason (no row, no digest, digest differs, cannot run, skipped).
3. Store port record_preload(vid, verdict) and preload_verdicts(), both adapters (Version properties preload_*); load_scenario records them and returns load.preload only when a report is configured (absent otherwise, so the record still matches).
4. gate.resolve_spec: res.preload, only when the store holds verdicts: the documents behind the task's keys (artefact and version of each live statement) unchecked or with findings. gate_cli: info findings, kind 'preload' (schema enum, additive), exit unchanged unless --fail-on info. mcp_server READS gains preload_verdicts.
5. Page: the ingest panel lists the verdict per document when load.preload exists.
6. Tests: stdlib (verdict mapping, gate findings, both adapters' source); harness.yml (rdflib) and the stack job (Neo4j) on the example instance with a report; the comparator unchanged without one.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Report: tools/preload_check.py now records sha256 of the bytes judged per file (optional in the schema; a task-0045 report without it leaves every document unchecked). Matching: the report row by the document's path relative to the subject's instance (the report's own 'instance' path is where its CI ran, not where the load runs). States recorded: clean, findings, held as reported; anything else, a missing row, a missing digest or a different digest -> unchecked. Directory (bundle) artefacts are never one judged file: unchecked. Gate: res.preload only when the store holds verdicts; the documents are the artefact and version (assertion id suffix) of each live statement on a key; a version with no verdict counts as unchecked. A store view without preload_verdicts (test stubs) holds none. Measured on the example instance (pumllint only): S1 records 10 versions, 2 clean (.puml), 8 unchecked; the codegen gate lists 5 documents at info, exit 0, 1 under --fail-on info; S6's v2 decision table is unchecked (its bytes are the stage-2 change). rdflib and a local Neo4j 5.26 give identical load.preload, D6_gate.preload and stage-2 verdicts; check_saved_queries on Neo4j: every saved query ran. Without a report: CargoQuote S1-S7 and J-F 0 differing leaves against the records; the example instance's S1-S7 0. Tests 185/185 (also a bare venv); J-F's test_decision_0004 failure is on main without this change.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The pre-load check's verdict now reaches the store. With a report (KG_PRELOAD_REPORT, or preload-report.json at the instance root), the load records on each document version the tool, its version, the state and the digest judged, through the store port in both adapters (record_preload, preload_verdicts); a version the report does not cover, or whose bytes differ from the digest, is unchecked, never clean. The gate's bundle and gate_cli.py's JSON list the documents behind the task's keys that were unchecked or had findings, as info findings (kind preload) that move the exit only under --fail-on info; the MCP server may read them. The page's ingest panel shows the verdict per document. Without a report nothing is recorded and every output, the record comparisons included, reads as before. harness.yml (rdflib) and the stack job (Neo4j) prove it on the example instance.
<!-- SECTION:FINAL_SUMMARY:END -->
