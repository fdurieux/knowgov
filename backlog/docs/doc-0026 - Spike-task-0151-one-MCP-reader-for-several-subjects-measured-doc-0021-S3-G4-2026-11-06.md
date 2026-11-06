---
id: doc-0026
title: >-
  Spike task-0151: one MCP reader for several subjects, measured (doc-0021 S3,
  G4), 2026-11-06
type: specification
created_date: '2026-11-06T04:53:00Z'
updated_date: '2026-11-06T04:53:00Z'
tags:
  - spike
  - mcp
  - subject
  - measurement
---
*2026-11-06. Maintainer register. task-0151's note (doc-0021 S3, G4): three designs for one MCP reader answering for several subjects, measured. Read on `main` at `1b8fee5`, as it stands; S2 (task-0141.06, generation-pinned reads) is in build elsewhere and will change the store's reads. The prototypes and the benchmark are on branch `spike/task-0151-multi-subject` (`410f71b`), never merged and given no pull request; the owner deletes it once decision-0013 is taken. Synthetic content only; no model calls.*

## Verdict

- **(a) a child process per call is under 1 s per call on Neo4j for CargoQuote:** `gate_verdict` 0.34 s median, 0.44 s p95, 0.43 s cold; a register read 0.08 s. By task-0151 AC #2's rule, (a). decision-0013 proposes it; the maintainer decides.
- **No re-measure after S2 is owed.** (a)'s Neo4j number is 0.44 s at p95, well outside 30% of the 1 s threshold (above 0.7 s).
- **(b) and (c) are faster warm, about 0.11 s on Neo4j, and cost more.** (b) keeps one child per subject alive (memory, a store handle each, a lifecycle to manage). (c) rewrites 17 of the 32 harness modules the reader reaches, which bind the subject at import.
- **rdflib is slower for every design** (0.55 to 0.71 s on `gate_verdict`): each read handle parses the 523 kB Turtle file. (a) adds about 0.15 s of process start and imports to that.

## Method

- **Subject and store.** CargoQuote, S1 loaded once per store by `gate_cli.py --scenario S1 --as-of record`; the verdict is PROCEED on both.
  - rdflib 7.6.0 on `KG_RDFLIB_FILE`.
  - Neo4j 5.26.0 community, the tarball started directly on Java 21, driver 6.4.1.
  - One container, no other load, CPython 3.13.
- **Calls.** `gate_verdict` as of the record, and `register_nodes` for CAP-0002, a register read that opens no store. Per design and call: one cold call, then 20 warm calls; the wall time of each.
- **(a) a child process per call:** `harness/mcp_child.py TOOL ARGS` with `KG_SUBJECT` set; every call is a cold process by design.
- **(b) a lazy pool:** one stdio `mcp_server.py` per subject, started on its first call and kept. Cold is spawn + initialize + first call; warm is one JSON-RPC round trip.
- **(c) the subject as a value:** today's in-process cost, which (c) keeps. Cold is a fresh interpreter's import + server + first call, timed inside it.
- **Equality.** The three designs' answers were checked equal before any number was kept.

## Numbers (seconds)

| store | design | call | cold | warm median | warm p95 |
|---|---|---|---|---|---|
| rdflib | a_child_per_call | gate_verdict | 0.705 | 0.711 | 0.774 |
| rdflib | a_child_per_call | register_nodes | 0.075 | 0.076 | 0.081 |
| rdflib | b_pool_per_subject | gate_verdict | 0.688 | 0.561 | 0.635 |
| rdflib | b_pool_per_subject | register_nodes | 0.011 | 0.010 | 0.010 |
| rdflib | c_subject_as_value | gate_verdict | 0.633 | 0.551 | 0.619 |
| rdflib | c_subject_as_value | register_nodes | 0.058 | 0.010 | 0.011 |
| neo4j | a_child_per_call | gate_verdict | 0.433 | 0.344 | 0.439 |
| neo4j | a_child_per_call | register_nodes | 0.076 | 0.077 | 0.083 |
| neo4j | b_pool_per_subject | gate_verdict | 0.297 | 0.113 | 0.130 |
| neo4j | b_pool_per_subject | register_nodes | 0.011 | 0.010 | 0.011 |
| neo4j | c_subject_as_value | gate_verdict | 0.275 | 0.106 | 0.118 |
| neo4j | c_subject_as_value | register_nodes | 0.052 | 0.010 | 0.010 |

## Lines touched and tests moved

| design | lines | tests moved |
|---|---|---|
| (a) child per call | 173 in the prototype: `subject_dispatch.py` 138 (id resolution, the child call, `with_subject`, `list_subjects`; shared with (b)), `mcp_child.py` 22, `mcp_server.py` 13 behind a switch | 1 of 565: `test_every_tool_listed_and_marked_read_only`, the tool-list pin; 0 with the switch off |
| (b) lazy pool | the same 173, the pool class included | the same 1 |
| (c) subject as a value | not prototyped. 17 of the 32 harness modules the reader reaches bind `SUBJECT` or `TASKS` at import: 235 references, plus 9 tools. The page took the same step in task-0032.01 | every reader test that relies on the import-time subject: 22 test files import `mcp_server`, 29 name `SUBJECT` or `KG_SUBJECT` |

The prototype, run on the spike branch with `KG_SUBJECT_DISPATCH=child` and with `pool`:
- A named `minimal` is routed to a child, which refuses CargoQuote's S1 as another subject's scenario. That is correct: the store is shared, and its scenario is CargoQuote's.
- A named `cargo_quote` stays in-process.
- `../x` is refused as not an id.

## What B7 must still settle

- **The store is per subject.** A child for subject X reads the same `KG_STORE` and refuses a scenario of another subject, as today's server does. Serving two subjects' gates at once needs each subject's own store, the `instance=` the port already takes, or a load.
- **knowgov-runs** takes the same id. Its runs already go through the page, which resolves `?subject=`.
- **The tool-list pin** gains `subject` and `list_subjects`, an additive schema change.

## Fit/gap and SWOT

See decision-0013.
