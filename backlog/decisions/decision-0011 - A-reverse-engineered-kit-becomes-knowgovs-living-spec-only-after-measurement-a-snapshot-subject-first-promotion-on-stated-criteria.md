---
id: decision-0011
title: >-
  A reverse-engineered kit becomes knowgov's living spec only after measurement:
  a snapshot subject first, promotion on stated criteria
date: '2026-11-06T00:05:00Z'
status: proposed
---
## Context

The maintainer, 2026-11-05 23:59, in the dogfooding session (`session_01HTAA1UekFrqhNeyKrfUf24`), answering its proposal to reverse-engineer knowgov the J-F way (pumllint `recreate_experiment/`, vendored here as `subjects/jef_data_load`):

1. scope: "Ultimately, I would like to use knowgov, to manage the roadmap and scope of knowgov, as an established product";
2. clean room: "Not needed; the objective is to create the artefacts that are needed to build knowgov; the more information we have, the more accurate these are likely to be";
3. home: "A subject in knowgov. (Just like J-F data load & CargoQuote";
4. "Living spec".

Answers 1 to 3 settle an experiment. Answer 4 is a different kind of decision. A kit maintained with the code is a second upstream record beside `backlog/`, so CLAUDE.md's "one record per thing" requires the division between them to be explicit. On 2026-11-06 the maintainer asked the coordinating session to explain its recommendation, then said: "record it as a proposed decision".

What holds on `main` at `772afbb`:
- **Both public kits are frozen.** `cargo_quote` and `jef_data_load` are vendored from pumllint at a tag, with a digest test per file, and the comparator holds each subject's deterministic record. Nothing in the subject format or in CI assumes a subject that moves.
- **The knowledge gate is not wired to this repository.** `.claude/hooks/protected_paths.py` guards the vendored files and the backlog. There is no knowgov subject and no gate on knowgov's own pull requests (CLAUDE.md).
- **The pace:** 53 pull requests merged to `main` on 2026-11-05. The backlog holds 174 task files and 25 docs.
- **The lane the session scoped is the gate lane:** `subject`, `kitio`, `plant`, `extract`, `load`, `store`, `store_rdflib`, `rules`, `gate`, `gate_cli`, `review`, `cadence`, `preload`, `schema_check`, `shacl`, `report`. It is 4,514 lines and carries the ten JSON Schemas under `harness/schemas/`.
- **Sufficiency is unmeasured.** Whether a kit is enough to rebuild what it describes is what the J-F method's scoring phase measures. It has not been run on knowgov.
- **Who attests:** under decision-0009, a load verifies and approves by construction only what the subject declares. Under ieam-register decision 0019, a session drafts and a person approves.

## Options

- **(a) Living spec now.** The kit is upstream from its first commit, and sessions write kit-first.
- **(b) Snapshot only.** The kit stays an experiment's record, frozen like J-F's, and `backlog/` stays the only upstream.
- **(c) Two steps.** A snapshot subject now. Promotion to living spec is decided later, against the criteria stated here.

## Decision

Proposed: **(c)**.

**Now.** Build the gate lane's kit as a knowgov subject at a named commit, by the J-F method: requirements in EARS form with `KGV-nnn` ids, contracts carrying the schemas, decision tables, PlantUML, and Gherkin tagged by id. The maintainer's answers 1 to 3 apply:
- **No clean room.** The pre-registration names the departure, and the scoring phase scores "the kit with its context", not "the kit alone".
- **The subject lives under `subjects/`,** frozen at its commit like the other two.
- **The run doubles as doc-0021 §9's spike step S6** and records its onboarding measures.
- **The kit is not upstream.** No task cites a `KGV-` id as its requirement, and `backlog/` stays the record.

**Shadow period.** After scoring, two to four weeks in which:
- a pull request that touches the lane also updates the kit;
- the gate runs on knowgov's pull requests, advisory only;
- the kit is not authoritative.

**Promotion** to living spec is a later decision record, taken only when all three of these hold:
1. **Fidelity:** the rebuild meets a fidelity bar fixed in the pre-registration before the run.
2. **Drift found:** the advisory gate found drift on real pull requests that review would otherwise have missed, counted.
3. **Cost:** the cost per pull request stays acceptable. The measure (kit lines touched, minutes added) is recorded in the shadow period, and the threshold is the maintainer's.

That later record fixes:
- **One record per thing.** The kit holds what the lane does: requirements, contracts, scenarios. `backlog/` holds why and what next: decisions, tasks, briefs. A task's acceptance criteria cite kit ids rather than restate them.
- **Same-PR rule.** A behaviour change edits the kit in the same pull request as the code, kit-first for new behaviour.
- **Attestation** per decision-0009 and ieam-register 0019: a session drafts and the maintainer approves. A statement the suite verifies on the code reaches `verified` without attestation. That shows the kit and the code agree, not that the behaviour is right, so new behaviour still needs the maintainer's approval.
- **Blocking gate.** The gate on knowgov's pull requests moves from advisory to blocking for the lane.
- **Scope.** The gate lane only, widened lane by lane by later records.

## Why not (a)

- **Nothing enforces it.** Without the gate on knowgov's pull requests, a living kit drifts. At 53 merges a day, it drifts within days.
- **Its sufficiency is unmeasured until scoring.** Making it upstream before then commits every session to a source whose completeness is unknown.
- **It is costly to reverse.** Once acceptance criteria cite `KGV-` ids and sessions write kit-first, undoing it means rewriting the backlog's references.
- **The record machinery assumes a frozen subject.** A live subject needs a gate per pull request, not a deterministic record. That CI shape is not designed yet.

## Why not (b)

It drops the maintainer's goal (answer 1): knowgov managing its own roadmap. (c) keeps that goal and earns it.

## Opportunity canvas

| Box | Content |
|---|---|
| Problem | knowgov's behaviour is recorded only in its code, its tests and the backlog's acceptance criteria. Nothing states what the gate lane does as checkable requirements, and nothing gates knowgov's own changes. |
| Solution | The J-F method on the gate lane as a snapshot subject, then a measured promotion. |
| Measure | Rebuild fidelity at scoring; drift found by the advisory gate; cost per pull request; S6's onboarding measures. |
| Cost | A run of J-F's kind, on a lane about 1.3 times J-F's size; the shadow period's cost per pull request. |
| Risk | Circular verification: a spec derived from the code is verified on that code. A session-drafted kit attested by nobody. CI load on the critical path. |

## Fit/gap

| Need | Today | Gap |
|---|---|---|
| Kit format and mappers | J-F's five bundle mappers read J-F's conventions | None, if the kit is written in them |
| Subject format | `subjects/<id>/`, vendored, frozen | A subject authored in place is new |
| Gate on knowgov's pull requests | Not wired | The shadow period needs it, advisory |
| Attestation | decision-0009, ieam-register 0019 | Applies as is |
| One record per thing | `backlog/` only | The division above, at promotion |

## SWOT

- **S.** The strongest proof of the product: knowgov governs its own changes, and acceptance criteria become testable requirements.
- **W.** Circular verification. The cost per pull request. A second record to keep.
- **O.** doc-0021's spike step S6 on a real corpus. doc-0004's hypothesis ("until a subject is built from a repository's own `CLAUDE.md`") tested. doc-0022 K3's backlog coverage gets a first user.
- **T.** Drift if unenforced. Churn on the critical path (task-0141, then 0.7.0). A kit read as authority before it is one.

## Consequences

- No change to `backlog/`, the subject format or CI until the maintainer approves.
- **If approved:** the dogfooding session's experiment proceeds as (c)'s first step. Its pull requests that touch `subjects/`, `harness/`, `tools/` or `demo/` wait until task-0141's S1, .07, H1 and H2 have merged. Its tasks are minted by the coordinating session, and doc-0026 is reserved for its study.
- The promotion criteria are fixed here, so the later record cannot set them after seeing the numbers.
