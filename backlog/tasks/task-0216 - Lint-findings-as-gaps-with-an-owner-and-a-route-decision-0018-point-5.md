---
id: TASK-0216
title: Lint findings as gaps with an owner and a route (decision-0018 point 5)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-08T11:17:00Z'
updated_date: '2026-11-08T13:09:00Z'
labels:
  - process
  - reverse-engineering
  - contract
  - preload
  - gate
dependencies:
  - TASK-0201
references:
  - >-
    backlog/decisions/decision-0018 -
    Reverse-engineering-and-knowledge-gap-identification-is-an-eight-step-process-knowgov-routes-and-re-finds-its-gaps-and-its-three-contract-changes-land-in-0.9.0.md
documentation:
  - >-
    backlog/docs/doc-0032 -
    Reverse-engineering-and-knowledge-gap-identification-as-a-repeatable-process-eight-steps-with-their-tools-and-gaps-the-bases-decision-0011-H7-and-what-F2-must-bind.-Opportunity-canvas-fit-gap-SWOT-advice.md
priority: high
type: feature
ordinal: 216000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0018 point 5 (doc-0032 §2 step 5; Dominique's attribute and route steps). Today the pre-load verdict reaches the gate at info only (task-0064), as form, and nobody is asked to resolve a finding. Each finding of tools/preload_check.py on a loaded document becomes a gap with an owner and a route from capture.routing (task-0201 G8): the document's owning unit, its questionnaire. A resolution (slip, choice, exception, open) is recorded through the existing routes: a slip is a new document version, a choice a decision record and an approval, an exception an elicited statement, an open item a gap with its owner. The info listing of task-0064 stays. A lint gap sits on its document; whether it lowers a key's level is the build's to show and state. A contract change (the gate report; a resolution record), for 0.9.0 (doc-0028 G9-12).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Each pre-load finding on a loaded document is a gap in the store and a gate finding naming the document's owner and route; the baseline (--baseline) holds a finding without raising it
- [x] #2 A finding's resolution (slip, choice, exception, open) is recorded and a re-lint at the same tool versions shows the delta
- [x] #3 Whether a lint gap lowers a key's level is stated in the PR, and the record's verdicts are unchanged
- [x] #4 CHANGELOG.md carries the line under Unreleased's contract heading
- [x] #5 The scored record (S1 to S7), the deterministic run and the comparator stay equal
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. preload.verdicts carries each judged row's findings; preload.lint_gaps makes one gap per finding, id from the document, version, tool, rule, line and message (never store order), held when the baseline holds it.
2. Store port: LintGap label (not Gap: the rules, census kinds and SHACL read the knowledge's gaps), record_lint_gap, resolve_lint_gap, lint_gaps (READS, MCP view); both adapters; the Turtle round trip generic.
3. Load: each judged version's findings recorded; reviews' [[resolves]] applied (not on stage 2's recheck).
4. Gate: lint_behind (the gaps on documents behind the keys, None with none held, so the record reads as before); gate_cli lint finding, the linter's severity at most major, info held or resolved choice/exception; owner and route from capture.routing over the keys behind it, each unit's route when several; a resolve act whose finding is gone at info.
5. review.check [[resolves]] (choice, exception, open; bound by the text's digest; the document's owners under closes); review_toml writes it.
6. preload_check --previous: the re-lint delta at the same tool versions (new, gone as slip or not, kept).
7. tools/check_lint_gaps.py on both stores; schemas; CHANGELOG; tests failing on the old code first.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Evidence (merged head over 3b931bb): tools/check_lint_gaps.py holds on rdflib and on Neo4j 5.26 (planted SEQ002 on the example instance: gap and minor finding behind 15 keys owned by several units, so owner null and each unit's route named; --baseline holds it at info; employee-3 resolves it as a choice, employee-1 refused for lacking closes; mended diagram, --previous delta comparable, SEQ002 gone as a slip, no gap left, the resolve act info; Turtle round trip equal). check_round_trip --chain --expect-preload on the planted instance: rdflib to rdflib (S1, S6), neo4j to rdflib to neo4j (S1). Comparator S1-S7 and J-F: 0 diffs. check_gate_after_change rc 0; check_mcp_server holds on both stores. New tests failed on the old code (AttributeError on preload.lint_gaps, gate.lint_behind, gate_cli.lint_finding, preload_check.delta). A lint gap never lowers a key's level: it sits on its document, the gate lists it beside the keys behind it, levels and verdict equal those of the unplanted instance.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Each pre-load finding on a loaded document is now a lint gap in the store (port: record_lint_gap, resolve_lint_gap, lint_gaps; a LintGap label apart from the knowledge gaps, so the rules, the census and SHACL read as before) and a gate finding of kind lint naming the document's owner and route from capture.routing over the keys behind it, each unit's route when several own them. Its severity is the linter's, at most major; info when the --baseline holds it or a review resolved it as a choice or an exception. A review's [[resolves]] (choice, exception, open) binds to the finding's text by digest and is the document owners' to make under the role closes; a slip is a new version. preload_check --previous reports a re-lint's delta at the same tool versions: new, gone (a slip when the bytes changed), kept. A lint gap never lowers a key's level: S1-S7 and J-F compare with 0 diffs. Proven by tools/check_lint_gaps.py on rdflib (harness.yml) and Neo4j (demo.yml); tests/test_lint_gaps.py; schemas gate-report (kind lint, act resolve) and preload-report (delta); CHANGELOG under Unreleased, Contract changes.
<!-- SECTION:FINAL_SUMMARY:END -->
