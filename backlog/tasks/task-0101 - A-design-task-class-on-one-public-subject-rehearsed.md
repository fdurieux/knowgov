---
id: TASK-0101
title: A design task class on one public subject, rehearsed
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T09:47:00Z'
updated_date: '2026-11-04T12:46:00Z'
labels:
  - gate
  - subjects
milestone: m-8
dependencies: []
priority: medium
type: feature
ordinal: 104000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From doc-0014 (C3). Add [tasks.design] to cargo_quote: the keys a requirements-and-design pass rests on, with rationale and block_levels. codegen and its frozen record stay untouched; store_status and the lighthouse rehearsal show both classes. A plan or review class follows only if the pilot asks.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The gate runs --task design on S1-S7 and the verdicts are recorded in the task notes
- [x] #2 The comparator and the codegen record are unchanged
- [x] #3 docs/lighthouse-evaluation.md names which class each pilot transition uses
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. [tasks.design] in subjects/cargo_quote/subject.toml: 36 keys a requirements-and-design pass rests on, rationale, codegen's block levels and bar; codegen untouched.
2. harness/tasks.py carries an optional rationale; store_status reports it.
3. tools/lighthouse_evidence.py runs every declared class per scenario (--no-load, no record comparison) and records the classes store_status lists; the summary shows both.
4. docs/lighthouse-evaluation.md: the class at each pilot transition (spec=design, plan and push=codegen); subjects/README.md names rationale.
5. Tests; S1-S7 design verdicts as of 2026-10-30 into the notes; comparator, round trip, MCP check, rehearsal.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Design verdicts, gate_cli.py --task design --as-of 2026-10-30, rdflib (codegen beside, as the record):
- S1 QUALIFIED exit 0 (codegen PROCEED): 5 keys below verified, the C4 calls (quote_api|uses:notification_service, quote_store, screening_service, tariff_engine; shipper|uses:quote_api), proposed, never verified.
- S2 BLOCKED exit 1 (codegen BLOCKED): REQ-06|text absent, QuoteAPI|on_screening_outage declared_gap (OD-1).
- S3 QUALIFIED exit 0 (codegen QUALIFIED): 9 below verified, 10 flagged ambiguous (the screening bands' bounds, statuses, notifications) plus the 5 C4 calls.
- S4 BLOCKED exit 1 (codegen BLOCKED): QuoteAPI|on_screening_outage disputed.
- S5 BLOCKED exit 1 (codegen BLOCKED): REQ-06|text absent, QuoteAPI|on_screening_outage declared_gap.
- S6 QUALIFIED exit 0 (codegen PROCEED): as S1. Stage 2, before and after --reverify: QUALIFIED, exit 1 on the subject-wide blocker finding (the suspect derived output); the change touches pricing keys the design class does not name.
- S7 BLOCKED exit 1 (codegen BLOCKED): 36 of 36 below verified, bar 25%.
Checks: comparator over S1-S7 identical (rdflib, D1 skipped by kind); vendored record and codegen table untouched; check_round_trip --chain rdflib,rdflib equal with 2 gate reports per scenario; check_mcp_server S1,S2,S6 holds; lighthouse_evidence (CQ full, J-F C,D3) exit 0, both classes shown; run_tests 325/325 for both subjects.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
CargoQuote gains [tasks.design]: 36 keys a requirements-and-design pass rests on (requirement text and carrier, screening bands and outcomes, failure behaviours, flow order, response statuses, the C4 calls), a rationale, codegen's block levels and bar. codegen and the record untouched; comparator identical over S1-S7. store_status reports a class's rationale; the lighthouse rehearsal runs every declared class per scenario and records the classes store_status lists. docs/lighthouse-evaluation.md maps the hook stages: spec=design, plan and push=codegen (--task codegen --task-for spec=design). Verdicts as of 2026-10-30 in the notes: S1/S3/S6 QUALIFIED (the C4 structure is never verified), S2/S4/S5/S7 BLOCKED. Follow-ups proposed, not created: the instance's hook snippets could carry --task-for spec=design for a subject that declares it; verify the C4 calls (or keep them as proposed) if a design pass should read PROCEED on a clean kit.
<!-- SECTION:FINAL_SUMMARY:END -->
