---
id: TASK-0067
title: >-
  Decide whether a document's verification by review lapses by date, under the
  register's review cadence
status: Done
assignee:
  - '@claude'
created_date: '2026-11-03T23:53:00Z'
updated_date: '2026-11-04T00:04:00Z'
labels:
  - capture
  - gate
milestone: m-5
dependencies:
  - TASK-0039
references:
  - backlog/docs/doc-0013
priority: medium
ordinal: 71000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0013 P1. A review verification never lapses by date: a statement verified by review stays verified however long its document goes untouched, while a person's answer lapses in six months (register decision 0008). The register already sets review months per kind (metamodel/lifecycle.toml). Needs a maintainer decision first: options (a) no date lapse, documented; (b) the owning kind's review months, then the statement reads validated (recommended by doc-0013); (c) one default.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A knowgov decision record (proposed, the maintainer approves by merging) weighs the options with their effect on the record's S1–S7 verdicts and on gate_cli --baseline record
- [x] #2 The record is consistent with decision-0004 (option B) and names the contract change under decision-0003
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Measure options (a)-(c) on the deterministic record of both subjects (rdflib, gate_cli's load) as of four dates, with review verifications lapsing by option. 2. Write decision-0005 through the CLI, status accepted on the maintainer's 2026-11-03 approval (doc-0013 §8), with the measurement, consistency with decision-0004 and the decision-0003 contract change. 3. Docs-only PR.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Measured (scratch script, not committed): CargoQuote S1 and S6 go PROCEED -> BLOCKED and S3 QUALIFIED -> BLOCKED from 2027-08-07 under (b) or (c): its ten review-only keys were verified 2026-08-06, and 10 of 36 is above the 25 % bar. J-F does not move, because all 163 keys rest on execution verifications. (b) = (c) on both subjects today. Finding: read against the wall clock, the record moves on 2027-08-07, so the decision adds an as-of date (gate_cli --as-of, with the record pinned). AC#1 asked for 'proposed'; the coordinator directed accepted because the maintainer approved (b) in this session on 2026-11-03.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
decision-0005 (accepted): a review verification lapses after the shortest [review.kinds] months among the kinds of the key's register_map nodes (else default_months); past that the statement reads validated and its approval falls; a lapse is a gate finding; renewal by review; gate_cli --as-of with the record pinned, so the comparator never moves by clock. Measured on both subjects as of four dates; consistent with decision-0004 B; minor version under decision-0003. task-0068 implements it.
<!-- SECTION:FINAL_SUMMARY:END -->
