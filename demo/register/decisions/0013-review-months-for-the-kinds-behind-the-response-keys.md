# 0013 — Review months for step, touchpoint, module and business entity

Date: 2026-11-04. State: approved (fdurieux, by the merge of #19 on 2026-11-04; the line read proposed when merged). Supersedes: nothing;
extends `metamodel/lifecycle.toml` `[review.kinds]`, whose two rows (capability 12, product 6) and
`default_months = 12` are unchanged.

## Decision

`[review.kinds]` gains four rows:

| kind | months | why this cadence |
|---|---|---|
| `step` | 6 | where the shipper meets the product; the product's cadence |
| `touchpoint` | 6 | the same |
| `module` | 12 | beneath a capability; the capability's cadence |
| `business_entity` | 12 | the same |

No node, link or `review_due` changes. The checker reads no `[review.kinds]` row for a node today;
the reader this affects is knowgov, whose decision-0005 lapses a review verification after the
shortest months among the kinds of the nodes a key's `register_map.toml` row names, else
`default_months`.

## The keys it concerns

knowgov's TASK-0087 (found by its task-0076): CargoQuote's review-only response keys
(`verification_map.toml` `[review]`) `response|statuses`, `response|price_presence` and
`response|quote_id_presence` each name APP-0002 QuoteAPI (`module`), JRN-0004 Quote API
(`touchpoint`), JRN-0003 "Receive the quote, hold or refusal" (`step`) and ENT-0003 Quote
(`business_entity`). None of the four kinds had months, so the keys fell back to the default. Their
seven fellow review-only keys each also name a capability or an activity and held 12 months by the
capability row; `module` and `business_entity` at 12 leave them at 12.

## Effect on CargoQuote

Computed from knowgov's cadence rule (`harness/cadence.py`) over its CargoQuote `register_map.toml`
and the register as of this pull request; the kit's review keys are verified on 2026-08-06
(knowgov decision-0005). Not run through knowgov's gate here; knowgov measures it on vendoring.

| key group | months before | months after | current until | lapsed as of |
|---|---|---|---|---|
| the three response keys | 12 (fallback) | 6 (`step`, `touchpoint`) | 2027-02-06 | 2027-02-07 |
| the other seven review-only keys | 12 | 12 | 2027-08-06 | 2027-08-07 |
| the 26 keys outside the review list, `response\|hold_presence` among them | — | — | not by date | — |

- **As of 2027-08-07**: no change. All ten review-only keys have lapsed under either cadence; S1
  and S6 stage 1 read BLOCKED · 10 · 10 as decision-0005 measured.
- **From 2027-02-07 to 2027-08-06**: the three response keys lapse six months sooner. On S1 and S6
  stage 1, which hold all ten verified today, 3 of 36 keys (8 %) fall below verified, under the
  25 % bar: PROCEED becomes QUALIFIED, naming the three. S7 is unchanged (36 below already). S2 to
  S5 are knowgov's to measure.
- **J-F data load**: no change. 22 of its 163 keys now review at six months, against 21 (the
  product keys) before: one more by a step. Every key rests on an execution verification, which
  does not lapse by date (decision-0005), so nothing lapses.

## Why

The response keys are the API's answer to the shipper: the touchpoint and the step are where the
product is met, and the product reviews at six months. A cadence the register did not set was
knowgov's fallback, which is a default, not a decision. `module` and `business_entity` at 6 would
have moved all ten review-only keys to 2027-02-07 and S1 to BLOCKED that day; that is a different
question (below), not this one's.

## Not decided here

The register's own practice: every approved node's `review_due` is its approval date plus six
months, whatever its kind, while `[review.kinds]` says capability 12 and `default_months` 12. The
checker does not hold `review_due` to the kind's months. Whether it should, and which of the two
gives way, is a later decision. Months for the other kinds (`journey`, the process kinds,
`application`, `logical_entity`, the domains and portfolios) stay at the default.
