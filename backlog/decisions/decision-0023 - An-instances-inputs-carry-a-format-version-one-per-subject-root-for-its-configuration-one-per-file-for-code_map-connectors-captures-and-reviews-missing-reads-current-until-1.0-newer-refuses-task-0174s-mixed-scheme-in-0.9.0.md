---
id: decision-0023
title: >-
  An instance's inputs carry a format version: one per subject root for its
  configuration, one per file for code_map, connectors, captures and reviews;
  missing reads current until 1.0, newer refuses (task-0174's mixed scheme, in
  0.9.0)
date: '2026-11-08T19:33:00Z'
status: accepted
---
## Context

doc-0028 G9-2 (decision-0016 point 1): 0.9.0 is not cut before an instance's inputs carry format versions, or a read rule. task-0174 (doc-0028 §9 P1, doc-0029 advice 4) holds the plan.

The plan was read at `main` `38ae719` by the v1.0 session and filed by the coordinator. It covers:
- nine inputs with no version today: `subject.toml`, `scenarios.toml`, `plants.toml`, `queries.toml`, `register_map.toml`, `code_map.toml`, `connectors.toml`, the captures and the review files;
- their readers and writers;
- six requirements;
- three schemes, each with the four parts.

The pre-load report, the gate baseline and the trace ledger already carry `schema_version`, so they are out of scope.

## Options

- **(A) One version per file.** Every input file carries `format = N`.
- **(B) One version per root.** `subject.toml` covers its root, and a new `instance.toml` covers the instance's files.
- **(C) No key.** A stated read rule and a JSON Schema per input.
- **(Mixed)** B for a subject's configuration, A for `code_map.toml`, `connectors.toml` and the records, and C's schemas later. This is the plan's recommendation.

## Decision

**Accepted: the mixed scheme, in 0.9.0**, on the maintainer's word (2026-11-08: "go with the recommended mix, in 0.9.0"), after the coordinator set out the plan's opportunity and SWOT.
- `subject.toml` carries `[format] version = 1`, covering `scenarios.toml`, `plants.toml`, `queries.toml` and the register map it names.
- `code_map.toml` and `connectors.toml` each carry a top-level `format = 1`.
- Each capture and each review file carries `format = 1`, stamped by `capture_toml` and `review_toml`.
- A missing version reads as the current one until 1.0. A higher one is refused with exit 2, naming the file, its version and the reader's. A lower one is read, and a migration note follows the first time a version moves.
- There is no new `instance.toml`.

It is a contract change for 0.9.0 (decision-0003 §2, decision-0016). task-0174 builds it and meets G9-2.

## Opportunity canvas

| Element | Content |
|---|---|
| Problem | Nothing tells a reader which knowgov an input was written for, so a change of meaning, or a file opened by an older knowgov, is misread in silence. Captures and reviews are records that outlive the version that wrote them |
| Users | An organisation running its instance over several knowgov releases, the lighthouse's first; the readers and the instance check |
| Proposal | The mixed scheme above |
| Unique value | A newer file is refused with a message that names both versions. Every record keeps the version it was written under. The instance layout gains no file |
| Cost | Nine readers and five writers touched; one key in each public subject's `subject.toml`; tests per reader |
| Risk | Files copied between subjects, or one number bumped and not another |

## Fit/gap

| Must satisfy (task-0174 §2) | Mixed | Evidence |
|---|---|---|
| 1. Missing reads current until 1.0 | Fit | the plan's §4 |
| 2. A newer file refused, exit 2, naming both versions | Fit, per root and per record | the gate contract |
| 3. A contract change, named in the CHANGELOG, in 0.9.0 | Fit | decision-0016 |
| 4. The attestation hook blocks only `[verification]` and `[provenance]` changes | Fit: `[format]` sits outside both | task-0147 |
| 5. Every writer stamps what it writes | Fit: the wizard skill, `tools/example_instance.py`, `capture_toml`, `review_toml`, the `subject_check` report | the plan's §1 |
| 6. The public subjects carry the key | Fit: three `subject.toml` files, none vendored | the plan's §2 |
| A rule for files that disagree | Fit: one number covers a root's configuration | (A)'s gap closed |

## SWOT

| | Helpful | Harmful |
|---|---|---|
| **Internal** | **S:** one number per subject, edited in one pull request; each record keeps its writer's version | **W:** two styles of key to document; a migration note at each format change |
| **External** | **O:** the same numbers anchor per-input schemas later (C), which also document the formats | **T:** a copied or half-bumped file, which `tools/check_instance.py` reports only when it is run |

## Advice

The mixed scheme, the drafter's recommendation, which the maintainer took:
- It is the only option that refuses a newer file with a clear message and also keeps the records' history.
- It adds no file to the instance layout.
- It is G9-2, which 0.9.0 waits on.

## Consequences

- **task-0174** builds it. Its AC #3, "no code until the maintainer has read the plan", is met by this decision, and its build acceptance criteria are added through the CLI.
- **The CHANGELOG** names it under Unreleased › Contract changes.
- **`instance/README.md`** documents the key in the adopter register.
- **doc-0028** G9-2 reads met once task-0174 merges.

## Amendment A1 (2026-11-08; accepted 2026-11-09, R1): what a missing version means after 0.9.0

*Drafted by the coordinating session during the maintainer's overnight delegation (2026-11-08) and **parked for the maintainer**. It would change the choice of a decision the maintainer accepted in their own words, and it has two coherent options. Raised by the reconciliation of the v1.0 scope handover against `main` `4c7fcb0` (its D1). The advice is the drafter's recommendation; the maintainer's word decides. This record's status stays accepted for everything else.*

**The problem.** The Decision's fourth bullet says "A missing version reads as the current one until 1.0", which schedules a change of meaning at 1.0.0. decision-0016 point 4 cuts 1.0.0 only once the lighthouse has run on the 0.9 contracts with no contract change. Point 2 makes any contract change after 0.9.0 a 0.10.0 that restarts the freeze. As written, 1.0.0 would either break point 4 or leave the rule undefined. The rule therefore has to be settled before the 0.9.0 cut.

### Options

- **(R1) A missing version reads as version 1, in every release.** Nothing changes at 0.9.0, since every input's current version is 1. After a format moves to 2, an unstamped file is still read as 1, the version it was written under. A variant has `tools/check_instance.py` note an unstamped file, but never fail on one.
- **(R0) A missing version is refused from 0.9.0.** It exits 2 and names the key to add. Every file then states its version, for good. Since task-0174, the public subjects and every writer already stamp their output. No lighthouse instance exists yet.
- **(R2) As written: missing reads current until 1.0, then refused.** This breaks decision-0016 point 4.

### Opportunity canvas (of R1)

| Element | Content |
|---|---|
| Problem | The read rule for an unstamped file expires at the release that must not change a contract |
| Users | An organisation writing `subject.toml`, `code_map.toml` and `connectors.toml` by hand; the readers in `harness/formats.py` |
| Proposal | R1 |
| Unique value | An old file's meaning is fixed for good, and a hand-written file needs no key to load |
| Cost | One constant held apart from `CURRENT`; the "Format versions" text and contracts row in `instance/README.md`; the CHANGELOG's Unreleased task-0174 line; one test that moves `CURRENT` to 2 (task-0236) |
| Risk | When version 2 exists, a file written for 2 that forgets its key is read as 1. Every writer stamps, so this is a hand-written file only |

### Fit/gap

| Must satisfy | R1: reads as 1 | R0: refused from 0.9.0 | R2: as written |
|---|---|---|---|
| decision-0016 point 4: no contract change from 0.9.0 to 1.0.0 | Fit | Fit | **Gap** |
| A record keeps the version it was written under | Fit: an unstamped record is fixed at 1 | Fit: every record names its version | Fit |
| A hand-written file loads without ceremony | Fit | **Gap**: a missing key exits 2, with a message naming it | Fit until 1.0 |
| The files that exist today | Fit | Fit: the public subjects are stamped, and no lighthouse instance exists yet | Fit |
| task-0174 §2 requirement 1 (missing reads current until 1.0) | Fit: current is 1 through 0.9.x | **Gap** | Fit |

### SWOT

| | Helpful | Harmful |
|---|---|---|
| **R1** | **S:** no behaviour change; an old file's meaning fixed forever. **O:** a format 2 needs no migration for unstamped files | **W:** a reader cannot tell "written before versions" from "written at 1". **T:** an unstamped hand-written file meant for 2 |
| **R0** | **S:** no ambiguity, ever; every file self-describes. **O:** the freeze is the cheapest moment, with nothing in the field | **W:** one more key an adopter must remember when writing by hand. **T:** an adopter copying an old example gets exit 2, though the message names the fix |

### Advice

The drafter recommends **R1**, with the `check_instance.py` note. The leniency costs nothing until a version 2 exists, and the inputs adopters write most often are hand-written. R0 is the coherent alternative if the maintainer prefers strictness at the freeze, which is the cheapest moment for it. R2 is not open, because of decision-0016 point 4.

### Consequences

- **If R1**, task-0236 builds it. The build is prepared overnight, and its pull request waits for the maintainer's word.
- **If R0**, task-0236's acceptance criteria are restated through the CLI: refuse a missing version, keep the message naming the key, and stamp the remaining fixtures.
- **Either way**, `instance/README.md`, `harness/formats.py`'s docstring and the CHANGELOG's task-0174 line drop "until 1.0", and doc-0028 G9-2 stays met.

### Acceptance of A1 (2026-11-09)

The maintainer, 2026-11-09: "all as advised", answering the six questions the coordinator set out with their four parts on the queue page (fdurieux/knowgov#392). **R1 is accepted:** a missing version reads as version 1, in every release. It replaces the Decision's fourth bullet, "A missing version reads as the current one until 1.0". task-0236 builds it in #397.
