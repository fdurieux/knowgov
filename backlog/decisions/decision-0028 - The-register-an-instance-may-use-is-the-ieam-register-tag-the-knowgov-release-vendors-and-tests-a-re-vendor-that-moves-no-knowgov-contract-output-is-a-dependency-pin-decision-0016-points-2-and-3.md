---
id: decision-0028
title: >-
  The register an instance may use is the ieam-register tag the knowgov release
  vendors and tests; a re-vendor that moves no knowgov contract output is a
  dependency pin (decision-0016 points 2 and 3)
date: '2026-11-08T23:45:00Z'
status: accepted
---
## Context

decision-0016 point 3 names "the ieam-register format versions an instance's register may be in" as a 1.0 contract. `instance/README.md`'s contracts table reads "not yet stated", and doc-0028 G9-10 is marked met only because point 3 names the category. The register carries no format number. Only its tag identifies it: `demo/register/SOURCE.md` names the tag knowgov vendors, `v0.2.11` at `main` `4c7fcb0`. Its patch releases change what is valid; v0.2.13's coverage rule C4 (ieam-register decision 0020) can fail a register that v0.2.11 passed. The maintainer said on 2026-11-08 "yes, re-vendor the register at v0.2.13 before 0.9.0", and stream A is building it.

Raised by the reconciliation of the v1.0 scope handover against `main` `4c7fcb0` (its D2; GAP-02).

*Drafted by the coordinating session during the maintainer's overnight delegation (2026-11-08) and **parked for the maintainer**: it writes the content of a contract decision-0016 point 3 named, and the content of every contract this cycle has been the maintainer's word (decision-0027: "settings as advised"). The advice below is the drafter's recommendation; the maintainer's word decides.*

## Options

- **(a) The vendored tag, exactly.** A knowgov release supports the ieam-register tag it vendors and runs its tests against, and no other.
- **(b) A range**, such as `v0.2.x` or "v0.2.13 or later".
- **(c) A register format key** in ieam-register, which knowgov reads as a range. This would need the register's own record first.
- **(d) Unstated.**

## Decision

**(a)**, the drafter's recommendation.
- `instance/README.md` states, in the adopter register: "knowgov X.Y.Z reads a register in the format of ieam-register `vA.B.C`, the tag it vendors (`demo/register/SOURCE.md`) and tests. A register at another tag may load, but is untested."
- A test holds the README's tag to `SOURCE.md`'s, so a re-vendor that forgets the README is red.
- Under decision-0016 point 2, a re-vendor that changes no knowgov contract output is a dependency pin, which a 0.9.x patch may carry. The contract outputs are the JSON shapes under `harness/schemas/`, the exit codes and the MCP outputs. A re-vendor that changes one of them is 0.10.0.
- 0.9.0 carries `v0.2.13`, on the maintainer's word.

## Opportunity canvas

| Element | Content |
|---|---|
| Problem | A 1.0 contract with no content. An adopter cannot tell which register structure their checkout must follow |
| Users | An organisation keeping its register beside its instance, the lighthouse's first |
| Proposal | (a), held by a test |
| Unique value | It claims only what CI runs. The pin rule says when a register move costs a knowgov minor |
| Cost | A README sentence in the contracts table and one test (task-0181's build) |
| Risk | A register patch that changes a knowgov output costs a 0.10.0 and a restarted freeze. The pin rule names this cost instead of hiding it |

## Fit/gap

| Must satisfy | (a) | (b) | (c) | (d) |
|---|---|---|---|---|
| decision-0016 point 3: stated | Fit | Fit | Fit, later | **Gap** |
| Honest: only what is tested | Fit | **Gap**: v0.2.13's C4 shows a patch changes validity | Fit, once the key exists | n/a |
| Holdable by a test | Fit: README to `SOURCE.md` | **Gap** | Fit | n/a |
| decision-0016 point 2: a dependency pin is a patch | Fit: the pin rule | Fit | Fit | n/a |
| Needs nothing from ieam-register first | Fit | Fit | **Gap**: a register decision | Fit |

## SWOT (of a)

| | Helpful | Harmful |
|---|---|---|
| **Internal** | **S:** precise and tested, with no new mechanism | **W:** widening support takes a knowgov release |
| **External** | **O:** a register `format` key later (c, the register's own record) would let a release read a range | **T:** a register change during the lighthouse period that moves a knowgov output restarts the freeze |

## Advice

(a). It is the only option that is stated, true and testable today, and it reads decision-0016 point 2's "a dependency pin is a patch" literally. (b) would claim what v0.2.13 itself disproves, and (c) waits on another repository's record. It is parked only because the content of a 1.0 contract is the maintainer's to set.

## Consequences

- **If accepted**, task-0181's build writes the sentence and the test (its AC #5). The build is prepared overnight, and its pull request waits for the maintainer's word.
- **The re-vendor at v0.2.13** (stream A) lands first, so 0.9.0's sentence names `v0.2.13`.
- **doc-0028 G9-10** reads met for the category; the statement waits on this record.
- **(c)** is ieam-register's to propose if a lighthouse register needs a range. Nothing is minted for it.

## Acceptance (2026-11-09)

The maintainer, 2026-11-09: "all as advised", answering the six questions the coordinator set out with their four parts on the queue page (fdurieux/knowgov#392). The decision is accepted as written: (a), the vendored tag exactly, `v0.2.13` at 0.9.0 (task-0240, #393). task-0181 AC #5 writes the sentence and its test in #397.
