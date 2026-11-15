---
id: doc-0040
title: The provenance plan's 44 acceptance IDs against main (read-only map)
type: other
created_date: '2026-11-15T19:49:00Z'
updated_date: '2026-11-15T19:49:00Z'
---
Read-only probe, step 3 of the coordinator's advice on the provenance plan (the maintainer, 2026-11-15). Baseline:
`origin/main` `c427338` (#559); the plan's baseline `0dd644a` is four commits behind it, and the four touch only
`tools/check_snapshots.py`, its task and `CHANGELOG.md`, so the plan's line references hold. ieam-register read at
`origin/main` `dd545b7`. Inputs: the plan (P0 to P6, 44 IDs) and the fix validation (V-F1 to V-F4, being fixed
elsewhere and not fixed here). Nothing in the code changed.

Reading the columns:
- **Today**: present, partial or missing, with the evidence. Presence is read from the code and the record, never from a name.
- **Contract** (decision-0016): *no*; *additive*, a 1.x minor under point 7; *breaking*, point 5's deprecation window and a major. VERSION is 0.9.1 and the 30-day soak (decision-0016 A1 condition 2) runs from 2026-11-12. So every contract-bearing ID waits for 1.1.0 or later (point 2; decision-0041).
- **Earliest**: the sequence the maintainer accepted on 2026-11-15:
  - 1.1.0: decision-0041's batch, P0 schema and policies, P4 labels;
  - 1.2.0: P1, the journal;
  - 1.3.0: P3, CI-issued execution evidence;
  - *later*: P2, with a lighthouse identity provider;
  - *on demand*: P5;
  - *each*: P6, every release.
- **Prereq**: the external prerequisite.

## 1. The 44 IDs

### P0: assurance policy, schema and honest descriptions

| ID | Requires | Today on main | Contract | Earliest | Prereq | Overlap |
|---|---|---|---|---|---|---|
| POL-01 | Legacy captures, reviews, attestations and ledgers keep their claims, read as legacy/unverified; no principal synthesised | **partial.** Claims survive: captures load with handle and date (`harness/load.py:464-503`); pre-0.9.0 review files and ledgers bind under read rules at info (task-0199 AC5); a missing format reads 1 (`harness/formats.py:38`, decision-0023 A1). No authenticated principal exists, so none is synthesised. No assurance label exists either: an execution verification reads `method: execution, outcome: pass` (`harness/store_rdflib.py:574`) | additive: an optional assurance field on the gate, three-valued and derived reports, all `additionalProperties: false` | 1.1.0 | none | task-0199, decision-0023, decision-0009 (a), task-0347 |
| POL-02 | Server-controlled enforced and compatibility policies, not weakened by a request or a manifest; enforced refuses authorisation | **missing.** Policy is the subject's own `[tasks.<class>]` (`harness/task_policy.py`), editable in the subject. The only guard is the attestation hook against an assistant's write (`instance/ci/claude/attestation_paths.py`, task-0147, task-0204), not against a person or a shell write | additive if compatibility stays the default and enforced is opt-in (a new documented `KG_*` setting or instance file is a contract, decision-0027); **breaking** if enforced became the default | 1.1.0, enforcing only what exists then (bound attestations, issued handles) | none | decision-0027, decision-0039 §3.1 (the fail-closed precedent), task-0147 |
| POL-03 | Signed-but-untrusted, authenticated-but-unsigned, unknown and unverifiable stay distinct; a signature changes no status | **missing.** No signature or authentication state exists. Today only verifications and rulings move a status (decision-0002, decision-0009), which the rule needs kept | additive | vocabulary 1.1.0; the signed and authenticated states only reachable at 1.3.0 (P3) and later (P2) | signing library, for the signed-state fixtures | decision-0002, decision-0009 |
| POL-04 | Unsupported envelope versions refused predictably; canonical payload stable across runtimes and readers | **partial.** Format versions per input with `FormatTooNew`, exit 2 (`harness/formats.py:30-62`, decision-0023). One canonical JSON digest: sorted keys, no whitespace, UTF-8 (`harness/store.py:166-168`). Canonical corpus lines (decision-0038 N4). No envelope, no cross-runtime test | additive | 1.1.0 | none | decision-0023, task-0174, task-0320 N4 |

### P1: the durable journal

| ID | Requires | Today on main | Contract | Earliest | Prereq | Overlap |
|---|---|---|---|---|---|---|
| JRN-01 | Old provenance survives another load, a wipe and a newer output at the same path | **missing.** Every load wipes every node but the publication node (`harness/store_neo4j.py:714-720`). The ledger drops a path's earlier entry (`harness/trace.py:243`; `tests/test_trace.py::test_register_records_the_file_its_app_and_the_statements_and_supersedes_by_path`). `record_inputs`, `record_attestation` and `record_act_finding` replace what they held (`harness/store.py:604-650`). Only the instance's git keeps the capture, review and manifest files' history | additive, if the journal is a new reader beside an unchanged ledger; **breaking** if the ledger stops superseding by path (ledger format, decision-0016 point 3) | 1.2.0 | none on a single host (`sqlite3`, standard library) | decision-0014, decision-0002 point 1, task-0199, task-0303 |
| JRN-02 | Crash before or after commit and before or after projection: no false acceptance, retries deduplicated | **partial.** A unit publishes whole or not at all: Neo4j one transaction with a sequence lock (decision-0014 and A1), rdflib a lock and an atomic replace. SNAP-01..11 and ST-05..08 hold it. A writer that wrote nothing publishes nothing (SNAP-09). There is no acknowledgement, no event id and no retry dedup | additive | 1.2.0 | none | decision-0014 and A1, task-0141.02, task-0141.06, task-0175, task-0348 |
| JRN-03 | Idempotency key: an identical retry is one event; an altered payload under the same key is a conflict | **missing.** Only natural-key dedup: one id per commit and path (`harness/trace.py:239`) and a taken `Derived` id refused (`harness/store_neo4j.py:975`) | additive: an optional field on the CLI and in the capture and review formats | 1.2.0 | none | none |
| JRN-04 | Journal down, disk full, a file or directory sync failure, or a projection failure: no durable-success claim | **partial.** On rdflib a failed serialisation, sync or replace keeps the old file and releases the lock (ST-06, ST-07). A directory fsync failure is swallowed (`harness/store_rdflib.py:1296-1307`, V-F3, still open on main). There is no journal | additive: a new pending-projection state | 1.2.0 | none | V-F3 (in fix elsewhere), ST-06 |
| JRN-05 | Correction or withdrawal appended; replay into rdflib and Neo4j gives equal evidence and gate outcomes | **partial.** The projection carries across adapters (`export_turtle`/`import_turtle`, `harness/store_rdflib.py:441-444`, `harness/store_neo4j.py:724-738`), and `tools/check_round_trip.py --chain` holds gate reports and answers equal (task-0070). Acts re-apply by content after a reload (task-0199 AC7). No events, so nothing is appended or replayed | additive | 1.2.0 | none | task-0070, task-0199, task-0222 |
| JRN-06 | Restore from backup and replay from a position: stable ids and order, no loss, missing segments detectable | **missing.** The Neo4j generation counter is monotonic, but it can advance without data and names no event (decision-0014 A1 SWOT). Nothing detects a missing segment | additive | 1.2.0 for ids and gaps; tail truncation needs P5 | none; a witness for the tail | decision-0014 |

### P2: authenticated acts and separation of duties

| ID | Requires | Today on main | Contract | Earliest | Prereq | Overlap |
|---|---|---|---|---|---|---|
| IDN-01 | A handle spoofed in flags, TOML, headers or git metadata creates no authenticated act | **missing.** No act is authenticated: "knowgov does not authenticate who ran the command" (`docs/security.md:271`); "Handles are self-asserted" (`CHANGELOG.md:1425`; Unreleased Known limits). Only claims are checked: issued, unwithdrawn, and holding `gives` (`harness/review.py:153-166`) | additive in enforced mode | later | identity provider | decision-0002, ieam-register 0009, task-0347, decision-0043 item 2 |
| IDN-02 | Wrong issuer, audience or tenant, expired evidence, a revoked role: refused before acceptance | **partial.** Role, issue date and withdrawal are checked against the issued list (`tests/test_review.py::test_a_withdrawn_handle_or_one_issued_after_the_review_is_refused`). There is no token, issuer, audience or tenant | additive | later | identity provider | ieam-register 0009 point 2 |
| IDN-03 | One person with two handles cannot give and approve | **missing.** The refusal compares handles (`harness/review.py:565-566`), a stated Known limit. A canonical person identifier collides with ieam-register 0009 point 1 (§4) | additive in enforced mode | later | identity provider | task-0347, decision-0002 point 2 |
| IDN-04 | An author named as approver, or an unbound PR approval, rejected under enforced four eyes | **missing.** `[provenance] human` is both attester and author (`harness/load.py:27-28`, `:168`). CargoQuote S1: 23 of 23 approved authored statements have author = reviewer = approver = `agent:maintainer` (task-0347). The four eyes are the pull request, unchecked (decision-0009 (a)) | additive in enforced mode; **breaking** as a default, since it moves the scored record (task-0347) | drafter finding 1.1.0 (task-0347 (b)); enforcement later | identity provider | task-0347 (b), decision-0009, ieam-register 0019 |
| IDN-05 | An accepted capture or review edited in attribution, content, outcome or record fails binding and is not applied | **partial.** A ruling binds to its statement's key, value and fragment digest; a changed or vanished one is not applied and is a major `act` finding (task-0199). A review records the giver from the capture's content, and a mismatch is named (`harness/review.py:677`, `:698`; task-0320 G1). Not held: a capture's `from` edited after ingest. The load compares neither the file stem nor the issued list (`harness/load.py:477-480`; task-0347 (a)) | additive | stem/issued re-check 1.1.0 (task-0347 (a)); envelope binding 1.2.0 and later | none for (a); signing for the envelope | task-0199, task-0320, task-0321, task-0347 |
| IDN-06 | A signed act replayed into another instance, or with changed content under one request id, is refused; backdating revives nothing | **missing.** No signed acts and no instance scope. Dates are claimed; only a future `on` is refused (`harness/review.py:52`) | additive | later | identity provider, signing library | none |
| IDN-07 | Delegation recorded as initiator, executor and approver; revocation race fails; no token or key in artefacts or logs | **missing.** No delegation or revocation. Partial hygiene only: a run records its initiator (`run.json` `by`, decision-0008). The key cache holds an HMAC fingerprint, never the key (`harness/key_check.py:22`, `:56`). The bearer compare is constant-time (`harness/http_boundary.py:291-293`) | additive | later | identity provider | decision-0008, decision-0043 item 2 |

### P3: trustworthy execution evidence

| ID | Requires | Today on main | Contract | Earliest | Prereq | Overlap |
|---|---|---|---|---|---|---|
| VER-01 | A signed pass from a trusted supervisor verifies only its scope; repeated import idempotent; original retrievable | **missing.** An execution verification is the manifest's declared result: no suite runs at load (`harness/load.py:260-298`, decision-0036; `docs/guide.md:692-699`). Its evidence is the reference code's digest (`harness/load.py:274`) | additive: a new evidence source beside the declared one | 1.3.0 | CI issuer trust, signing library | decision-0036, decision-0038 N-b, decision-0040, task-0320, task-0338, task-0341 |
| VER-02 | Wrong signer, untrusted fork, workflow or ref, a forged signature or an altered result: refused, naming the failed check | **missing** | additive | 1.3.0 | CI issuer trust, signing library | none |
| VER-03 | Empty or malformed output, no tests, a missing feature, a required skip, nonzero exit or timeout: no verification; a failed probe proves the test goes red | **missing** for evidence: no producer exists. The worker's results are capped and shape-checked, and a timed-out job is a failed cell (decision-0012 condition 3, task-0203). EXEC-01 passes on a failed probe (`tools/check_worker.py:88`, V-F2, open on main) | additive | 1.3.0 | real worker, CI issuer trust | V-F2 (in fix elsewhere), decision-0012, task-0141.05, task-0203 |
| VER-04 | Code edited without a commit change, a suite, configuration or document edit, or a deleted input: the evidence stops authorising | **partial.** The declaration binds to the document Versions it lists (decision-0036, task-0306), and to the raw-byte digests of the implementation and suite files, `[oracle] suite` included, a deleted file named (task-0320, task-0338, task-0340). Configuration is in the identity (task-0335), not in the binding. Re-listing a digest re-attests with no run (0.9.0 Known limits, `CHANGELOG.md:1413-1418`) | additive | binding as it is now in 0.9.x; producer-bound at 1.3.0 | CI issuer trust | decision-0036, decision-0038, decision-0039 §3.5, task-0340 |
| VER-05 | Valid evidence replayed into another instance or task, or with other artefact bytes: refused | **missing.** A declaration has no instance or task scope, and there is no result artefact | additive | 1.3.0 | CI issuer trust | none |
| VER-06 | Generated code cannot forge results or reach issuer credentials; host canaries absent; on a real worker | **partial.** The worker confines model code; Landlock stops a job forging a result or the attestation (`docs/security.md`, task-0203; `tests/test_execution.py::test_a_job_cannot_write_the_jobs_folder_so_it_cannot_forge_a_result_or_the_attestation`). No issuer credential exists to reach. The canary check carries V-F2's false positive. The worker grades arms output only, never an instance's evidence (`harness/execution.py:82-94`) | additive | 1.3.0 | real worker (Landlock ABI 3 or later), CI issuer trust | decision-0012, decision-0015, task-0203, V-F2 |
| VER-07 | Key rotation and a revoked compromised issuer follow a stated historical and current policy, verified offline | **missing** | additive | 1.3.0 | signing library, trust policy | none |
| VER-08 | Legacy declared and genuine attested results told apart in UI, CLI, MCP and gates; the loader never claims a run; neither grants approval | **partial.** The docs say a verification is declared (`docs/guide.md:692-701`; 0.9.0 Known limits). The outputs carry `method: execution` with no declared label (`harness/store_rdflib.py:574`). Approval comes only from a declared `approval` (decision-0009), never from execution | additive | label 1.1.0; side by side 1.3.0 | none for the label | decision-0009, decision-0036 |

### P4: honest dependency records

| ID | Requires | Today on main | Contract | Earliest | Prereq | Overlap |
|---|---|---|---|---|---|---|
| DEP-01 | Registration on every gate statement and on keys or citations, labelled; neither called causal | **partial.** The three routes exist: the task gate's statements by default, `--keys`, `--cited` (`harness/trace.py:204-231`). The entry carries no label of its route: `--keys` and `--cited` both write `keys` (`:229-236`). The guide's wording is "a derived output that used certain assertions" (`docs/guide.md:613`) | additive | 1.1.0 | none | task-0051, task-0124, task-0199, task-0303 |
| DEP-02 | Offered-not-fetched, failed, refused, returned and truncated reads distinct; a request never counted as delivered | **partial.** `consulted` is appended before the read runs (`harness/agent.py:371`, `:375`; the tool says "each call is recorded as consulted", `:54`). `consulted_assertions` comes only from successful reads (`harness/gate.py:352-356`). The trace keeps each result's summary, an error included (`harness/agent.py:393-395`). Truncation is marked only inside the text. **Observed:** every tool result reaching the model is clipped at `RESULT_LIMIT` = 6,000 characters (`harness/agent.py:390`), though `READ_LIMIT` allows a document 60,000 (`:32`), while the trace records the unclipped length (`:392`). The record overstates what was delivered; whether this is intended cannot be verified from the record | additive: new delivery fields in an unpinned run record. Clipping at 60,000 would change what the arms deliver, so it is the maintainer's | 1.1.0 | none | V-F4, task-0022 |
| DEP-03 | Push and pull context both record the observable delivery, content digests and model and run identity | **partial.** Push writes `bundle_<arm>.txt` and `prompt_<arm>.txt` to the run folder, without a digest (`harness/run.py:130-131`). Pull records `consulted`. The model's reported identity is kept apart from the configured one (`harness/agent.py:222`, `harness/arms.py:251` vs `:177`). The run has `run.json` and its initiator | additive | 1.1.0 | none | decision-0008 (`run.json`), task-0127 |
| DEP-04 | Resume, an edit after generation, and a new commit at one path: relations stay on the right output digest and run; history survives | **partial.** The entry id carries commit and path, and the entry its digest (`harness/trace.py:232`); trace check reports drift by digest. Earlier entries for the path are dropped (`:243`), and a load wipes the store's registration (task-0303 notes) | additive if history is in the journal; **breaking** if the ledger changes meaning | 1.2.0 (needs P1) | none | task-0199, task-0303 |
| DEP-05 | A citation removed after its source changed: the dependency stays auditable; nothing clears suspect automatically | **partial.** Suspect is computed from the ledger's `used` record (`store.suspicion`, task-0199 AC3). `--cited` refuses a header with no citation (`harness/trace.py:224-226`). A re-registration replaces the entry with no review (`:243`), so the earlier dependency is lost | additive | 1.2.0 (needs P1) | none | task-0199, task-0124 |
| DEP-06 | Page, CLI and MCP show declared, delivered, cited, unknown and legacy alike; no single "used" | **missing.** One suspect rule is shared (task-0199 AC3), but there are no association labels; `derived_outputs`' `used` is unqualified (`harness/schemas/derived-outputs.schema.json`) | additive | 1.1.0 | none | task-0144, task-0199 |

### P5: verifiable history and retention

| ID | Requires | Today on main | Contract | Earliest | Prereq | Overlap |
|---|---|---|---|---|---|---|
| AUD-01 | An edited event, attribution, order or artefact in an export fails offline verification | **missing.** The Turtle export has no manifest. Analogues only: the connector's `MANIFEST.toml` sha256 per file (`tools/connector.py:213-227`); vendored `SOURCE.md` digests held by tests | additive | on demand | signing library | decision-0010, task-0138 |
| AUD-02 | Deleted tail events or an older valid chain detected against an independent checkpoint | **missing** | additive | on demand | witness | none |
| AUD-03 | An ordinary writer cannot update or delete history; a correction appends | **missing.** Writers wipe at every load. A read handle refuses changes (ST-03), which is a different property | additive | on demand; application-level refusal possible with P1 at 1.2.0 | none | decision-0014 |
| AUD-04 | An administrator's rewrite with recomputed hashes exposed by the witness or signing boundary | **missing** | additive | on demand | witness, signing library | none |
| AUD-05 | Witness outage, signing failure and lag shown as pending or unavailable; strict workflows never falsely succeed | **missing** | additive | on demand | witness | none |
| AUD-06 | Key rotation, a trust-policy change and a stale-backup restore follow policy; rollback detected | **missing** | additive | on demand | signing library, witness | none |
| AUD-07 | Restore, export, import and replay on both adapters: equal governance state, history kept, missing payloads visible | **partial.** The round trip holds gate reports, answers, part digests and preload verdicts across neo4j→rdflib→neo4j (task-0070, task-0094, task-0085). Recorded inputs survive export and import (`tests/test_decision_0038.py::test_n2_the_inputs_survive_export_and_import_and_are_a_read_of_the_port`). No history to keep | additive | on demand (needs P1) | none | task-0070, task-0320 |
| AUD-08 | Exports carry no credential or token; protected payloads; payload deletion leaves an authorised tombstone | **partial.** The store keeps a document's digest and size, never its text (`tests/test_security.py::test_the_store_gets_a_documents_digest_and_size_never_its_text`). The transcript route keeps the digest only. Excerpts are stored by design (`docs/security.md` Gap 2). No canary test on an export, no tombstone | additive | on demand | none | ieam-register 0009 point 5 (erasure) |

### P6: integration and release acceptance

| ID | Requires | Today on main | Contract | Earliest | Prereq | Overlap |
|---|---|---|---|---|---|---|
| INT-01 | Authenticated giver → distinct reviewer → trusted evidence → output → change → invalidation, every link to content and events; page, CLI and MCP agree | **partial.** The unauthenticated path runs and is held. S2 goes BLOCKED to PROCEED by command (decision-0002). S6 invalidates and marks code suspect (`tools/check_gate_after_change.py`, `tools/check_trace_walkthrough.py`). The MCP report equals `gate_cli --no-load`'s (`tools/check_mcp_server.py`). No authenticated or trusted link, no events | additive | each; whole only after P2 and P3 | identity provider, CI issuer trust | decision-0002, task-0199, task-0303 |
| INT-02 | Wipe the graph and replace the ledger, then reconstruct the same state with historical attribution and prior registrations | **partial.** A reload re-applies acts by content (task-0199 AC7), and stage 2 re-reads the reviews (task-0222). A lost ledger loses registrations; no history | additive | 1.2.0 | none | task-0199, task-0222 |
| INT-03 | A policy downgrade by request, manifest, old client, import or rollback fails; unsupported versions refuse | **partial.** Newer formats refuse, exit 2 (decision-0023), and the hook guards assistant edits of attestation tables. No instance policy exists to downgrade | additive | 1.1.0 (with POL-02) | none | decision-0023, task-0147 |
| INT-04 | CI runs the suites, both comparators, the round trips and the new crash, concurrency, worker and verifier tests; 0/1/2 kept | **partial.** CI holds today's: the `tests`, `rdflib`, `rdflib-readers` and `stack` jobs, the comparators, `check_snapshots` SNAP-01..11, `check_worker` EXEC-01..14, and the exit contract through `cli_exit`. New tests absent | no | each | real worker | task-0084 (CI budget), task-0163 |
| INT-05 | A fresh operator follows configure, authenticate, attest, export, verify and restore; failures name the missing part without secrets | **partial.** Configure and attest are documented (`instance/README.md`, `docs/guide.md`). There is no authenticate, export-verify or restore flow | no (docs) | each | follows the packages | task-0181 |

**Counts.**

| Package | Present | Partial | Missing |
|---|---|---|---|
| P0 | 0 | 2 | 2 |
| P1 | 0 | 3 | 3 |
| P2 | 0 | 2 | 5 |
| P3 | 0 | 3 | 5 |
| P4 | 0 | 5 | 1 |
| P5 | 0 | 2 | 6 |
| P6 | 0 | 5 | 0 |
| **All** | **0** | **22** | **22** |

**By contract class.**
- No: 2 (INT-04, INT-05).
- Additive: 42.
- Breaking as specified: 0.
- Breaking if a choice goes the other way: 4 rows.
  - POL-02 and IDN-04: if enforced became the default.
  - JRN-01 and DEP-04: if the ledger stopped superseding by path rather than history going to a separate journal.
- Unresolved: the store-port question in §4.6, which could reclassify the P1 rows.

## 2. Per package

**P0.**
- *Exists:* format versions with refusal, one canonical JSON digest, a report identity that names its inputs (decision-0029, 0037 to 0040), honest docs on what a verification is, and an assistant-write hook.
- *Missing:* the assurance vocabulary and fields, any instance-level policy, a written threat model. `docs/security.md` lists flows and gaps but names no adversary.
- *Depends on:* nothing; every other package depends on it.
- *Decisions for the maintainer:*
  - the threat model: the five actors, and whether the storage administrator is in scope before P5;
  - where enforced policy lives: a documented `KG_*` setting, which is a contract under decision-0027, or an instance file outside the subject root, so that a subject edit cannot downgrade it;
  - the canonical serialisation: today's sorted-key compact JSON, or RFC 8785;
  - the public subjects' status: compatibility only, with their attestations labelled declared or legacy. decision-0044 point 2 and decision-0019 keep them the maintainer's.

**P1.**
- *Exists:* whole-unit publication, fencing, recovery, content-bound acts, the ledger outside the store.
- *Missing:* any append-only record, event ids, idempotency, an acknowledgement, replay.
- *Depends on:* P0, and V-F3's fix (directory fsync) before a durability claim.
- *Decisions for the maintainer:*
  - **The backend.**
    - `sqlite3` is in the standard library and transactional, but single-host, local disk only: the same assumption as `flock` for `KG_RDFLIB_FILE`.
    - A journal in Neo4j would need a label the wipe spares, as `_KgPublication` is (`harness/store_neo4j.py:720`), and would leave rdflib needing another.
    - Several hosts need a server database, which is a new dependency.
  - **Authority:** what is authoritative, the instance's git files (decision-0002 point 1) or the journal (§4.2).
  - **The acceptance boundary** against decision-0014 (§4.1).
  - **The ledger:** whether it keeps superseding by path.

**P2.**
- *Exists:* issued handles with unit, roles and dates; the self-review refusal by handle; content-bound rulings; the giver read from content.
- *Missing:* any authentication; a canonical person; delegation; four eyes on documents.
- *Depends on:* P0, P1 (the plan: no authenticated write before durable recording), and an identity provider.
- *Decisions for the maintainer:*
  - the identity route: OIDC tokens or signed acts. Either needs a signature library: Python's standard library has `hashlib` and `hmac`, no asymmetric verification, and the plan forbids custom cryptography;
  - the ieam-register 0009 amendment (§4.4);
  - task-0347's two checks, which can land at 1.1.0 ahead of P2.

**P3.**
- *Exists:* declared execution results bound by digest to the documents, the implementation and the suite; a worker that confines model code and cannot be forged by it.
- *Missing:* a producer, a signature, issuer policy, positive-proof checks, scope, rotation.
- *Depends on:* P0, P1, a signing library, CI issuer trust, a real worker for VER-06, and V-F2's fix as the negative-control pattern.
- *Decisions for the maintainer:*
  - the issuer: GitHub Actions OIDC through Sigstore, or a supervisor key;
  - whether the worker may run an instance's suite (§4.7);
  - the positive-proof rule: required counts and no required skip;
  - whether enforced mode refuses a re-listed digest with no run (§4.10).

**P4.**
- *Exists:* three registration routes; a content-bound `used` record; one suspect rule; a reported model identity; a run initiator; prompt and bundle files kept.
- *Missing:* route labels, delivery outcomes, content digests of what was delivered, history.
- *Depends on:* P0 for the labels, which can be 1.1.0; P1 for DEP-04 and DEP-05.
- *Decisions for the maintainer:* the DEP-02 clipping observation (§3), and the label names.

**P5.**
- *Exists:* digest manifests for connector exports and vendored copies; round trips; excerpt-only storage.
- *Missing:* everything the IDs test.
- *Depends on:* P1, a signing library and a witness.
- *Decisions for the maintainer:*
  - the witness: a public transparency log leaks an instance's metadata; a private, separately controlled store is the alternative;
  - erasure against retention (ieam-register 0009 point 5);
  - whether P5 stays on demand or becomes conditional P1, as the plan allows.

**P6.**
- *Exists:* CI for everything that exists now.
- *Missing:* the new checks and the operator flow.
- *Decisions for the maintainer:*
  - the CI budget (task-0084, 12 minutes) for the new crash and worker tests;
  - Landlock-capable runners for VER-06.

## 3. Allowed now in 0.9.x

Fix-only or docs-only, no contract moved:
1. **The threat-model decision record** (P0 step 1), drafted and decided. A record is not a build: decision-0041's "no build dispatched before 1.0.0" holds.
2. **Wording.** In `docs/security.md`, `docs/guide.md` and `instance/README.md`:
   - a registered dependency is not demonstrated use (DEP-01);
   - `consulted` counts requests, not deliveries (DEP-02);
   - an execution verification is a declared result (VER-08, largely done at `docs/guide.md:692-701`; the MCP tool descriptions could say it too, as decision-0041's 0.9.x mitigations did).
3. **Known-limits lines** under `## Unreleased`, the precedent being decision-0041 N-3:
   - the ledger keeps one entry per path;
   - a load keeps no history of acts;
   - `consulted` includes attempts;
   - the delivery clipping, once its intent is confirmed.
4. **Characterisation tests that pin today's behaviour.** For example, that a refused read is in `consulted` and not in `consulted_assertions`, and that no oracle runs at load. Tests move no contract.
5. **Prerequisites already being fixed elsewhere**, not part of this plan's work: V-F2 (VER-03, VER-06), V-F3 (JRN-04). V-F1 matters to any new HTTP intake under P2, and V-F4 to DEP-03 deadlines.

**Not allowed now, though it looks small:**
- Clipping tool results at `READ_LIMIT`, not `RESULT_LIMIT`, changes what the arms deliver. Whether that is a fix or a record move is the maintainer's.
- task-0347 (a) and (b) are 1.1.0 under decision-0041.

## 4. Conflicts with the record

1. **decision-0014 (with A1).** The publication boundary is the act's acceptance today: "the wipe, the load, the rules and the reviews, is one transaction, so nothing of it is visible before it commits and a failure leaves nothing behind" (`docs/security.md`, store generations).
   - P1 step 4 and JRN-02/JRN-04 accept at journal commit, with projection pending. That is a state decision-0014 does not have, and one no reader can name.
   - Needs an amendment: two boundaries, a generation naming the journal position it reflects, and how the lease or lock covers the journal append ("every writer takes the same lease or lock").
   - The history the plan wants is compatible with "no earlier generation is retained" only because it lives outside the graph.
2. **decision-0002 point 1 and decision-0009 (a).**
   - A ruling's record is the review file, "append-only", beside the captures.
   - An attestation is the manifest's declaration, its four eyes the pull request.
   - The store's port docstring: "Status and provenance are the store's; content stays in git."
   - P1 step 2 makes journal events authoritative over these files, and P2 step 7 binds acts to envelopes rather than to the TOML. A decision must say which record wins and how a git edit to a file meets an accepted event.
3. **decision-0009 (a) and ieam-register 0019 against IDN-04.**
   - The four eyes are an unchecked pull request, and on the public subjects author = attester = `agent:maintainer` (task-0347).
   - Enforced four eyes supersedes 0009 (a) for enforced instances. The public subjects stay compatibility, or the record moves, which task-0347 calls a later major.
   - Under ieam-register 0019 the drafter is the session, which is task-0347 (b)'s field.
4. **ieam-register decision 0009 points 1 and 5 against P2 steps 1 to 3, IDN-03 and the retention of P1 and P5.**
   - 0009 point 1: "The register, the knowledge store and their tools never hold the key and never call the directory."
   - 0009 point 5: the key is erased, and "the handle in git is then effectively anonymous".
   - A principal-to-handle mapping, a canonical person id, or a stored `sub` is that key. The amendment starts in ieam-register's `decisions/`, or P2 is shaped so that the identity provider's signed act carries the handle only and knowgov stores issuer and handle, never the subject. decision-0002's closing line ("the directory answers who") follows 0009.
5. **decision-0008.** The reader stays read-only, which the plan keeps. Two tensions:
   - Journal reads (a report's journal position, DEP-06's labels over MCP) need to be in `store.READS` or a separate read path.
   - decision-0043's verdict audit log, if it is the journal, makes the reader write. That needs its own process, as `knowgov-runs` is, or an amendment.
6. **decision-0016 point 3 (the store port is a 1.0 contract) with point 7.**
   - P1's "narrow journal interface" and step 6's event ids on assertions, approvals, attestations and registrations change port writes.
   - The record does not say whether a new port operation is additive (for callers) or breaking (for an adapter outside this tree). The maintainer's ruling sets the P1 rows' class.
   - Point 2: none of it before 1.0.0.
7. **decision-0012 (condition 1 and its scope, `harness/execution.py:82-94`).**
   - The worker grades only the subjects its image ships; an instance's subject is refused; results are untrusted data.
   - VER-06's "real supported worker" as a producer of an instance's evidence needs that scope amended. Otherwise P3's producer is CI alone, and VER-06 tests the arms path only.
8. **decision-0043 (the order after 1.0.0).**
   - It orders C5-1, then the verdict audit log and per-user identity "as one decision before either is built", then one connector, then suggested map rows.
   - The sequence accepted on 2026-11-15 does two things to it. It puts P2 behind P1 and P3 and gates it on a lighthouse identity provider, which splits identity from audit. It also leaves the connector's place unstated.
   - That sequence is not yet in `backlog/decisions` on main (no record names it). Until a record amends decision-0043, its order is the record's.
9. **decision-0041.** 1.1.0 is its batch. Adding P0 and P4 labels enlarges 1.1.0, which is consistent, but it is a scope change the record does not yet carry.
10. **decision-0036 and decision-0038's standing consequence.** "Re-listing an edited document's digest re-verifies it by execution although nothing ran on the new content" (the 0.9.0 Known limits).
    - VER-04 under enforced policy must not authorise on a re-listing alone.
    - That narrows decision-0036's meaning for enforced instances; compatibility keeps it.
11. **The MCP reader's dependency rule.** `docs/security.md`, "The MCP server adds no package: standard library only" (`tests/test_demo.py::test_the_mcp_server_adds_no_dependency_to_the_image`).
    - Signature verification inside the reader would break it.
    - Verify at load and read the stored state back, or amend the rule.
    - A signing library is also a new pin. Its licence must sit with decision-0026's boundary, and the plan's own "maintained implementation" rule excludes a standard-library substitute.

Not conflicts, checked:
- decision-0023's refusal of newer formats is what P6 step 5 asks for a rollback.
- decision-0019 and decision-0044 point 2 keep the public subjects' attestations the maintainer's act, which POL-01's legacy labelling leaves untouched provided the comparator learns the new fields as unknown, as for `code` and `preload` (task-0341).
