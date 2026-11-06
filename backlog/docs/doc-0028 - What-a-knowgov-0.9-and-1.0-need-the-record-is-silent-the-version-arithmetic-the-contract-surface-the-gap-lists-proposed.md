---
id: doc-0028
title: >-
  What a knowgov 0.9 and 1.0 need: the record is silent, the version arithmetic,
  the contract surface, the gap lists (proposed)
type: specification
created_date: '2026-11-06T09:04:00Z'
updated_date: '2026-11-06T11:15:00Z'
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
