---
id: decision-0004
title: >-
  Whether a captured, unreviewed statement lowers a key's level, and what the
  ratchet against the record then does
date: '2026-11-03T23:34:00Z'
status: accepted
---
## Context

doc-0007 F4, task-0039. `gate.resolve` gives a key the lowest status of its live statements (the
min rule, `ORDER`). A capture (task-0009) loads a person's answer as basis `elicited`, status
`proposed`, and nothing but a review (decision-0002, task-0037) raises it. So a correct answer
lowers the key it answers until someone reviews it.

The S2 case, run by command on the example instance (rdflib): S2's `response|statuses` is
`validated` on two extracted statements (contract/openapi.yaml, contract/spec.md). `employee-1`
answers the same value; R-CORROBORATE pairs it with both (task-0038) and raises nothing. The key
reads `proposed`, the verdict stays BLOCKED (OD-1), and

    gate_cli.py --scenario S2 --baseline record
    baseline (record): BLOCKED; REGRESSION; response|statuses validated -> proposed
    exit 1: a regression against the baseline

A pipeline that ratchets on the record fails on the first agreeing answer, and doc-0007 §12 names
the likely end: the ratchet, or capture, is switched off. A contradicting answer is a different
case: since task-0038, R-CONFLICT pairs it with each document statement, all three read
`disputed`, and the key falls to `disputed` whatever this decision says.

## Options

**A. Every live statement counts (today's rule), documented.** An unreviewed capture lowers its key
to `proposed`, agreeing or not, until a review approves it (then min(validated, approved) =
`validated` again) or rejects it.
- S2: `response|statuses` validated -> proposed; `response|hold_presence` absent -> proposed; verdict
  BLOCKED either way. `--baseline record` exits 1 after the capture, 0 again after the review.
- Ratchet: a capture is a regression until reviewed. The adopter reviews before merging the capture,
  or records a new baseline deliberately (`-o`, then commit). The rule stays one line; the cost is a
  red pipeline for knowledge that added no doubt.

**B. An unreviewed elicited statement does not lower a key that holds a better one.** In
`gate.resolve`, a live statement of basis `elicited` at `proposed` is left out of the min when the
key holds another live statement at `validated` or above; it stays in the key's assertions, the
bundle and the questionnaire, marked pending review. Everything else is unchanged: alone on a key it
sets the level (`absent` -> `proposed`); a contradicting one is `disputed` by R-CONFLICT and counts;
a declared gap still outranks it; a review's approval or rejection applies as now.
- S2: `response|statuses` stays validated; `response|hold_presence` absent -> proposed; verdict
  BLOCKED. `--baseline record` exits 0 after the capture.
- Ratchet: a capture regresses a key only by contradicting what the documents say, which is the
  regression a ratchet exists to catch. The deterministic record carries no capture, so the
  comparator does not move. A reader of the level loses one fact (an unreviewed answer exists on a
  validated key); the bundle keeps it.

## Decision

Proposed: **B**. The min rule exists so that the weakest evidence governs what an assistant may rely
on. An agreeing, unreviewed answer adds no doubt to a key two documents already state; the doubt it
could carry, a different value, is what R-CONFLICT has surfaced since task-0038, and that case still
lowers the key. A rule that turns corroboration into a regression teaches adopters to stop
capturing. The maintainer approves by merging this record; until then `gate.resolve` is unchanged.

## Consequences

- Under B, task-0039 changes `gate.resolve` (both adapters read through it, so one place), adds the
  S2 case to the tests (statuses stays validated, an agreeing capture; disputed, a contradicting
  one), and says in `instance/README.md` and the `gate_cli.py` docstring what a capture does to a
  ratchet against the record: nothing, unless it contradicts.
- Under A, task-0039 changes no code: the README and the docstring say that a capture lowers its key
  until reviewed, that `--baseline record` then exits 1, and the two ways out (review it, or record a
  new baseline).
- Either way the gate report's schema does not change; B changes what a level means for a key with
  an unreviewed capture, a contract change under decision-0003 (minor version while 0.x), named in
  the release PR.
- Neither touches decision-0002: who may approve, reject or settle stays as it is.
