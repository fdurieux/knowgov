---
id: decision-0007
title: >-
  Journey reuse shows through shared processes and the name match; no new
  register type for now
date: '2026-11-04T20:25:00Z'
status: accepted
---
## Context

doc-0017 §5. An initiative's new customer journey is often based partly on an existing one. The
register (v0.2.9) has no relationship type for that: a journey's steps are its children by `parent`,
and a step reaches a process by `is_supported_by`. Three options were weighed: (a) no new type,
reuse showing through shared processes plus the name match D3; (b) a register type `derives_from`,
walked from base to derived; (c) one step shared by several journeys through an `includes` link.

## Decision

**(a)** (maintainer, 2026-11-04, on doc-0017's recommendation). Journey reuse shows through the
processes two journeys share (`is_supported_by`) and through the evaluator's exact name match (D3).
The proposal evaluator (task-0130) reports a step of a new journey as "same step as JRN-…" when D3
matches it, marked `inferred`. No relationship type is proposed to ieam-register now.

## Consequences

- A process change already reaches both journeys, through the dependants walk.
- A change to the base journey that is not a process change (its wording, its order, a touchpoint)
  does not reach the derived journey, and copied names stay unchecked by the register. This is a
  known limit of the evaluator's report.
- (b) `derives_from` stays parked as a register proposal (doc-0017 candidate 6). Its trigger is an
  instance that shows a derived journey whose base changed without a process change. (c) is
  rejected.
