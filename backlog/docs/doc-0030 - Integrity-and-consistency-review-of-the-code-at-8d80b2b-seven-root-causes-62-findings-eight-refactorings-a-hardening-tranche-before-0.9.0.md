---
id: doc-0030
title: >-
  Integrity and consistency review of the code at 8d80b2b: seven root causes, 62
  findings, eight refactorings, a hardening tranche before 0.9.0
type: specification
created_date: '2026-11-06T23:41:00Z'
updated_date: '2026-11-07T07:15:00Z'
tags:
  - review
  - integrity
  - consistency
  - canvas
  - fit-gap
  - swot
---
*2026-11-07. Maintainer register. The maintainer asked, on 2026-11-06, for "an integrity and consistency validation of the code; is it semantically sound & also from functional perspective → is the logic sound & semantically correct? Draw your conclusions and list potential improvements/refactorings." Nothing is built here and no task is minted (the finalization guide: no follow-up without the maintainer's approval). Every finding is a proposal.*

## Scope and method

- **Code:** knowgov `main` at `8d80b2b` (#327 merged), about 28,000 lines of production code (harness 15,010; demo/app 3,634; tools 8,025; instance/ci 748), read against CLAUDE.md, the decision records and the briefs. The 17,638 lines of tests were read where they bear on a finding.
- **Six reviewers in parallel**, one area each:
  1. the gate's semantics (gate, rules, cadence, review, gate_cli);
  2. the store port and its two adapters;
  3. the ingest path (load, extract, change, reviews, captures);
  4. the MCP and HTTP read surfaces;
  5. runs, the arms, the contained worker and trace;
  6. the page, the instance CI wrappers and hooks, and the check tools.
- **Each finding** quotes its lines and gives a concrete failure scenario. Each is reproduced by a probe on an rdflib store (Neo4j reasoned from its Cypher) or is unambiguous from the code, and is marked CONFIRMED or PLAUSIBLE. The probes are kept outside the repositories.
- **The coordinator re-checked 20 of the high and medium findings against the code**, and all hold. Three defects were found independently by two or three reviewers: the subject identity (three times), stage 2 reopening a closed gap (twice) and the wall-clock lapse (twice).
- **Excluded as already known:**
  - doc-0023's four arm defects (task-0185 to task-0188);
  - `gate_cli`'s former shared-store reload (decision-0017, #327);
  - the Known limits of CHANGELOG.md and doc-0028 §10;
  - the QUALIFIED band's strict `>` 25 %.

## Verdict

**Sound with defects, in every area.** What holds, measured:

- **The gate's core:**
  - the min rule and decision-0004's pending rule;
  - the five-step ladder, `--fail-on` and the three verdicts;
  - lapse boundaries to the day (S1: PROCEED on 2027-02-06, QUALIFIED on 2027-02-07, BLOCKED with 10 of 36 keys on 2027-08-07);
  - `--baseline` regression semantics;
  - the report shape.
- **The record:**
  - the first load reproduces it (CargoQuote S1: 145 statements, 111 approved; J-F C: 712, all approved);
  - the deterministic run is identical under `PYTHONHASHSEED` 1 and 977 and under `KG_TODAY` 2026-10-30 and 2031-01-01 with `--as-of record` (0 differing leaves over 7 scenarios);
  - raw-byte Version and part digests are right.
- **decision-0014's generations**, on both adapters:
  - the seqlock order and idempotent counters;
  - fencing under the lock;
  - task-0175's recovery;
  - rdflib's lock-then-load, atomic replace and inode-keyed cache.
- **Read-only holds:**
  - the reader's view;
  - an AST walk of the rdflib reads finds no mutation;
  - the store file's digest is unchanged across every reader probe;
  - `scratch_store()` shares nothing with the configured store.
- **Equalities:**
  - `gate_verdict` equals `gate_cli --no-load` (43 of 43 combinations);
  - `evidence_bundle` equals the arms' `render_bundle`;
  - all 17 reader tools validate against their schemas.
- **Containment:**
  - no path runs a model's code outside the worker or before a fresh attestation;
  - the Landlock rules are correct;
  - the network check fails closed;
  - the sandbox never follows a link.

**Where it is not sound.** The defects are not scattered. They cluster in seven root causes, each a place where one concept is held twice or implicitly. Five of the seven can give a wrong verdict, or a right verdict on the wrong data, with no error.

1. **The store does not know whose load it holds.** The extraction activity is `act:extract:<scenario>:<version>`, with no subject, and five readers parse it the same way. Two subjects that share a scenario id (the onboarding skill gives every subject `S0`) answer each other's gates.
2. **Ids name positions, not content.** A person's ruling, trace's ledger and the derived-output link bind to `A:<short>:<entity>|<pred>[#n]@v1`, which a reload re-mints for whatever the document now states.
   - An approval moves to a new value.
   - Code built on the old value reads clean.
   - The gate and trace disagree on "suspect".
3. **Stage 2 is not a re-load.** It re-runs every rule but not the reviews, pairs statements within one version only, resolves symbols from the one re-ingested file, and skips a statement whose remaining fragments were reused. Its gate can therefore differ from a fresh load of the same documents, in both directions.
4. **Two clocks.** A person's approval lapses at load time by the wall clock, while the gate reads `--as-of`. Some approvals never lapse, and events dated after `--as-of` count.
5. **One concept, two definitions:**
   - *superseded*: the gate reads the key, the stale finding reads the artefact;
   - *suspect*: a stored flag against the statuses;
   - *unknown* against *disputed*;
   - the owner route;
   - the held version, by lexical order of tags;
   - the order of three port reads and the gap ids they number;
   - id uniqueness per adapter.
6. **Contract edges:**
   - the exit codes 0/1/2 leak tracebacks as exit 1;
   - the MCP server accepts unknown arguments and dies on a malformed name;
   - an HTTP refusal leaves the connection open to a smuggled request;
   - `subject_check` reads any path a proposed manifest names;
   - two hook bypasses.
7. **Checks that pass vacuously:**
   - the round trip computes the store reads and never compares them;
   - `| tee` without pipefail hides a failing saved query;
   - the comparator accepts a partial run;
   - `check_instance` accepts an empty or duplicated subject set;
   - `test_security` scans one directory level;
   - `schema_check` takes `true` for `1`.

## Findings

Deduplicated, most severe first: 7 high, 25 medium, 30 low. The ids are this doc's; the area prefix names the reviewer that found it (G gate, S store, I ingest, M MCP, R runs, P page and CI). ✓ marks a finding the coordinator re-checked against the code.

### High

| Id | Root cause | Where | Finding | Failure, measured |
|---|---|---|---|---|
| H1 ✓ | 1 | `load.py:72`; `gate_cli.py:389`; `mcp_server.py:489`; `proposal_impact.py:820`; `demo/app/server.py:428,463` | The held scenario is matched to a subject by its bare id | Two subjects with `S1`: `gate_verdict {subject: twin}` answers PROCEED from CargoQuote's data while the twin's own S1 is BLOCKED; the page serves A's 35 gaps as B's; `--no-load --subject B` answers PROCEED on A's statements. Breaks decision-0013 A1 and known limit U1's refusal. Found by three reviewers |
| H2 ✓ | 3 | `change.py:37`; `store_rdflib.py:744`; `store_neo4j.py:928` | Stage 2 re-runs every rule and never re-applies the reviews; R-REQ resets a closed declared gap to open | S2 with the compliance owner's close of OD-1: PROCEED after stage 1, BLOCKED on `QuoteAPI\|on_screening_outage (declared_gap)` after a stage-2 re-ingestion. Found by two reviewers |
| H3 ✓ | 4 | `load.py:294,321`; `gate_cli.py:517`; `cadence.py:155` | A person's six-month approval lapses at load by `review.today()`, not `--as-of`; `cadence.lapse` skips elicited statements | `--as-of 2026-11-03` reads PROCEED under KG_TODAY 2026-11-03 and QUALIFIED under 2027-05-03, the report naming the same `as_of` and no `lapsed` finding; `--as-of record` is not reproducible. Contradicts decision-0005 points 3 and 5. Found by two reviewers |
| H4 ✓ | 3 | `store_rdflib.py:666`; `store_neo4j.py:886` | R-CONFLICT and R-CORROBORATE pair only statements of one version | Stage 2 changes the table's accept row to 45 while the DMN and the sequence diagram say 41: stage 2 reads QUALIFIED (`proposed`), a fresh load of the same documents BLOCKED (`disputed`) |
| H5 | 2 | `review.py:192-203,272-274`; `load.py:316-326` | A ruling binds to a positional assertion id with no value or digest | The table is edited after employee-3 approved `A:dt:S-accept\|max@v1` at 41: the same id now carries "below the low forties" and reads approved by that review. A vanished id refuses the whole review, on stderr only |
| H6 ✓ | 2 | `load.py:108`; `trace.py:259-260` | `trace check` reads only the used statements' statuses, and a reload re-mints the same id for the new value | S6 published, `reference_impl.py` registered, P2 edited 316.00 → 341.00, reloaded: `trace check` exit 0, `unchanged`, although instance/README.md says such a change makes the file suspect |
| H7 ✓ | 6 | `subject.py:141,145`; `subject_check.py:11-12` | `subject_check` confines the documents a call carries, not the paths its proposed manifest names | `[[artefact]] path` absolute or `../` beyond the temp root is read. Existence oracle, and the parser's excerpt of any server file in the report. Over HTTP, any token holder on a wide bind; on stdio, the local user only. `x/../subject.toml` also overwrites the passed manifest |

### Medium

| Id | Root cause | Where | Finding |
|---|---|---|---|
| M3 ✓ | 6 | `mcp_server.py:1322-1344` | An HTTP refusal (404, 421, 403, 401) is answered without reading the body or closing the connection. On keep-alive, the body is parsed as a second request with a forged Host: the rebinding defence is bypassed (probe: 421, then a 200 tools/call). The page closes on refusal; the reader does not |
| G3 ✓ | 5 | `gate.py:46`; `store_rdflib.py:931`; `store_neo4j.py:1062` | *Superseded* is computed two ways. The gate drops an invalidated statement when any statement on the key is settled, while the stale finding, `superseded_by` and the bundle count same-artefact successors only. Result: gate PROCEED beside "major stale, no successor" (`--fail-on major` exits 1). 25 of 36 codegen keys rest on two or more documents |
| R5 | 5 | `store_rdflib.py:624,940`; `store_neo4j.py:863,1070`; `trace.py:236-238` | *Suspect* is a stored flag for the gate and a status reading for trace. After a reload, trace re-registers with `suspect: false`, so one store gives trace's suspect blocker beside a gate that lists another output only |
| M4 ✓ | 5 | `gate.py:116,144` | `three_valued_answer` says "unknown, no assertion" for a key whose statements are all disputed. On S4, `QuoteAPI\|on_screening_outage` (four disputed) reads unknown while the gate blocks it disputed |
| S2 ✓ | 5 | `store_neo4j.py:881,1016,1021`; `store_rdflib.py:650-879`; `rules.py:115` | `candidate_pairs`, `conflict_gaps` and `declared_gaps_for_key` have no defined order, so R-CONFLICT numbers gap ids in store order. On S4, `:0` is bpmn-vs-table on the Neo4j record and table-vs-puml on rdflib. Since decision-0017, the default gate (rdflib scratch) and the page and MCP (Neo4j) name one conflict by different ids. This is #256's class, and `check_round_trip`'s canonical sort hides it |
| G4 | 4 | `cadence.py:158` | An approval from a review file, with no verification, never lapses (`if not vers: return None`). Contradicts decision-0005 point 4 |
| I9 | 4 | `load.py:22-36,204-209`; `change.py:42` | An undated `[verification] authored`, `approval` or `review` is dated by each load's day, so it never lapses. The attester defaults to `agent:maintainer`, and an undated stage-2 `reverify` is stored undated; `check_subject` is silent on all three. Probe, KG_TODAY 2028-06-01: the dated subject reads BLOCKED with two lapses, the undated one PROCEED |
| G5 | 3 | `store_rdflib.py:732`; `store_neo4j.py:923`; `rules.py:137` | A declared gap outlives the statement that declared it, because `declared_open` has no status filter. A spec v2 that specifies REQ-06 leaves the key at `declared_gap` |
| I5 | 3 | `load.py:39-43,70`; `change.py:34`; `extract.py:206-221` | Stage 2 resolves symbols from the one re-ingested file, and the definition sentence (`ACCEPT_MAX = 41`) is no fragment. (a) Re-ingesting the sequence diagram flags `S-accept\|max` ambiguous falsely, so PROCEED becomes QUALIFIED. (b) Changing only `ACCEPT_MAX` invalidates nothing, so it reads PROCEED where a fresh load reads BLOCKED |
| I6 ✓ | 3 | `load.py:105` | The re-ingest skip drops a statement whose value changed while its remaining fragments were reused. On J-F, removing one `@JDL-001` tag leaves `JDL-001\|verified_by` invalidated with no successor. This affects every multi-fragment bundle mapper |
| I4 ✓ | 2 | `review.py:209-216` | A reviewer holding `closes` can approve a model's statement (basis `inferred`), contrary to "never promoted". The gate then raises only a minor "approved but flagged inferred" |
| I8 ✓ | 2 | `load.py:256-275` | Route-c candidates load into every scenario and count in the min rule, so a model's guess lowers a documented key (S1 goes from PROCEED to QUALIFIED). They are attributed to `[provenance] llm`, not to the file's model |
| S1 ✓ | 5 | `load.py:76-77,85-113` | An artefact with a `mapper` and `store = false` still has its statements loaded, without a Version. They pair, corroborate or dispute, and can BLOCK. The fragment count is inflated (95 counted against 87 nodes) |
| G6 | 6 | `gate_cli.py:305-309,541-552` | A malformed or unreadable `--baseline`, or an unwritable `-o`, exits 1 with a traceback (exit 1 is reserved for a finding). Other errors read "the store did not answer" |
| M5 | 6 | `mcp_server.py:676-720` | Every `inputSchema` says `additionalProperties: false`, but only `register_nodes` refuses an unknown argument. `gate_verdict {senario: S4}` answers S1 with no guard, and a misspelt `as-of` is ignored |
| M6 ✓ | 6 | `mcp_server.py:1134`, `serve_stdio` | An unhashable `params.name` raises out of `handle`. That kills the stdio server, the reader and knowgov-runs alike, and drops the HTTP connection |
| P2 | 6 | `instance/ci/claude/knowgov_hook.py:109-146` | The spec-commit transition reads `git diff --cached` before the command runs. `git add x && git commit` and `git commit -m x path` are never gated, and pushes through `/usr/bin/git`, `bash -c` or `git -C` are not seen |
| P4 | 6 | `instance/ci/claude/attestation_paths.py:51,129-190` | `[capture]` is not guarded. Writing `notes/c1.toml` with `[[answer]]` tables and then adding `[capture] dir = "notes"` are both allowed, and every load then reads fabricated answers as elicited |
| R2 ✓ | 6 | `execution.py:282`; `run.py:174,195` | A model-output outcome the worker reports (timeout, kill, unparseable) raises and aborts the whole run: no summary, usage or SHA256SUMS. On the host backend the same outcome is a failed cell. J-F's oracle allows 1,500 s against the job's 900 s |
| R3 | — | `run.py:192-195,280-306`; `agent.py:76` | A reused `--out` folder carries earlier attempts into the record. The sandbox is never emptied (`--resume` grades an old file), `usage.json` is summed regardless, and stage 2 reads a leftover `S1/run1_G.py` (a deterministic S6 then differs by 8 leaves) |
| R4 ✓ | — | `worker.py:298-317,345` | The reaper kills one level of escaped descendants per round, for 50 rounds. A 70-deep `setsid` chain leaves 21 processes alive, counted as the next job's `before` and never killed, sharing the process and memory caps with every later job (under Landlock ABI 7) |
| S3 ✓ | — | `store_rdflib.py:265` | Every publish forces the store file to 0644, so an operator's `chmod 600` on `KG_RDFLIB_FILE` is undone. Contradicts docs/security.md:374 |
| P3 | — | `demo/app/server.py:91-166`; `page_subject.py:86-93` | The rescan rebuilds on a changed mtime, but `page_subject.of` caches by root forever. An edited name, `listed`, tasks or id is never served, and `scenarios.toml` is not watched. With `KG_SUBJECTS` set and nothing loadable, the page serves public CargoQuote, against its docstring |
| P5 ✓ | 7 | `tools/check_round_trip.py:77,116-133` | `answers()` collects `store_reads`, and `differences()` never compares them, so task-0144's cross-store claim is vacuous |
| P6 ✓ | 7 | `.github/workflows/demo.yml:206,232,322,334` | With no `shell:`, steps run `bash -e` without pipefail, so `check_saved_queries.py \| tee` discards an exit 1. CLAUDE.md's "a syntax error in one fails there" does not hold |

### Low

| Id | Where | Finding |
|---|---|---|
| G7 | `gate_cli.py:404-406` | `--publish` commits before the report is validated and written, so the shared store is replaced and the command can still fail |
| G8 | `capture.py:122-184`; `register_change.py:147` | A key with several owners routes to an `-unassigned` questionnaire that is never written; the register-change owner is a third computation |
| G9 | `gate_cli.py:207-209,298-305` | `--stage 2 --baseline record` compares against stage 1's record, so the record's own stage-2 outcome reads as a regression (exit 1) |
| G10 | `cadence.py:165-171` | As-of counts approvals and verifications dated after `on` |
| G11 | `cadence.py:73` | Review months take the minimum over nodes with the default mixed in, where decision-0005 point 2 says "else default": a 24-month kind is cut to 12 |
| G12 | `schema_check.py:62-65` | `enum` and `const` accept `true` for `1` and `2.0` for `2` |
| I11 | `load.py:86`; `check_subject.py:180` | A duplicate `short` is not refused, so statements are attributed to the first artefact; a duplicated requirement row fails as "the store did not answer" |
| I12 | `preload.py:75`; `citation.py:41,59` | preload compares the report's raw-byte digest with an LF text digest, so an unchanged CRLF document reads unchecked; a line-1 citation after a BOM is missed |
| R6 | `agent.py:150-160,279`; `run.py:219` | The run's seconds ceiling reached mid-stream is recorded as an API error, so `--resume` re-runs and spends again |
| R7 | `worker.py:357-394` | Model code can forge the job result through the parent's stdout during the 5 s drain (confirmed under Landlock); low, since the oracles' own channels are writable anyway |
| R8 | `annotate.py:17-18,93-99` | Under `--baseline`, annotate marks held findings as errors though the gate exited 0 |
| R9 | `trace.py:403-407`; `run.py:242`; `transcript.py:126` | `review.WallClock` escapes `except ValueError`, so the command exits 1 with a traceback |
| R10 | `worker.py:70,216` | `write_confined` is attested at Landlock ABI 1, but truncation is denied only from ABI 3; a denial of service only (PLAUSIBLE) |
| R11 | `tests/test_security.py:130-167` | The network rule scans one directory level and misses `asyncio`, `ssl`, `socketserver`, dynamic imports, `instance/ci/claude` and `subjects/*/oracle`; nothing violates it today |
| R12 | `transcript.py:120-129` | Route (c) records the configured model, not the one that answered |
| M7 | `upward.py:235` | `code_path`'s ledger leg reads `drift: false` for a file never looked at |
| M8 | `mcp_server.py:982-1000` | `three_valued_answer` ignores review currency |
| M9 | `tools/check_mcp_server.py:253` | The equality check hardcodes `task_codegen`; it would diverge on a scenario whose prompts differ |
| M10 | `mcp_server.py:1372` | `--host ::1` passes `bind_check`, then crashes (AF_INET only), exit 1 |
| M11 | `register_impact.py:64` | `exec_module` writes `__pycache__` into `KG_REGISTER/tools` |
| S4 | `store_neo4j.py:37-47,717-865`; `store_rdflib.py:309-327` | Id uniqueness differs per adapter: Neo4j can hold a duplicate Derived, which `export_turtle` then cannot carry |
| S5 | `store_neo4j.py:1127`; `store_rdflib.py:1009` | The held version comes from the tags' lexical order when the stage-1 and stage-2 `at` tie |
| S6 | `load_memory.py:95-108` | The preflight forecasts first loads only, so a refusal can come at S7, after six scenarios' paid calls |
| S7 | `store_neo4j.py:508-607`; `store_rdflib.py:250-275` | A writer that only reads still publishes, so every reader re-reads; a failing saved query may poison the Neo4j unit (PLAUSIBLE) |
| S8 | `store_neo4j.py:968,984`; `store_rdflib.py:816,841` | `invalidated_at` means epoch seconds on Neo4j and a node sequence on rdflib |
| P7 | `demo/tools/compare_deterministic.py:116-120` | A requested scenario missing from the run is skipped (1 of 7 present: exit 0) |
| P8 | `knowgov_hook.py:157-207`; `.claude/hooks/protected_paths.py:117` | A valid-JSON non-object report raises, so the hook exits 1, which the advisory profile treats as a warning (fails open) |
| P9 | `instance/ci/knowgov-gate.sh:53-54` | `KG=$(cd "$KG" && pwd)` has no `|| exit 2`, so bash exits 1 on a mistyped path |
| P10 | `tools/connector.py:188` | An export file sharing a basename with another is dropped silently |
| P11 | `tools/check_instance.py:145-147` | An empty `subjects/` and duplicate subject ids pass |

## Refactorings

Eight, each removing a class rather than one instance; the ids they remove are listed. The cost is rough. The release column follows decision-0016: a contract change after 0.8.0 gathers for 0.9.0, and a fix is not bound.

| # | Refactoring | Removes | Cost | Release |
|---|---|---|---|---|
| F1 | **A subject-stamped held state.** Record the subject at load, as a meta node or a property of the activity. One port read `held() → {subject, scenario, version per artefact, loaded_at}` comes from the `CURRENT` edges, not activity order, and replaces the five `split(":")[2]` parsers. Until then, `check_instance` refuses a scenario id two subjects declare, and refuses empty or duplicate subjects | H1, S5, P11 | medium | contract (the activity, `store_status`): 0.9.0; the `check_instance` guard a fix, now |
| F2 | **Bind every person's act and every derived output to content.** A ruling carries the value and the fragment digest, and a changed statement is skipped and reported in the gate report. The trace ledger carries each used statement's value or Version digest. *Suspect* is computed from statuses by one port read that the gate, MCP and trace share. `authored`, `approval` and `review` require `at` and an attester. `inferred` is refused at ruling time | H5, H6, R5, I4, I9 | medium | contract (review file, ledger): 0.9.0 |
| F3 | **Stage 2 as a whole re-load.** The stage-2 kit loads as v2, and statements are diffed by id stem on value and fragment set. R-STALE runs, then the rules across versions, then the reviews again. R-REQ never reopens a closed gap, and R-STALE withdraws a gap whose declaring statement it invalidated. A test holds a stage-2 gate equal to a fresh load's gate plus the stale and suspect findings | H2, H4, I5, I6, G5 | medium | a fix; the record's S6 must stay equal |
| F4 | **One clock.** The resolved as-of reaches `load_reviews`. Every lapse is decided in `cadence.lapse` against `on`, a person's approval included, each with a `lapsed` finding. Events dated after `on` are ignored. `three_valued_answer` reads as of the session date | H3, G4, G10, M8 | medium | a fix, with an additive report entry |
| F5 | **One definition per concept.** Supersession comes from one successor set, and the status as of a date includes *disputed*. One owner and route module. A port order contract: every list-valued read declares its order, tested on the shuffling fake driver. One uniqueness rule in the port | G3, M4, G8, S2, S4 | small to medium | the order contract moves gap ids, so it needs a decision with S2's record note |
| F6 | **Uniform edges:**<br>• one CLI exit wrapper for gate_cli, trace, run and transcript (`CannotRun`, `WallClock` and the unexpected map to 2; the report is validated and written before `commit()`);<br>• MCP arguments validated against each tool's own `inputSchema` in `Server._tools`, with `schema_check` made type-strict;<br>• a catch-all to JSON-RPC errors;<br>• refuse-then-close in `http_boundary`;<br>• one confinement helper for every client-influenced path;<br>• one hook entry wrapper | H7, M3, M5, M6, G6, G7, R9, M10, P8, P9, G12 | small each | M5 is a behaviour change (unknown arguments refused): 0.9.0; the rest fixes |
| F7 | **Checks that compare by construction.** `differences()` iterates over every key `answers()` returns. The comparator takes the expected scenario set as required. `defaults: run: shell: bash` in both workflows. `test_security` scans recursively | P5, P6, P7, R11 | small | a fix; worth doing first, since it guards the rest |
| F8 | **Worker isolation and the run-folder lifecycle.**<br>• After each job, kill every uid-65534 process but the worker;<br>• `worker_job.py` is non-dumpable and its output is closed at exit;<br>• `write_confined` requires ABI ≥ 3.<br>A job-stage error becomes the kind's failed cell. A fresh cell clears its sandbox, `usage.json` merges only under `--resume`, and stage 2's derived input is an explicit flag | R2, R3, R4, R7, R10 | small to medium | fixes |

Left as single fixes, outside the eight: S1 (one loaded-mappers set), S3 (keep the file's mode), S6 (count stage-2 loads), S7 (a dirty flag gates publish), P2 and P4 (the two hook bypasses), P3 (one page cache keyed by both manifests' mtimes), P10, I11, I12, R6, R8, R12, M7, M9, M11, S8, G9 and G11.

## Opportunity canvas: a hardening tranche before 0.9.0

| Block | Content |
|---|---|
| Users | The lighthouse pilot's architects and owners (task-0062); an instance's CI and its Claude hook; MCP clients; the maintainer, who freezes the contracts at 0.9.0 |
| Problem | Five of the seven root causes can give a wrong verdict, or a right verdict on the wrong data, with no error. A pilot with two subjects, a document edit after a review, a stage-2 change or a review date read as of another day meets them in its first weeks. 0.9.0 would freeze contracts (the activity id, the review file, the ledger) that two of the fixes must change |
| Solution | F7 first. Then F1, F6's security edges (H7, M3) and the `check_instance` guard. Then F3, F4 and F2, the semantic core. Then F5 and F8. Each fix comes with a probe from this review turned into a test |
| Value | A verdict that depends only on the documents, the subject and the date. The checks that claim equality then hold it |
| Metrics | The 62 findings closed or explicitly kept. A stage-2 gate equal to a fresh load's on S6 and on a cross-version plant. The same report under any `KG_TODAY` for one `--as-of`. A test per high finding |
| Channels | The backlog: one task per refactoring, with this doc's ids in its description; CHANGELOG under Unreleased, contract changes under their heading |
| Cost | F7 and F6 are small (a day's session each). F1, F2, F3 and F4 are medium (one to two sessions each, with the CI budget). F5 and F8 are small to medium |
| Risks | The record's S6 or a scenario's ids move: F5's order contract renumbers conflict gap ids, so it needs a decision. Contract changes miss 0.9.0's cut and wait for 0.10.0 |
| Unfair advantage | The record and the probes already exist, so each fix is provable against a measured failure, not argued |

## Fit/gap against what it must satisfy

| Must satisfy | The tranche |
|---|---|
| decision-0016: contract changes after 0.8.0 gather for 0.9.0, fixes are not bound | Fit. F1 (activity, `store_status`), F2 (review file, ledger) and F6's M5 are contract changes and gather; F3, F4, F7 and F8 are fixes |
| The scored record and its comparator (CLAUDE.md: the record is never subset) | Fit for F3 and F4 if S6 and the deterministic run stay equal, which is each task's AC. A gap for F5's order contract, which moves gap ids the record holds: it needs a decision and a record note |
| decision-0013 A1: a child never answers from another subject's data | Gap today (H1); F1 closes it |
| decision-0005: lapses are gate findings, read as of the date | Gap today (H3, G4, G10); F4 closes it |
| decision-0002 and decision-0009: a person's act is attributable, dated and bound to what was approved | Gap today (H5, I4, I9); F2 closes it |
| decision-0008 and decision-0012: the reader never writes, and model code is contained | Fit (verified), apart from M11's `__pycache__` and R4's escaped processes, which F6 and F8 close |
| The CI budget (task-0084, 12 minutes) | Risk: each new test lands in `rdflib` or `rdflib-readers`. task-0180's third job would absorb them |
| Standard library only (harness) | Fit: nothing proposed adds a dependency |

## SWOT

- **Strengths.**
  - Every finding comes with a probe and measured output.
  - The defects cluster in seven root causes, so eight refactorings close most of them.
  - The core the record rests on is sound: the gate's ladder, the generations, read-only and containment.
- **Weaknesses.**
  - The tranche touches load, change and the store port, the most coupled parts.
  - Four of the eight are medium.
  - The Neo4j halves were reasoned from the Cypher, not run, except through the stack job.
- **Opportunities.**
  - 0.9.0's freeze would carry contracts proven against named failures.
  - The probes become the tests the area lacked: stage-2 equality, as-of reproducibility, two subjects and a document edit after a review.
  - The lighthouse evaluation (doc-0013) gains a cited integrity pass.
- **Threats.**
  - Contract changes missing 0.9.0's cut push it to 0.10.0, restarting the freeze.
  - A fix in the semantic core could move the record. *Response:* each task's AC holds S6 and the deterministic run equal, and F5's renumbering waits for its own decision.

## Advice

**Run the hardening tranche before 0.9.0's cut, in this order: F7, then F1 with the `check_instance` guard, H7 and M3, then F3, F4 and F2, then F5 and F8.**

1. **F7 first.** It is small, and until it lands the round trip, the comparator and the stack job can stay green over regressions of the rest.
2. **H1, H7 and M3 next.** They are the findings that answer for the wrong subject or open the boundary. The `check_instance` guard is a one-line interim for H1 that any instance can run today.
3. **F3, F4 and F2 together.** They are the semantic core. A pilot meets each of them on its first stage-2 change, the first review read as of another day, or the first document edit after an approval.
4. **F5 and F8 last.** F5's order contract needs a decision first, because it renumbers gap ids the record holds. F8 hardens a worker that already contains model code.

**Reasons.**
- Five of the seven root causes can give a wrong answer silently.
- Three of the fixes change contracts that 0.9.0 would freeze.
- The record survives every proposed fix except F5's renumbering, which is kept apart for that reason.

**The maintainer's questions:**
1. Accept the tranche and its order, and mint one task per refactoring (F1 to F8) plus the single fixes? *Recommended: yes.*
2. Add H1 to H7 and M3 to doc-0028's G9 list, so that 0.9.0 is not cut over them? *Recommended: yes.* They decide what the frozen contracts mean.
3. Ship the `check_instance` guard against shared scenario and subject ids now, as a fix, ahead of F1? *Recommended: yes.*
4. F5's order contract renumbers the record's conflict gap ids: a decision of its own, after the tranche? *Recommended: yes.* Until then, fix only the order of `declared_gaps_for_key`, which numbers nothing.

## Answered (2026-11-07)

The maintainer: "accept the advise on all four". In force:

1. **The tranche and its order.** Minted, in that order:
   - F7, task-0193;
   - the `check_instance` guard, task-0194;
   - F1, task-0195;
   - H7 and M3, task-0196;
   - F3, task-0197;
   - F4, task-0198;
   - F2, task-0199;
   - F6, task-0200;
   - F5, task-0201;
   - F8, task-0203.

   The single fixes, by area:
   - the two hook bypasses P2 and P4, task-0204;
   - store and ingest (S1, S3, S6, S7, S8, I11, I12), task-0205;
   - page and connector (P3, P10), task-0206;
   - runs and trace (R6, R8, R12), task-0207;
   - MCP (M7, M9, M11), task-0208;
   - gate (G9, G11), task-0209.

   Each task cites this doc's ids and keeps the record, the deterministic run and the comparator equal.
2. **H1 to H7 and M3 join doc-0028's G9 list as G9-11.** 0.9.0 is not cut over them. They are carried by:
   - H1: task-0195, with task-0194 as its interim;
   - H2 and H4: task-0197;
   - H3: task-0198;
   - H5 and H6: task-0199;
   - H7 and M3: task-0196.
3. **The `check_instance` guard ships now, as a fix:** task-0194, ahead of task-0195.
4. **The renumbering of the record's conflict gap ids is a decision of its own, after the tranche:** task-0202, which depends on task-0201. Until it is accepted, only `declared_gaps_for_key` is ordered, under task-0201.
