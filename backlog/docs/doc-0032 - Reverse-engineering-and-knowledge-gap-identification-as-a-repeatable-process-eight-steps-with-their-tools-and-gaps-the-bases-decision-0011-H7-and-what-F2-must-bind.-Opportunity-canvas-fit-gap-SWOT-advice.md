---
id: doc-0032
title: >-
  Reverse engineering and knowledge-gap identification as a repeatable process:
  eight steps with their tools and gaps, the bases, decision-0011, H7 and what
  F2 must bind. Opportunity canvas, fit/gap, SWOT, advice
type: specification
created_date: '2026-11-07T23:59:00Z'
updated_date: '2026-11-07T23:59:00Z'
tags:
  - brief
  - canvas
  - fit-gap
  - swot
  - process
  - reverse-engineering
  - gaps
---
*2026-11-07. Maintainer register. A brief for task-0213, document only: no code, no task minted; the proposals below carry no ids. Drafted by the testing-class session on the coordinating session's dispatch. The timing was the coordinator's call under the maintainer's delegation of 23:51 UTC ("opportunity, swot, fit/gap => decide"); task-0213's notes record it. Read on knowgov `main` at `96e23c9` and pumllint `main` at `b0ce75f`. Sources:*

- *knowgov: task-0213; doc-0030 and its Answered section; decision-0011 (proposed); doc-0031; `tools/preload_check.py`; `instance/kinds.toml`; `harness/capture.py`, `rules.py`, `gate.py`, `store.py`; `docs/guide.md` §2 and §6; `subjects/jef_data_load/subject.toml`.*
- *pumllint: `docs/recreate-experiment.md`; `recreate_experiment/` (the kit and its README's precedence rule; `hidden/MUTANTS.md`; `results/coverage/UNREALISED.md`; `knowledge-transfer/DOMINIQUE-CASE.md` Phase 1 and Appendix E; `degradation-2026-10-28`; `openwiki-2026-10-27/PREREGISTRATION.md` H7 and M9); methods 1.2 and 1.3 in `rebuilds/codex-2026-10-24/EVALUATION-METHOD.md` (pumllint #187).*

*Executed: nothing. Every "exists" below is a file read at those commits.*

**Provisional marks.** A step marked *provisional* depends on a tranche task not yet merged:
- F2, task-0199, binding acts and derived outputs to content;
- F4, task-0198, one clock, in flight;
- F5, task-0201, one definition per concept, with task-0202 on gap-id numbering;
- F6, task-0200, uniform CLI edges;
- F8, task-0203, worker isolation and the run-folder lifecycle.

F3 (task-0197, stage 2 a real re-load) and F1 (task-0195) are merged.

## Verdict

The experiment can be a process. Six of its eight steps already have a tool or a record on one side or the other, so the work is to chain them, not to invent them.

Three gaps matter more than the rest:
1. **Lint findings are routed to nobody.** They reach the gate only at info, as form. Questionnaires come from key findings, and only `register_map.toml` rows have owners.
2. **The observed/inferred/intended split has no field.** The J-F kit's `basis` (`both`, `logic`, `prose`) records where the reverse engineer's evidence came from, and every kit statement loads as `extracted`.
3. **Nothing distinguishes "the original does this" from "someone intends this".** The gate's PROCEED takes verified or approved. A defect verified by execution on the original therefore passes, which is the outcome method 1.3 forbids: "a source defect must not silently become desired behaviour".

The two knowgov-side steps that decide outcomes, load-and-route (5) and re-run (8), depend on F2, F4 and F5. So the process can be decided now and built after the tranche's semantic core.

## 1. What exists, by side

**pumllint, one run, frozen** (vendored here as `subjects/jef_data_load`):
- the pre-registration and its clean room;
- the kit, with five layers, `MANIFEST.sha256`, and the precedence rule (suite, then requirements, then contracts, then decision tables and glossary, then diagrams);
- the hidden provenance map and quirk notes;
- the lab checks `harness/glossary_check.py` and `harness/dmn_check.py`;
- the unrealised-code register (#188: 141 of 1,520 statements never executed, in classes A to D);
- the Dominique loop (#193: lint, attribute, route, resolve, re-lint);
- the degradation test (#207, #208);
- OpenWiki's H7, not run.

**knowgov, standing:**
- subjects and their five bundle mappers (`requirements_json`, `contracts_markdown`, `dmn_decisions`, `plantuml_realises`, `gherkin_tagged`);
- the instance layout and `check_instance`/`check_subject`;
- `preload_check` with six linters;
- the load and its rules (R-REQ, R-CONFLICT, R-VAGUE, declared gaps, silent entities);
- the gate with owners and routes (task-0102, task-0110);
- capture: questionnaires, answers `elicited` at proposed, review files, rulings (decision-0002);
- the attestation rule (decision-0009);
- stage 2 and R-STALE, knowgov-trace, the arms, the worker, and the J-F oracle.

What the J-F subject vendors: the kit, the codex rebuild and the degradation plant. It does not vendor the coverage register, the quirk notes or the lab checks.

## 2. The process, step by step

| # | Step | Tool or record that exists | Gap | Provisional on |
|---|---|---|---|---|
| 1 | **Scope at a named commit**: the code base, its commit, the lane's file set, the roles (extraction, recreation, validation), the clean-room rule, and the bars fixed in advance | pumllint `recreate_experiment/PREREGISTRATION.md` (pinned tree, clean room); decision-0011 (the gate lane at a commit, A1's bundle rule); `code_map.toml` (paths to an application); `SOURCE.md` notes (commit, tag, digest) | No template. The lane's file set is no knowgov artefact; `code_map.toml` names paths, not a frozen scope. The clean-room rule should be a stated parameter: J-F used a full clean room, while decision-0011 A1 sets none for the author and keeps the bundle rule for the rebuilder | — |
| 2 | **Reverse-engineer into a kit**, each statement observed, inferred or intended | method 1.3's split and its two transformations; J-F's kit format and its five mappers; the precedence rule; `MANIFEST.sha256`; the hidden provenance map | The kit has no field for the split (see §3), and no mapper reads one. knowgov has no skill for the extraction role. An inferred rule is not marked apart in the kit | F2 (`inferred` refused at ruling) |
| 3 | **Gather the existing artefacts**: documents, models, contracts, decision records, comments the code carries | instance `artefacts/<kind>/`; `instance/kinds.toml`; `tools/connector.py` for an incumbent's export; `check_subject`'s zero-yield warning and did-you-mean (task-0149) | **Key alignment.** An existing artefact without the kit's ids yields keys that do not join, and the join is manual. In the experiment, J-F's nine existing diagrams were read post hoc only, never loaded beside the kit | — |
| 4 | **Lint both**, the kit and the existing artefacts | `preload_check` (pumllint, markdownlint, gplint, bpmnlint, dmnlint, Spectral; `--baseline`; `--layout`); `pumllint trace --features`; pumllint's lab `glossary_check.py` and `dmn_check.py` (gaps, overlaps, untyped outputs); the coverage register; the quirk notes; Dominique's Appendix E (what each tool finds and cannot) | `trace`, the glossary check and the DMN gap check do not run in `preload_check`. The coverage register was a session's work, with no tool or format. Quirks have no format. The process chains these by exit codes | F6 (one exit wrapper) |
| 5 | **Load as a subject**, so that lint findings, code quirks and missing documentation become gaps routed to owners | the load and rules; gate key findings with `owner` and `route` from `register_map.toml`; `capture.py questionnaire` per owner; the pre-load verdict per document version, listed at info (task-0064); `trace check` (`unmapped`, `uncited`) | Lint findings are form at info, routed to nobody. No mapper reads a quirk or a coverage register. "Intended" has no bar (§3). Only mapped keys have owners, so a gap on an unmapped key routes nowhere (decision-0011 A6 names the same need) | F5 (gap ids stable, one owner-and-route module), F2 |
| 6 | **Address** | capture answers (`elicited`, proposed); review files (approve, reject, close a declared gap); rulings on disputes (decision-0002); approval lapse (six months); review lapse (decision-0005); Dominique's four resolutions (slip, choice, exception, open) | No resolution field per finding, and the re-lint report is not linked to the first. A slip becomes a new document version (stage 2), a choice a decision record and an approval, an exception an elicited statement, and an open item stays a gap with an owner. Nothing records which happened | F2 (the act bound to content), F4 (lapses as of the date) |
| 7 | **Optionally rebuild and grade** | the arms (agent loop, `[arms.agent]`); the worker (decision-0012); the subject's oracle (J-F's suite through `oracle/jef_suite.py`); `jef_data_load`'s deterministic record and degradation scenarios; method 1.2/1.3 independence (the rebuilder never gets the source) | A new code base needs its own oracle adapter and sandbox layout (task-0021.03's pattern). pumllint's reference differential (`harness/run_arm.sh`, `seam_check.py`) is not ported. Sufficiency is reported per bounded inventory, never as a percentage (method 1.2) | F8 (job isolation, explicit stage-2 derived input) |
| 8 | **Re-run on change**: a new commit, a new kit version, a changed existing artefact | stage 2 as a real re-load (F3, merged); R-STALE (a changed fragment digest invalidates its assertions, ends their verifications and marks derived outputs suspect); `trace check` (suspect, drift); `--register-previous`; cadence | Process-level versioning: two kits at two commits read as versions of one subject, with each person's act carried over or reported (§6). Behaviour drift is seen only by execution (§5) | F2, F4 |

Notes per step:

- **Step 1** carries the bars before anything is measured: fidelity in J-F's shape (gated: identical outputs, exit codes and schemas; reported: the CLI surface), and the bounded inventories against which coverage is stated. That is method 1.2's "no percentage of all tacit knowledge". Without it, step 7 measures copying and step 5 has no denominator.
- **Step 2's roles are separate contexts.** The extraction role may read everything; the recreation role gets the frozen package only (method 1.3). Running both in one informed context cannot substantiate a blind rebuild.
- **Step 3 is where missing documentation becomes visible.** A key the kit states and no existing artefact states is undocumented, which is a fact about the corpus, not a defect in the code. A key an existing artefact states differently from the kit is a conflict.
- **Step 4 does not fix anything first** (Dominique step 1): every finding is a candidate gap, and only its author can say whether it is a slip or an exception.
- **Step 5's mapping** of the experiment's findings onto knowgov's gaps:

  | Finding in the experiment | Becomes in knowgov |
  |---|---|
  | a quirk (the code says seconds, the comment says milliseconds) | an observed statement and an asserted one on the same key: R-CONFLICT, disputed, a ruling under decision-0002 |
  | missing documentation | a key with an observed statement and no intended one: below approved |
  | coverage class B (specified, never exercised) | a key with no execution verification: below verified |
  | coverage class C (no caller) | a code path no requirement reaches: knowgov-trace `unmapped` or `uncited` |
  | a requirement no scenario verifies | R-REQ's gap, as now |
  | a lint finding | today, info only; proposed, a gap with the document author's owner and route (Dominique's attribute and route steps) |

- **Step 6 re-lints at the same tool versions** (Dominique step 5). The second report is the evidence that slips are gone and the rest are recorded choices or exceptions.
- **Step 8** is §5.

## 3. Observed, inferred and intended onto knowgov's bases

| Method 1.3 | knowgov basis | Ceiling and verification | Exists |
|---|---|---|---|
| **Observed**: what the pinned original does | `extracted`, read by a mapper from the kit's document | `verified` by execution: the kit's suite on the pinned original, as `jef_data_load`'s `derive_execution` from `verified_by` tags. Without a scenario it stays proposed or validated | yes, for a statement a tagged scenario reaches |
| **Inferred**: a proposed explanation or generalised rule, with confidence | `inferred`; `hypothesised` for an abductive explanation of a quirk | **never above proposed** (`harness/policy.md` rule 2). Transcript route (c) and `proposal_impact` D1–D4 hold it there. F2 makes a ruling refuse it (task-0199). Confidence has no field | the ceiling yes; the refusal at ruling provisional on F2 |
| **Intended**: accepted by the responsible authority | `authored`, with the attester the manifest declares (decision-0009) | `approved` by a person under an issued handle (decision-0002), never the drafter (ieam-register 0019) | yes |
| *(method 1.2)* tacit knowledge a person gives | `elicited` | proposed until a review approves it; the approval lapses after six months | yes |
| *(the deck)* an asserted artefact: a docstring, a comment, an existing document | `extracted` from that artefact | its own evidence; against an observed statement, disputed | yes, once loaded (step 3) |

**Keep, never merge.** Method 1.3: "These statements may disagree. Preserve their provenance rather than merging them". knowgov keeps every live assertion of a key. The key's level is the lowest counted, and a disagreement is disputed under R-CONFLICT until ruled. Fit.

**Two gaps.**
1. **The kit needs a per-statement field** (say `claim = observed | inferred | intended`), and its mappers need to read it into the basis. Today all five load every kit statement as `extracted`, so an inferred rule in the kit is indistinguishable from an observed one. This is a mapper and kit-format change: harness, provisional on F2.
2. **An "intended" bar.** A task class can block on levels and cap the share below verified (`gate.py`). It cannot require approved. An observed behaviour verified on the original therefore reads PROCEED without anyone intending it. decision-0011 says the same of its kit: verified "shows the kit and the code agree, not that the behaviour is right". A bar relative to approved is a subject-format addition: a contract change for decision-0016's 0.9 set, or later.

## 4. decision-0011

**Its first in-house instance, not superseded.** decision-0011 chooses (c): a snapshot subject, then promotion on stated criteria. The process defines the steps any instance runs. decision-0011 is the application to knowgov's own gate lane.

| decision-0011 | Process step |
|---|---|
| the gate lane at a named commit; A1 (no clean room for the author; the bundle rule for the rebuilder); A4 | 1 |
| the J-F method's kit, `KGV-nnn` ids | 2 |
| A5, the subject frozen under `subjects/`; A6, the register slice so map rows have owners | 5 |
| scoring and its fidelity bar | 7 |
| the shadow period, its drift instruments and promotion | 8, and beyond |

**What it lacks.**
- **Steps 3 and 4.** knowgov's own existing artefacts (the backlog's acceptance criteria, `docs/`, the JSON Schemas, the code's docstrings) are neither gathered nor linted.
- **Step 6.** How a finding is addressed.

**Sequencing.**
- A4 put the snapshot after S1, which is merged (task-0141.02).
- The tranche's F2, F4 and F5 now change the same lane's behaviour (gate, load, review, cadence). A snapshot taken before them would be re-extracted at once.

**Proposed.** Amend decision-0011 while it is still proposed:
- cite this process;
- add steps 3, 4 and 6;
- move the snapshot commit after F2, F4 and F5 merge.

Its choice, (c), does not move. So under CLAUDE.md the amendment needs no four parts of its own. It is the maintainer's call (question 6).

## 5. H7's drift question, in the re-run step

H7 (OpenWiki pre-registration §4, not run, M9): "m2 edits a guard a claim is likely to cite and is flagged stale; m1 reorders two calls without changing any cited line's content and is not flagged. Staleness detection sees edits, not behaviour."

knowgov's instruments split the same question differently, and none of its edit instruments sees behaviour:
- **R-STALE** sees a changed fragment digest in a loaded document: the kit, or an existing artefact. A code mutant changes no document, so R-STALE flags neither m1 nor m2.
- **knowgov-trace `drift`** (`harness/trace.py`) compares a registered file's whole digest. It flags every edit of a registered code file, m1 and m2 alike, and cannot say whether behaviour moved.
- **The subject's suite on the new commit** sees behaviour. Its failures end the execution verifications of the statements they cover: m1 fails 2 scenarios, m2 fails 11 (pumllint `hidden/MUTANTS.md`).

So edit detection here is either too narrow (document fragments) or too coarse (whole files). Step 8 runs all three and records which caught which change.

**Proposed: H7's two mutants as step 8's first probe**, on `jef_data_load`, with no new fixture. `recreate_experiment/hidden/MUTANTS.md` holds them in pumllint, outside the vendored set. Expected:

| | R-STALE | trace `drift` | the suite |
|---|---|---|---|
| m1, bar fetch moved before the actions refresh | not flagged | flagged, behaviour unknown | 2 failures |
| m2, crypto end-guard removed | not flagged | flagged, behaviour unknown | 11 failures |

The suite is the only instrument that tells the two apart. That is H7's question answered on the knowledge side: staleness sees edits, and only execution sees behaviour.

## 6. What the process needs from F2 (task-0199)

For the coordinator to pass to F2 before dispatch. Items 1, 4 and 5 are in F2's row of doc-0030 already. Items 2 and 3 are what the process adds.

1. **A person's act binds to content.** A ruling, review approval, gap close or attestation carries the statement's key, value and fragment digest (or the Version digest for a whole document), not a positional assertion id (H5).
2. **A re-run neither loses nor misplaces an act.**
   - An act whose content is unchanged re-applies.
   - An act whose content changed is not applied. It is reported as a finding that names the act, its author and the change, routed to the act's owner, so it becomes a gap for step 6, not a silent loss.
3. **Identity across kit versions.** Two extractions of one document at two commits pair statements by content, so a reordered table or a renumbered fragment moves no act onto another statement.
4. **The trace ledger** records each used statement's value or Version digest (H6). A re-run then marks suspect exactly the derived outputs whose inputs changed, including outputs of an earlier process run: a rebuild, generated test cases (doc-0031's task-0212).
5. **Bases at ruling time.** `inferred` is refused, and `authored`, `approval` and `review` require `at` and an attester. §3's mapping holds only with both.

Item 6, not F2's but needed by step 8: suspect computed by one port read that the gate, MCP and trace share, so the three readers agree (F2's row names it).

## 7. Opportunity canvas

| Element | Content |
|---|---|
| Problem | The experiment is a one-off record. Its findings (12 diagram claims contradicted by the code, 141 statements unexercised, the quirks, the degradation test's concealed defects) were found by a session, not by a process, and nothing routes them to an owner or re-finds them at the next commit |
| Users | The maintainer, defining the process; an organisation reverse-engineering a lane before a rebuild or a departure (the Dominique case); knowgov itself, under decision-0011 |
| Today's alternative | A session repeats the method from the record by hand; findings go to a document or a register nobody re-runs |
| Proposal | Eight steps (§2), each with its tool or record. knowgov is the platform for steps 4 to 6 and 8; steps 1, 2 and 7 are roles with records |
| Unique value | Gaps with an owner and a route, kept with their provenance (observed, inferred, intended kept apart), and re-found on change by both an edit and an execution instrument |
| Measures | Per run: findings by step and by route; resolutions (slip, choice, exception, open); re-lint delta; fidelity at step 7 against the pre-registered bar; at step 8, which instrument caught which change (H7) |
| Cost | Steps 2 and 7 are a J-F-sized session each. The knowgov builds (lint routing, the split field, an intended bar, ported checks) are each small to medium, after the tranche |
| Risks | Circular verification (a kit derived from the code is verified on it); a session-drafted kit attested by nobody; the process read as authority before its first instance is scored |
| How it starts | The maintainer decides the steps and where each record lives. Then the first instance, after the tranche's F2, F4 and F5 (§10) |

## 8. Fit/gap

| Must satisfy | Status | Evidence |
|---|---|---|
| Repeatable at a named commit | **Partial** | pre-registration and `SOURCE.md` exist as patterns; no template, no scope artefact |
| Observed, inferred and intended kept apart | **Gap** in the kit format; **fit** in the store | §3: no field; R-CONFLICT keeps disagreements |
| Inferred never above proposed | **Fit** for the ceiling; **provisional** for the refusal at ruling | `policy.md`; route (c); F2 |
| Lint both sides | **Partial** | six linters run; `trace`, glossary and DMN-gap do not; coverage and quirks have no tool |
| Findings become gaps routed to owners | **Gap** for lint findings; **fit** for key findings on mapped keys | task-0064 lists form at info; questionnaires from key findings |
| Missing documentation and quirks as gaps | **Partial** | expressible as below-approved keys and disputes once loaded (§2, step 5); not extracted |
| Intended distinguished from verified | **Gap** | the gate takes verified or approved; decision-0011 names it |
| Addressed with a recorded resolution | **Partial** | capture, review, ruling exist; no resolution field |
| Rebuild and grade, independent | **Fit** on J-F; **gap** for a new code base | arms, worker, oracle; adapter per subject |
| Re-run finds drift | **Partial** | edits by R-STALE and trace; behaviour by the suite only; H7 not run |
| A person's act survives a re-run | **Provisional** | F2, §6 |
| Lapses read as of the run's date | **Provisional** | F4 |
| Gap ids stable across runs | **Provisional** | F5, task-0202 |
| One record per thing | **Fit** if the process doc is knowgov's and each run's record is its instance's | CLAUDE.md; pumllint keeps the frozen first run |
| No bank data | **Fit** | public subjects only; an organisation's instance stays private |

## 9. SWOT

| | Helpful | Harmful |
|---|---|---|
| **Internal** | **S:** six of eight steps have a tool or record; one complete run to copy (J-F), with an oracle; the store already keeps disagreements apart and routes key gaps to owners; the method's independence and no-percentage rules are written down | **W:** lint findings unrouted; no field for the split; no intended bar; the coverage register and quirks had no tool; steps 5, 6 and 8 wait on F2, F4 and F5; one instance is the whole evidence |
| **External** | **O:** the Dominique case is the same process applied to a person; decision-0011 is a ready first in-house instance; doc-0031's generated cases are derived outputs step 8 re-checks; a lighthouse organisation's lane before a rebuild | **T:** circular verification read as validation; the process taken as authority before its first scored instance; drift between the process doc and the lab record; a process heavy enough that sessions skip steps 3 and 4, the ones the experiment ran only post hoc |

## 10. Advice

**Decide the process now, as eight steps; build it after the tranche's semantic core.** Order:

1. **The maintainer decides** the steps, where each step's record lives, and §11's questions. The coordinator records the answers in task-0213 (its AC #3) before any step is built.
2. **Nothing in `harness/`** (the split field, lint routing, the intended bar) before F2, F4 and F5 merge. They change exactly what steps 5, 6 and 8 read.
3. **What can come first**, outside the semantic core:
   - a pre-registration template for step 1;
   - porting `trace --features`, the glossary check and the DMN gap check into `preload_check` for step 4 (`tools/`; provisional on F6 for the exit wrapper);
   - H7's probe written as a pre-registration for step 8.
4. **First instance.**
   - **J-F at a new commit:** the only subject with a scored round trip. Steps 1 to 4 and 7 need no tranche task. Steps 5, 6 and 8 follow the tranche, and H7 runs there.
   - **Then decision-0011's gate lane:** the first new code base, after the amendment in §4.

Reasons:
- **The experiment already proved the method.** What a process adds is the routing and the re-run, and both depend on F2, F4 and F5.
- **The cheapest proof of repeatability** is the same subject at a new commit, with its oracle in hand.
- **decision-0011's lane is what the tranche is changing**, so it should come second.

## 11. Questions for the maintainer

1. Accept the eight steps (§2) as the process, each mapped to its tool or record? *Recommended: yes.*
2. Where the records live: the process definition in knowgov (this doc, later `docs/`); each run's record with its instance; J-F's first run frozen in pumllint as it is? *Recommended: yes.*
3. Add a per-statement `claim` field (observed, inferred, intended) to the kit format, read into the basis by the mappers, after F2? *Recommended: yes.*
4. An "intended" bar: may a task class require `approved` for a key? It is a subject-format contract change, so it either joins the 0.9 set or waits. *Recommended: yes; timing yours.*
5. Lint findings as gaps with an owner and a route (Dominique's attribute and route), after F5? *Recommended: yes.*
6. Amend decision-0011 while proposed: cite the process, add steps 3, 4 and 6, and snapshot after F2, F4 and F5? *Recommended: yes.*
7. First instance: J-F at a new commit, then decision-0011's lane? *Recommended: yes.*
8. H7's mutants as step 8's first probe on `jef_data_load`? *Recommended: yes.*
