---
id: TASK-0215
title: >-
  An intended bar: a task class may require approved for its keys (decision-0018
  point 4)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-08T11:17:00Z'
updated_date: '2026-11-08T12:18:00Z'
labels:
  - process
  - reverse-engineering
  - contract
  - gate
dependencies: []
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
ordinal: 215000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0018 point 4 (doc-0032 §3, gap 2; method 1.3: a source defect must not silently become desired behaviour). Today a task class can block on levels and cap the share below verified (gate.py), and PROCEED takes verified or approved, so an observed behaviour verified by execution on the original reads PROCEED without anyone intending it (decision-0011: verified shows the kit and the code agree, not that the behaviour is right). A task class gains an opt-in bar requiring approved for its keys; a key below it is a finding with its owner and route (capture.routing). Opt-in, so no existing task class and no record verdict moves. A contract change (the subject format, the gate report), for 0.9.0 (doc-0028 G9-12).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A task class may declare that its keys require approved; a key verified but not approved is then a finding naming its owner and route, and the verdict follows the class's blocking rule
- [x] #2 Without the declaration every task class reads as today
- [x] #3 subjects/README.md documents the field; tools/check_subject.py checks it; the gate report schema carries the finding
- [x] #4 CHANGELOG.md carries the line under Unreleased's contract heading
- [x] #5 The scored record (S1 to S7), the deterministic run and the comparator stay equal
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. tasks.py: require_approved, opt-in (only true is true).
2. gate.resolve_spec: with the bar, a verified key is unintended and counts with the keys below verified under the class's rule (share, QUALIFIED); PROCEED needs every key approved; unintended in the result only then.
3. gate_cli: an intended finding (major) per such key, owner and route through OWNED (capture.routing); keys.unintended in the report only then.
4. Schemas (gate-report kind and keys.unintended; store-status tasks.require_approved), check_subject, subjects/README.md, CHANGELOG.
5. Tests failing on the old code first; the record, the deterministic run and the comparator unchanged.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Field: [tasks.<class>] require_approved = true. A key read verified (not approved) is then in res["unintended"], counted with below_verified for the share and QUALIFIED rules, why says "below approved"; PROCEED reads "all n required keys approved". Finding kind intended, major, level verified, owner and route from capture.routing (OWNED); report keys.unintended; store_status tasks.<class>.require_approved. Without the field: no new key in the result, report or findings; resolve_spec equal to require_approved false.
The record holds no verified-but-not-approved key in any scenario (S1..S7: approved or below; J-F the same), and no public class declares the bar, so nothing in the record can move; the comparator holds both.
New tests (tests/test_intended_bar.py) failed on origin/main's code (KeyError unintended/require_approved, the check_subject field refused as unknown, the schema without the kind, no CHANGELOG line) and pass on the change.
Checks: stdlib without yaml 724/761 (and J-F 724/761); pinned 759/761, pinned J-F 758/761, 0 failed; comparator 0 differing leaves over S1..S7 and J-F's 6; check_round_trip --chain both subjects; check_mcp_server S1,S2,S6 and C,D3; check_gate_after_change exit 0.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The intended bar: a task class may declare require_approved = true; a key verified but not approved then reads below its bar, an intended finding (major) naming its owner and route from capture.routing, and the verdict counts it as the class counts a key below verified (QUALIFIED, BLOCKED past the share; PROCEED needs every key approved). Opt-in: without it every class and the record read as before. check_subject checks the field, subjects/README.md documents it, the gate report and store_status schemas carry it; CHANGELOG contract line for 0.9.0.
<!-- SECTION:FINAL_SUMMARY:END -->
