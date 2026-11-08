---
id: decision-0031
title: >-
  The v1.0 scope handover's acceptance matrix becomes the lighthouse's
  acceptance protocol; decision-0016 point 4's three conditions stay
date: '2026-11-08T23:45:00Z'
status: proposed
---
## Context

The maintainer had a v1.0 scope and release-acceptance handover prepared at `ec4e693` (2026-11-08). It proposes:
- scope items S01–S15;
- acceptance gates A01–A18, all P0 or P1 at the R phase;
- acceptance tests AT01–AT12;
- foundation, pilot and release phases (F/P/R);
- six gaps, GAP-01 to GAP-06.

The coordinator's read-only reconciliation sub-session read it against `main` `4c7fcb0` and the record.

decision-0016 point 4 cuts 1.0.0 when three conditions hold:
- the lighthouse's instance has run on the 0.9 contracts with no contract change;
- the incumbent's route is verified;
- a support counterparty exists.

Adopting A01–A18 as release conditions would add conditions knowgov does not control: A05 the full matrix, A07 owner acceptance, A14 an adopter's security sign-off, A18 an upgrade proof. The handover's own §1.1 says that changing accepted policy needs a maintainer decision.

Raised as the reconciliation's D5.

**Parked for the maintainer.** It would amend, or decline to amend, a decision the maintainer accepted about what 1.0 promises. It changes no contract and costs no time while it waits, so the coordinator does not take it under the overnight delegation.

## Options

- **(a) Amend decision-0016 point 4** to require A01–A18 and the F/P/R exit criteria.
- **(b) Keep point 4 as accepted.** The matrix becomes the lighthouse's acceptance protocol instead: A07–A14 and AT01–AT12 go into `docs/lighthouse-evaluation.md`, task-0057's pre-registration and task-0062's pilot plan. Only the contract-bearing items go forward before the cut (D1–D4, decided the same night: decision-0023 A1 and decision-0028 to decision-0030).
- **(c) Record the matrix only**, as a reference, with no protocol change.

## Decision (proposed)

(b), the drafter's recommendation. The maintainer's word decides.

## Opportunity canvas (of b)

| Element | Content |
|---|---|
| Problem | An external acceptance matrix arrived after 1.0's conditions were accepted. Unplaced, it competes with the record |
| Users | The maintainer, the lighthouse's owners and its auditors |
| Proposal | (b) |
| Unique value | A ready-made pilot checklist, with no change to what 1.0 promises |
| Cost | The protocol docs at the pilot's go: three gaps minted then. GAP-03, owners accepting a task's key set, as an AC on task-0062. GAP-04, the composed delivery recipe, on task-0103 AC #1 and `docs/lighthouse-evaluation.md`. GAP-05, restore, upgrade and the worker-restart drill, as a task |
| Risk | 1.0 can be cut with A14 or A18 unproven |

## Fit/gap

| Must satisfy | (a) | (b) | (c) |
|---|---|---|---|
| decision-0016 point 4 as accepted | **Gap**: amended | Fit | Fit |
| The handover's §1.1 ("does not … override") | Needs this decision | Fit | Fit |
| An adopter's need for a sign-off record | Fit | Fit: in the pilot's protocol | **Gap** |
| 1.0 depends only on what knowgov and its counterparties control | **Gap**: A07, A14 | Fit | Fit |
| One record per thing (GAP-01: doc-0028 §4/§5 is the ledger) | Fit | Fit | Fit |

## SWOT (of b)

| | Helpful | Harmful |
|---|---|---|
| **Internal** | **S:** the record stays as accepted, and the matrix still guides the pilot | **W:** 1.0 can be cut with A14 (security sign-off) or A18 (upgrade proof) unproven |
| **External** | **O:** the matrix absorbs task-0103 AC #2's checklist; GAP-03 to GAP-05 have a home | **T:** an adopter who reads 1.0 as "accepted by the matrix" |

## Advice

(b). Point 4 already makes the lighthouse's own run the test of 1.0. The matrix is the best checklist for that run, and requiring it would make 1.0 wait on sign-offs knowgov does not control. If the maintainer wants A14 or A18 as conditions, a narrow amendment naming those two is better than adopting all eighteen.

## Consequences

- **If (b):** the protocol changes are minted at the pilot's go, by reusing task-0062, task-0103 and task-0069's protocol first. Nothing is minted before then.
- **If (a):** decision-0016 gains an amendment with the four parts, and doc-0028 §5 lists A01–A18.
- **Either way:** GAP-06, the tested platforms and clients, is a docs task now (task-0239), and is not a cut item.
