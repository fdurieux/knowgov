---
id: doc-0010
title: 'Digital twin: where knowgov sits, read against pumllint''s twin bridge'
type: specification
created_date: '2026-11-03T17:18:00Z'
updated_date: '2026-11-03T17:19:00Z'
tags:
  - brief
  - digital-twin
  - fit-gap
---
*2026-11-03. Maintainer register. A study: nothing built, nothing queued. Trigger: the maintainer's question of this date, how knowgov fits the concept of a "digital twin". Read on `main` at `d7ebd10`, register v0.2.3. The record this reads against is pumllint `docs/ea-ontology-stack-evaluation.md` §12 (2026-09-14) and its ROADMAP entry of the same date. The bridge lives there; this doc places knowgov on it and adds nothing to it. One record per thing.*

## Verdict

**knowgov is the governed knowledge layer over the *declarative* twin. It is not a twin of the running estate.** Do not rebrand it as a digital twin. To most readers the term means live, two-way synchronisation and simulation, and knowgov does neither by design. Use the term only to translate for adopters, in the qualified form under "Wording" below.

## 1. The bridge on record (pumllint §12)

The EA deck's platform slide feeds the DATA layer of a knowledge pyramid with three inputs. §12.1 maps them to the two loops of the 2026-09-06 process-architecture brief:

| The pyramid's feed | The brief's name | What produces it |
|---|---|---|
| "Declarative" Digital Twin | Loop A, commit-time | ARIS EPC → aris2puml → pumllint |
| "Running" Digital Twin | Loop B, run-time | Process mining / conformance to an event log. Neither repository's; its trigger has never fired. |
| Operational Data | — | Telemetry |

Loop C, the ontology validation, is the *ascent* (Cognition, Judgment), not a fourth feed. §12.3: each step up the pyramid drops the qualifications on the data, so a defect fed in at the red end arrives at the green end "wearing green". §12.4: the chain carries its uncertainty upward in machine-readable form; "telemetry does not know what it failed to observe". When §12 was written, knowgov was still `kg_experiment/` inside pumllint. Neither repository used the term then, and knowgov does not use it now.

## 2. knowgov against the properties of a twin

| Twin property | knowgov | Reading |
|---|---|---|
| A model of a real counterpart | The register: CAP, PRD, JRN, PROC, APP, ENT, ORG and ten relationship types. The counterpart is the organisation's *declared* design. | Yes, declarative |
| Synchronisation | One-way and periodic. Exports are append-only, at `exports/<system>/<date>/` with `MANIFEST.toml` and `RECONCILE.json`. A vanished external id becomes a `stale` finding, never a deletion. No write-back: the store holds status, provenance and links, never content (doc-0001 §0). | Partial: per export, by design |
| State | The *epistemic* state of each statement: its source, how it was obtained, its verification level and `valid_until`. Also the staleness chain from a changed fragment to the code built on it (S6), and the three-valued answer: asserted, documented absent, unknown. | The distinctive part, §3 |
| What-if | The impact walk (`demo/register/tools/impact.py`, saved query `register-impact`), and the Legible systemic model, which places a defect where it entered and draws the path it travelled. | Yes, but narrow, §4 |
| Acting on the result | The gate (`harness/gate.py`): PROCEED, QUALIFIED, BLOCKED. As a command (`harness/gate_cli.py`) it exits 0/1/2 and stops an assistant or a build pipeline. | Yes. It acts on delivery, not on operations |

## 3. The distinctive part: a twin that records what it does not know

§12.3 names the failure and §12.4 names the remedy at the input. knowgov is that remedy carried up the pyramid. Each statement keeps its provenance and status as it rises. The three-valued answer keeps "unknown" separate from "absent". The gate refuses to let an assistant build on required keys that are below verified or flagged; a change that invalidates a fragment (S6) takes its keys down with it until they are verified again. A telemetry-fed running twin has no equivalent by construction. This is the sentence to give an adopter who arrives with the pyramid: knowgov keeps the qualification that the ascent would otherwise drop.

## 4. Gaps against the full claim

1. **No running twin.** There is no observed-state feed: no event logs, no CMDB, no telemetry. pumllint `docs/ea-stack-in-the-sdlc.md` sizes the gap analysis between declared and running as "the most expensive thing on the slides… size this one separately and late". The register ids `CAP-` and `PROC-` would be the join keys if Loop B ever fires, but nothing builds that join, and nothing here should until it does.
2. **The what-if walk is partial** (doc-0008, finding 1). `FORWARD` starts only from applications, processes and journeys. It follows `supports`, `delivers`, `realizes`, `is_supported_by` (inverse) and `concerns`, never `crud`, `manages`, `requires`, `owns` or `maps_to`. From a capability or an information entity it walks zero edges. Whether the walk grows is the register's decision.
3. **Traceability runs one way**, from document to statement to code. A change *to code* reaches nothing (doc-0008, finding 2).
4. **The cadence is per export.** That is right for a twin of the design, and wrong for a reader who hears "twin" and expects live data.

## 5. Wording

When an adopter's material uses the pyramid's vocabulary, the qualified form is:

> knowgov governs the *declarative* twin: what was decided, by whom, how well it is known, and what a change reaches. The *running* twin (Loop B: process mining, event logs, telemetry) is out of scope.

Nothing else changes. No glossary term is added to `demo/GLOSSARY.md`, because the page does not use the word. No milestone moves, and no task is opened.

## 6. What would reopen this

- Loop B's trigger fires: an adopter with an event log asks for conformance against the declared process. That is a running-twin feed, a decision in pumllint's ROADMAP first, then a join here on register ids.
- An adopter asks for impact from a capability or an entity, which is gap 2. That decision belongs to ieam-register, not this backlog.
