---
id: decision-0045
title: >-
  A provenance programme after 1.0.0: assurance kept apart from status, a
  journal, CI-issued execution evidence, then authenticated acts; nothing before
  1.0.0 but wording and fixes
date: '2026-11-15T20:00:00Z'
status: accepted
---
*Accepted. The maintainer, 2026-11-15, relayed by the coordinating session: "all as recommended", on the ten questions put with this record (approve it whole; Q1–Q8 as recommended; Q9's amendments each at its release; Q10 (i)). Drafted by a sub-session of the coordinating session; approval is the maintainer's word (ieam-register decision 0019's rule, which knowgov follows).*

## Context

On 2026-11-15 the maintainer received an external plan for stronger provenance, "knowgov: prioritized plan for stronger provenance" (code baseline `0dd644a`). It has seven packages, P0 to P6, and 44 acceptance IDs:
- **P0**, assurance policy, schema and honest descriptions: POL-01..04;
- **P1**, a durable journal apart from the projection: JRN-01..06;
- **P2**, authenticated acts and separation of duties: IDN-01..07;
- **P3**, execution evidence from a trusted producer: VER-01..08;
- **P4**, honest dependency records: DEP-01..06;
- **P5**, signed checkpoints, witnesses and export verification: AUD-01..08;
- **P6**, migration, integration and release acceptance: INT-01..05.

Its rule is that assurance (who attested, whether a producer issued the evidence, what was delivered, whether history is tamper-evident) is kept apart from an assertion's `basis` and `status`. A signature never moves a status.

doc-0040 (#565, branch `claude/provenance-id-map`, baseline `main` `c427338`, read-only) mapped the 44 IDs against `main`:
- 0 present, 22 partial, 22 missing;
- 42 additive, 2 with no contract (INT-04, INT-05), 0 breaking as specified;
- 4 rows breaking only if a choice went the other way: POL-02 and IDN-04 if enforced became the default; JRN-01 and DEP-04 if the trace ledger stopped superseding by path;
- one question unresolved, the store port (§4.6), which could reclassify the P1 rows.

Its §4 lists eleven conflicts with the record, and its §2 the decisions each package puts to the maintainer. This record answers both lists.

The constraints this record works under:
- VERSION is 0.9.1. decision-0016 point 2 makes 0.9.x fixes only. A1 condition 2 runs the 30-day soak from 2026-11-12. Point 7 makes an additive change after 1.0.0 a minor release.
- decision-0041 holds the 0.9.x residues for 1.1.0, and says no build is dispatched before 1.0.0.
- decision-0043 orders the work after 1.0.0:
  1. C5-1;
  2. the verdict audit log and per-user identity, as one decision;
  3. one connector;
  4. suggested map rows.
- The public subjects are the maintainer's attestations (decision-0009 (a), decision-0044 point 2), and CargoQuote is the scored record.

The Known limits under `## Unreleased` already say:
- handles are issued strings, not authenticated;
- a document's statements are attested by the same identity recorded as their author (task-0347).

`docs/security.md` lists the flows and two gaps but names no adversary.

## Accepted already (the maintainer, 2026-11-15: "I go with your advise and proposed sequence")

- The plan is the design input of decision-0043's "audit and identity" decision. It is phased, and no contract changes before 1.0.0.
- **0.9.x now:**
  - honest wording (#561);
  - the V-F1..V-F4 fixes (#562 to #564 and one more);
  - doc-0040.
- **The sequence:**

| Release | Carries | Plan IDs it can close | External prerequisite |
|---|---|---|---|
| 1.1.0 | decision-0041's batch with C5-1; P0 schema and policies; P4 labels | POL-01..04; DEP-01, DEP-02, DEP-03, DEP-06; VER-08's label; IDN-05 (a), task-0347 | none |
| 1.2.0 | P1, the journal | JRN-01..06 (tail truncation excepted); DEP-04, DEP-05; INT-02; AUD-03 at application level | none on one host |
| 1.3.0 | P3, CI-issued execution evidence | VER-01..08 | a signing library; CI issuer trust; a Landlock-capable runner for VER-06 |
| later | P2, once a lighthouse has an identity provider | IDN-01..07 | the lighthouse's identity provider |
| on demand | P5 | AUD-01, AUD-02, AUD-04..08 | a witness; a signing library |
| each release | P6 | INT-01, INT-03, INT-04, INT-05 as their packages land | the packages |

- The public subjects always stay in compatibility mode.

## Options and choice

For the programme as a whole:
- **(a) The plan phased over 1.x minors.** Compatibility is the default and enforced is opt-in per instance, so every package is additive under decision-0016 point 7.
- **(b) The plan as one build, with enforced as the default.** That is a major: it moves the scored record (task-0347: 23 of 23 approved authored statements read author = attester), and IDN-04 and POL-02 become breaking.
- **(c) P0 and P4 in 0.9.x now.** Every contract-bearing ID is a contract change, so this is a 0.10.0 that restarts the freeze and the soak. decision-0041 rejected the same trade for smaller items.
- **(d) Wording only, no programme.** The Known limits stand indefinitely. decision-0043's audit-and-identity item has no design input.

**The choice: (a), with the drafter's recommendations, accepted by the maintainer on 2026-11-15 ("all as recommended").** The sequence was already the maintainer's word; the ten design questions below are now in force as recommended.

## The design questions

### Q1. Threat model

Options considered:
- (i) The plan's five actors, all in scope from P0.
- (ii) The five actors, with the storage administrator out of scope until P5 is triggered.
- (iii) No written model; keep `docs/security.md`'s flows and gaps.

**Recommended: (ii).** The five actors are the ordinary user, model-generated code, the authorised operator, a compromised producer and the storage administrator.

| Actor | In scope from | What holds against it | Outside its boundary |
|---|---|---|---|
| Ordinary user (reads the page or the reader, submits a capture or review) | now | the read-only reader (decision-0008); issued handles and roles (decision-0002); content-bound acts (task-0199) | handle authenticity, until P2 |
| Model-generated code | now | the worker (decision-0012, decision-0015); Landlock; results untrusted | none in knowgov's code; a host without Landlock refuses |
| Authorised operator (writes the instance repository, its policy and its manifests) | 1.1.0, policy | the policy file outside the subject and outside request data (Q2); a change to it is a journal event from 1.2.0 | the instance's own pull request review |
| Compromised producer (a CI job, a fork, a workflow) | 1.3.0 | issuer, repository, workflow and ref pinned in the trust policy (Q6) | the CI platform's own identity tokens |
| Storage administrator (can write the store, the journal and the trust policy together) | **only when P5 is triggered** | nothing in knowgov's code | the witness, which is not built |

Reason:
- The plan itself says application permissions do not stop this administrator, and only a separately controlled witness does (P5 step 1, AUD-04).
- Claiming the threat in scope before a witness exists would be a claim the code does not hold.
- Naming it out of scope is the honest form. The identity provider, the CI issuer's roots and any witness sit outside knowgov's boundary, and are named as trust roots, never as knowgov's guarantees.

**Known limit, to add under `## Unreleased` now (docs only, doc-0040 §3 item 3):** knowgov's history is not tamper-evident against whoever administers its storage. An administrator who can write the store, the trace ledger and, once it exists, the journal and its trust policy can rewrite them together and recompute every digest. Detection needs an independently controlled witness, which is built only on demand (P5).

### Q2. Where compatibility and enforced live

Options considered (doc-0040 §2 P0):
- (i) A documented `KG_*` setting.
- (ii) The subject's own `[tasks.<class>]` or `subject.toml`.
- (iii) A server-controlled instance policy file with its own `format` version.

**Recommended: (iii).** The file sits at the instance root, outside every subject root and outside any request. The name is the drafter's: `<instance>/policy.toml`.
- It carries a top-level `format = 1` under decision-0023's per-file rule. A missing version reads as 1 (A1, R1). A newer version is refused with `FormatTooNew`, exit 2.
- An absent file means compatibility.
- It is read once at process start by every writer and reader of the instance.
- No CLI flag, MCP argument, HTTP field, manifest key or `KG_*` setting names a policy or weakens one (POL-02, INT-03).
- From 1.2.0, a change to it is a journal event (P6 step 4).
- The attestation hook (`instance/ci/claude/attestation_paths.py`) adds it to the paths it blocks, as it blocks `register/`.

Reasons:
- (i) adds a decision-0027 contract setting that a process environment, a compose override or a CI variable can flip per run: the request-level downgrade POL-02 forbids.
- (ii) puts the policy inside the content it governs, where any subject edit could downgrade it.
- (iii) is an instance-layout addition, which is additive under decision-0016 point 3 and point 7.

**What enforced enforces at 1.1.0 is only what exists then:**
- execution and authored attestations bound to listed Versions (decision-0019, decision-0036);
- task-0347 (a), a capture whose file stem names another giver, or whose `from` is not issued, refused;
- task-0347 (b), a drafter unknown or equal to the attester, a blocker;
- every missing assurance label read as not authorising.

Under compatibility the same checks are findings and labels, never refusals, so the scored record does not move. The public subjects carry no policy file and stay compatibility, always (the maintainer, 2026-11-15).

### Q3. Canonical serialisation for new envelopes

Options considered:
- (i) Today's canonical JSON: sorted keys, compact, UTF-8 (`harness/store.py:166-168`).
- (ii) RFC 8785, the JSON Canonicalization Scheme (JCS).
- (iii) A binary form such as deterministic CBOR.

**Recommended: (ii) for every new envelope; (i) kept for every existing digest.**
- JCS is implemented in the tree with the standard library and held to the RFC's published vectors. It is a serialisation, not cryptography, so the plan's "no custom cryptography" is not engaged.
- The existing digests are `task_profile`, `corpus`, `configuration`, `code`, `register.files` and the record's part digests (decision-0029, decision-0037 to decision-0040). Re-deriving them would move the report identities and every baseline, so they keep (i).
- The two forms differ where it matters for numbers (JCS uses ECMAScript number formatting) and for key order outside the Basic Multilingual Plane (JCS sorts UTF-16 code units). So the drafter adds one rule: an envelope carries no floating-point number. Counts are integers, and times and digests are strings, so JCS's number rule never has to decide.

Reason: POL-04 asks for a payload stable across runtimes and independent readers. A published scheme with vectors gives that. A home-grown "sorted keys" description does not, and a binary form adds a dependency for no gain.

### Q4. The journal's backend at 1.2.0

Options considered (doc-0040 §2 P1):
- (i) `sqlite3`, from the standard library.
- (ii) A label in Neo4j that the wipe spares, as `_KgPublication` is. It leaves rdflib needing another backend.
- (iii) A server database. That is a new dependency.
- (iv) An append-only JSON file. The plan says it is insufficient.

**Recommended: (i).** The journal is a single host on a local disk: the same limit `flock` already sets for `KG_RDFLIB_FILE`.
- A network filesystem is not supported, as SQLite's own guidance states.
- Several hosts mean a later decision, with (iii) as its candidate.
- The journal's place is named in the policy file (Q2), not in a new `KG_*` setting.

Reasons:
- It is transactional, durable after commit, and adapter-independent: one journal under both projections, which JRN-05's replay into rdflib and Neo4j needs.
- It adds no pin.
- (ii) ties history to one adapter. (iv) fails JRN-02 to JRN-04.

V-F3's directory-fsync fix precedes any durability claim.

### Q5. What is authoritative

Options considered (doc-0040 §4.2):
- (i) The instance's git files stay authoritative and the journal indexes them.
- (ii) The journal is authoritative for every act, the files included.
- (iii) The journal is authoritative for acts accepted after it ships. The files stay inputs, and the legacy record is labelled.

**Recommended: (iii).** The files are the captures, the reviews and the manifest's `[verification]`, `[provenance]` and `[capture]` declarations.
- From 1.2.0, an act is accepted when its event commits to the journal.
- The file it was submitted from remains the input, and its digest is in the event.
- A later git edit to that file does not alter the accepted act. It is a new submission, or a binding failure (IDN-05).
- Acts before 1.2.0 are read from the files as today and labelled `legacy`. Nothing is synthesised for them (POL-01).
- The trace ledger stays a projection, still superseding by path, so its format does not move. Its history lives in the journal.

Reasons:
- JRN-01 and DEP-04 stay additive, because the ledger keeps its meaning.
- decision-0002 point 1's review file stays the place a ruling is written, so the person's act is unchanged.
- Nothing already recorded is reinterpreted.
- (i) cannot meet JRN-02 or JRN-03. (ii) would rewrite the meaning of every existing record.

### Q6. Signing and verification for P3 at 1.3.0

Options considered (doc-0040 §2 P3):
- (i) Sigstore keyless signing with GitHub Actions identity tokens.
- (ii) A supervisor key held by knowgov.
- (iii) Both.

**Recommended: (i) for CI producers.** A supervisor key for the contained worker comes only if decision-0012's scope is amended to let the worker run an instance's suite. Until then the worker grades the arms only, and P3's producer is CI alone.

The trust policy pins the issuer, the repository, the workflow file and the ref, with no wildcard identities (VER-02).

Verification happens at load:
- through a pinned verification library, chosen and licence-checked under decision-0026's boundary;
- the pin goes to the maintainer first, as every new pin does;
- the result is written to the store as an assurance state.

The MCP reader stays standard library only (`tests/test_demo.py::test_the_mcp_server_adds_no_dependency_to_the_image`). It reads the verification results back through a port read, and never verifies itself.

Reasons:
- No long-lived key to rotate or leak on the CI side (VER-07).
- Identity binds to the workflow that ran, not to whoever holds a key.
- The reader's dependency rule (doc-0040 §4.11) holds.

Caveat for the 1.3.0 decision: public-good Sigstore logs each signature in a public transparency log, so a private instance's CI attestations would publish their metadata. The route for private repositories has to be verified before 1.3.0. Candidates are a private Sigstore instance or the CI platform's own private-repository attestation service (Questions, item 5).

### Q7. Identity for P2, later

Options considered (doc-0040 §2 P2):
- (i) OIDC from the lighthouse's identity provider.
- (ii) Actor-signed acts with keys knowgov registers.
- (iii) A knowgov account system.

**Recommended: (i)**, when a lighthouse has an identity provider.
- The signed act carries the issued handle only. The provider emits the handle as a claim, the directory attribute ieam-register decision 0009 point 1 already names (`knowledgeHandle`).
- knowgov verifies the issuer, the audience, the expiry and the instance scope (IDN-02).
- It stores the issuer, the handle and the act's binding, never the subject identifier, an email or the token.
- The principal-to-handle mapping stays in the organisation's directory.
- IDN-03's "one person, two handles" is then the directory's issuance rule: one active handle per account and unit. It is not a knowgov table.
- An amendment to ieam-register decision 0009 is needed only if that proves insufficient, for example one person with two accounts. It would start in ieam-register's `decisions/`.

Reasons:
- 0009 point 1 says the register, the store and their tools never hold the key and never call the directory.
- 0009 point 5 relies on erasing the key leaving the handle anonymous; a stored `sub` would be that key.
- (ii) makes knowgov a key registry. (iii) is the enterprise identity platform the plan rules out.

### Q8. Witness for P5, on demand

Options considered (doc-0040 §2 P5):
- (i) A public transparency log.
- (ii) A private, separately controlled store, such as object-lock (write-once) storage under another administrator.
- (iii) None; a local hash chain.

**Recommended: (ii) as the default. (i) is opt-in per instance.**

Reasons:
- (iii) cannot detect tail truncation or a replaced chain (AUD-02, the plan's P5 step 3).
- (i) leaks an instance's metadata (event counts, timings, digests of predictable content) to the public.
- (ii) gives AUD-02 and AUD-04 their independent control without publishing anything.

Erasure against retention (ieam-register 0009 point 5, AUD-08) is settled in P5's own decision.

### Q9. Amendments this programme needs

These are consequences, listed and not decided here. Each is drafted as its own amendment, with its four parts, when its release's turn comes:
1. **decision-0014 A2.** Two boundaries: journal acceptance, and generation publication.
   - A generation names the journal position it reflects.
   - The lease or lock covers the append.
   - A "projection pending" state is nameable by readers.
   - "No earlier generation is retained" stays true of the graph, because history lives in the journal. For 1.2.0.
2. **decision-0009 (a), for enforced instances.** Enforced four eyes replaces the unchecked pull request, for instances whose policy enforces it. Compatibility, and so the public subjects, keep (a) as it is. For 1.1.0 (the drafter check) and later (authenticated four eyes).
3. **decision-0012's scope**, only if the worker becomes a producer of an instance's execution evidence. Not otherwise.
4. **A ruling under decision-0016 point 3:** a new port operation with a default is additive. Callers are unaffected, and an adapter outside this tree inherits the default. This sets the P1 rows' class (doc-0040 §4.6). Before 1.2.0.
5. **decision-0043's order**, recording the sequence accepted on 2026-11-15:
   - identity now follows audit, and is gated on a lighthouse identity provider;
   - the connector stays after audit;
   - the decision on audit and identity becomes this programme's packages, decided per release.
6. **decision-0041's 1.1.0 scope**, which grows by P0's schema and policies and P4's labels.

### Q10. A separate question: the tool-result clipping

`harness/agent.py:390` clips every tool result to `RESULT_LIMIT` (6,000 characters). Its comment at `:33` says that limit is for `run_suite`, and `READ_LIMIT` (60,000, `:32`) is what `read_document` and the knowledge readers promise (`:372`, `:376`). The trace records the unclipped length (`:392`), so the run record overstates what was delivered (doc-0040 DEP-02).

Options considered:
- (i) A defect, fixed in 0.9.x: a read result is clipped at `READ_LIMIT` and `run_suite` at `RESULT_LIMIT`, and the trace records the delivered length.
- (ii) The intended cap: keep 6,000 and correct the comment, the tool descriptions and the trace, with a Known limit.
- (iii) Wait for P4 at 1.1.0.

**Recommended: (i)**, a fix-only item for 0.9.x behind an unchanged contract. The arms' limits are experiment knobs, not contracts (decision-0027).
- It changes what the arms deliver in future runs: a document read could carry up to ten times more text.
- The scored record's stored arms results are unchanged, but reruns would differ from them.
- So the maintainer decides between (i) and (ii).

## Opportunity canvas

| Box | Content |
|---|---|
| Problem | knowgov records claims (a handle, a declared result, a registered dependency) that read like stronger facts: an authenticated act, an observed run, a demonstrated use. A load and a re-registration keep no history. 22 of the plan's 44 IDs are missing on `main`. |
| Users | A lighthouse's security reviewer and its AI-governance buyer ("who allowed the agent to build this?", decision-0043); the instance's operator; the maintainer, whose 1.0 promise depends on saying only what holds. |
| Proposal | The accepted sequence: honest wording and fixes in 0.9.x; then 1.1.0 (labels and policy), 1.2.0 (journal), 1.3.0 (CI-issued evidence), P2 with a lighthouse's identity provider, P5 on demand. Compatibility is the default; enforced is opt-in per instance; the public subjects stay compatibility. |
| Unique value | Each assurance dimension (identity, integrity, execution evidence, dependency evidence) is named separately, and nothing is upgraded silently. Every step is additive, so the 1.0 deprecation promise is never spent on it. |
| Measure | The plan's completion matrix: every applicable ID with an executed test, positive and negative controls, and real-backend evidence. The comparator shows 0 differing leaves in compatibility mode at each release. |
| Cost | Three minors of build work plus two later packages. One new pin at 1.3.0 (signature verification). A policy file in the instance layout. Six amendments (Q9). CI time for crash, concurrency and verifier tests within task-0084's budget. |
| Risk | Enforced mode is built and no instance turns it on. The Sigstore private route does not exist where needed. A lighthouse needs P2 before P1. The new CI tests do not fit 12 minutes. |

## Fit/gap

Against what the programme must satisfy:

| Must satisfy | Fit | Gap |
|---|---|---|
| decision-0016 point 2 and A1: nothing contract-bearing before 1.0.0 | 0.9.x carries wording, the V-F fixes and doc-0040 only | Q10 (i) changes what the arms deliver; it is no contract, but it is the maintainer's |
| decision-0016 point 7: additive after 1.0.0 is a minor | 42 of 44 IDs additive. The 4 conditional rows are resolved additive by Q2 (enforced opt-in) and Q5 (ledger unchanged) | the store-port class waits for Q9 item 4's ruling |
| decision-0041: the 1.1.0 batch | kept first, C5-1 included | 1.1.0 grows (Q9 item 6) |
| decision-0043: audit and identity as one decision | this record is that decision's design input | identity is now split behind audit; an amendment records it (Q9 item 5) |
| decision-0008: the reader stays read-only | the journal is written by writers only; the reader reads verification states and journal positions through port reads | a read-side audit of who asked for a verdict needs a writer outside the reader (Questions, item 7) |
| decision-0002 and decision-0009: only a person's act or a declaration moves status | a signature or a run never moves status (POL-03); a pass never approves (VER-08) | enforced four eyes amends 0009 (a) for enforced instances (Q9 item 2) |
| decision-0012: the worker grades the arms only | P3's producer is CI | VER-06 tests the arms path only, unless the scope is amended |
| decision-0014 and A1: one generation per read | unchanged for the graph | the journal's acceptance boundary needs A2 (Q9 item 1) |
| decision-0023: format versions | the policy file and every envelope carry `format`; newer refused | none |
| decision-0026: licence boundary | envelope schemas under `harness/schemas/` (Apache-2.0); verification in the platform (GPL) | the verification library's licence is checked at its pin |
| decision-0027: documented settings are contracts | no new `KG_*` setting for policy or journal | none |
| decision-0036 and decision-0038: re-listing re-attests | compatibility keeps it | under enforced from 1.3.0, a re-listed digest with no issued run authorises nothing; before 1.3.0 it is the maintainer's (Questions, item 6) |
| ieam-register 0009 points 1 and 5 | handle-only acts; no subject identifier stored | an amendment only if the directory's issuance cannot stop one person holding two handles |
| ieam-register 0019: the drafter is the session | task-0347 (b)'s drafter field reads the session from trailers | enforcement of four eyes is per instance |
| The plan's §9 definition of done | the completion matrix is P6's per-release gate | real-backend checks (Landlock runners, a real issuer) are prerequisites, not this record's |
| decision-0044 point 2: the public subjects' content | compatibility only; the comparator learns new fields as unknown, as it did for `code` and `preload` (task-0341) | none |

doc-0040 §4's eleven conflicts, answered:

| # | Conflict | Answer here |
|---|---|---|
| 1 | decision-0014 publication boundary | A2, for 1.2.0 (Q9 item 1) |
| 2 | decision-0002 point 1, decision-0009 (a), which record wins | Q5 (iii) |
| 3 | decision-0009 (a) and ieam-register 0019 against IDN-04 | enforced only (Q2); 0009 (a) amended for enforced instances (Q9 item 2); the public subjects stay compatibility |
| 4 | ieam-register 0009 points 1 and 5 | Q7: handle-only acts; the mapping stays in the directory |
| 5 | decision-0008, journal reads and the verdict audit log | port reads for journal positions; the reader never writes; the verdict log is Questions, item 7 |
| 6 | decision-0016 point 3, the store port | a ruling (Q9 item 4) |
| 7 | decision-0012's scope | CI is P3's producer; the scope is amended only on demand (Q6) |
| 8 | decision-0043's order | an amendment (Q9 item 5) |
| 9 | decision-0041's 1.1.0 scope | an amendment (Q9 item 6) |
| 10 | decision-0036 and decision-0038 re-listing | compatibility keeps it; enforced narrows it (Questions, item 6) |
| 11 | the MCP reader's standard-library rule | verify at load, and read back (Q6) |

## SWOT

| | Helpful | Harmful |
|---|---|---|
| **Internal** | **S:** every step is additive and opt-in, so the record and the comparator do not move. The four assurance dimensions say exactly what is known. The reader keeps its standard-library rule and its read-only contract. The journal uses the standard library. | **W:** three minors plus two later packages to keep coherent. A dual-read period (legacy and new) in every reader. Enforced mode adds a second behaviour to test on both adapters. One new pin at 1.3.0. |
| **External** | **O:** answers the first questions a lighthouse's security review and an AI-governance buyer ask (decision-0043). SLSA-shaped execution evidence is something reviewers recognise. P2 can adopt the lighthouse's own provider rather than one knowgov chose. | **T:** public-good Sigstore publishes a private instance's metadata unless a private route is verified. No lighthouse has an identity provider, so P2 has no date. CI budget (task-0084) and Landlock-capable runners for VER-06. A reviewer may read "signed" as "true" despite POL-03. |

## Advice

The drafter recommends approving this record as proposed: the sequence as the maintainer accepted it, Q1 to Q8 as recommended, Q9's six amendments drafted at their releases, and Q10 (i). The reasons:
1. **It spends nothing on 1.0.0.** Before the cut it is wording, fixes and a map. After it, every package is a minor, and the deprecation promise stays intact.
2. **It never claims more than the code holds.** The storage administrator is out of scope until a witness exists and is said so. A declared result stays labelled declared. A request is never counted as a delivery.
3. **It keeps the record's strongest properties.** The read-only, standard-library reader; status moved only by a person's act or a declaration; ieam-register's rule that the tools never hold the key to a person.
4. **It chooses the smallest dependency at each step.** `sqlite3` and JCS from the standard library; one verification library, only at 1.3.0; no account system, and no public log by default.
5. **It leaves every choice that touches what the maintainer decides with the maintainer:** the clipping, the enforced re-listing, the public log, the pin.

## Consequences

If approved:
- **0.9.x (docs and fixes only):**
  - the Q1 Known limit under `## Unreleased`;
  - doc-0040 §3's Known limits: the ledger keeps one entry per path; a load keeps no history of acts; `consulted` includes attempts; the clipping, once Q10 is answered;
  - Q10 (i) or (ii) as the maintainer decides, as a fix-only task.
- **1.1.0:**
  - decision-0041's batch;
  - the assurance vocabulary and optional fields on the gate, three-valued and derived reports (POL-01, POL-03);
  - `<instance>/policy.toml` with compatibility and enforced (POL-02, INT-03);
  - JCS envelopes (POL-04);
  - P4's labels (DEP-01, DEP-02, DEP-03, DEP-06);
  - VER-08's `declared` label;
  - task-0347 (a) and (b), refusals only under enforced;
  - amendments Q9 items 2 and 6.
- **1.2.0:** the `sqlite3` journal; idempotency keys; acceptance acknowledgement; replay into both adapters; amendments Q9 items 1 and 4 before the build.
- **1.3.0:** CI-issued execution evidence and the trust policy; verification at load; the verification library's pin and licence check; the private-route verification for Sigstore.
- **Later:** P2 on a lighthouse's identity provider, with an ieam-register 0009 amendment only if needed.
- **On demand:** P5, with a private witness by default.
- **Each release:** P6. The completion matrix row per package. The comparator at 0 differing leaves in compatibility on both stores. Any environment-blocked check reported as outstanding, never as done.
- Tasks are minted per release by the coordinating session through the CLI. This record mints none, and no build is dispatched before 1.0.0 (decision-0041).
- If the maintainer rejects a question, the sequence stands and only that question's consequence lines change.

## Questions for the maintainer

1. Approve this record as a whole, or question by question (Q1 to Q10)?
2. Q1: is the storage administrator out of scope until P5 is triggered, with the Known-limit line above added under `## Unreleased` now?
3. Q2: is the policy a file at `<instance>/policy.toml`, outside every subject, with its own `format`, guarded by the attestation hook? And at 1.1.0, does enforced mode turn task-0347 (a) and (b) and the bound-attestation rule into refusals, leaving them findings under compatibility?
4. Q3: JCS for new envelopes, implemented in the tree against the RFC's vectors, with no floating-point number in an envelope, and today's canonical JSON kept for every existing digest?
5. Q6: before 1.3.0, may the session verify a private-repository route for Sigstore (a private instance or the CI platform's private attestation service), so that a private instance's attestations are not published to a public log? And does the verification library's pin come to you with its licence check under decision-0026?
6. decision-0036's re-listing under enforced mode: before 1.3.0, does a declared execution attestation still authorise when it is labelled `declared`, or does enforced require an issued run and so wait for 1.3.0?
7. decision-0043's verdict audit log (who asked for a verdict): is it a separate writer outside the reader that ships with the journal at 1.2.0, or does it wait for P2's identity?
8. Q9 item 4: is a new store-port operation with a default an additive change under decision-0016 point 3?
9. Q9: are the six amendments drafted now as proposed records (no build), or each at its release's turn?
10. Q10, the tool-result clipping: fix it in 0.9.x (reads clipped at `READ_LIMIT`; future arms runs differ from the stored results), or keep 6,000 as the cap and correct the wording and the trace, with a Known limit?
