---
id: decision-0009
title: >-
  Who attests an authored document's statements: a load verifies and approves by
  construction only what the subject declares
date: '2026-11-04T22:47:00Z'
status: accepted
---
## Context

doc-0018 F1, probe P2 (rdflib, the record's pins, 2026-11-04). `load.load_verifications` always calls
`verify_authored(authored.get("at", ts), authored.get("scope", "authored"), HUMAN["id"])` and then
`approve_verified(approval.get("at", ts), approval.get("record", "approval"), HUMAN["id"])`, whether or
not the manifest declares `[verification] authored` and `approval`. `HUMAN` defaults to
`agent:maintainer`. `verify_authored` marks every `basis = "authored"` assertion verified by review
performed by that agent. `approve_verified` then approves every verified assertion, including the
execution-verified ones. Which statements are authored is the mappers' choice (`harness/extract.py`):
requirement text, links, the bundle mappers' citations, DMN rule counts, Gherkin scenario counts and
PlantUML elements.

The probe subject declared neither table. Its requirement `REQ-01`, written by an assistant and reviewed
by nobody, read `approved`: verification `review`, scope `authored`, agent `maintainer`, approval record
`approval`. Those are the loader's defaults, and no person is named anywhere in the subject. An adopter
who drafts a document with an assistant, or loads an export whose author is unknown, gets the same today.

"Reviewed by construction" was right for the two public kits because someone declared it. Both declare
both tables: `subjects/cargo_quote/subject.toml:154` (authored 2026-10-30, approval 2026-08-06) and
`subjects/jef_data_load/subject.toml:101`. J-F's kit was written by a model, "the reverse engineer from
the code alone". Its declaration is the maintainer's attestation of a review ("the fourth rebuild's
review of the kit ... all corrected", approval "kit CHANGES.md revision 2026-10-24"), not a claim of
authorship. That is what a declaration is for. The defect is the default.

decision-0002 put a person's ruling in a review file: an issued handle with a role, never a model. It
did so for what a person gave (captures), not for documents. decision-0004 keeps an unreviewed capture
from lowering a validated key.

## Decision

**(a), accepted by the maintainer on 2026-11-04** ("approve (a)", in the coordinating session's chat,
relayed by it). The question was who may attest that an authored document's statements were
reviewed and approved, and where that attestation is recorded.

Options:

- **(a) The manifest, required.** `[verification] authored` and `approval` keep their present meaning but
  stop having defaults. A load runs `verify_authored` only when `authored` is declared and
  `approve_verified` only when `approval` is declared. Without them, authored statements stay
  `proposed`, and execution-verified statements reach `verified`, not `approved`. The attester is
  `[provenance] human`, and an instance names it by an issued handle, never a name. The four eyes are
  the pull request that adds the declaration, reviewed by someone other than its author.
- **(b) A review file per artefact version.** decision-0002's route, extended from captures to
  documents: the manifest's tables stop counting, and a review file by an `approves` handle approves an
  artefact version or each of its statements.
- **(c) (a), bound to the versions it attests.** The declaration lists the digest of each artefact it
  covers. A later version of an artefact reads `proposed` until it is attested again, as the pre-load
  verdict is unchecked unless its digest matches (task-0064).
- **(d) No change; document the default** (task-0134 does this while the decision is open).

**Accepted: (a).** (c) follows as its own decision, proposed at m-8. (b) and (d) are rejected.
- (a) is the smallest change that stops "approved by nobody", and it moves no record.
- (c) closes the remaining gap: an attestation silently extends to a later edit, because the next
  load verifies the new version's authored statements under the same declaration. In the public
  subjects a digest test holds the vendored bytes, so the gap is an instance's, not the record's.
- (b) is rejected as the default for documents. Per-statement rulings over a kit's hundreds of
  statements (J-F: 163 requirements) would make the review file a rubber stamp. It stays the route for
  a single statement (decision-0002, as it is).
- (d) is rejected: an instance subject's first load would keep reading approved by nobody.

## Consequences

- **What moves.** `cargo_quote` and `jef_data_load` declare both tables, so their records, the
  comparator and the scored record do not move. `subjects/minimal/` has no artefacts, and the example
  instance is built from CargoQuote. A new or instance subject with no declaration reads its authored
  statements `proposed`. It is BLOCKED when the share below verified exceeds `max_unverified_share`,
  else QUALIFIED, until a person attests by declaring `authored` and `approval` in a reviewed pull
  request.
- **Contract.** The gate's verdict changes for an undeclared subject: a contract change, a minor version
  while 0.x (decision-0003), with a line under `## Unreleased`'s contract changes.
- **The build: task-0136.** `load_verifications` verifies authored statements and approves only on
  a declaration; a test on doc-0018's probe subject (`REQ-01|text` `proposed`, not `approved`); every
  fixture that relied on the default declares it. task-0135's subject check reports, as a note naming
  this decision, a subject whose mappers emit `authored` statements and that declares no `authored`.
  task-0134's README lines move from today's default to the rule.
- **Follow-ups.** (c), an attestation bound to each attested artefact's digest, is a decision to
  propose at m-8, once an instance exists; not created here. doc-0018 candidate 5, the attestation
  hook, guards `[verification]` and `[provenance]` against an assistant's write.
