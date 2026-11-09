---
id: doc-0037
title: >-
  The 0.9.0 release candidate's state of affairs: the contract pass and the
  functional review at main f194aac, the decisions it raises
type: other
created_date: '2026-11-09T21:24:00Z'
updated_date: '2026-11-09T21:25:00Z'
---
# The 0.9.0 release candidate: the state of affairs after the contract pass and the functional review (main f194aac)

**Status:** filed 2026-11-09 by the coordinator, on the maintainer's request for "a functional, semantic perspective: completeness, ambiguity, correctness, based on the usage scenarios". The review ran in three fresh, read-only sessions at `main` `f194aac`:
- A: `session_01HTAA1UC5tSJ4yRcP1AcDFW`, the stored knowledge and query-ability;
- B: `session_01HTAA1Re9TEvFEokRYMR175`, up and down, impact and what-if;
- C: `session_01HTAA1RJ9Rg2FP5uZoxBXic`, the adopter's lifecycle.

Their reports are quoted, not re-run. The coordinator verified the finding two of them reached independently (§3.1) on `main`.

## Verdict

**The contracts are validated.** The validation pass (decision-0032, task-0256) closed every contract-bearing finding through two rounds and an independent spot check. One amendment is still building: task-0301, keys in NFC (decision-0034 A2).

**Functionally, the core mechanisms work, and their answers are correct against the record.** Re-verified at `f194aac`:
- the comparator shows 0 differing leaves;
- Neo4j equals rdflib on 13 reads;
- the round trip holds;
- every walk equals the register's own;
- slicing, proposal impact, the register-change staling, trace suspect and drift, lapses as of a date, and three-valued answers all behave as the record and the documents say.

**One cross-cutting semantic hole contradicts FR-01 and FR-04 on an organisation's own instance (§3.1).** An execution verification is an attestation written at load, never a run. So an edited document's value inherits "verified by execution", and the gate can say PROCEED on unverified knowledge.

**Two more findings bear on integrity and audit:**
- a review's approval can re-bind to another person's identical answer (§3.2);
- a report does not identify the corpus it decided on, and a baseline compares across a changed identity without a word (§3.3).

**Three report shapes are worth settling before the freeze (§3.4):**
- the ledger leg's ids;
- the trace report's owner, route and identity;
- "withdrawn" used for two things.

**The rest is usability:**
- routes that don't run from the instance repository;
- next steps not named;
- the page and MCP joining impact differently;
- owner vocabulary.

Plus documentation:
- the guide's "the oracle runs on every load";
- doc-0035 against decision-0016 A1;
- the changelog's settings lines;
- security.md's gaps.

## 1. Where the release stands

| Item | State |
|---|---|
| G9-1 to G9-16 | met (doc-0028) |
| G9-17, the validation pass | every re-check done and holding; task-0301 (NFC, decision-0034 A2) building, then its re-check; then the pass report, doc-0036 |
| G9-3, the Desktop test | the maintainer's |
| This review | §3's decisions are put to the maintainer; fix-only work is tasked for 0.9.x (§5) |
| 0.9.0 release PR | after the above; its Known limits gain §6 |
| 1.0.0 (decision-0016 A1) | 0.9.0, 30 days with no contract change across a 0.9.x patch, task-0285, and the Known limits naming G1-1, G1-2 and G1-4 |

## 2. Requirement by requirement (doc-0035 §5)

| FR | Verdict | Why (finding) |
|---|---|---|
| FR-01 statements with source, status and verification | partly met | the execution leg is an attestation, not a run (A-F1, C-C2-2); the version label is not a content identity (A-F2, A-F7) |
| FR-02 rules; one id per conflict | met | content-derived, sorted ids on both stores (A) |
| FR-03 the gate, exit codes, baseline, identity | met for gating; audit partly met | corpus unidentified, baseline identity-blind (A-F2, A-F3) |
| FR-04 change: stale and suspect | partly met | correct within a store (S6 stage 2, `--register-previous`); an edited document on an instance does not stale (C-C2-2); trace findings name no owner (B2) |
| FR-05 review cadence | partly met | the reading as of a date is right; a lapse's route is a dead end (A-F4) |
| FR-06 the register join and walks | partly met | realisers silent on a journey or product (B-X2); four "owner"s (B-D1); no `thread` walk in `register_impact` (B-D7) |
| FR-07 a proposed addition, slices | met | doc-0017 and doc-0022 as written; "withdrawn" and "inferred" wording (B3, B-D6) |
| FR-08 trace | met; the upward read partly met | the ledger leg returns counts, not ids (B1) |
| FR-09 MCP | met | stdio equals HTTP; the prompts' Desktop test open (K10, G9-3) |
| FR-10 CI and hooks | met | routes, annotations and QUALIFIED to the assistant fix-only (C3-1 to C3-3) |
| FR-11 checks and pre-load | partly met | "CLEAN" when the kind's linter never ran (C-C4-1); no check for a missing register map (C-C1-1) |
| FR-12 capture and review | partly met | proposed until reviewed, the review rules, lapse and due all hold; the approval re-binds across givers (C-C2-1) |
| FR-13 exports | partly met | stale lasts one export; no reader of RECONCILE.json (C-C5-1, C-C5-2) |
| FR-14 the store port | met | Neo4j equals rdflib on 13 reads; the round trip holds (A) |
| FR-15 containment | partly met | `execution_guard` refuses a configured worker on an instance's own corpus unless an "uncontained" escape is set, and its message is stale (C-F7-1) |
| FR-16 arms | met | off with no key (C) |
| FR-17 reverse engineering | not probed | |
| FR-18 the page | partly met | the walk is equal; the impact knowledge is joined differently from MCP (B-X4, C-C6-1); the record check and the comparator disagree on a correct S6 run (C-C6-2) |

## 3. The decisions this review raises (before the freeze)

### 3.1 What "verified by execution" means (A-F1, C-C2-2; FR-01, FR-04)

`harness/load.py` `load_verifications` calls `verify_by_execution` for every live statement whose (key, value) the pristine kit states. It writes `outcome: pass` with `evidence_sha256` the reference code's digest, and no suite runs. On a subject the pristine kit is the vendored record, so the record is right. On an instance the pristine kit is the documents on disk, so an edited value is "pristine".

C's repro, the example instance with S1's P2 changed from 316.00 to 341.00:
- with the shipped `versions`: QUALIFIED, and P2|surcharge reads VERIFIED at 341;
- without `versions`: PROCEED.

docs/guide.md:686 says "the oracle runs again on every load".

**Options:**
- **(a) Before 0.9.0, bind an execution verification to the document Versions it was attested on**, as decision-0019 binds approvals and reviews. An unlisted Version is not verified by execution. The guide is corrected.
- **(b) Correct the guide and name it in the Known limits now; bind it in the first 0.9.x patch.**
- **(c) Run the oracle at load.** That is a larger build, post-1.0.

**Canvas.**
- Problem: the gate can say PROCEED on an edited, unverified value.
- Users: every instance and its assistants.
- Cost: one build behind the unchanged shapes; the record's documents are pristine, so the record should not move.
- Value: the gate's verdict means what it says.

**Fit/gap.**
- (a) makes FR-01 and FR-04 true on an instance.
- (b) ships a known false PROCEED in the frozen release.
- (c) is the full promise, too large for the cut.

**SWOT, (a).**
- Strengths: the core claim holds.
- Weaknesses: one more build before the cut.
- Opportunities: decision-0019's binding already exists for approvals.
- Threats: the build finds the record moves, in which case fall back to (b).

**Advice: (a).**

### 3.2 A review's approval re-binds to another giver's answer (C-C2-1; FR-12)

`harness/review.py` `bind()` "repairs" a vanished id to the one statement with the same key, value and sha256. A capture's sha256 is the empty-text digest, so another person's identical answer inherits the approval.

This is fix-only, behind an unchanged contract: confine the repair to the same capture giver, and document the empty-text digest. Like task-0289, it breaks a documented promise, so the coordinator pulls it before the cut as task-0302. No decision is needed.

### 3.3 Audit identity (A-F2, A-F3; FR-03, U5)

- **A-F2:** a gate report names its task profile, register and build, but not the corpus. After a document edit, `version`, `task_profile`, `register` and `knowgov` are identical; only the verdict differs.
- **A-F3:** `--baseline FILE` accepts a baseline whose task profile, register, build or date differ, and says nothing.

**Options:**
- **(a) A `corpus` digest in the report's identity** (sha256 over the loaded Versions), completing decision-0029's "what it decided on". The baseline names on stderr each identity field that differs: a note, not a refusal, since a baseline exists to compare across a change.
- **(b) Name both in the Known limits until 0.10.0.**

**Canvas.**
- Problem: a reviewer cannot replay or audit a verdict from the report alone.
- Users: auditors (U5) and pipelines.
- Cost: one schema field and a note.
- Value: decision-0029 complete.

**Fit/gap.** The schema is `additionalProperties: false`, so (a) is a contract change: now, or 0.10.0.

**SWOT, (a).**
- Strengths: replay is complete.
- Weaknesses: one more field to freeze.
- Opportunities: decision-0029 already shaped the identity block.
- Threats: none to the record; its corpus is fixed.

**Advice: (a).**

### 3.4 Traceability shapes and one word (B1, B2, B3)

- **B1:** `code_path`'s ledger leg returns the assertions and keys as counts. The ledger holds the ids, so "this generated file → its keys → key_nodes" breaks over MCP.
- **B2:** trace-report findings carry no `owner` or `route`, and its gate block lacks gate-report v3's identity.
- **B3:** "withdrawn" means deprecated or retired in `register_change` and the gate, but any edge not followed, a proposed one included, in proposal-impact's `slices.map[].withdrawn`, `keys.behind_withdrawn`, `register_impact` and the page.

**Options:**
- **(a) Settle all three before the freeze:**
  - B1: return the ids and keys;
  - B2: add owner, route and identity, as the gate report has them;
  - B3: rename the not-followed fields to `not_followed`, keeping `withdrawn` for deprecated or retired.
- **(b) Document them, and change them in 0.10.0.**

**Canvas.**
- Problem: the upward read from built code stops at a count; a suspect-code annotation names no one; one word carries two meanings.
- Users: assistants (U4), squads (U3), CI.
- Cost: three schema edits and their readers.
- Value: the up-and-down chain is complete over MCP, and a frozen vocabulary means one thing.

**Fit/gap.** Every schema involved is `additionalProperties: false`, so each is a contract change: now, or 0.10.0.

**SWOT, (a).**
- Strengths: no ambiguity frozen in.
- Weaknesses: three builds before the cut.
- Opportunities: the gate report already models owner, route and identity.
- Threats: the rename touches the page and proposal-impact readers.

**Advice: (a).** Each is small, and a frozen ambiguity costs a minor version to undo.

## 4. The usage scenarios in brief

- **Query-ability (A).** An assistant learns what is known, unknown, conflicting, stale and unverified, each with its source fragment, version, basis, verifications and approvals, on both stores. The gaps:
  - "asserted" reads as "known" for a disputed key (A-F5);
  - the gate report carries a conflict count, not its sides or ids (A-F6);
  - a statement's `version` is the one that first yielded it (A-F7);
  - `held_keys` shows the stored status beside the level as of a date (A-F8);
  - there is no console on rdflib (A-F9);
  - an unmodelled key reads like a modelled absence (A-F10).
- **Up and down (B).** Capability to keys works in two walks of opposite direction: from a capability, product and journey are dependants. Code to capability works through `code_path`, `register_impact` with children, and `register_nodes`. The gaps:
  - the ledger counts (B1);
  - four owners (B-D1);
  - file granularity only (B-K1).
- **Impact (B, C).** Retiring a node, a register update and a document change are correct and complete against the register's walk, within a store. The gaps:
  - an instance's edited document (§3.1);
  - the page's knowledge join (B-X4, C-C6-1);
  - the sub-gate's wording (B-X3).
- **What-if (B).** These are answered:
  - a proposed addition, with its slices and the D1–D5 candidates;
  - an exception or review expiring on a date;
  - retiring an application or a process;
  - a register PR in branch mode.

  These are not answered:
  - "if this owner leaves": no keys-by-owner read (B-K2);
  - "if this document version were approved" (B-K3);
  - "if this link were withdrawn": an overlay only adds.
- **The adopter's lifecycle (C).** Onboarding reaches a first gate with `instance/README.md` alone. Capture and review hold. CI and hooks behave. Exports land append-only, and the security claims hold. The gaps:
  - `capture.py` routes that run only from a knowgov checkout (C3-1);
  - routes absent from annotations (C3-2);
  - QUALIFIED silent to the assistant (C3-3);
  - the reviewer's next step undiscoverable (C2-3);
  - questionnaires that don't say why (C2-4);
  - tools defaulting to different registers (C1-2);
  - no check for a missing register map (C1-1).

## 5. Fix-only, for 0.9.x (to be tasked)

- **Routes and next steps:** capture routes runnable from the instance repository (C3-1); routes in annotations and the summary (C3-2); QUALIFIED reaching the assistant with a message (C3-3); the lapse route naming `capture.py review` and its role, and the bar blocker given a next step (A-F4); the reviewer's assertion id in the finding (C2-3); questions saying which task and finding asked them (C2-4).
- **Onboarding:** a missing `register_map.toml` reported (C1-1); one register default across tools, or a warning when a subject outside the checkout reads the demo register (C1-2).
- **Pre-load:** a kind whose linter never ran is unchecked, never "CLEAN" (C4-1); a missing `KG_PRELOAD_REPORT` named as such (C4-6).
- **Exports:** stale persisting until the id returns, and a reader of RECONCILE.json with an owner (C5-1; C5-2 is a 1.0 gap).
- **The page:** its impact knowledge joined as `register_impact`'s, or both naming their join (B-X4, C-C6-1); the record check agreeing with the comparator (C-C6-2); a capability group in the summary (B-X5).
- **Walks and tools:**
  - realisers refuses on a kind with no such walk (B-X2);
  - the sub-gate's "why" says "on the N keys reached" (B-X3);
  - exit 2 on an unloadable subject in `upward`, `register_nodes` and `proposal_impact` (B-X1);
  - `key_nodes` answers "mapped: false" for a held, unmapped key (B-X6);
  - `--help` read as an output directory (B-X7);
  - `store_status` names the stage (B-X8);
  - `related` carries conflict ids (A-F6);
  - a did-you-mean on an unknown key (A-F10).
- **Containment:** `execution_guard` admits a configured worker on an instance's own corpus, and its message is current (C-F7-1).
- **Capture:** C2-5, C2-6 and C2-7.

## 6. Documentation and Known limits (the release PR)

- **Correct:**
  - guide §9 and :686 on execution verification (§3.1);
  - doc-0035's Verdict, §7 and §8 against decision-0016 A1 and SNAP-04 (C-F8-1, C-F8-4);
  - the changelog's settings lines: "twenty … from 1.0" against 65 contracts frozen at 0.9.0 (C-F8-3);
  - `security.md`'s gaps: the MCP reader on loopback with no token, the hooks and K20 (C-F7-2, C-F7-3);
  - instance/README's stale task-0252 line (C1-3);
  - the "QUALIFIED" row in the hook mapping (C3-3);
  - "conflicts" counts pairs (A-F6);
  - "asserted" means statements exist (A-F5);
  - `version` semantics (A-F7);
  - the owner vocabulary (B-D1);
  - "invalidated", "stale" and "suspect" (B-D3).
- **State, in an adopter page:** what 1.0 now means (C-F8-2); the key, scenario-id and task-class rules in an adopter guide section (C-F8).
- **Known limits:**
  - keys up to U+FFFF (decision-0034 A1);
  - no console on rdflib (A-F9);
  - code-to-knowledge is file-grained (B-K1);
  - no hypothetical "this document version approved" (B-K3);
  - no keys-by-owner read (B-K2);
  - `attestation_paths` reads content in `.toml` only (C3-6);
  - the GitLab include unproven on a runner (task-0108).

## 7. Not probed by any reviewer

- FR-17 (reverse engineering, the h7 probe);
- the page in a browser;
- the worker container and Landlock;
- the GitHub action and GitLab include on real runners;
- Neo4j for groups B and C;
- J-F beyond C;
- the Desktop prompts test (G9-3).
