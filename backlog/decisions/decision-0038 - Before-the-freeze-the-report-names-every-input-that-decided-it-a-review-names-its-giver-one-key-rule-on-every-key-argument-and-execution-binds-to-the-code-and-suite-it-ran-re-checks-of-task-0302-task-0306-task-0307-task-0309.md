---
id: decision-0038
title: >-
  Before the freeze: the report names every input that decided it, a review
  names its giver, one key rule on every key argument, and execution binds to
  the code and suite it ran (re-checks of task-0302, task-0306, task-0307,
  task-0309)
date: '2026-11-11T08:26:00Z'
status: accepted
---
## Context

The re-checks of the cut's builds found six gaps in what the 0.9.0 contract promises. None is a regression; each was outside the claim of the task it came from. Each would be a 0.10.0 change after the freeze (decision-0016).

- **N2** (reviewer A, re-check of task-0307, `121370c`). The identity covers the document Versions only. Changing `subject.toml`'s `[verification]`, `[provenance]` or `[capture]`, a capture or review file, or the vendored register under the same tag can move S1 from PROCEED to BLOCKED while `task_profile`, `register`, `knowgov`, `corpus` and `as_of` are all unchanged.
- **N3** (same). Only the CLI names identity drift, on stderr. MCP `gate_verdict` with a baseline reports the regression but not why.
- **N4** (same). The corpus digest's input line `<artefact>\t<version>\t<sha256>` is not injective for a tab or newline in an id, and `None` and `""` hash alike. The field is unreleased.
- **G1 and G2** (group 3, re-checks of task-0308 and task-0310, `9a1df7e` and `02167e4`). A vanished capture's giver is read from its file stem. With issued handles `X` and `X-n`, no answer of `X-n` can be approved, and a dispute raised by one cannot be settled by any review. task-0308 and task-0310 made this fail closed and refused it at write time; the cause remains.
- **N7** (spot check, re-check of task-0309, `9a1df7e`). The single-`key` tools (`three_valued_answer`, `derived_outputs`, `key_nodes`) publish a bare-string `key`. Nonsense, invisible or astral keys come back as a silent `unknown` or an empty answer, which is K1's class.
- **N-b** (reviewer A, re-check of task-0306, `e4f73e0`). An execution verification records `evidence_sha256` of the reference code, but the load compares it with nothing. Editing `reference_impl.py` keeps every execution verification and PROCEED, and nothing is named.

## Options

- **(a)** Close each before the cut, additively where a shape grows:
  - N2: the identity also names what decided it beyond the documents.
  - N3: a `differs` list in the CLI report and in MCP `gate_verdict`'s baseline.
  - N4: canonical JSON lines in the corpus digest.
  - G1: the review file records the ruled answer's giver.
  - N7: `KEY_ITEM` on every single-`key` argument.
  - N-b: `[verification] execution` lists the digest of the code it ran on.
- **(b)** A Known-limits line for each, until 0.10.0. For N7: refuse in the handler with the schema unchanged. For G1: a different same-day suffix, or a register rule against `X` and `X-n`.

## Opportunity canvas

- **Problem.** A replay cannot tell from the report alone what changed. One reader is silent where the other speaks. One person's approval can be blocked by another's file name. "Verified by execution" survives a change to what was executed.
- **Users.** A reviewer replaying a gate (U5), a CI baseline, an assistant reading the MCP verdict, the owner settling a dispute.
- **Value.** The 0.9 identity becomes complete before the 30-day soak, which is when an adopter first relies on it.
- **Cost.** One narrow contract build and one re-check, about two to three hours.

## Fit/gap

- **decision-0029 and decision-0037** ("the report names what it decided on"). (a) completes the identity; (b) leaves "same identity, different verdict".
- **decision-0019 and decision-0009** (an approval binds to its giver; a ruling is a person's act). (a) binds by the giver read from the capture's content; (b) keeps the stem heuristic.
- **decision-0034** (one key rule). (a) applies it on every key argument.
- **decision-0036** (execution binds to what it attested). (a) extends it from the documents to the code and the suite.
- **decision-0016** (0.9.0 is the freeze). (a) lands before it; (b) defers to 0.10.0.

## SWOT, (a)

- **Strengths.** Every change is additive or unreleased, the record does not move, and each fails closed.
- **Weaknesses.** More fields in the report and the manifest for an adopter to keep current.
- **Opportunities.** The last free moment before the freeze.
- **Threats.** One more build and re-check before the cut. A shape mis-specified now is frozen, so the build is held to the refinements below.

## Advice

(a) on all six. It is the option that keeps the results correct: each gap otherwise lets a report, a reader or a verification say something the inputs no longer support.

The coordinator refines (a) in three places, to keep a wrong result from slipping through the specification itself:
1. **N2.** The identity carries separately named digests:
   - `attestations`: the canonical JSON of `[verification]`, `[provenance]` and `[capture]` as the load read them;
   - `captures`: the answers and reviews the load applied;
   - the register's file digests beside its tag and commit.

   Each is computed from what the load used, not from the files on disk, so a skipped file cannot change the identity, and `differs` (N3) names which input moved. Each field is additive and optional under schema v3.
2. **G1.** The giver is read from the capture's own content (its signed `[answered]` handle), never from the file name. The review file records it, and the load binds by it. A review without the field keeps today's rule: fail-closed `ambiguous`, refused at write time.
3. **N-b.** The binding covers the reference implementation and the test suite that judged it, each digested as a directory artefact is (the load's own part selection, as task-0319). A changed helper or a weakened test voids the verification, as a changed document does.

## Decision

Accepted on the maintainer's word, 2026-11-11: **"(a) as advised for all six"**, given with the question whether these are the best solutions for the correctness of the results and knowgov's behaviour. The coordinator answered yes, with the three refinements above stated before the build and open to the maintainer's veto before it merges. Built as task-0320.

A consequence that stands either way, for the 0.9.0 Known limits: re-listing an edited document's digest re-verifies it by execution although nothing ran on the new content. knowgov records an attested result and runs no oracle at load.
