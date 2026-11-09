---
id: doc-0028
title: >-
  What a knowgov 0.9 and 1.0 need: the record is silent, the version arithmetic,
  the contract surface, the gap lists (proposed)
type: specification
created_date: '2026-11-06T09:04:00Z'
updated_date: '2026-11-09T07:11:00Z'
tags:
  - brief
  - release
  - versioning
  - v1
---
*2026-11-06. Maintainer register. A study: nothing built, no task minted. Trigger: the maintainer's question of this date, "what is needed for a knowgov v1.0 (or even a v0.9)?". Read at knowgov `43ee83f` and checked again at `a743cca`; ieam-register `735b2e2` (v0.2.12) and `0826ebc`; pumllint `a39d800`. One record per thing: the scores are doc-0012's (§8, this date); the definition of 0.9 and 1.0 is proposed in decision-0016; doc-0027 is the brief for the external pass. The gap lists below are proposals. The coordinating session reviews them and mints the tasks; none is minted before that.*

## Verdict

The record does not define 1.0. What decision-0016 proposes:
- **0.9.0 is the contract freeze.** The maintainer can reach it alone, and it is mostly decisions, not code.
- **1.0.0 is those contracts, unchanged through the lighthouse's foreign corpus.** This brings doc-0012 §6 S3's "1.0 contracts after a foreign corpus" forward to S1.

A 1.0 by declaration is possible after the freeze. It buys one Execute point (doc-0012 §8), and every break the pilot then forces becomes a major. 0.9's meaning needs deciding now: by decision-0003 §2's arithmetic, the counter reaches it within two contract-changing releases.

## 1. What the record says

- decision-0003 covers 0.x only: SemVer from 0.1.0, a contract change raises the minor, the contracts named (§2). Nothing on 1.0.
- doc-0012 §6 S3 (18–36 months) says "1.0 contracts after a foreign corpus".
- pumllint (v0.35.0) and ieam-register (v0.2.12) define no 1.0 either.
- task-0159's "V1" is task-0141's verification work package, not a version.

## 2. The arithmetic

- 0.1.0 (2026-11-03) to 0.7.0 (2026-11-06) is six contract-changing minors in four days (`CHANGELOG.md`).
- At `a743cca`, `## Unreleased` holds four contract changes:
  - whole generations (task-0141.06);
  - the pre-load report's layout block (task-0115);
  - contained execution (task-0141.05);
  - the worker behind `--profile arms` (decision-0015).

  The next release is therefore 0.8.0, which is being prepared.
- The next contract-changing release after it is 0.9.0. Without a decision, 0.9 arrives by counting and means nothing.

## 3. The contract surface

decision-0003 §2 names five contracts:
- the gate command's exit codes and flags;
- the JSON shapes under `harness/schemas/` (13 schemas);
- the instance layout;
- the store port;
- the subject manifest format.

An adopter also depends on surfaces it does not name:

| surface | where | named by decision-0003 |
|---|---|---|
| the reader's 16 MCP tools and 2 prompts | `harness/mcp_server.py` | no; only those tools' JSON that a schema pins |
| the runs server's tools | `harness/mcp_runs.py`, decision-0008 | no |
| `KG_*` settings: about 96 names across `harness/`, `demo/app/`, `instance/` and `tools/`, not all documented | `instance/README.md`, `docs/security.md` | no |
| the page's `/api/*` | `demo/app/` | no |
| the CI templates' inputs and outputs | `instance/ci/`: the action, the GitLab include, `knowgov-gate.sh`, `preload-check.sh` | no |
| the hooks' settings snippets | `instance/ci/claude/` | no |
| the image's name and tag scheme | `ghcr.io/fdurieux/knowgov:<tag>`, decision-0003 §3 | partly |
| names inside reports | `"tool": "knowgov gate"` and the like | no |

**Versioned inputs.** Reports and the trace ledger carry `schema_version`. `subject.toml`, `register_map.toml`, `code_map.toml`, `connectors.toml`, the captures and the review files carry no format version. A 1.0 that promises to read an instance's files needs one, or a stated read rule.

**Upstream.**
- An instance's `register/` is in ieam-register's format: 0.2.x, with the demo vendoring v0.2.11.
- The sequence-diagram mapper imports pumllint 0.33.0's parser.

Both are pinned or vendored, so knowgov is insulated. What is not stated is which register versions an instance's own checkout may be in.

## 4. 0.9: the contract freeze (proposed gap list)

Every item here is the maintainer's to meet.

| # | gap | today | proposed |
|--:|---|---|---|
| G9-1 | What 1.0 promises: the contracts at 1.0, a deprecation rule, a support window | nothing | decision-0016 |
| G9-2 | Format versions on the instance's inputs (§3), or a read rule | none carries one | P1 |
| G9-3 | The known contract changes landed | task-0157 (B7: every reader tool gains `subject`); task-0160 (a file Version's digest over raw bytes); task-0148 (the wizard's prompts, In Progress) | the existing tasks |
| G9-4 | A published image that runs every feature, and matches `main`'s security claims | 0.7.0's image predates the worker; the external pass (doc-0012 §9) read 0.7.0's Known limits against Unreleased's fixes as the published image lagging `main` | 0.8.0, being prepared; the compose pin's digest moves after each Release (the planned follow-up) |
| G9-5 | CI hygiene and budget | task-0159 merged (#285): timeouts, machine-readable outcomes, coverage with a declared denominator. rdflib is over budget: a median of 24.9 min over 128 PR runs, against 12 | task-0163, the rdflib split |
| G9-6 | Every Known limit closed or carried as a named 1.0 limit | 0.7.0 lists fourteen, and Unreleased closes two (containment, whole publication). Three have no task: response size is not capped; the Neo4j window between raising the lock and committing; transaction memory bounding a unit (task-0159's description) | P3 |
| G9-7 | Names, before they freeze | task-0061 is To Do. `knowgov` sits in the image name, the `KG_` prefix, `knowgov-gate.sh`, the reports' `tool` strings and the MCP server's name | task-0061; deciding "the technical name stays knowgov" is enough |
| G9-8 | The licence boundary | task-0058 is To Do; its AC #3 stamps a licence on every file under the boundary | task-0058 |
| G9-9 | Accurate adopter docs | `docs/guide.md:321-324` says task-0037 is not built and that nothing takes S2 to PROCEED; task-0037 is Done, and its AC #5 shows that path. `README.md:25` and `demo/README.md:1024` say Python 3.13; the image is `python:3.12-slim` (`demo/Dockerfile:9`). #291 (open) fixes both. The external pass (doc-0012 §9) found them too, and a third: `docs/guide.md` describes a narrower impact walk than the register's three walks (dependants, realisers, thread) | P2 |
| G9-10 | The upstream formats an instance may use | unstated | decision-0016 point 3 |
| G9-11 | The code review's high findings fixed (doc-0030, the maintainer's acceptance of 2026-11-07) | Open at `8d80b2b`: H1 a held scenario matched by bare id; H2 stage 2 reopens a closed gap; H3 a person's approval lapses by the wall clock; H4 conflicts paired within one version; H5 rulings bound to positional ids; H6 trace misses a document edit; H7 subject_check reads any manifest-named path; M3 HTTP refusals smuggle a request | task-0195 (task-0194 its interim), task-0196, task-0197, task-0198, task-0199 |
| G9-12 | The reverse-engineering process's contract changes (decision-0018, the maintainer, 2026-11-08: "include in 0.9") | Not built: the kit's `claim` field, the intended bar, lint findings as routed gaps | task-0214, task-0215, task-0216 |
| G9-13 | An attestation bound to the Versions it attests (decision-0019, the maintainer, 2026-11-08: "Build it in 0.9") | Not built; K12 below is decided for 0.9.0 by this row | task-0221 |
| G9-14 | One id per conflict on every store (decision-0020, the maintainer, 2026-11-08: "accept decision-0020's advice") | Not built: document conflicts are numbered in store order (doc-0030 S2) | task-0223 |
| G9-15 | pumllint 0.35.0 as the record's pin, so the image runs step 4's feature trace (G9-4; the maintainer, 2026-11-08: "bump pumllint to 0.35.0") | 0.33.0 pinned; trace --features first in 0.35.0 | task-0224, then task-0217 |
| G9-16 | The third-party code review's reproduced defects fixed (doc-0033; the maintainer, 2026-11-09: "all as advised") | R1 a malformed block_levels weakens the gate; R2 float comparison corroborates distinct numbers; R3 inference-basis flags by hash seed; R4 .env files enter a locally built image; a test leak and three hygiene items | task-0242 to task-0246 |

### Status at `main` `6d27961` (2026-11-09)

*Filed by the coordinating session, refreshed after the reconciliation of the v1.0 scope handover (decision-0023 A1 and decision-0028 to decision-0031, accepted by the maintainer on 2026-11-09: "all as advised"). The table above is the list as accepted; this records where each row stands. decision-0016 point 1 cuts 0.9.0 when G9-1 to G9-10 are met; G9-11 to G9-15 were added to the list since.*

| # | state | evidence |
|--:|---|---|
| G9-1 | met | decision-0016, accepted 2026-11-06 |
| G9-2 | met | task-0174 Done (#382): `[format] version` and `format = 1` (decision-0023). What a missing version means after 0.9.0 is decision-0023 Amendment A1, accepted 2026-11-09 as R1: it reads as version 1, in every release. task-0236 builds it in #397 |
| G9-3 | **open: one task** | task-0157 and task-0160 Done; task-0148 In Progress, its AC #5 waiting on the maintainer's Claude Desktop test (K10) |
| G9-4 | met for 0.8.0; met again at the cut | v0.8.0 published (tag `0c629d8`), the compose file pins its digest; 0.9.0's image is the release's own build, carrying pumllint 0.35.0 (G9-15) and naming its commit (task-0227, #375) |
| G9-5 | met, on decision-0016 point 1's text ("task-0163 merged") | task-0163 Done (rdflib and rdflib-readers in parallel). The CI budget (task-0084: 12 min uncontended) is not shown: task-0163 AC #2 stays open (contended rdflib-readers runs of 12.5, 13.9 and 16.8 min), task-0180 To Do. rdflib-readers is not yet a required check, which is the maintainer's to add. Neither is a cut condition |
| G9-6 | **met, but K10** (decision-0024, 2026-11-08) | P3 done (task-0173). The proposed 1.0 limits of §10 are named (decision-0024); K21 is a 1.0 limit by decision-0021; K22, the worker's manual restart after (A'), is tasked (task-0238) |
| G9-7 | met (decision-0025, 2026-11-08: the technical name stays knowgov) | task-0061 stays To Do for the buyer-facing name |
| G9-8 | met (decision-0026, 2026-11-08: the platform GPL-3.0-or-later; `harness/schemas/`, `instance/` and any SDK Apache-2.0) | the re-stamp and README's section (task-0058 AC #2, #3) after counsel's check |
| G9-9 | met | task-0230 (#384): every adopter-facing claim held against the code, and a docs gate; task-0234 (#388) and task-0235 (#387) its follow-ups. task-0181's statement of the contracts: AC #1 to #3 merged in #395; #4 to #6 (decision-0023 A1, decision-0028, decision-0030) in #397 |
| G9-10 | met | decision-0016 point 3 names it; decision-0028 (accepted 2026-11-09) states the versions: the ieam-register tag a release vendors and tests, `v0.2.13` at 0.9.0 (task-0240, #393), written by task-0181 AC #5 in #397 |
| G9-11 | met | H1–H7 and M3: task-0194 to task-0199 Done; the tranche F1–F8 and the singles 0205–0209 merged (task-0204 open as #376, task-0228 as #377) |
| G9-12 | met | task-0214 (#356), task-0215 (#352), task-0216 (#357); step 4's checks, task-0217 (#371) |
| G9-13 | met | task-0221 (#354, #355) |
| G9-14 | met | task-0223 (#359) |
| G9-15 | met | task-0224 (#362); `pumllint trace --features` smoke step in rdflib-readers |
| G9-16 | **open: five tasks** | task-0242 (R1), task-0244 (R3), task-0243 (R2), task-0245 (R4) and task-0246, dispatched 2026-11-09 |

**Left before the cut:**
- **work**: #397 (task-0236, task-0181 AC #4 to #6), merging on green; task-0241, C4 in `proposal_impact` and the register view (in 0.9.0 on the maintainer's word, 2026-11-09), dispatched. G9-16's five fixes (task-0242 to task-0246, doc-0033), dispatched. Merged on 2026-11-08 and 09: the re-vendor at `v0.2.13` (#393), task-0181 AC #1 to #3 (#395), and task-0237, the report's identity (#396, decision-0029);
- **the maintainer's**: G9-3's Desktop test (2026-11-09);
- **the release PR**: its Known limits. These are decision-0024's thirteen, decision-0021's K21, K10 unless the Desktop test closes it, and the tasked K16, K19, K22 and U1, with K1 at the current Landlock floor (ABI 3, task-0203).

**Not cut conditions:**
- task-0058's re-stamp. decision-0016 point 1 needs the boundary decided, and decision-0026 decided it. The re-stamp lands in a 0.9.x when counsel answers, or before the cut if counsel answers first.
- The CI budget (task-0180).
- decision-0031 (accepted 2026-11-09): the acceptance matrix becomes the lighthouse's protocol, and decision-0016 point 4 stays.

## 5. 1.0: the contracts proven (proposed gap list)

| # | gap | control | today |
|--:|---|---|---|
| G1-1 | A foreign corpus: an instance whose documents and register the maintainer did not write | third party | task-0062 AC #2 and #3 wait for the pilot organisation's go |
| G1-2 | The incumbent's export route verified on a real installation | third party | task-0063 AC #2 and #5. The register's `mapping/matrix.toml` reads 17 rows `unverified` and 0 verified (`0826ebc`) |
| G1-3 | 0.9's contracts unchanged through the pilot | both | a change means 0.10.0, and the freeze restarts (decision-0016 point 2) |
| G1-4 | A counterparty that supports a 1.0 | the maintainer, with a third party | task-0060 is To Do |
| G1-5 | An ordering, not a version condition: the outcome study pre-registered before the pilot's first governed change | maintainer | task-0057 is To Do |
| G1-6 | At the pilot, not blocking: the gate-unavailable case (task-0103) and the GitLab include on a real runner (task-0108) | third party | To Do |

## 6. Not blockers

None of these changes a contract that 1.0 would freeze:
- the parking lot: task-0008, task-0053, task-0073;
- task-0074, task-0097, task-0104, task-0123, task-0125, task-0153, task-0154, task-0162;
- task-0164, the per-subject snapshots: parked until the pilot, it needs its own decision, and it would be additive if built.

## 7. Placement

From doc-0012 §10, the placement of record (the mean of the two external passes, accepted 2026-11-06), with §8's home re-score beside it:

| state | record V · E | §8 V · E |
|---|--:|--:|
| now | 14 · 2.5 | 16 · 4 |
| contracts frozen, a declared 1.0 | 14 · 3 | 16 · 5 |
| 1.0 with its conditions met | 15.5 · 8 | 17–18 · ≈ 9 |

The version number is worth half an Execute point on the record, one on §8. The rest needs G1-1, G1-2 and G1-4, and the stack stays Visionary even with them.

## 8. Corrections to the session's first reading (2026-11-06, in chat)

- ieam-register's latest tag is v0.2.12, not v0.2.9: the tags were read unsorted.
- "Ship the worker" is in hand. Unreleased carries the worker, behind `--profile arms` (decision-0015), for 0.8.0.
- task-0159 has since merged (#285); what remains of the CI budget is task-0163.

## 9. Proposed tasks (not minted)

- **P1 (G9-2).** A format version on `subject.toml`, `register_map.toml`, `code_map.toml`, `connectors.toml`, the captures and the review files, read by `tools/check_instance.py` and the loaders. A missing version reads as the current one until 1.0. This is a contract change, so it goes in 0.9.0.
- **P2 (G9-9).** Fix the two stale claims. At 0.9.0, a pass holding every adopter-facing claim against the code; a check like pumllint's `tests/test_docs_flags.py` is the model where one fits.
- **P3 (G9-6).** The Known limits pass: each limit in 0.7.0 and Unreleased closed, tasked, or named a 1.0 limit in the 0.9.0 section. Each of the three with no task gets a task or a named limit.
- **P4 (decision-0016 point 3).** Once decision-0016 is accepted, `instance/README.md` states the contracts at 1.0 in the adopter register.

## 10. The Known limits pass (task-0173, P3)

*Drafted by the v1.0 session (session_01HTAA1TThDg3TA2qJHCemaG) at `main` `38ae719`; filed by the coordinating session under the maintainer's delegation (doc-0029).*

**Scope.** Every Known limit listed for 0.7.0 and 0.8.0, plus what Unreleased (at `main` `38ae719`) adds. Each was read against the code at `38ae719` and the backlog.

**Classes:**
- **closed**, citing the PR that closed it;
- **tasked**, citing the task that owns it;
- **to mint**: a task the pass proposed, now minted (task-0175 to task-0178);
- **proposed 1.0 limit**: offered to the maintainer to name in 1.0's Known limits. Each carries a sentence on why. None is declared without the maintainer (decision-0016 point 1).

No released `CHANGELOG.md` section is edited.

**Totals:** 2 closed, 6 tasked, 4 to mint (now task-0175 to task-0178), 13 proposed as 1.0 limits, out of 25 entries.

| # | Known limit (first listed) | Class | Evidence and why |
|--:|---|---|---|
| K-a | Code a model writes is not yet contained (0.7.0) | closed | task-0141.05, #271, decision-0012; shipped in 0.8.0, and the compose file now pins the v0.8.0 image that carries the worker (Unreleased) |
| K-b | A load is not yet published whole on Neo4j (0.7.0) | closed | task-0141.06, #278, decision-0014; shipped in 0.8.0 |
| K1 | Contained execution needs Linux with Landlock; Docker Desktop for Mac's kernel lacks it (0.8.0) | **1.0 limit** (decision-0024; task-0162 found Docker Desktop for Mac 4.48.0 without Landlock, the EC2 route attested) | task-0162 tests an engine whose VM kernel enables Landlock. If none does, this becomes a 1.0 limit; since task-0203 the floor is Landlock ABI 3 (Linux 6.2 or later), which 0.9.0's Known limits state |
| K2 | Neo4j keeps no earlier generation: a read across a publication is refused and read again, then refused after `KG_STORE_READ_ATTEMPTS` (0.8.0) | **1.0 limit** (decision-0024; proposed by the pass) | decision-0014 chose whole publication without history. Keeping earlier generations is a second read path, which is task-0164's question, parked until the pilot |
| K3 | A writer killed between raising the publication counter and committing makes reads wait up to `KG_NEO4J_READ_WAIT`, then refuse, until the next writer takes the lease (0.8.0) | to mint | no task: the window is named in task-0159's description only. `store_neo4j.py` (the pin and the lease) has no recovery for a reader. Minted as task-0175 (T-a) |
| K4 | The server's transaction memory bounds a Neo4j load (41 MiB CargoQuote, 64 MiB J-F, against 70% of a 1 GiB heap) (0.8.0) | to mint | no task: the bound is measured on the public subjects only. An instance's load size is unknown until the pilot. Minted as task-0176 (T-b) |
| K5 | Terminating a stale writer's transaction needs a role allowed `TERMINATE TRANSACTIONS` (0.8.0) | **1.0 limit** (decision-0024; proposed by the pass) | a database privilege knowgov cannot grant itself (`store_neo4j.py` runs `TERMINATE TRANSACTIONS`). Without it the epoch check still refuses the stale commit, so correctness holds and only lock release waits for the connection to end |
| K6 | One MCP process holds one parsed rdflib store, the latest publication: about 15 MB for CargoQuote S1, 82 MB for J-F C (0.8.0) | **1.0 limit** (decision-0024; proposed by the pass) | the memory price of task-0097's cache, by design. Each other-subject call adds a child (task-0157), which starts its own. A sizing fact for operators, not a defect |
| K7 | A file artefact's Version digest hashes its text, so a CRLF file's digest differs from a register citation over raw bytes (0.8.0) | tasked | task-0160, under doc-0029's plan; its AC #3 stops it if a recorded digest would move |
| K8 | A file-backed store supports its writers on POSIX with `flock`, on a local disk (0.7.0) | **1.0 limit** (decision-0024; proposed by the pass) | `store_rdflib.py` refuses a writer where `fcntl.flock` is missing. The rdflib file store is the no-database route; Neo4j is the shared, multi-host store. Windows and network filesystems are not writer platforms for it |
| K9 | Response sizes are not capped by the HTTP limits (0.7.0) | to mint | no cap in `demo/app` or `harness/mcp_server.py`. H2 (task-0141.04) bounded requests only. Minted as task-0177 (T-c) |
| K10 | Claude Desktop's role is asking the gate until the maintainer's own Desktop test shows the prompts and `subject_check` (0.7.0) | tasked | task-0148 AC #5, In Progress, waits on the maintainer's test |
| K11 | A proposal's slices are as fine as the register's links: steps supported only by one end-to-end process share one thread (0.7.0) | **1.0 limit** (decision-0024; proposed by the pass) | by design: doc-0022 K1 slices on the register's own `THREAD` walk, facts only. A finer slice is the register's to model (ieam-register), not knowgov's to infer |
| K12 | An attestation is the manifest's declaration and is not bound to a document's version (0.7.0) | **decided for 0.9.0** (decision-0019, 2026-11-08; G9-13); first proposed as a 1.0 limit | decision-0009 (a) chose attestation by the subject's declaration, built by task-0136. Binding an attestation to a version is a new decision, not a fix. If the maintainer wants it before 1.0, it needs a decision record first |
| K13 | A run folder from before `run.json` is inferred: status, start and initiator unknown (0.7.0) | **1.0 limit** (decision-0024; proposed by the pass) | historical runs only. Every run since task-0127 writes `run.json`, and `runs/` is gitignored and never the record |
| K14 | `proposal_impact`'s branch mode reads a branch's additions only (0.7.0) | **1.0 limit** (decision-0024; proposed by the pass) | `branch_overlay` reads added node files; a modified one is listed as reused ("changed") and a deleted one is not read. That matches doc-0017's question, a proposed addition. A change or a removal is `register_impact`'s and `--register-previous`'s question |
| K15 | The subject check compares keys with the documents' yield only where the mappers run (0.7.0) | **1.0 limit** (decision-0024; proposed by the pass) | knowgov extracts keys only through deterministic mappers. Route c (task-0139) measured model proposals for the prose kinds and adopted none. A kind with no mapper yields nothing to compare |
| K16 | The connector has run only on the synthetic CargoQuote export (0.7.0) | tasked | task-0063 AC #2 and #5, at the pilot |
| K17 | A register change is read only when the gate is given the previous register (0.7.0) | **1.0 limit** (decision-0024; proposed by the pass) | by design: CI passes the base ref's register (`--register-previous`, task-0122). A gate with no previous register cannot know what changed |
| K18 | The page's register panel does not show what a register change withdrew (0.7.0, the same entry as K17) | to mint | no module under `demo/app` reads a previous register. Minted as task-0178 (T-d) |
| K19 | The GitLab include is proven by shell, not on a GitLab runner (0.7.0) | tasked | task-0108, at the pilot |
| K20 | The hooks see Edit and Write, not a shell command writing the same file (0.7.0) | **1.0 limit** (decision-0024; proposed by the pass) | Claude Code's PreToolUse hook on Bash sees a command string, not the files it writes, and parsing shell is unreliable. The pre-load check, the review files and the pull request remain the backstop (task-0147) |
| K21 | An execution verification is not bound to the code the suite last passed on: its digest is the reference code's at load, so a changed reference code loads verified (Unreleased, task-0219's H7 probe) | **1.0 limit** (decision-0021, the maintainer, 2026-11-08: "Agreed") | `load.py` `load_verifications` records `sha256(SUBJECT.reference_code())` at load. Nothing records the code the oracle passed on. The probe's two mutants read PROCEED (#366). The guard is `trace check --fail-on minor`, named in the guide's step 8. task-0225 proposes the binding at m-8 with the lighthouse's instance |
| K22 | A worker whose reaper cannot confirm a job's processes gone within its bound exits with code 4, and arms runs are refused until it is restarted by hand; nothing restarts it (Unreleased, task-0233 (A')) | tasked (task-0238, parked past the lighthouse). The manual restart is what the maintainer's "(A') yes" accepted on 2026-11-08; naming it a 1.0 limit is the maintainer's | `harness/worker.py` `ReapIncomplete`; `docs/security.md` ("exits with code 4 … refuses arms until it is restarted"). Seen once in 260 hostile jobs under load before task-0233's fix. (B) to (D) and an automatic restart are task-0238, parked |
| U1 | A store-backed tool answers only for the subject whose scenario the store holds; for another subject it refuses, naming the run that would load it (Unreleased, task-0157) | tasked | task-0164, per-subject read snapshots, parked until the pilot and needing its own decision (decision-0013 A1) |
| U2 | A call naming another subject runs a child process: about 0.4 s a call on Neo4j (p95 0.51 s), bounded by `KG_SUBJECT_CALL_TIMEOUT` (Unreleased) | **1.0 limit** (decision-0024; proposed by the pass) | the isolation decision-0013 chose: one process per other-subject call, with no shared state. A latency fact, not a defect |
| U3 | A page older than task-0167, which reports no `execution`, reads as refused to `knowgov-runs` (Unreleased) | **1.0 limit** (decision-0024; proposed by the pass) | a compatibility rule between two components, fail-closed by design. It lapses once every page reports `execution` |

The 0.7.0 and 0.8.0 entries count once each: 0.8.0 repeats 0.7.0's fourteen and adds K1–K7, minus the two it closed. K17 and K18 split one 0.7.0 entry: the gate half is by design, the page half is a gap.
