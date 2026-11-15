---
id: decision-0042
title: >-
  Neo4j Desktop and AuraDB Free are documented, probed targets beside the
  record's 5.26 Community container
date: '2026-11-15T09:28:00Z'
status: accepted
---
## Context

The maintainer, 2026-11-15, asked to move from the stack's Neo4j to Neo4j Desktop, AuraDB Free, or both. The coordinator answered with an opportunity canvas, a fit/gap, a SWOT, an impact note and advice (below). The maintainer then answered: "Go with the advice".

Today:
- **The container.** The stack runs `neo4j:5.26-community`, pinned by digest in `demo/docker-compose.yml`. The scored record, D1's constraint measurement (6 accepted, 3 refused as Enterprise-only) and the `stack` CI job rest on it.
- **The adapter.** `harness/store_neo4j.py` reaches any Neo4j through `KG_NEO4J_URI`, `KG_NEO4J_USER` and `KG_NEO4J_PASSWORD` (instance/README's settings table), so connecting elsewhere is configuration, not code.
- **What can break on another store.** Four adapter behaviours depend on the store:
  - the generations lease and sequence lock (decision-0014, SNAP-01..11);
  - the stale writer's `TERMINATE TRANSACTIONS`;
  - the load-memory forecast's settings read (task-0176);
  - D1's constraint attempts.

The facts about Desktop and Aura are Neo4j's published offering and are unverified here:
- Desktop runs a local DBMS, with Enterprise features under a developer licence.
- AuraDB Free is one hosted instance per account. It has node and relationship caps, pauses when idle, runs a current Neo4j version, and connects over `neo4j+s://`.

## Options and choice

- **(a) Replace the container with Desktop or Aura.** The scored record moves (D1 at least). The `stack` job cannot run Desktop, and should not depend on an external service that pauses, with a password in a public repository's CI.
- **(b) Keep the container as the record's and CI's store, and add Desktop and AuraDB Free as documented, probed targets.** Desktop comes first; Aura follows once the instance exists and the maintainer has ruled on which data may live there.
- **(c) Do nothing.** No cost, but the maintainer keeps a store that is awkward to explore. The Enterprise question D1 has left open since the proof of concept also stays open.

**Chosen: (b)**, by the maintainer on 2026-11-15: "Go with the advice".
- **Desktop:** a docs section and a runbook, then the maintainer's run on their machine. A cloud session cannot reach a local Desktop: no computer folder is connected.
- **Aura:** a later task, gated on the instance being created and on a data ruling.

## Opportunity canvas

| Box | Content |
|---|---|
| Problem | The container suits CI and reproducibility, but is awkward to explore by hand: it competes for Docker Desktop's memory on the maintainer's machine, and showing the graph to anyone else means the whole stack. |
| Users | The maintainer, exploring and demoing the graph; a prospective lighthouse, who would rather open a hosted graph than run Docker; sessions, which need a store they can reach. |
| Proposal | Keep the 5.26 container. Add Desktop (local exploration, with Enterprise features to measure) and AuraDB Free (a shared, cloud-reachable demo), each through the existing `KG_NEO4J_*` settings, documented and proven by one run of the existing checks. |
| Unique value | A graph you can open and share without the stack, and a measured answer to what an Enterprise-capable Neo4j changes in D1. |
| Cost | A docs section and a runbook. One run per target, of the existing checks: `tools/check_snapshots.py`, the deterministic run and `demo/tools/compare_deterministic.py`, and `demo/tools/check_saved_queries.py`. The Aura instance is the maintainer's to create. No change to the record. |
| Risk | A newer Neo4j version than 5.26 (Cypher and setting names); Aura's pausing, caps and privileges; data leaving the machine for a hosted service. |

## Fit/gap

| Must satisfy | Desktop | AuraDB Free |
|---|---|---|
| The adapter's connection settings | fits (`bolt://localhost:7687`, or `host.docker.internal` from the stack) | fits if the driver takes a `neo4j+s://` URI; instance/README's "a bolt URL" needs one line |
| Generations, SNAP-01..11 (decision-0014) | expected; to prove with `check_snapshots.py` | expected; to prove. Latency may want a longer `KG_NEO4J_LEASE_SECONDS` |
| `TERMINATE TRANSACTIONS` on a stale writer | fits as admin | the instance user's privilege is unverified; without it the epoch check still refuses the commit (an existing known limit) |
| The load-memory forecast (task-0176) | reads the transaction-memory setting | the settings may not be exposed; `KG_LOAD_MEMORY_CHECK=off` is the existing escape |
| D1, the record's constraint measurement | **gap:** Enterprise features may accept all 9, so D1 differs from the record. Report it apart and never compare it with the record's (task-0004 compares D1 only within a store kind) | **gap:** depends on Aura Free's tier; reported apart |
| CI runs the stack on every PR | **gap:** a GUI application, not a CI service | **gap:** an external, pausing service with a secret; not for a public repository's PRs |
| Cloud sessions can reach it | no | yes, once the instance's exact host is on the environment's allowlist |
| No bank-related data; client instances private (Boundaries) | fits: local | **gap for client data:** a third-party cloud. Public subjects (CargoQuote, J-F's public kit) are fine; a client instance is not; knowgov-bench's synthetic data is the maintainer's ruling |
| decision-0016's freeze | docs and configuration: a 0.9.x change | the same, unless a new `KG_*` setting is needed, which would be 1.1.0 (decision-0041) |

## SWOT

- **Strengths**
  - No code change to connect.
  - Desktop brings Browser, Bloom and Enterprise features to measure.
  - Aura gives a link-shareable graph without Docker, reachable by cloud sessions.
  - The record and CI stay untouched.
- **Weaknesses**
  - Neither can replace the container in CI.
  - A newer engine than the record's means results are not strictly comparable.
  - Aura Free pauses when idle, and its caps and privileges are unverified.
  - The Desktop probe needs the maintainer's machine and hands.
- **Opportunities**
  - Measure D1's Enterprise question.
  - Give a lighthouse a hosted demo before any install.
  - Desktop sidesteps the Docker memory squeeze on the maintainer's machine.
- **Threats**
  - A hosted graph drifts from the repository unless it is reloaded from the record.
  - Client data in Aura would breach the instance-privacy rule.
  - A Cypher or setting difference in a newer version could surface as a defect only off the record's store.

## Advice

(b), for four reasons:
- Replacing the container would move the scored record and break CI.
- Adding the two targets costs docs and one run of existing checks each, with no contract change.
- Desktop first: it is local, raises no data-residency question, and answers the Enterprise question for D1.
- Aura only once the instance exists and its data is ruled on.

## Consequences

- **task-0345:** Desktop as a target. A docs section in `instance/README.md`, and a runbook of the existing checks against `KG_NEO4J_URI`, proven here against a 5.26 Community tarball. The maintainer then runs it on their machine and the results are recorded, D1 apart.
- **task-0346:** AuraDB Free as a target. Gated on the instance being created by the maintainer, a data ruling, the allowlist entry and the credential through the environment. Then the same runbook, with `neo4j+s://`.
- **No change to the record.** The `demo/docker-compose.yml` image, the record and the `stack` job stay on `neo4j:5.26-community`.
