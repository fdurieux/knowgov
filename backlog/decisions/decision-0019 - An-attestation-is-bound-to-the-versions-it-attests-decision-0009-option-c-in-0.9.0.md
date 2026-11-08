---
id: decision-0019
title: >-
  An attestation is bound to the versions it attests: decision-0009 option (c),
  in 0.9.0
date: '2026-11-08T11:16:00Z'
status: accepted
---
## Context

decision-0009 accepted (a): an authored document's statements are verified and approved by construction only when the subject declares `[verification] authored` and `approval`, attested by `[provenance] human`. It left (c), the declaration bound to the versions it attests, as its own decision, to be proposed at m-8 once an instance exists. Its reason: "an attestation silently extends to a later edit, because the next load verifies the new version's authored statements under the same declaration". doc-0028 listed the gap as K12, a proposed 1.0 limit.

task-0199 (F2, #342, #343) bound every ruling, gap close and ledger entry to content. It left the declaration per load and put the question to the maintainer. The coordinator advised keeping K12 as a stated 1.0 limit and deciding (c) at m-8, sized on the lighthouse's instance. The maintainer, 2026-11-08: "Build it in 0.9".

## Options

- **(a) Keep the per-load declaration.** K12 stays a stated 1.0 limit, and (c) is decided at m-8. This was the coordinator's advice.
- **(b) decision-0009's (c) now, in 0.9.0.** The declaration lists the digest of each artefact Version it attests.
- **(c) A review file per artefact version.** decision-0009 rejected this as the default for documents, because per-statement rulings over hundreds of statements make the review file a rubber stamp.

## Decision

**Accepted: (b)**, on the maintainer's word (2026-11-08).

- **What a declaration lists.** `[verification] authored` and `approval` list the Version digest of each artefact they attest: the raw-byte SHA-256 of a file (task-0160), and the part digests of a directory (`part_sha256`, task-0094).
- **An unlisted Version is not attested.** Its authored statements read `proposed`, and nothing in it is approved by construction. This mirrors the pre-load verdict, which reads unchecked unless its digest matches (task-0064).
- **The gate names it.** It names each unattested Version behind its keys, with the owner's route from `capture.routing`. The build states the severity.
- **Read rule for declarations written before this change.** A declaration with no digest list attests per load, as decision-0009 (a) has it. The gate lists the subject's attestation as not bound at info, and `tools/check_subject.py` notes it, naming this decision.
- **The public subjects' digests are the maintainer's act.** Listing which Versions `cargo_quote` and `jef_data_load` attest is an attestation, not a build. It comes in its own pull request, held for the maintainer's approval, never merged on green alone.

A contract change: the subject format and the gate report. It gathers for 0.9.0 (decision-0016), and doc-0028's G9-13 holds the cut until it lands.

## Opportunity canvas

| Element | Content |
|---|---|
| Problem | A person's attestation covers whatever the documents hold at each load, so an edit made after it inherits it. The public subjects are protected by their vendored digests; an instance is not |
| Users | An instance's attesters; the reverse-engineering process's steps 6 and 8, where a person's act must survive a re-run (doc-0032 §6) |
| Proposal | The declaration lists the Versions it attests. An unlisted Version reads `proposed` until it is attested again |
| Unique value | The last of a person's acts that is not bound to content becomes bound, by the same digests the pre-load verdict already uses |
| Cost | A manifest edit per attested document edit; one build (task-0221) |
| Risk | Re-attesting becomes a rubber stamp |

## Fit/gap

| Must satisfy | Status | Evidence |
|---|---|---|
| decision-0009: an attestation is attributable, dated and bound to what was approved | **Fit** once built. Today's gap is the binding | decision-0009 (c); task-0199 I9 dated and attested it |
| decision-0016: contract changes gather for 0.9.0 | **Fit**. The cut waits for one more build | G9-13 |
| The scored record unchanged | **Fit through the read rule** | The public subjects keep their declarations until the maintainer lists their digests. Whether S6's later version stays attested then depends on which Versions the maintainer lists, and the build measures it |
| decision-0002 and ieam-register 0019: approval is the maintainer's, never the drafter's | **Fit** | The public subjects' digests come in a held pull request |
| One mechanism for a digest | **Fit** | task-0160's raw-byte Version digest and task-0094's part digests |
| Sized on an instance (decision-0009's own plan) | **Gap** | No instance exists yet. The grain is per Version for now and can be revisited at m-8 |

## SWOT

| | Helpful | Harmful |
|---|---|---|
| **Internal** | **S:** it closes the last unbound act; the mechanism exists (pre-load digests); the record is held by the read rule | **W:** a manifest edit per document edit; the per-load meaning lingers for any declaration without digests |
| **External** | **O:** the lighthouse instance starts on bound attestations; steps 6 and 8 of the process keep a person's act across re-runs | **T:** a rubber-stamp re-attestation; a grain (per Version) that the first instance finds wrong |

## Advice

The coordinator advised (a): keep K12 as a stated 1.0 limit and decide (c) at m-8, sized on the lighthouse's instance, because no instance existed yet and F2 was complete without it.

The maintainer chose (b). The reason recorded is that deciding (c) after 0.9.0 would be 0.10.0's contract change and restart the freeze. Building it now closes the last way a person's approval stretches over words they never read before the contracts freeze.

The read rule keeps the record unchanged, and the held pull request keeps the public subjects' attestation the maintainer's own act.

## Consequences

- **The build: task-0221.** The declaration's digest list is read by `harness/load.py` (`load_verifications`) and checked by `tools/check_subject.py`, and the gate's finding comes from `capture.routing`. A probe shows an edited, unlisted Version reading `proposed` on both stores. The scored record, the deterministic run and the comparator stay equal.
- **A second pull request** lists `cargo_quote`'s and `jef_data_load`'s attested Versions. It is held for the maintainer, with the measured effect on S6 stated.
- **doc-0028:** K12 moves from a proposed 1.0 limit to decided for 0.9.0 by this record, and G9-13 holds the cut until task-0221 lands.
- **decision-0009's follow-up (c)** is taken here, before m-8, on the maintainer's word.
