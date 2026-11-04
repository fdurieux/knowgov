---
id: TASK-0120
title: >-
  register_impact takes a task class, and flags the keys that rest on a
  withdrawn descendant
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-04T18:19:00Z'
updated_date: '2026-11-04T18:35:00Z'
labels:
  - mcp
  - register
milestone: m-8
dependencies: []
priority: medium
ordinal: 120000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer chose both on 2026-11-04. task-0111 proposed that `register_impact` read each landed key under a named task class, as `gate_verdict --task` does, since the answer a retirement touches differs by class (CargoQuote declares `design` beside `codegen`). task-0118 proposed showing, flagged, the keys that rest on a withdrawn descendant when `children` is on, rather than omitting them silently: a reader who retires a node should see every map row the descent reaches, withdrawn or not, while the walk itself stops there.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 register_impact takes an optional `task` (a declared task class; default the server's default class, codegen). Each landed key's level, block levels and route are read under that class, as `gate_verdict --task` would. On CargoQuote, `design` and `codegen` give their own answers. A `keys` value is refused.
- [ ] #2 With `children=true`, a map row that names a withdrawn descendant lands its keys flagged `withdrawn: true`. They are listed but not walked onward. With children, CAP-0001's dependants walk then lands 32 keys, the 32nd (QuoteAPI|on_notification_failure) flagged.
- [ ] #3 `check_mcp_server.py` checks both on S6, the record is unchanged, and the README tool table and INSTRUCTIONS name the new input.
- [ ] #4 task-0118's per-walk numbers are restated in this task's notes: dependants 31 (32 with the flag), realisers 36, and 36 only across both walks.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. `register_impact.landed_rows` takes the withdrawn descendants: a row naming none of start, walked or reached but a withdrawn descendant lands after the others, `withdrawn: true`, via the withdrawn ids it names.
2. `mcp_server.register_impact` takes `task` (declared class, default codegen; `keys` or anything undeclared refused) and evaluates the landed key set under `TASKS[task]` with `route_task=task`, as `gate_verdict --task --keys`.
3. Tests: CHILDREN_LANDS carries (total, flagged); CAP-0001 dependants 32 with QuoteAPI|on_notification_failure last; per class equality with gate_verdict; design differs from codegen on CargoQuote (route).
4. `check_mcp_server.py`: flag and per-class checks from the parent with children; at S6 stage 2 the classes must differ.
5. Schema text, INSTRUCTIONS, instance/README tool table, CHANGELOG contract heading.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Per-walk numbers, restated from task-0118 (CargoQuote, CAP-0001 with children): dependants 31 keys walked, 32 with the flag (the 32nd QuoteAPI|on_notification_failure, via the proposed CAP-0005 only); realisers 36, none flagged (that row lands through APP-0002/PROC-0005); 36 distinct across both walks, i.e. every codegen key. J-F: CAP-0006 dependants 30, realisers 80, ENT-0006 dependants 154, none flagged.

A flagged key is listed with its level and findings (it is in the gate key set), only the descent stops at it. design vs codegen: at S6 stage 1 every landed key is verified and no finding carries a route, so the two classes agree; at stage 2 the stale findings route by class and the answers differ, which check_mcp_server.py requires. The unit stub (one absent codegen key outside design) differs by route.

Verified: tests/run_tests.py 349/349 on both subjects; KG_STORE=rdflib check_mcp_server.py --scenarios S6 and J-F C,D3 hold. No record file touched.
<!-- SECTION:NOTES:END -->
