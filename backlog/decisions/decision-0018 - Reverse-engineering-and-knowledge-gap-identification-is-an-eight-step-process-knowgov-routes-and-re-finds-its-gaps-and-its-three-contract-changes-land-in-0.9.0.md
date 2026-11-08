---
id: decision-0018
title: >-
  Reverse engineering and knowledge-gap identification is an eight-step process:
  knowgov routes and re-finds its gaps, and its three contract changes land in
  0.9.0
date: '2026-11-08T11:16:00Z'
status: accepted
---
## Context

task-0213. The maintainer, 2026-11-07: "I want the reverse engineering experiment to be repeatable, as I want to define it as a process. The identification of knowledge gaps/issues is part of this, by running the linter tools on the different reverse-engineered & already available artefacts; quirks in code, missing documentation, etc. will then be identified as knowledge gaps, to be addressed."

The brief is doc-0032 (#340, `f39b323`). It defines eight steps, maps each to the tool or record that exists and its gap, and puts eight questions (§11). The maintainer, 2026-11-08, answering them: "Do them now. include in 0.9."

Since doc-0032 was written, F4 (#341), F2 (#342, #343) and F5 (#345) have merged. Steps 5, 6 and 8 are therefore no longer provisional. Two marks remain:
- step 4's exit wrapper waits on F6 (task-0200);
- step 7's job isolation and explicit stage-2 input wait on F8 (task-0203, in flight).

## Options

- **(a) Decide the process, build after the 0.9.0 cut.** Its contract changes land in 0.10.0, which restarts the freeze (decision-0016).
- **(b) Decide the process now, its three contract changes in 0.9.0:** the `claim` field, the intended bar and lint findings routed as gaps.
- **(c) Keep the experiment as a record, with no process.** Findings stay in pumllint's report, and nothing routes or re-finds them.

## Decision

**Accepted: (b)**, on the maintainer's word (2026-11-08). The eight answers of doc-0032 §11, as recommended there:

1. **The process is doc-0032 §2's eight steps:**
   1. scope at a named commit;
   2. reverse-engineer into a kit;
   3. gather the existing artefacts;
   4. lint both;
   5. load as a subject;
   6. address;
   7. optionally rebuild and grade;
   8. re-run on change.

   knowgov is the platform for steps 4 to 6 and 8. Steps 1, 2 and 7 are roles with records.
2. **Where the records live:**
   - the process definition is knowgov's: doc-0032, then an adopter guide under `docs/`;
   - each run's record lives with its instance;
   - J-F's first run stays frozen in pumllint, read and never written.
3. **A per-statement `claim` field in the kit** (`observed`, `inferred`, `intended`). The mappers read it into the basis:
   - `observed` → `extracted`;
   - `inferred` → `inferred`, never above proposed;
   - `intended` → `authored`, approved only under an attestation (decision-0009, decision-0019).

   A statement without `claim` loads as today, so the vendored kits and the scored record do not move.
4. **An intended bar.** A task class may require `approved` for its keys. A behaviour that is only observed, even when verified by execution on the original, then does not read PROCEED without a person intending it (method 1.3: "a source defect must not silently become desired behaviour").
5. **Lint findings become gaps with an owner and a route,** taken from `capture.routing` (F5). These are Dominique's attribute and route steps. The pre-load verdict's info listing stays, for the form.
6. **decision-0011 is amended while proposed (A7).** It cites this process, adds steps 3, 4 and 6, and takes its snapshot after F2, F4 and F5, which have merged. Its choice, (c), does not move.
7. **First instance:** J-F at a new commit, then decision-0011's lane.
8. **H7's two mutants are step 8's first probe,** on `jef_data_load`.

Points 3, 4 and 5 are contract changes. They gather for 0.9.0 (decision-0016), and doc-0028's G9-12 holds the cut until they land.

## Opportunity canvas

| Element | Content |
|---|---|
| Problem | The experiment is a one-off record. Its findings were found by a session, not a process, and nothing routes them to an owner or finds them again at the next commit: 12 diagram claims contradicted by the code, 141 statements never executed, the quirks, and the degradation test's concealed defects |
| Users | The maintainer; an organisation reverse-engineering a lane before a rebuild or a departure (the Dominique case); knowgov itself (decision-0011) |
| Today's alternative | A session repeats the method from the record by hand, and its findings go to a document nobody re-runs |
| Proposal | The eight steps, each with its tool or record, and the three contract changes in 0.9.0 |
| Unique value | Every gap has an owner and a route. Observed, inferred and intended are kept apart with their provenance. Every gap is found again on change, by an edit instrument and an execution instrument |
| Measures | Per run: findings by step and by route; resolutions (slip, choice, exception, open); the re-lint delta; fidelity at step 7 against the pre-registered bar; at step 8, which instrument caught which change |
| Cost | Steps 2 and 7 each take a J-F-sized session. The knowgov builds are small to medium each: tasks 0214 to 0219 |
| Risks | Circular verification: a kit derived from the code is verified on that code. A session-drafted kit attested by nobody. The process read as authority before its first scored instance |

## Fit/gap

| Must satisfy | Status | Evidence |
|---|---|---|
| decision-0016: contract changes after 0.8.0 gather for 0.9.0 | **Fit**. The cut waits for three more builds | G9-12 |
| The semantic core first (doc-0032 §10, item 2) | **Fit** | F3, F4, F2 and F5 have merged |
| doc-0032's provisional marks | **Partial** | Step 4's exit wrapper (F6) and step 7's isolation (F8) remain |
| The scored record unchanged | **Fit, to be shown by each build** | A statement without `claim` loads as today. The intended bar is opt-in per task class. Lint gaps sit on documents, not on a key's level, unless a build shows otherwise |
| J-F's code is private | **Gap** | Steps 1 and 2 at a new J-F commit read it in a private context. What a run may publish is the maintainer's call (task-0220) |
| One record per thing | **Fit** | The process doc is knowgov's, each run's record is its instance's, and pumllint keeps the frozen first run |
| No bank data | **Fit** | Public subjects only |

## SWOT

| | Helpful | Harmful |
|---|---|---|
| **Internal** | **S:** six of eight steps have a tool or a record; one complete run to copy (J-F), with an oracle; the store already keeps disagreements apart and routes key gaps to owners | **W:** three builds before 0.9.0 can be cut; one instance is the whole evidence so far; step 4 and step 7 still carry a provisional mark |
| **External** | **O:** the Dominique case is the same process applied to a person; decision-0011 is a ready first in-house instance; doc-0031's generated cases are derived outputs that step 8 re-checks | **T:** circular verification read as validation; 0.9.0's cut slipping; a process heavy enough that sessions skip steps 3 and 4 |

## Advice

The drafter's advice (doc-0032 §10) was to decide now and build after the semantic core. That core has merged, so building now follows the advice.

The maintainer's addition is the timing: the three contract changes go into 0.9.0. The reason for (b) over (a) is that the freeze then holds them from its start. Landing them in 0.10.0 would restart it.

## Consequences

- **Tasks, minted with this record:**
  - task-0214, the `claim` field;
  - task-0215, the intended bar;
  - task-0216, lint findings as routed gaps;
  - task-0217, step 4's checks in `preload_check` (pumllint `trace --features`, the glossary check, the DMN gap check);
  - task-0218, the adopter guide and the pre-registration template (steps 1 and 2);
  - task-0219, H7's probe;
  - task-0220, the first instance, which waits on the maintainer for the J-F commit and the route to its private code.
- **The builds hold the scored record (S1 to S7), the deterministic run and the comparator equal.** A build that would move them stops and comes back to the maintainer.
- **doc-0028** gains G9-12.
- **task-0213's** AC #3 is met by this record.
- **decision-0011** gains amendment A7. It stays proposed, and its approval stays the maintainer's.
