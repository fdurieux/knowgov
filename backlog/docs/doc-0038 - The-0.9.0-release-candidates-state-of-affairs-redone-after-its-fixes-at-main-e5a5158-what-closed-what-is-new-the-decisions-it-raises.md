---
id: doc-0038
title: >-
  The 0.9.0 release candidate's state of affairs redone after its fixes at main
  e5a5158: what closed, what is new, the decisions it raises
type: other
created_date: '2026-11-11T13:33:00Z'
updated_date: '2026-11-11T16:44:00Z'
---
# The 0.9.0 release candidate: the state of affairs redone after its fixes (main e5a5158)

**Status:** filed 2026-11-11 by the coordinator, on the maintainer's request: "when you have implemented the agreed/decided fixes/changes, can you redo the state of affairs?" It redoes doc-0037 (main `f194aac`) after every decision doc-0037 raised was taken and built:
- decision-0034 A2;
- decisions 0035, 0036, 0037 and 0038;
- tasks 0301 to 0322, each re-checked FIXED.

Three fresh, read-only sessions, on the most capable model at high effort, ran the same scenario groups at `main` `e5a5158`:
- A: `session_01HTAA1TXUvboU1nXJwqR1gs`, the stored knowledge and query-ability. It ran on rdflib and on Neo4j 5.26.
- B: `session_01HTAA1RCfH8c1dZaZHnS3wt`, up and down, impact and what-if, on rdflib.
- C: `session_01HTAA1R97DK5D3Q1B1z6cKo`, the adopter's lifecycle, on rdflib.

Each first read doc-0037, then probed afresh. Each reported every doc-0037 finding in its group as CLOSED, STILL OPEN or CHANGED, then what is new. Their reports are quoted, not re-run. The coordinator verified §3.1's mechanism on `main`: `harness/cadence.py:35` and `harness/capture.py:71` fall back to `demo/register`, and `instance/ci/knowgov-gate.sh` never sets `KG_REGISTER`.

## Verdict

**doc-0037's four decisions hold where they were aimed.** The two holes it named are closed, verified on an instance and, for group A, on both stores:
- **§3.1:** an edited document blocks the gate, and so does an edited reference implementation. Each is named with its digest.
- **§3.2:** a review no longer binds to another person's answer.

Audit identity:
- the corpus is in the report;
- a baseline names each identity field that differs;
- the ledger leg returns its ids;
- trace findings name their owner and route;
- "withdrawn" is now `not_followed`.

**The record still holds:**
- the comparator shows 0 differing leaves over 7 scenarios;
- Neo4j equals rdflib leaf for leaf on about 206 reads in each of 4 states;
- the round trip neo4j → rdflib → neo4j holds on every scenario;
- stdio equals HTTP;
- every walk equals the register's own;
- all seven CargoQuote scenarios give the record's verdict on the example instance.

**Four new findings bear on contracts that freeze at 0.9.0 (§3), and a fifth (§3.5) came from a re-check, and one of them is high:**
- **§3.1, high:** on an organisation's instance, the gate, the CI template, the hook and capture read knowgov's public register unless `KG_REGISTER` is set. The instance's own register is never read, and nothing says so. The verdict, the review cadence and the handle check then follow the public register, whose example handles would be accepted as givers and reviewers.
- **§3.2:** the identity still misses the subject-side inputs that decide a verdict: `register_map.toml`, `scenarios.toml` and `[rules]`. The trace report's gate block lacks the corpus, attestations and captures the gate report gained.
- **§3.3:** `register_impact` has no `thread` walk, though FR-06 names one.
- **§3.4:** an execution verification's `at` is the load's clock.

**Five fix-only findings either fail open or are needed to finish a decided fix, so the coordinator pulls them before the cut under decision-0032 (§4).** The first is high: the gate's own attestation route, followed verbatim, re-creates doc-0037 §3.1's false PROCEED.

**The rest is fix-only for 0.9.x (§5) and documentation for the release PR (§6),** most of it already tasked (task-0311 to task-0315 and task-0323).

## 1. Where the release stands

| Item | State |
|---|---|
| G9-1 to G9-17 | met (doc-0028; G9-17 by doc-0036) |
| doc-0037's decisions | taken and built: decision-0034 A2 and decisions 0035 to 0038, tasks 0301 to 0322, each re-checked FIXED |
| This redo | §3's four decisions go to the maintainer; §4's five fixes are pulled before the cut; §5 is 0.9.x |
| G9-3, the Desktop test | the maintainer's |
| 0.9.0 release PR | after §3 and §4; its Known limits gain §6 |
| 1.0.0 (decision-0016 A1) | 0.9.0, then 30 days with no contract change across a 0.9.x patch, task-0285, and Known limits naming G1-1, G1-2 and G1-4 |

## 2. Requirement by requirement (doc-0035 §5), against doc-0037

| FR | doc-0037 | Now | Why |
|---|---|---|---|
| FR-01 statements with source, status and verification | partly met | partly met, narrower | Execution is bound to its Versions, code and suite (A-F1 CLOSED). Still open: the attestation route re-lists by reading (§4 P1); a statement's `version` is the first Version that yielded it (A-F7); execution's `at` (§3.4) |
| FR-02 rules; one id per conflict | met | met | content ids, sorted, on both stores; the gate's `related` stays empty (A-F6, task-0314) |
| FR-03 the gate, exit codes, baseline, identity | gating met, audit partly met | gating met, audit partly met | corpus and `differs` are built (A-F2, A-F3 CLOSED); the subject-side inputs are outside the identity (§3.2) |
| FR-04 change: stale and suspect | partly met | partly met | An edited document on an instance now blocks (CLOSED). Open: a register change cannot be cleared by its route and the CI template never passes one (B-N2); the impact join under-reports suspect outputs (§4 P4) |
| FR-05 review cadence | partly met | partly met | The reading as of a date is exactly guide §9's. Open: the lapse route (A-F4, task-0311); `held_keys` shows the stored status beside the dated level (A-F8); on an instance without `KG_REGISTER`, the public register's months (§3.1) |
| FR-06 the register join and walks | partly met | partly met | joins and walks are equal to the register's; no `thread` walk (§3.3); realisers silent (B-X2); held unmapped keys refused (B-X6); four owners (B-D1) |
| FR-07 a proposed addition, slices | met | met for additions | branch mode reads a node retired in place as harmless (§4 P3); "inferred" is used for two things (B-D6) |
| FR-08 trace | met; upward read partly met | met | the ledger ids are built (B1 CLOSED); the trace identity is incomplete (§3.2); routes (task-0311) |
| FR-09 MCP | met | met | CLI equals MCP on 18 reports; stdio equals HTTP; the Desktop test remains (G9-3) |
| FR-10 CI and hooks | met | partly met | the template reads the public register (§3.1); QUALIFIED is silent to the assistant (C3-3); routes don't run from the instance repository (C3-1) |
| FR-11 checks and pre-load | partly met | partly met | a never-run linter's file is counted as checked (C4-1, changed); a missing register map passes (C1-1); a missing pre-load report blames the store (C4-6) |
| FR-12 capture and review | partly met | met on its rules; partly met on an instance | The giver binding is CLOSED (decisions 0019, 0036, 0038). Open: public handles accepted without `KG_REGISTER` (§3.1); the next steps (C2-3, C2-4); a declaration listing no Versions explains nothing (§4 P2); same-day opposing rulings (§4 P5) |
| FR-13 exports | partly met | partly met | append-only, and a vanished id is never deleted; stale lasts one export (C5-1); no reader of RECONCILE.json (C5-2); bare GUIDs |
| FR-14 the store port | met | met | Neo4j equals rdflib on about 206 reads in each of 4 states; the round trip holds on every scenario |
| FR-15 containment | partly met | partly met | on an instance, the worker runs only behind an escape named "uncontained" (C-F7-1) |
| FR-16 arms | met | met | off with no key |
| FR-17 reverse engineering | not probed | not probed | |
| FR-18 the page | partly met | partly met | the walks are equal; the knowledge join differs from MCP's (B-X4, task-0313); capabilities are not counted (B-X5); the record check and the comparator disagree on a correct S6 run (C-C6-2, changed) |

## 3. The decisions this redo raises (before the freeze)

### 3.1 Which register an instance's gate, CI, hook and capture read (C-N1; FR-10, FR-12, FR-05)

**The mechanism.** These tools read `KG_REGISTER`, and without it fall back to `demo/register`, knowgov's vendored public register:
- `cadence.register_root` (`harness/cadence.py:35`), used by the gate, `run.py`, the lifecycle months and `proposal_impact`;
- `capture.register_root` (`harness/capture.py:71`), used by the questionnaire, ingest, review and `due`;
- `register_impact`;
- the MCP server.

`instance/ci/knowgov-gate.sh` and `knowgov_hook.py` never set `KG_REGISTER`, and neither "Running the gates" nor "Capturing what people know" tells the adopter to. Only `tools/check_instance.py` reads `<instance>/register`. This is task-0312's C1-2, but worse than that task says.

**C's repros, on a copy of the example instance:**
- With its own lifecycle at 1 month, `gate_cli --task codegen --as-of 2027-01-15` gives PROCEED without `KG_REGISTER` and BLOCKED (10/36) with it.
- `knowgov-gate.sh … gate` gives PROCEED, and the report's `register.files` is the public register's digest.
- A handle issued only in the instance's `handles.toml` is refused by `capture.py ingest` without `KG_REGISTER`. So the public register's employee-1 to employee-4 would be accepted as givers and reviewers on a client's instance.

**Options:**
- **(a) Fail closed, and make the template explicit.** Two parts:
  - When the subject lies outside the knowgov checkout and `KG_REGISTER` is unset, every tool that reads a register refuses with exit 2 and names the setting. The tools are the gate, `run.py`, `trace`, capture, `register_impact`, `proposal_impact`, `register_nodes`, upward and the MCP server. The test is the one `execution_guard` already uses for "an instance is mounted".
  - `knowgov-gate.sh` and the hook pass `KG_REGISTER=<instance>/register` unless one is set. The adopter guide says so in both sections.
- **(b) Default to `<instance>/register` when it exists, else refuse.** This is quieter, but it guesses the instance root from `KG_SUBJECT`'s path.
- **(c) A stderr warning only, in 0.9.x.** The silent public default stays.

**Canvas.**
- Problem: a client's verdicts, review cadence and accepted givers follow knowgov's public register without a word.
- Users: every instance (U1, U2), its CI and its assistants (U4).
- Cost: (a) is one shared helper, its call sites, the template's default, two guide paragraphs and tests. Subjects inside the checkout keep `demo/register`, so the record does not move.
- Value: the instance's own register decides, or nothing runs.

**Fit/gap.**
- (a) makes FR-10, FR-12 and FR-05 true on an instance. Its exit-2 refusal is the existing "cannot run" contract. The template default moves the effective default of a contract setting, which is why it is decided now and not in 0.9.x.
- (b) is the same outcome by inference, and inference is what failed here.
- (c) leaves a fail-open default frozen into 0.9.0.

**SWOT, (a).**
- Strengths: fails closed, needs no guessing, and is the same test the execution guard already relies on.
- Weaknesses: an adopter running a CLI by hand must set one more variable. The refusal names it.
- Opportunities: `check_instance` already reads `<instance>/register`, so it can name the mismatch too.
- Threats: a local workflow that relied on the public register for a private subject breaks. That workflow was wrong.

**Advice: (a).**

### 3.2 The identity's remaining inputs: the subject's configuration, and the trace report's gate block (A-N2, B-N1; FR-03, FR-08, U5)

**What is still missing.**
- decision-0038 N2 made the gate report name its `attestations`, `captures` and `register.files`. Three subject-side inputs that decide the verdict are still in no digest:
  - `register_map.toml`: a key's owner, its rows and so its review months;
  - `scenarios.toml`: a scenario's `verifications`, `extraction` and `inferred`;
  - `subject.toml`'s other tables, `[rules]` among them.
- The trace report's gate block (`trace-report.schema.json`, `additionalProperties: false`) gained `task_profile`, `register` and `knowgov` (decision-0035 B2). It has none of `corpus`, `attestations`, `captures`.

**A's repros**, each in a temp copy with `--baseline` against the pristine report. Every one leaves every identity field equal and `differs []`:
- (a) `register_map.toml`'s `response|*` rows reduced: QUALIFIED becomes PROCEED as of 2027-02-07;
- (b) `verifications = false` in `scenarios.toml`: PROCEED becomes BLOCKED (36 of 36);
- (c) `[rules] vague_words = []`: S3's flagged keys go from 13 to 4.

CHANGELOG Unreleased says the report "names every input that decided it", which is false for these.

**Options:**
- **(a) Before 0.9.0, add one `configuration` identity field and complete the trace gate block.**
  - `configuration` holds the sha256 of each subject configuration file the load read: `subject.toml` whole, `scenarios.toml`, `register_map.toml`, and `plants.toml` and `queries.toml` where read. It is recorded at load on `agent:harness` through decision-0038 N2's `record_inputs`/`inputs`, named by `differs`, and additive with no version change.
  - The trace gate block gains `corpus`, `attestations`, `captures` and `configuration`.
- **(b) Narrow the claim.** The report names the documents, attestations, captures and register, not the subject's configuration. Name it in Known limits until 0.10.0.
- **(c) (a) for the gate report only; the trace gate block in 0.10.0.**

**Canvas.**
- Problem: U5 cannot tell from a retained report that the configuration which decided it changed.
- Cost: (a) reuses N2's mechanism, one schema field per report and the CHANGELOG line.
- Value: the claim decision-0038 made becomes true.

**Fit/gap.**
- (a) closes FR-03's audit leg and FR-08's.
- (b) is honest but freezes a known hole for at least a minor version.
- (c) leaves trace, the code gate, behind the gate.

**SWOT, (a).**
- Strengths: one mechanism, already proven on both stores.
- Weaknesses: every comparator and check that holds identity fields learns the new one.
- Opportunities: `differs` names exactly what changed.
- Threats: a file read by more than one path digests twice. The digest is per file as read, like `register.files`.

**Advice: (a).**

### 3.3 A `thread` walk in `register_impact` (B-D7; FR-06)

FR-06 names three walks: dependants, realisers and thread. `register_impact`'s `walk` enum is `[dependants, realisers]`. The thread is reachable only through `proposal_impact --scope` on a journey, step or product, which uses the register's `THREAD` walk.

So from a capability or a process, no MCP walk reaches the entities and attributes. An enum value is a tool argument, so adding it after 0.9.0 is a contract change (0.10.0).

**Options:**
- **(a) Add `thread` to `register_impact`'s walk before 0.9.0,** with the register's `THREAD` walk as `proposal_impact` already loads it, and the same answer shape.
- **(b) Name it in Known limits, point to `proposal_impact --scope`, and narrow FR-06's wording.**

**Canvas.**
- Problem: "what does this process touch, down to the attributes" has no direct read.
- Users: U2 and U4.
- Cost: small, since the walk exists in the register's tool and `proposal_impact` already loads it.
- Value: FR-06 is met as written.

**Fit/gap.**
- (a) closes it.
- (b) keeps a scoped route that answers from a journey or product only, not from a process or a capability.

**SWOT, (a).**
- Strengths: reuse, no new semantics.
- Weaknesses: one more tool argument value to hold equal on the page.
- Opportunities: the page's impact view can offer it later behind the same route.
- Threats: none in the record, since no record field reads `register_impact`.

**Advice: (a).**

### 3.4 What an execution verification's `at` means (A-N3; FR-01, U5)

`load_verifications` stamps each execution verification with the load's clock (`ts = now()`). With `KG_TODAY=2026-11-11`, `ver:exec:price_exact_heavy:…` reads `at` 2026-11-11, while its scope says "smoke 2026-10-30" and its approval is dated 2026-08-06.

Under decision-0036 no suite runs at load, so an auditor reading `at` infers a run that never happened. `review`, `authored` and `approval` take `at` from their declaration; `[verification] execution` has none. The gate report is unaffected, and the record holds.

**Options:**
- **(a) An optional `on` date on `[verification] execution`** (subject format, additive). If it is missing, `at` is the load's clock, and the store says so.
- **(b) Document it.** `at` is when the load recorded the attestation; the run is identified by its digests (decision-0038 N-b: Versions, implementation, suite), not by a date. The guide and the `three_valued_answer` description say so, and Known limits names it.

**Canvas.**
- Problem: a misleading timestamp on the store's evidence.
- Cost: (a) is a format field plus its reader and docs; (b) is two sentences.
- Value: an auditor reads the right thing.

**Fit/gap.**
- (a) adds a date the attester writes and knowgov cannot check: it never sees the run.
- (b) states what the evidence actually binds.

**SWOT, (b).**
- Strengths: true, cheap, and points the auditor at the digests that do bind.
- Weaknesses: `at` stays a load time.
- Opportunities: a real run date arrives with an oracle at load, post-1.0 (doc-0037 §3.1 (c)).
- Threats: an auditor who skips the docs. Mitigated by naming it in the field's description.

**Advice: (b).** A self-written date adds no assurance that the digests do not already give.

### 3.5 What the `suite` digest binds (group A's re-check of task-0330, N-2; FR-01, U5)

decision-0038 N-b binds an execution verification to the code and suite it ran. `Subject.code_parts` takes the suite as `[oracle] script`'s own bytes. CargoQuote's script is `stack_experiment/smoke_test.py`, but the suite's expectations live in `vendor/tools/acceptance/cargo_quote_suite.py`, which the script imports and no digest covers.

Group A's re-check at `e8ac07c` followed the route honestly: the implementation changed to 341.0, the suite's expectations changed (3186 → 3211), and the suite passed 11/11. The `suite` digest stayed `23f3c9cc…` before and after. So the route's "with the implementation and suite digests" asks the adopter to list an unchanged suite digest, and its caveat "if they are unchanged, listing only asserts the old result" reads as applying when it does not. The converse is unseen: editing the expectations to match a wrong implementation moves no digest.

**Options:**
- **(a) An optional `[oracle] suite` list of files, each digested into `suite`, before 0.9.0.** It is additive in the subject format. If it is missing, `suite` is the script alone, as now. CargoQuote's manifest lists its acceptance module; the record's digests move only in the subject's own `[verification] execution` lists, which the vendored record re-pins.
- **(b) Name the limit.** `suite` is the oracle script's own bytes, and files it reads are not bound. Say so in the route, guide §9 and Known limits, and bind more in 0.10.0.
- **(c) Follow the script's local imports automatically.** This is fragile across languages and refused here.

**Canvas.**
- Problem: an attestation's suite binding can miss the very file that holds the expectations.
- Users: U5 auditors, and every instance whose oracle splits runner and expectations.
- Cost: (a) is one format field, `code_parts` reading it, a digest move in CargoQuote's manifest, and its re-check. (b) is three sentences.
- Value: "the suite it ran" means the suite.

**Fit/gap.**
- (a) makes decision-0038 N-b true as written, and freezing without it fixes the gap for a minor version.
- (b) is honest, but it leaves the route's caveat misleading on the honest path.

**SWOT, (a).**
- Strengths: small, additive, explicit (no import guessing).
- Weaknesses: one more field to learn; CargoQuote's execution lists move.
- Opportunities: J-F's oracle can declare its own.
- Threats: the record moves if a vendored file's digest is involved. Fall back to (b) for the record and (a) for instances.

**Advice: (a).**

## 4. Pulled before the cut (decision-0032: fix-only, but failing open or completing a decided fix)

The coordinator pulls these under decision-0032's delegation, tasked as task-0324 (P1), task-0325 (P2), task-0326 (P3), task-0327 (P4) and task-0328 (P5). The maintainer may veto any of them.

| # | Finding | Why it is pulled | The fix, behind unchanged contracts |
|---|---|---|---|
| P1 | A-N1 and C-N3: the attestation finding's route says "agent:maintainer reads the document and lists sha256 … under approval, authored, execution and review versions", and `check_subject` says "replace the old digest with the new one". Followed verbatim, after P2 316 → 341, the gate gives PROCEED with 341.00 "verified by execution" while `reference_impl.py` still holds 316.0 | fails open: the gate's own instruction re-creates doc-0037 §3.1's false PROCEED. **High** | Route per declaration: execution is re-listed only after the suite passes on the Version, with the implementation and suite digests (decision-0038 N-b); approval and review are the approver's or reviewer's own act; authored is the author's. `check_subject`'s fix text likewise |
| P2 | C-N2: a `[verification] execution` or `review` listing no `versions` gives BLOCKED (26 majors routed to questionnaires) and no finding naming the cause. Only `check_subject` notes it | completes decision-0036: it is the CHANGELOG's own upgrade path, and an existing instance moving to 0.9.0 sees PROCEED turn BLOCKED unexplained | an `attestation` finding (info or above) naming each declaration that lists no Version, as `authored` and `approval` already get |
| P3 | B-N4: `proposal_impact` branch mode reads a node moved to `retired` or `deprecated` in place as a "changed" reuse, approved, reaching nothing new, with a self-candidate; the advisory CI step reads a retirement PR as harmless | fails open in the advisory step | list such a node under `not_read`, pointing to `register_impact` and `--register-previous`; no self-candidate |
| P4 | B-N3: `register_impact` attributes a suspect output to a key only through the key's stale statements. After an in-place edit (suspect by `used_changed`, nothing stale), it gives `suspect []` while `derived_outputs` and `gate_verdict` hold the output suspect | fails open: the impact read says nothing built is suspect | attribute by `used_changed` as well as by stale statements, so both tools answer alike |
| P5 | task-0323 L2's repro B: on one day, one reviewer approves an answer and another rejects it. The key reads approved whichever was written first, by handle order, and no finding names the conflict | fails open on a review's integrity | opposing same-day rulings of one statement by different reviewers are an act finding naming both, at major, and the key does not read approved from either alone. The rest of task-0323 stays 0.9.x |

## 5. Fix-only, for 0.9.x

Already tasked, and still open, matched by the reviewers:
- **task-0311:** routes and next steps, including the lapse route (A-F4), C2-3, C2-4 and C3-1;
- **task-0312:** onboarding and pre-load (C1-1, C4-1 changed, C4-6). Its C1-2 is superseded by §3.1;
- **task-0313:** the page's knowledge join and counts (B-X4/C6-1, B-X5);
- **task-0314:** B-X1 to B-X3, B-X6 to B-X8, A-F6, A-F10 and N2;
- **task-0315:** including `review --show` on a document statement;
- **task-0323:** L1 and L3. L2 is otherwise documented; its repro B is P5.

New, for 0.9.x, tasked as task-0329 (A-F8 added to task-0314's notes):
- **A-F8 (now in task-0314):** `held_keys` shows the stored status (`approved: 2`) beside the level as of a date (validated), while `three_valued_answer` shows each statement validated. Add it to task-0314.
- **B-N2:** `--register-previous` re-applies on every run and invalidates every live statement on a landed key, reviewed captures included. So the route (questionnaire, ingest, review) can never restore a key; only moving the previous register forward clears it, silently. The CI template never passes a previous register, and the guide never names the flag. Fix: a route that names the real remedy (re-map the key, or advance the previous register once the owner confirms), plus an adopter paragraph. Optionally, `KG_REGISTER_PREVIOUS` in `knowgov-gate.sh`.
- **A-N4:** PROCEED with exit 1 (a suspect output), and `why` silent on it.
- **A-N5:** `--no-load`'s default scenario differs between CLI and MCP.
- **B-N6:** "changed" printed for a value whose source row changed but whose value did not.
- **B-N8:** a relative `KG_SUBJECT` breaks `check_gate_after_change` and `check_register_change`.
- **B-N9:** `register_impact` with children repeats an edge once per descendant.
- **C-N6:** the "is not attested" findings print "[owner none in the register map]".
- **C-C6-2, changed:** the page's record check and the comparator disagree on a page-started S6 run.
- **C-F7-1:** the execution guard's "uncontained" escape actually leads to contained execution when a worker is configured.

1.0 gaps:
- **A-N6:** `evidence_bundle` names no owner, closer or route.
- **B:** a register-change lifecycle (acknowledgement or persistence); keys by owner (B-K2) and a hypothetical approval (B-K3); shared keys across slices (doc-0034 (b)); a register-evidence-against-Version read on rdflib and MCP (B-N7).
- **C5-2:** a RECONCILE.json reader with names and owners.

## 6. Documentation and Known limits (the release PR)

Known limits, already named:
- keys up to U+FFFF;
- no oracle at load, so re-listing re-verifies (now with P1's route);
- no rdflib console;
- file-grained traceability;
- no keys-by-owner read;
- document paths not normalised;
- the `captures` and `corpus` digests are bytes as read;
- an honest-ambiguous giver edited to the other reading binds.

To add:
- **C-N4 and C-F7-3:** handles are self-asserted. `capture.py review` accepts any issued `approves` or `closes` handle, whoever runs it. `attestation_paths` does not see shell writes. Only the pull request guards an approval. The permission matrix reads as enforcement and must say so.
- **C-F7-2:** the MCP reader needs no token on loopback, so every local user can read it.
- **B-N2:** `--register-previous` lasts as long as it is passed.
- **A-N10:** stage 2 carries statements forward at fragment grain, while a fresh load is bound to the Version.
- **A-N9:** two compatible approved readings of one key (a subset) are not a conflict, and `three_valued_answer` returns both. State the rule.
- **§3.4 (b),** if taken.

Wording:
- **A-N8 and C-N5:** CHANGELOG defines `corpus` twice. Keep the canonical-JSON form.
- **C-F8-3, changed:** three settings counts (20, 63, 65 of 105).
- **C-F8-1 and C-F8-4:** doc-0035's pre-A1 criteria, "fifteen cut builds" and "SNAP-04 open".
- **C-F8-2:** no adopter statement of what 1.0 means under A1.
- **C §8:** which adopter CLIs beside `gate_cli` are contract (trace, preload_check, check_instance, check_subject, capture.py, connector.py, proposal_impact, register_nodes, upward); whether the hook's and the annotations' text is; the questionnaire's lack of a `format`; the `route` field's content (task-0311 N4).
- **A-F5:** "asserted" for a disputed key.
- **A-F7:** a statement's `version` is the first Version that yielded it.
- **A-N7:** the page shows the record's conflict numbering.
- **B-D1, B-D3, B-D6:** four owners; invalidated, stale and suspect; "inferred" used twice.
- **B-N5:** `register_impact`'s gate block is the verdict before the change.
- **C1-3:** the "until task-0252 lands" line.
- **C-N7:** minimal's S0 copied onto a subject with documents.
- **C-N8:** `add_artefact`'s prompt text.
- **§3.2 empty-text digest:** document the empty-string digest a capture prints.

## 7. Not probed by any reviewer

- The page in a browser (JSON routes only).
- SNAP-01..11.
- Streamable HTTP by hand, beyond `check_mcp_server`, and the 2026-07-28 stateless era by hand.
- The worker container and Landlock.
- The GitHub action and the GitLab include on real runners.
- `transcript.py`.
- J-F beyond C, and minimal's gate.
- FR-17 and the h7 probe.
- Neo4j for groups B and C. Group A ran both stores; group C re-checked task-0322 on Neo4j separately.
- `LoadTooLarge`.
- The Desktop prompts test (G9-3).
