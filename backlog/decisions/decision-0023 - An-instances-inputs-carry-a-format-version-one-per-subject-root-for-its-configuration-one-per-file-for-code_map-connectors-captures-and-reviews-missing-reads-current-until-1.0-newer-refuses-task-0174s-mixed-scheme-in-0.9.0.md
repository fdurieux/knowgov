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

## Amendment A1 (2026-11-08): a missing version reads as version 1, in every release

*Taken by the coordinating session under the maintainer's overnight delegation (2026-11-08: "continue working autonomously … before you make the call that I am needed, perform a swot, fit/gap, opportunity, and if you cannot call a clear decision then, park it for me to review"). Raised by the reconciliation of the v1.0 scope handover against `main` `4c7fcb0` (its D1). It changes what this record chooses, so it carries the four parts.*

**What changes.** The Decision's fourth bullet, "A missing version reads as the current one until 1.0", becomes **"A missing version reads as version 1, in every release."** At 0.9.0 every input's current version is 1, so no reader's behaviour changes now. When an input moves to version 2, a file that names no version is still read as 1, the version it was written under. It is never reinterpreted as 2. The rest of the Decision stands: a higher version is refused with exit 2, naming the file and both versions, and a lower one is read.

**Why.** "Until 1.0" schedules a change of meaning at 1.0.0. decision-0016 point 4 cuts 1.0.0 only once the lighthouse has run on the 0.9 contracts with no contract change, and point 2 makes any contract change after 0.9.0 a 0.10.0 that restarts the freeze. As written, 1.0.0 would either break point 4 or leave the rule undefined.

### Opportunity canvas

| Element | Content |
|---|---|
| Problem | The read rule for an unstamped file expires at the release that must not change a contract |
| Users | Every instance whose files predate task-0174, the lighthouse's first; the readers in `harness/formats.py` |
| Proposal | A missing version is version 1, permanently |
| Unique value | An old file's meaning is fixed for good. No reader reinterprets it when a format moves |
| Cost | One constant held apart from `CURRENT` in `harness/formats.py`; the "Format versions" text and the contracts row in `instance/README.md`; the CHANGELOG line (Unreleased, task-0174's); one test that moves `CURRENT` to 2 |
| Risk | None at 0.9; at a version 2, an unstamped file written for 2 would be misread, which every writer stamping its output prevents (requirement 5 above) |

### Fit/gap

| Must satisfy | Reads as 1 | Refused from 0.9.0 | Refused from 1.0.0 |
|---|---|---|---|
| decision-0016 point 4: no contract change from 0.9.0 to 1.0.0 | Fit | Fit | **Gap**: a change at 1.0.0 |
| No adopter file breaks at the freeze | Fit | **Gap**: every unstamped file refused at 0.9.0 | Fit until 1.0.0 |
| A record keeps the version it was written under | Fit: an unstamped record is fixed at 1 | Fit | Fit |
| task-0174 §2 requirement 1 (missing reads current until 1.0) | Fit: current is 1 through 0.9.x | Gap | Fit |

### SWOT (of "reads as 1")

| | Helpful | Harmful |
|---|---|---|
| **Internal** | **S:** the meaning of old input is fixed forever; no behaviour change now; one constant | **W:** unstamped files persist, and a reader cannot tell "written before versions" from "written at 1" |
| **External** | **O:** a format 2 needs no migration for unstamped files | **T:** a future writer that forgets to stamp, which the writers' tests catch |

### Advice

"Reads as 1". It is the only option that keeps both accepted decisions and breaks no adopter's file, and it costs one constant and a test. That makes the call clear, so it is taken under the delegation. The maintainer can reverse it before publishing the 0.9.0 Release.

### Consequences

- **task-0236** builds it. `harness/formats.py` reads a missing version as 1, and a test moves `CURRENT` to 2 and still reads an unstamped file as 1.
- `instance/README.md` ("Format versions" and the contracts row) and the CHANGELOG's task-0174 line drop "until 1.0".
- doc-0028 G9-2 stays met.
