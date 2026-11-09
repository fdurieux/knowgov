---
id: decision-0037
title: >-
  A gate report names the corpus it decided on, and a baseline names each
  identity field that differs (doc-0037 §3.3)
date: '2026-11-09T21:39:00Z'
status: accepted
---
## Context

The functional review of the 0.9.0 release candidate (doc-0037 §3.3; group A, `session_01HTAA1UC5tSJ4yRcP1AcDFW`, at `main` `f194aac`) found two audit gaps (FR-03, U5):
- **A-F2.** Gate-report v3 names `task_profile`, `register` and `knowgov` (decision-0029). A document's content shows only as the label `version: "v1"`. After an in-place document edit, all four are identical to the pristine report's; only the verdict, `why`, the findings and the levels differ. A reviewer cannot tell from the report alone that the documents differed.
- **A-F3.** `--baseline FILE` accepts a baseline whose `task_profile`, `register.tag`, `knowgov.version` or `as_of` differ, with "no regression", exit 0, and says nothing. It does refuse another scenario or task.

The report's schema is `additionalProperties: false`, so (a) is a contract change: before the 0.9.0 cut, or a 0.10.0.

## Options

- **(a)** A `corpus` digest in the report's identity: sha256 over the loaded document Versions' digests, in a stated order. This completes decision-0029's "what it decided on". `--baseline` names on stderr each identity field that differs from the baseline's: `task_profile`, `register`, `knowgov`, `corpus`, `as_of`. A note, not a refusal, since a baseline exists to compare across a change.
- **(b)** Name both in the Known limits until 0.10.0.

## Opportunity canvas

- Problem: a reviewer cannot replay or audit a verdict from the report alone.
- Users: auditors (U5) and pipelines.
- Cost: one schema field and a note.
- Value: decision-0029 complete.

## Fit/gap

- (a) completes FR-03's audit claim.
- (b) freezes a report that cannot say what it read.

## SWOT, (a)

- Strengths: replay is complete.
- Weaknesses: one more field to freeze.
- Opportunities: decision-0029 already shaped the identity block.
- Threats: none to the record; its corpus is fixed, and the comparator compares outcomes, not identity.

## Advice

(a). It is one field and one note, and it makes a verdict auditable from the report alone.

## Decision

Accepted by the maintainer on 2026-11-09: "§3.3 (a)". The build is task-0307, which holds the 0.9.0 cut.
