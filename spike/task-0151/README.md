# Spike task-0151: one reader for several subjects (doc-0021 S3, G4)

**Never merged; no pull request.** The owner deletes branch `spike/task-0151-multi-subject` once the
decision it informs is taken. The record is the backlog doc and the proposed decision on `main`;
this branch only lets the numbers be reproduced.

Measured 2026-11-06 on `main` at 1b8fee5, as it stands: S2 (task-0141.06, generation-pinned reads,
in build) will change the store's reads. Design (a) is to be re-measured after S2 only if its
Neo4j number comes within 30% of the 1 s threshold (above 0.7 s); it measures 0.34 s median,
0.44 s p95, so it does not.

## What is here

- `harness/subject_dispatch.py`: the subject named by id and resolved under `KG_SUBJECTS` (never a
  path; `../x` refused), the process's own `KG_SUBJECT` when none is named; (a) `via_child`, (b)
  `Pool`; `with_subject` adds an optional `subject` to every tool's schema and `list_subjects`.
- `harness/mcp_child.py`: (a)'s child, one `tools/call` for the subject `KG_SUBJECT` names.
- `harness/mcp_server.py`: 13 lines, all behind `KG_SUBJECT_DISPATCH=child|pool`; unset, nothing changes.
- `spike/task-0151/bench.py` and `results/`: the numbers below.

## Method

- CargoQuote, S1 loaded once per store by `gate_cli.py --scenario S1 --as-of record` (PROCEED on both).
- rdflib 7.6.0 with `KG_RDFLIB_FILE` (523 kB of Turtle); Neo4j 5.26.0 community, the tarball started
  directly on Java 21, driver 6.4.1, on the same machine. CPython 3.13, one container, no other load.
- Two calls: `gate_verdict` as of the record, and `register_nodes` for CAP-0002 (a register read,
  no store). Per design and call: one cold call, then 20 warm calls; wall time each.
- (a) a child process per call: every call is cold by design (spawn, import, open the store).
- (b) a lazy pool: cold is spawn + initialize + the first call (on `gate_verdict`); warm is one
  JSON-RPC round trip to the kept child.
- (c) the subject as a value: today's in-process cost, which (c) keeps; cold is a fresh
  interpreter's import + server + first call, timed inside it.
- The three designs' answers are checked equal before any number is kept.

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

| design | lines (prototype) | tests moved |
|---|---|---|
| (a) child per call | 173: `subject_dispatch.py` 138 (shared with (b)), `mcp_child.py` 22, `mcp_server.py` 13 | 1 of 565 (`test_every_tool_listed_and_marked_read_only`, the tool list pin); 0 with dispatch off |
| (b) lazy pool | the same 173, the pool class included | the same 1 |
| (c) subject as a value | not prototyped: 17 of the 32 harness modules the reader reaches bind `SUBJECT` or `TASKS` at import, 235 references, plus 9 tools | every reader test that relies on the import-time subject: 22 test files import `mcp_server`, 29 name `SUBJECT` or `KG_SUBJECT` |

Reproduce: load S1 as above, then
`KG_STORE=rdflib KG_RDFLIB_FILE=store.ttl KG_TODAY=2026-11-06 python spike/task-0151/bench.py --out rdflib.json`
and, with Neo4j up, `KG_TODAY=2026-11-06 python spike/task-0151/bench.py --out neo4j.json`.
