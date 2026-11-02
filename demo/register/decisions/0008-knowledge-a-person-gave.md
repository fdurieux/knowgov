# 0008 — Knowledge a person gave: who, when, the record of the answer, and a shorter review

Date: 2026-11-02. State: approved (fdurieux, by the merge of #10 on 2026-11-02; the line read proposed when merged). Supersedes: nothing.

## Decision

Two metamodel additions, both checked by `tools/check_register.py`; no node, link, state,
relationship type or glossary term changes.

**1. A person as a source.** Knowledge that rests on what a person said, and not on a document
or a system's export, is recorded as data with three fields, `metamodel/types.toml` `[elicited]`:

| field | holds | checked |
|---|---|---|
| `from` | the person, as an opaque handle (`^[a-z][a-z0-9-]{1,39}$`) | the pattern: never a name, an e-mail address or a staff number |
| `on` | the date the person gave it | a date, not in the future |
| `record` | the path of the record of the answer: the answered questionnaire or the decision that quotes it | the path exists |

On a link it is an inline table, `elicited = { from, on, record }`. The handle's key to a real
person lives in the organisation's own instance, outside any public repository; this test case
uses role handles only. knowgov's capture path (its task-0009) writes the same three fields on
every assertion it ingests from an answered questionnaire, so a statement from a person is named
the same way in the register and in the knowledge store.

**2. An elicited evidence class with a shorter review.** `metamodel/lifecycle.toml`
`[review.evidence] elicited = { months = 6 }`: a link carrying an `elicited` block must have a
`review_due` no later than six months after `on`, whatever its type's default (twelve months for
a capability, six for a product). A person's memory ages faster than a document's text, and the
check refuses a link that claims otherwise.

**What the register already required, and keeps.** The other capture fields the knowgov brief
names exist here already and are unchanged: a link's `rationale` (types.toml `[relationship]`
`required`), an exception's `rationale` and its expiry (`exceptions/`), and the decision record
every approval names (`approval.record`). The four together are the register's required capture
fields; knowgov's `instance/README.md` points here for them.

## Why

Knowledge that lives only in people shows in the knowgov gate as an absent key or a declared gap,
and it blocks. The cheapest capture route is a questionnaire per owner generated from the gate's
gap list (knowgov task-0009); an answer must then land somewhere that says who gave it, when, and
where the answer is kept, so it can be reviewed and, when the person leaves, found. A model may
propose such knowledge as an inferred statement; it never gives it, so `from` is always a person's
handle and never a model.

## Not decided here

How a handle maps to a person (the organisation's own record, kept privately), and whether a node
may carry an `elicited` block (a node holds identity and a checked name only, so not now).
