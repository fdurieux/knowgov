---
id: decision-0013
title: >-
  One MCP reader for several subjects: the subject named by id under
  KG_SUBJECTS, defaulting to KG_SUBJECT, served by a child process per call
date: '2026-11-06T04:53:00Z'
status: accepted
---
## Context

doc-0021 G4: both MCP servers, the reader and `knowgov-runs`, answer for one subject per process. They take `KG_SUBJECT` at start, and the harness binds `SUBJECT` at import (F6). So *n* subjects mean *2n* client registrations, and adding one means relaunching and reconnecting. task-0151 (doc-0021 S3) measured three designs on `main` at `1b8fee5` (doc-0026, branch `spike/task-0151-multi-subject`):
- (a) a child process per call, the page's pattern;
- (b) a lazy pool, one child per subject;
- (c) the subject as a value through the harness.

The maintainer (2026-11-05) set the rule before the numbers: the subject is resolved by id under `KG_SUBJECTS`, never a path, and defaults to `KG_SUBJECT`, so today's clients see no change. Choose (a) if it measures under 1 s per call on Neo4j for CargoQuote, else (c). Build B7 only after 0.7.0, which has shipped.

What was measured on Neo4j 5.26 for CargoQuote, 20 warm calls (seconds):

| design | `gate_verdict` cold | median | p95 | register read median |
|---|---|---|---|---|
| (a) child per call | 0.43 | 0.34 | 0.44 | 0.08 |
| (b) lazy pool | 0.30 | 0.11 | 0.13 | 0.01 |
| (c) subject as value | 0.28 | 0.11 | 0.12 | 0.01 |

On rdflib, the gate is 0.55 to 0.71 s for every design. (a) is the slowest, at 0.71 s median and 0.77 s p95: each read parses the store's Turtle file, and (a) adds about 0.15 s of process start. The register read is 0.08 s on rdflib under (a).

Lines touched:
- (a): 173 in the prototype, of which 13 are in `mcp_server.py`, plus one tool-list test moved.
- (b): the same, plus a child lifecycle.
- (c): 17 of the 32 modules the reader reaches, with 235 import-time references to `SUBJECT` or `TASKS`; 22 to 29 test files move.

## Decision

Proposed; the maintainer decides.

1. Every tool of the reader and of `knowgov-runs` takes an optional `subject`, an id under `KG_SUBJECTS` resolved as the page resolves `?subject=`.
   - A path, an unknown id or one outside `KG_SUBJECTS` is refused.
   - A call that names none, or names the process's own subject, answers exactly as today, from `KG_SUBJECT`.
2. `list_subjects` names the subjects and the default.
3. A call naming another subject is answered by design (a): a child process running that one call with `KG_SUBJECT` set to the subject's root, then exiting. That is the page's pattern for runs. It measures 0.34 s median and 0.44 s p95 on Neo4j for CargoQuote, under the 1 s threshold.
4. (b) and (c) are not taken. (b) needs a pool's lifecycle for a 0.2 s gain. (c) is the larger rewrite the measurement does not require. Either can follow if a client's latency budget asks for it.
5. B7 (task-0157) builds it, and only once this decision is accepted. If S2 (task-0141.06) moves (a)'s Neo4j p95 above 0.7 s, (a) is re-measured first.

## Fit/gap

| Need | (a) child per call | Fit |
|---|---|---|
| One registration for every subject | `subject` on every tool, `list_subjects` | Fit |
| Today's clients unchanged | none named: KG_SUBJECT, the current code path | Fit |
| Under 1 s per call on Neo4j | 0.44 s p95 | Fit |
| No path from a client | id under `KG_SUBJECTS`; `../x` refused | Fit |
| Each subject's gate on its own data | the child reads the same `KG_STORE`; another subject's held scenario is refused, as today | Gap: per-subject store (the port's `instance=`) or a load, left to B7 |
| rdflib latency | 0.71 s median, 0.77 s p95 | Partial: under 1 s, but most of it is the Turtle parse, which any design pays |
| knowgov-runs | the same id; runs already go through the page's `?subject=` | Fit |

## SWOT

- **Strengths.**
  - The smallest change: 13 lines in the reader, behind the tool call.
  - Process isolation per call: one subject's state never leaks into another's.
  - The default path is untouched.
  - The pattern is the page's own.
- **Weaknesses.**
  - About 0.15 to 0.25 s of process start per call on another subject.
  - No warm cache across calls for that subject.
  - Two code paths: in-process for the own subject, a child for the others.
- **Opportunities.**
  - The same dispatch serves `knowgov-runs`.
  - (b) can be added later behind the same `subject` argument if latency matters, with no schema change.
- **Threats.**
  - S2's reads may slow the child's store open; the re-measure rule covers it.
  - A per-subject store is not yet in the port's configuration; B7 must name where each subject's store lives.
  - A client issuing many calls on a non-default subject pays the start cost each time.

## Consequences

- The tool schemas gain an optional `subject` and `list_subjects`: an additive contract change, a minor version while 0.x (decision-0003), under `## Unreleased`.
- instance/README's "one subject per process" note changes.
- `check_mcp_server.py` must hold a call routed to another subject equal to a server started on it.
- The spike branch is deleted by the owner once this is taken.

## Acceptance (2026-11-06)

Accepted by the maintainer on 2026-11-06, with amendment A1: "approve decision-0013 with amendment A1". Before approving, the maintainer asked for a SWOT and an opportunity canvas on the shared-store gap; both are below, and A1 is what they recommended.

### The gap, as checked at `main` `43ee83f`

- The store holds one scenario of one subject at a time: a load wipes it. Neo4j Community serves one database; the rdflib store is one `KG_RDFLIB_FILE`.
- The reader already refuses another subject's scenario, another scenario of its own subject, and an empty store (`mcp_server.py` `_check_scenario`); the spike showed the same refusal in a child. The gap is one of usefulness, not of correctness: a child never answers from another subject's data.
- The port's `instance=` is passed (`SUBJECT.id`) and stored by both adapters but read by neither. The remedy this record named in its fit/gap, "the port's `instance=`", is therefore not built.
- About half the tools read no store (`register_nodes`, `key_nodes`, `code_path`, `document_links`, `subject_check`, `scenario_runs`, `scenario_result`) and gain full multi-subject reach at once; the store-backed ones (`gate_verdict`, `three_valued_answer`, `evidence_bundle`, `held_keys`, `derived_outputs`, `document_statements`, `store_status`; `register_impact` and `proposal_impact` for their keys' status) answer only for the held subject and scenario.

### SWOT, on the gap

- **Strengths:** fails closed; the register and file tools are unaffected; the limit is the one users already meet within one subject (one scenario at a time); answer-equality across stores is already proven (`check_round_trip --chain`), which makes a snapshot remedy credible.
- **Weaknesses:** the store-backed tools serve only the subject loaded last; this record's remedy pointer (`instance=`) names a no-op; Neo4j, the default store, cannot separate subjects without a rewrite.
- **Opportunities:** per-subject read snapshots would also lift one-scenario-at-a-time for reads; `list_subjects` can show each subject's held scenario, so a refusal becomes a next step; the pilot can measure whether the gap matters.
- **Threats:** "one registration for every subject" read as "every answer for every subject"; load-on-demand added later to silence refusals, making the read-only reader write and readers wipe each other (S2's lease would serialise them only by refusing); a stale snapshot presented as current.

### Opportunity canvas

- **Problem:** with one registration an assistant can name any subject, but store-backed answers exist only for the held scenario.
- **Who, and when:** the demo, rarely; an organisation's CI, never (each job loads its own store); an organisation's assistant sessions across two or more subjects, sometimes (the lighthouse pilot's likely setting).
- **Today:** one registration per subject, or a load through the page or a run first.
- **Options:** O1 an actionable refusal (small, in B7; required); O2 one rdflib file per subject (moderate; rdflib only); O3 a read-only Turtle snapshot per subject and scenario after each committed run, read by the child whatever the live store (moderate; covers both stores and lifts one-scenario-at-a-time for reads; a second read path, so its own decision); O4 subject-scoped data in one Neo4j (rewrites the Cypher and changes D1; rejected, as S2 rejected it); O5 load on demand in the child (breaks "this server never loads"; rejected); O6 one Neo4j per subject (operational weight; rejected).
- **Measures:** at the pilot, store refusals for another subject per assistant session, and fallbacks to a second registration; for O3, answer-equality between a snapshot and the live store by the existing round-trip check.

### Amendment A1

1. B7 (task-0157) includes O1:
   - every tool is classed as store-backed or not, and the class is visible to a client;
   - a store-backed tool naming a subject whose scenario the store does not hold refuses, naming the held subject and scenario and the next step (which run to start);
   - `list_subjects` names, for each subject, its held scenario or none.
2. The remedy for the shared store is per-subject read snapshots (O3), not the port's `instance=`. O3 is a separate task, parked until the pilot's measure shows the need, and needs its own decision before it is built: it adds a second read path, and every answer from a snapshot must carry its generation and date.
3. Load-on-demand in a reader (O5) is rejected: the reader never writes.
4. The port's `instance=` is recorded as a no-op today; B7 neither relies on it nor removes it.
