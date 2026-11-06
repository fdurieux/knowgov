---
id: decision-0013
title: >-
  One MCP reader for several subjects: the subject named by id under
  KG_SUBJECTS, defaulting to KG_SUBJECT, served by a child process per call
date: '2026-11-06T04:53:00Z'
status: proposed
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
