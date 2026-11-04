---
id: decision-0006
title: The lighthouse incumbent is ARIS
date: '2026-11-04T15:27:00Z'
status: accepted
---
## Context

task-0062 AC #1. doc-0012 §6: both external reviewers put one lighthouse ahead of four connectors and
ahead of standards work; the stack scores Execute 3 because nothing it does has met a real
installation (0 of 3 export routes verified, no client instance). doc-0012 lists three incumbents:
SAP LeanIX + Signavio, Ardoq, and ARIS. The choice decides which connector (task-0063), which
register mapping row and which buyer the next months serve.

Compared on what exists today:

| | ARIS | SAP LeanIX + Signavio | Ardoq |
|---|---|---|---|
| Already built | aris2puml (ARIS export to PlantUML, its footer carrying `CAP-` and `PROC-` ids), the register's ARIS rows in `mapping/matrix.toml` | nothing | nothing |
| Connector (task-0063) | smallest: an export route aris2puml already reads | an API and a process export, both new | an API, new |
| A real installation within reach | most likely, for the maintainer | only through a client | only through a client |
| Market | strong in regulated enterprises | the widest | mid-market EA teams |

## Decision

The lighthouse incumbent is **ARIS** (maintainer, 2026-11-04, on the coordinator's comparison).
It is the only option where most of the route already exists, so it reaches a first real
installation soonest, which is the gap doc-0012 scores. SAP LeanIX + Signavio stays the candidate
for a second connector once the method is proven on ARIS; Ardoq is not pursued now.

The pilot organisation is not committed yet. Per task-0062 AC #2 it is named only in the private
record; this repository records that one exists, its sector and the date of its go once it gives
it, and nothing before.

## Consequences

- task-0063 (the connector) targets ARIS: a dated export into the instance layout with
  `MANIFEST.toml` and `RECONCILE.json`, append-only, a vanished external id reported stale. Its
  AC #1, #3 and #4 can run on the public example instance now; AC #2 and #5 (the pilot's
  installation, the register's mapping row moved off `unverified`) wait for the pilot.
- task-0062 stays In Progress: AC #1 met by this record; AC #2 (the organisation) and AC #3 (one
  product, one journey) wait for the pilot's go.
- task-0057 (the outcome study's pre-registration) waits for the pilot slice.
- No bank-related data and no client name enter this repository; a client instance stays in the
  client's repositories.


