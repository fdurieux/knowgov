---
id: decision-0005
title: >-
  A document's verification by review lapses after the review months of the kind
  it concerns
date: '2026-11-04T00:03:00Z'
status: accepted
---
## Context

doc-0013 §5 candidate 3(a), task-0067. A statement verified by review stays verified however long its
document goes untouched: a review verification's `valid_until` is set only when a source change ends
it (R-STALE, the S6 chain). A person's answer is treated more strictly. ieam-register decision 0008
gives an `elicited` link a review within six months, and knowgov decision-0002 lets the approval of a
person's statement lapse six months after the capture's `on`. A document read in 2026 and reviewed
once can therefore hold a key at `verified` in 2030, while a person who said the same thing last
spring has lapsed. The register already says how often each kind is reviewed:
`metamodel/lifecycle.toml` `[review] default_months = 12`, `[review.kinds]` capability 12, product 6.

Execution verifications are not in question. The oracle re-runs the suite on every load, and a source
change already ends them; a passing test is as current as its last run.

Measured on the deterministic record (rdflib, `KG_STORE=rdflib`; harness at `780985a`; register
v0.2.6). Each scenario was loaded as `gate_cli.py` loads it, then the codegen gate was resolved as of
four dates, with a review verification lapsing at its `at` plus the option's months. A statement left
with no current verification reads `validated`. A cell gives verdict · keys below verified · keys
whose statements lapsed:

**CargoQuote** (36 required keys, `max_unverified_share` 25 %; review keys verified at 2026-08-06,
authored statements at 2026-10-30):

| Scenario | today, every option | (a) at any date | (b) or (c) at 2027-02-07 | (b) or (c) at 2027-08-07 and 2027-10-31 |
|---|---|---|---|---|
| S1 | PROCEED · 0 · 0 | unchanged | PROCEED · 0 · 0 | **BLOCKED · 10 · 10** |
| S2 | BLOCKED · 3 · 0 | unchanged | BLOCKED · 3 · 0 | BLOCKED · 12 · 9 |
| S3 | QUALIFIED · 4 · 0 | unchanged | QUALIFIED · 4 · 0 | **BLOCKED · 13 · 9** |
| S4 | BLOCKED · 1 · 0 | unchanged | BLOCKED · 1 · 0 | BLOCKED · 11 · 10 |
| S5 | BLOCKED · 3 · 0 | unchanged | BLOCKED · 3 · 0 | BLOCKED · 12 · 9 |
| S6 (stage 1) | PROCEED · 0 · 0 | unchanged | PROCEED · 0 · 0 | **BLOCKED · 10 · 10** |
| S7 | BLOCKED · 36 · 0 | unchanged | BLOCKED · 36 · 0 | BLOCKED · 36 · 0 |

**J-F data load** (163 required keys; review at 2026-10-24): C and D1 read PROCEED · 0 · 0, D2 to D5 read QUALIFIED with 6, 6, 2 and 5 keys below verified. These verdicts are the same under every option at every date measured. No statement lapses, because every key rests on an execution verification derived from the suite's `verified_by` tags (`[verification] derive_execution`). Under (b), 21 of the 163 keys concern a product and would review at six months, but nothing they hold is review-only.

Three readings:

- The ten keys are the kit's review-only keys (`verification_map.toml` `[review]`), verified on
  2026-08-06. 10 of 36 below verified is 28 %, above the 25 % bar, so S1 and S6 go to BLOCKED, not
  QUALIFIED. The authored statements (2026-10-30) sit on requirements and links, not on codegen
  keys, so 2027-10-31 adds nothing.
- On both subjects, (b) and (c) give the same result. Every key's `register_map.toml` row names only
  capabilities, processes, applications and entities, all at twelve months. On J-F the 21
  product keys are verified by execution. The two options would differ on a review-only key that
  concerns a product, which (b) reviews at six months.
- **Read against the wall clock, the record moves on 2027-08-07.** `demo/tools/compare_deterministic.py`
  would fail that day with no change to the code. `--baseline record` would report ten regressions.
  Whichever option lapses by date, the record must be read as of a pinned date.

## Options

**(a) No date lapse, documented.** Review verifications end only on a source change. The README and
the guide say so. The record never moves. A key can stay `verified` for years on one review, which
is the asymmetry this record exists to settle.

**(b) The review months of the kind the key concerns.** A review verification is current until its
`at` plus the shortest review period among the kinds of the register nodes the key's
`register_map.toml` row names (`[review.kinds]`, else `default_months`). A key with no row takes
`default_months`. Past that date the statement reads `validated`. The register and the store keep one
cadence.

**(c) One default.** `default_months` for every key. It is simpler, but a product's six months are
ignored.

## Decision

**(b)**, approved by the maintainer on 2026-11-03 in session
https://claude.ai/code/session_01HTAA1SbMoohquJnGyrve5d ("go with your recommendations on the four
decisions"; doc-0013 §8, PR #111). Recorded as accepted on that approval.

1. **What lapses.** A verification of method `review`, including the maintainer's review of authored
   statements (`verify_authored`), is current until `at` plus the months of point 2. Execution
   verifications do not lapse by date. A source change ends any verification as it does today, and
   it ends first if it comes first.
2. **The months.** The shortest `[review.kinds]` months among the kinds of the nodes the key's row in
   the subject's `register_map.toml` names, else the register's `default_months`. The register's
   `lifecycle.toml` is read, never copied. When the register changes its cadence, the store follows.
3. **What a lapse does.** A statement left with no current verification reads `validated`, and its
   approval falls with it: an approval rests on a verification. The key's level then follows the min
   rule as today. A lapse is a gate finding, as stale statements are since task-0048, so a pipeline
   sees why the level fell. Nothing is deleted: the verification keeps its `at` and gains the
   `valid_until` date it lapsed on.
4. **Renewal.** A new review by the owner stand-in or a person with `approves` renews it from the new
   date, through the review file (decision-0002). Re-running the oracle renews nothing that was
   reviewed rather than executed.
5. **The as-of date.** The gate reads currency as of a date. `gate_cli.py` takes `--as-of DATE`,
   which defaults to today. A deterministic run and the comparator read as of the subject's pinned
   record date, so the record never moves by the clock. A run for an instance's pipeline reads as of
   today, so the ratchet catches currency loss.

## Consistency with decision-0004

decision-0004 (B) leaves an unreviewed elicited statement out of the min when the key holds another
live statement at `validated` or above. A lapsed document statement reads `validated`, so B still
applies: an agreeing capture on a lapsed key does not lower it further. The two rules now ask one
question, "is this current?", with one cadence. A person's answer, alone on a key, sets `proposed` as
before. Its own approval lapses at six months (decision-0002), the same as or sooner than any kind's.

## Effect on `gate_cli.py --baseline record`

- Read as of the record's date (the default for the record), nothing changes: exit 0 where it was 0.
- Read as of today in an instance, a key falls when its review lapses. The baseline names it
  `verified -> validated` (REGRESSION) and the gate exits 1. That is the ratchet working: the remedy
  is a review, or deliberately recording a new baseline. On CargoQuote as of 2027-08-07, ten keys of
  S1 regress, and the verdict PROCEED -> BLOCKED is reported against the record.

## Consequences

- task-0068 implements it:
  - both adapters through `gate.resolve` and the verification reads;
  - the `--as-of` flag;
  - a `lapsed` finding in the gate report;
  - the subject's pinned record date read by `run.py --deterministic` and the comparator;
  - tests for the S1 case at 2027-08-07, a product-concerning key at six months, and renewal by review;
  - `instance/README.md`, `docs/guide.md` and the `gate_cli.py` docstring.
- Contract change under decision-0003, a minor version while 0.x: a new flag on the gate command, a
  finding kind in `harness/schemas/gate-report.schema.json`, and a change to what a level means for a
  key whose review has lapsed. The release PR names it.
- No change to the register or to decision-0002. The register's cadence is read as it stands. Who may
  renew a review stays decision-0002's.
- S6's re-verification (`[scenario.stage2] at = 2026-10-30`) lapses on the same rule. Stage 2 was not
  part of this measurement; task-0068's tests cover it.
