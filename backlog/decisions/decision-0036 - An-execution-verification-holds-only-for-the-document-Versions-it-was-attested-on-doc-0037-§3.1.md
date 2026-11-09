---
id: decision-0036
title: >-
  An execution verification holds only for the document Versions it was attested
  on (doc-0037 §3.1)
date: '2026-11-09T21:32:00Z'
status: accepted
---
## Context

The functional review of the 0.9.0 release candidate (doc-0037 §3.1) found the same hole twice, independently:
- group A, F1, `session_01HTAA1UC5tSJ4yRcP1AcDFW`;
- group C, C2-2, `session_01HTAA1RJ9Rg2FP5uZoxBXic`.

The coordinator confirmed it in `harness/load.py`:
- `load_verifications` calls `verify_by_execution` for every live statement whose (key, value) the pristine kit states. It writes `outcome: pass` with `evidence_sha256` the reference code's digest, and no suite runs at load.
- On a subject, the pristine kit is the vendored record, so the record is right.
- On an instance, the pristine kit is the documents on disk, so an edited value is "pristine" and inherits "verified by execution".

The repros:
- C, on the example instance with S1's P2 changed from 316.00 to 341.00: with the shipped `versions`, QUALIFIED with P2|surcharge VERIFIED at 341; without `versions`, PROCEED.
- A: `three_valued_answer P2|threshold` reads 1300 verified, by a suite scenario whose input cannot tell 1244 from 1300.

`docs/guide.md:686` says "the oracle runs again on every load". This contradicts FR-01 and FR-04 on an instance.

## Options

- **(a) Before 0.9.0, bind an execution verification to the document Versions it was attested on,** as decision-0019 binds `authored` and `approval`. An unlisted Version is not verified by execution, so an edit drops the statement below verified. The same holds for every verification kind written per load (review included), wherever it is not yet bound. The guide is corrected.
- **(b)** Correct the guide and name it in the Known limits now; bind it in the first 0.9.x patch.
- **(c)** Run the oracle at load: a larger build, post-1.0.

## Opportunity canvas

- Problem: the gate can say PROCEED on an edited, unverified value.
- Users: every instance and its assistants.
- Cost: one build behind the unchanged shapes; the record's documents are pristine, so the record should not move.
- Value: the gate's verdict means what it says.

## Fit/gap

- (a) makes FR-01 and FR-04 true on an instance.
- (b) ships a known false PROCEED in the frozen release.
- (c) is the full promise, too large for the cut.

## SWOT, (a)

- Strengths: the core claim holds.
- Weaknesses: one more build before the cut.
- Opportunities: decision-0019's binding already exists for approvals.
- Threats: the build finds the record moves; then fall back to (b) and say so.

## Advice

(a), before the cut. It is a build behind the existing report shapes, and the record should not move because its documents are untouched. Otherwise 0.9.0 ships with a PROCEED we know can be false.

## Decision

Accepted by the maintainer on 2026-11-09: "Agreed", quoting the advice. The build is task-0306, which holds the 0.9.0 cut.

decision-0019's read rule for `authored` and `approval` (a declaration that lists no Versions attests per load) is unchanged. An approval applies only to a verified assertion, so a statement that loses its execution verification on an edit is not approved either.

## Consequences

- An execution verification is the subject's attested result, bound to the document Versions it lists: on an instance, an edited document's statements fall below verified until the attestation lists the new Version.
- `docs/guide.md` §9 and :686 say what an execution verification is.
- The 0.9.0 Known limits say that no oracle runs at load.
