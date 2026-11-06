---
id: decision-0014
title: >-
  Store generations: a writer's whole unit is one Neo4j transaction under a
  lease in the database, published under a sequence lock every read checks;
  rdflib keeps S1's lock and atomic replace
date: '2026-11-06T05:40:00Z'
status: accepted
---
## Context

task-0141.06 (S2), from the 2026-11-05 code and architecture review. The page, the CLI or the MCP server could observe a half-done publication: a load, a later version, a re-verification, a capture, a register projection or change, an import, or a trace update. Its AC #1 asks for the publication design to be recorded before the migration; AC #2 asks for SNAP-01..07 against a real Neo4j and a file-backed rdflib store.

What S1 (task-0141.02) left in place:
- **rdflib**: a writer takes `flock` on `<file>.lock` before it loads, and publishes by an atomic replace; a reader loads the file once. A reader therefore already answers from one generation for its whole life.
- **Neo4j**: every port statement autocommits as it runs. A reader can see a half-loaded graph, and `abort()` cannot undo anything.

Every Neo4j statement already goes through `Neo4jStore.run`, and every writer through one handle (`open_store(access="write")`). Constraints are `IF NOT EXISTS`. The deterministic record compares D1 (the edition's constraint measurement) and D2 (the census) on Neo4j runs.

## Options

1. **Generation-scoped data and a published pointer.** Every node and relationship carries a generation, and every query filters on it.
   - This rewrites the adapter's ~900 lines of Cypher and the saved queries.
   - It turns single-property uniqueness into composite keys, which changes D1 against the record.
   - It leaves old generations to retire.
2. **The unit in one transaction, a lease in the database, and a sequence lock that reads check (revision-and-retry).**
   - A writer opens one explicit transaction for its unit and owns the store from open to close by a lease with a fencing epoch.
   - It raises a counter in its own transaction before the unit commits, and matches it inside the unit's transaction.
   - A read handle pins the counter at open and checks it after every read call. A mismatch refuses the read, and the caller reads again.
   - Schema statements run before the unit's transaction, measured once per handle.
3. **Build the unit in an in-memory rdflib store and replace Neo4j's contents in one transaction at commit.** The Neo4j edition's runs would then execute on rdflib, which voids what the record measures on Neo4j.
4. **A staging database.** Not available: Community serves one database.

## Decision

Accepted by the coordinating session under the maintainer's overnight delegation (2026-11-05: 'In case of doubt, create an opportunity canvas, fit/gap, swot, to inform your decision, record the canvas, fit/gap, swot and proceed with the decision'); the maintainer may supersede it.


Option 2 on Neo4j; S1's design, plus a lock-file fence, on rdflib.

**Neo4j:**
- The publication node `_KgPublication {id:'publication'}` holds `begin`, `end`, `owner`, `epoch` and `expires`, under its own uniqueness constraint. It is outside every evidence label: the wipe, the export and the census leave it out.
- The lease lasts `KG_NEO4J_LEASE_SECONDS` (60) and a heartbeat renews it. A second writer waits `KG_NEO4J_LOCK_TIMEOUT` (60), then gets `StoreBusy`.
- A writer that takes over an expired lease does three things:
  - raises the epoch;
  - closes any open gap (`end = begin`);
  - terminates the former owner's unit transaction, found by its transaction metadata.

  The former writer's commit is then refused (`StoreFenced`).
- A commit runs in this order:
  1. lock the node and check the epoch;
  2. raise `begin` in its own transaction;
  3. in the unit's transaction, lock the node, check the epoch, set `end = begin`;
  4. commit.

  A failure after step 2 closes the gap itself. A writer killed between step 2 and step 4 leaves readers waiting `KG_NEO4J_READ_WAIT` (10), then refusing, until the next writer takes the lease.
- A read handle pins `(begin, end)` with `begin == end`, and checks it after every port read. A publication during a read raises `StoreChanged`.
  - `store.read(fn)`, the page's three compound reads and the MCP server's `_with_store` run the read again, up to `KG_STORE_READ_ATTEMPTS` (3).
  - No earlier generation is retained. A reader open across a publication is refused, never answered from a retired generation.

**rdflib:** S1's lock and atomic replace. A writer publishes only while the lock file at the path is still the one it locked (`StoreFenced` otherwise).

**Coordination:**
- Every writer, whether the page's run, the projection, the CLI or a tool, takes the same lease or lock.
- The page decides a projection under the lock that starts a run.

## Consequences

- **The record is unchanged.** On Neo4j: the comparator finds 0 differing leaves (D1 and D2 included), and every scenario of both subjects passes the full `neo4j,rdflib,neo4j` round trip, J-F's 47 part digests included.
- **SNAP-01..07** pass on the real Neo4j 5.26 and on a file-backed rdflib store (`tools/check_snapshots.py`, run by both workflows).
- **A long run holds one transaction** and the lease for its whole length. The page shows the previous generation until the run commits; it no longer shows a load in progress.
- **Writers serialise.** A projection during a run answers 409 instead of interleaving.
- **Limits:**
  - Neo4j's read-committed isolation is why the sequence lock exists; a single transaction alone would not give a stable multi-query read.
  - `TERMINATE TRANSACTIONS` needs a role allowed to run it. Without it, the epoch check still fences the commit, but the former owner's open transaction holds its locks until its connection ends.

## Fit/gap against task-0141.06's acceptance criteria

| AC | Fit | Gap |
|---|---|---|
| #1 the publication design recorded and accepted before the migration | This record. Only the adapters, the port's three additions and the readers' retry change; the loader, the rules and the gate are untouched. | None. |
| #2 SNAP-01..07 against a real Neo4j and a file-backed rdflib store | `tools/check_snapshots.py --disposable`: every check holds locally on Neo4j 5.26 Community and file-backed rdflib. CI runs it in `harness.yml` (rdflib) and `demo.yml`'s stack job (Neo4j). | On Neo4j, SNAP-06's "active reads remain valid" holds as "refused and retried", never as "answered from a retired generation". |
| #3 the full round trips pass, S6 stage 2, part digests and preload included; Turtle and the external evidence schema unchanged | `neo4j,rdflib,neo4j` on every CargoQuote scenario and every J-F scenario with `--expect-parts` (47 digests); the stack job's preload round trips. The publication node is never exported. | None. |

## Opportunity canvas

- **Problem:** readers could see a half-built Neo4j graph, and a failed writer left partial evidence.
- **Who:** the page, the MCP server, `gate_cli --no-load`, and an organisation's CI gate reading a shared store.
- **Solution:** one transaction per unit, a lease with a fencing epoch, and a sequence lock checked after every read, retried by the readers.
- **Measures:** SNAP-01..07, the comparator on D1 and D2, the round trips.
- **Cost:** the Neo4j adapter's lifecycle (one class); the port gains two errors and `read()`; the three readers retry; one check tool.
- **Risk:**
  - a long unit holds one transaction;
  - transaction memory bounds a unit;
  - a writer killed mid-publication blocks reads until the next writer.

## SWOT

- **Strengths:**
  - keeps every Cypher statement and D1;
  - one mechanism for every writer;
  - the fence acts on the server as well as at commit.
- **Weaknesses:**
  - no earlier generation is retained, so a reader across a publication is refused;
  - transaction memory bounds a unit.
- **Opportunities:**
  - a shared store for several instances or subjects can use the same lease;
  - the generation counter can name what a report read.
- **Threats:**
  - a role without `TERMINATE TRANSACTIONS` leaves a stale owner's locks until its connection ends;
  - a much larger instance needs a larger heap.

## Gaps stated and measured (the coordinator's review, 2026-11-06)

- **Transaction memory.** One transaction per unit means Neo4j's transaction memory bounds a load.
  - The bounds: `db.memory.transaction.max` (unset) and `db.memory.transaction.total.max` (70% of the heap; the compose heap is 1 GiB).
  - Measured peak of the unit's estimated heap (`SHOW TRANSACTIONS`, sampled every 0.1 s): CargoQuote's whole seven-scenario deterministic run about 41 MiB; J-F's whole run about 64 MiB.
  - A unit over the limit fails with `MemoryPoolOutOfMemoryError`. The previous generation is read whole and the sequence lock is closed. Shown with `db.memory.transaction.max=2m` (`check_snapshots --memory-limited`). That proof is local only: Community sets the limit only at server start, so CI does not run it.
- **Exhausted retries are refusals.**
  - `gate_cli --no-load` exits 2 ("cannot run").
  - The MCP server answers an error result.
  - The page's `/api/store` and `/api/gaps` answer 503 with `Retry-After: 1` and `busy: true`; `/api/scenarios` keeps 200 and carries `busy`.
  - These are contract changes in CHANGELOG.
- **Settings.** Each is bounded, and refused with its name outside its bounds:
  - `KG_STORE_READ_ATTEMPTS`: 1 to 10 (default 3);
  - `KG_NEO4J_LEASE_SECONDS`: 1 to 3600 (default 60; the heartbeat runs every third of it);
  - `KG_NEO4J_LOCK_TIMEOUT`: 0 to 86400 (default 60);
  - `KG_NEO4J_READ_WAIT`: 0 to 600 (default 10).
- **The server-side fence.** `TERMINATE TRANSACTIONS` ran on Community 5.26: right after a takeover, the former owner's unit transaction reads `Terminated` in `SHOW TRANSACTIONS`, and its commit raises `StoreFenced`. SNAP-05 checks both.
