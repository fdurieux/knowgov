---
id: doc-0039
title: 'Tenant separation in one Neo4j Community database: spike (measurement only)'
type: other
created_date: '2026-11-15T15:35:00Z'
updated_date: '2026-11-15T15:35:00Z'
---
# Tenant separation in one Neo4j Community database: spike (measurement only)

**Status:** filed 2026-11-15 by a sub-session of the coordinator, on the maintainer's "go with the spike" (option 4: several teams, subjects or scenarios sharing one Neo4j Community deployment). Measurement only: no contract moves, no code is merged. The prototype lived on a local branch (`spike/tenancy-proto`, based on `main` `a626c0e`), never pushed; its shape and key excerpts are below. The probe scripts lived in the session's scratchpad and are not committed. knowgov is in its 0.9.x fix-only soak (decision-0016 A1).

**The question.** Can tenant separation be built as an additive 1.x change, the default single-tenant path identical (the scored record, D1 and the comparator unchanged), or does it need 2.0.0?

**The answer, in three lines.**
1. **Additive 1.x.** With no tenant, the path is identical: comparator 0 differing leaves on both adapters, D1 equal to the record, SNAP-01..11 and `--chain` hold. Not one of the port's 92 operation signatures changes; tenancy is opt-in at `open_store(tenant=)`.
2. **Not now, and not as a first resort.** In the soak any contract change is 0.10.0 and restarts the freeze. On Community, tenancy separates data by query, never access: there are no roles, and any credential reads and writes every tenant.
3. **Cheaper alternative.** One Community container per tenant gives separation of both data and access with no code (1.4 GiB RSS each at the compose heap). Build in-database tenancy as a 1.x minor only if a lighthouse refuses that cost.

## 1. Set-up

- Neo4j **5.26.18 Community**, the tarball (`neo4j-community-5.26.18-unix.tar.gz`) started directly with `bin/neo4j start` on OpenJDK 21.0.12.1. Heap 512m initial and 1g max, page cache 512m (the compose file's), password `kgpoc2026`. With these settings `SHOW SETTINGS` reads `db.memory.transaction.max` = 0B, `db.memory.transaction.total.max` = 0B and `dbms.memory.transaction.total.max` = 716.80MiB.
- CPython 3.12.3 venv with `demo/Dockerfile`'s pins (pumllint 0.35.0, neo4j 6.4.1, rdflib 7.6.0, pyshacl 0.40.2, openai 3.41.0, pyyaml 6.0.3, and the J-F oracle's pins), `KG_CLOCK=pinned`. No model call: the arms are off.
- "Identical" means the comparator's leaves. `main` itself is not byte-stable on Neo4j from run to run: two runs of unchanged `a626c0e` differ in all seven `deterministic.json` files, in list order (store order), which the comparator compares as sets. On rdflib, the prototype's seven files are byte-identical to `main`'s.

## 2. Measurement 1: composite uniqueness on Community 5.26

| Statement | Result |
|---|---|
| `CREATE CONSTRAINT … FOR (n:<L>) REQUIRE (n.tenant, n.id) IS UNIQUE`, for each of Assertion, Fragment, Entity, Version, Artefact and Gap | **accepted**, all six |
| the same id in two tenants | accepted |
| the same `(tenant, id)` twice | refused: `Neo.ClientError.Schema.ConstraintValidationFailed`, "Node(0) already exists with label `Assertion` and properties `tenant` = 'a', `id` = 'spk:1'" |
| two nodes with the same id and **no** tenant | **accepted**: a composite constraint skips a node that lacks a member |
| `REQUIRE (n.tenant, n.id) IS NODE KEY` | refused: "Node Key constraint requires Neo4j Enterprise Edition." |
| `REQUIRE n.tenant IS NOT NULL` | refused: "Property existence constraint requires Neo4j Enterprise Edition." |
| `REQUIRE n.tenant IS :: STRING` | refused: "Property type constraint requires Neo4j Enterprise Edition." |
| `CREATE INDEX … ON (n.tenant, n.key)` (a composite range index) | accepted |

Consequences:
- **Uniqueness per tenant needs no code**: the composite constraint enforces it.
- **The tenant's presence cannot be enforced by the database.** The code must guarantee it: every CREATE and MERGE carries it, and a guard refuses a mixed database. No extra read per create is needed. `_refuse_taken`'s pattern (one read per create, used today for Activity and Derived) would be needed only for a label with no constraint.
- **D1's six single-property constraints (`n.id IS UNIQUE`) are database-wide**, so a second tenant's equal ids break them: a tenanted database must drop them. D1 therefore changes for a tenanted run (§4), never for an untenanted one.

## 3. Measurement 2: the prototype's shape

Four files, +130 −32. The tenant is bound once, at open: `open_store(kind, access=, tenant=None)`, falling back to `KG_TENANT`, so the existing tools ran per tenant unmodified. No port operation's signature changes. `None` is today's code path, apart from one read at open (§4).

- **Neo4j** (`harness/store_neo4j.py`, +102 net):
  - **The rewriter.** A tenanted handle rewrites every statement it runs in `run()`. Each labelled node pattern gets `tenant:$kg_tenant`, except the publication and the tenancy marker. Three unlabelled forms are rewritten by rule: `WHERE NOT n:_KgPublication` (the wipe, the census, the export), `MATCH ()-[`, and the whole-map `SET n = r`.
  - **Per-tenant publication.** One publication node per tenant (`_KgPublication {id:'publication:<tenant>'}`), so each tenant has its own lease, epoch, sequence lock and recovery.
  - **Fence.** The unit's transaction metadata carries `kg_tenant`. `terminate_stale` terminates only its own tenant's stale units.
  - **Wipe.** The in-unit wipe deletes only its own tenant's nodes.
  - **Constraints.** D1 for a tenanted handle is `CONSTRAINTS_TENANT`: the six composite constraints plus the three refused families as they are.
  - **Guard.** A `_KgTenancy` marker makes a database either tenanted or not. An untenanted handle refuses a tenanted database, since its wipe would empty every tenant. A tenanted writer refuses a database that holds an untenanted store, and drops the six single-id constraints.
  - **Export and memory.** `export_turtle` strips `tenant`, so the Turtle is the tenant's store in the untenanted form. `transaction_memory` counts the tenant's own published statements.
- **rdflib** (`harness/store_rdflib.py`, +16): a file per tenant, `store.ttl` → `store.<tenant>.ttl`, each with its own `.lock`. The in-memory store is per process already.
- **Port** (`harness/store.py`, +3): `open_store` passes `tenant`, and `ReadOnly` carries it.
- **Check tool** (`tools/check_snapshots.py`, 3 lines): it read `KG_RDFLIB_FILE` directly, and `_writer_epochs` read every writer on the server (§5.3).

Key excerpts:

```python
def tenanted(cypher: str) -> str:
    if _SCHEMA.match(cypher):                       # CREATE CONSTRAINT/INDEX, DROP, SHOW, TERMINATE, CALL db.
        return cypher
    def node(m):
        var, first, more, props = m.group(1), m.group(2), m.group(3) or "", m.group(4)
        if first.strip("`") in TENANT_FREE:         # _KgPublication, _KgTenancy
            return m.group(0)
        inner = props[1:-1].strip() if props else ""
        return f"({var}:{first}{more} {{{inner + ', ' if inner else ''}tenant:$kg_tenant}})"
    out = _NODE.sub(node, cypher)                   # (x:Label {..}) anywhere: MATCH, MERGE, CREATE, EXISTS, comprehensions
    out = out.replace(f"WHERE NOT n:{PUB}", "WHERE n.tenant = $kg_tenant")          # wipe, census, export
    out = re.sub(r"MATCH \((\w*)\)-\[", lambda m: f"MATCH ({m.group(1)} {{tenant:$kg_tenant}})-[", out)
    out = re.sub(r"SET n = (r(?:\.props)?)\b", r"SET n = \1, n.tenant = $kg_tenant", out)
    return out

class _Unit:
    def __init__(self, ..., tenant=None):
        self.pid = "publication" if tenant is None else f"publication:{tenant}"
        self.pm = f"MATCH (p:{PUB} {{id:'{self.pid}'}})"      # every PUB_MATCH of the unit now self.pm

    def terminate_stale(self):                                  # the per-tenant fence
        ... "WHERE m.kg_writer IS NOT NULL AND m.kg_tenant = $tn AND m.kg_epoch <> $e RETURN id"

CONSTRAINTS_TENANT = [... "CREATE CONSTRAINT assertion_tenant_id IF NOT EXISTS FOR (n:Assertion) REQUIRE (n.tenant, n.id) IS UNIQUE" ...]

def run(self, cypher, **params):
    if self.tenant is not None:
        cypher, params = tenanted(cypher), {**params, "kg_tenant": self.tenant}
    ...                                                         # unchanged below

# store.open_store
kw["tenant"] = kw.get("tenant") or os.environ.get("KG_TENANT") or None

# store_rdflib
def tenant_path(path, tenant):          # "store.ttl" -> "store.<tenant>.ttl"; None or in-memory: unchanged
```

A build would not rewrite by regex. It would write the tenant into each statement, or carry it as a per-tenant label (§6.1). Over a full CargoQuote run, a tenanted handle ran 67 distinct statements and the rewriter changed all 67.

## 4. Measurement 3: the default path, with the prototype in place

| Check | Result |
|---|---|
| `KG_STORE=rdflib python harness/run.py --deterministic --out <dir>`, then `demo/tools/compare_deterministic.py <dir>` | **0 differing leaves** over 7 scenarios; all seven files byte-identical to `main`'s; 9.3 s against `main`'s 10.1 s |
| the same against the tarball Neo4j | **0 differing leaves** over 7 scenarios; 10.2 s |
| D1 | **equal to the record**: six uniqueness constraints accepted; existence, node key and property type refused, with the same messages |
| `tools/check_snapshots.py --disposable` | Neo4j: **60 ok, 0 FAIL** (202.8 s). rdflib: **33 ok, 0 FAIL** (472.9 s) |
| `tools/check_round_trip.py --chain rdflib,rdflib` | every answer survives |
| `tools/check_round_trip.py --chain neo4j,rdflib,neo4j` | every answer survives (92.9 s) |
| `demo/tools/check_saved_queries.py` | every saved query ran |
| `python tests/run_tests.py` | 1318/1324 passed, 1 skipped, **5 failed**: each is a shape guard (§6.3) |

What does not stay identical with no tenant:
- **One read at every open**, `MATCH (m:_KgTenancy) RETURN count(m)`, so that an untenanted handle can refuse a tenanted database. It changes no output.
- **`export_turtle` skips an edge whose end it did not export.** That never happens untenanted.
- **Five shape tests** that pin the code's text.

Nothing in any output, D1 or the record changes.

## 5. Measurement 4: two tenants and more, side by side

### 5.1 Every reader answers only its tenant

Three tenants were loaded into one database with `gate_cli --scenario <S> --publish`:

| Tenant | Content | Nodes | Load time |
|---|---|---|---|
| `s1` | CargoQuote S1 | 597 | 5.2 s |
| `s2` | CargoQuote S2: same subject, so its ids collide with `s1`'s | 564 | 1.8 s |
| `jf` | J-F C | 3,365 | 7.0 s |

- Each tenant's `gate_cli --no-load` report equals the untenanted reference: the same scenario loaded into an rdflib scratch store. The only differences are the mode fields `loaded` and `store`, and `published` on a loading run.
- A tenant asked for another tenant's scenario is refused: "the store holds S1, not 'S2'". A tenant with nothing in it is refused: "the store holds no scenario".
- Through a tenant's `console_query`, all 20 saved queries run (16 in the adapter, 4 in CargoQuote's `queries.toml`), and `loaded` returns 1 row. **The same text in the Browser, unrewritten, reads every tenant**: `loaded` returns 3 rows (the S1, S2 and C extractions), and `gaps-concerns` mixes 40 rows.

### 5.2 SNAP-01..11 per tenant

| Run | Result | Bystanders |
|---|---|---|
| Neo4j, tenant `a` alone, with `s1`, `s2` and `jf` resident | **60 ok, 0 FAIL**, 227.6 s against 202.8 s untenanted | node counts, publication counters and gate reports byte-identical before and after, through every kill and recovery of SNAP-03, 05, 08 and 11 |
| Neo4j, tenants `a` and `b` concurrently (each wipes, kills and races its own writers while the other runs) | **60 ok, 0 FAIL each**, 354.7 s and 350.5 s | unchanged |
| rdflib, `KG_TENANT=a` (`store.a.ttl`) | **33 ok, 0 FAIL**, 487.2 s | — |
| rdflib, CargoQuote and J-F full runs as two tenants in one folder, concurrently | both comparators 0 differing; `store.cq.ttl` and `store.jf.ttl`, each with its own lock | — |
| `check_round_trip.py --chain neo4j,rdflib,neo4j` in tenant `rt`, four J-F tenants resident | every answer survives (143.2 s) | data and publications unchanged; only `rt`'s publication added |
| J-F `--chain neo4j,rdflib,neo4j --expect-parts --scenarios C,D3` in tenant `rtj` | every answer survives (250.7 s) | unchanged |

**The record per tenant.** A tenanted `run.py --deterministic`, compared with the record, shows CargoQuote 42 differing leaves (6 composite constraint texts × 7 scenarios) and J-F 36 (6 × 6). Everything else is equal. On rdflib it shows 0, since D1 is skipped there.

### 5.3 The cross-tenant cases that are new

1. **The fence.** `terminate_stale` as written terminates every knowgov unit whose epoch differs from the new writer's, in every tenant. Tenant epochs are independent counters.
   - With `y`'s epoch offset, tenant `y`'s writer opening while tenant `x`'s unit was open **terminated `x`'s unit** (`Neo.ClientError.Transaction.Terminated`); `x` kept its previous generation.
   - With both counters at 3, the probe passed by coincidence.
   - With the per-tenant fence (`m.kg_tenant = $tn`), `x` publishes.
   - The same confounder sits in `check_snapshots.py`'s `_writer_epochs` (SNAP-05), which had to filter by `kg_tenant`.
2. **The schema wait.** A writer's D1 runs `CREATE CONSTRAINT` for the three families Community refuses.
   - The existence constraint (`Assertion.status IS NOT NULL`) validates the existing data before it refuses. It **waits for any open unit that writes `Assertion`, in any tenant**: more than 5 s in the probe, against 0.00–0.01 s for each of the eight other schema statements measured (the existing composite constraint, node key, property type, `kg_publication`, the guard's `DROP`, `kg_import` and its drop, `SHOW CONSTRAINTS`).
   - In one process, two tenants' writers deadlock: `x`'s unit is open, and `y`'s D1 waits for `x`'s commit.
   - Across processes, units serialise:
     - tenant `rb`'s S1 gate load took 11.1 s wall for 1.4 s of CPU, behind tenant `ra`'s run;
     - CargoQuote beside a concurrent J-F run took 60.8 s (10.5 s alone), and that J-F run 61.8 s (36.6 s alone);
     - four J-F runs started together took 146.2, 146.2, 217.0 and 217.0 s in one trial and about 50 s each in another. The spread is unexplained: it depends on whether the writers measured D1 before or after another's unit opened.
3. **Deadlock.** Four first-time tenanted J-F runs were started together on a database new to tenancy.
   - In one trial of seven, two of the four failed with `DeadlockDetected` (a transient error; the unit's one transaction is not retried).
   - The six further trials were clean. The cause is not isolated.
   - Untenanted, the lease makes two concurrent units impossible.
4. **The marker race.** The prototype's unconstrained `MERGE (:_KgTenancy)` produced 2 and then 3 marker nodes when first writers started together. A build needs a constraint on the marker, which is a schema statement too.
5. **The sequence lock, global or per tenant.**
   - **Per tenant** (the prototype) gives each tenant concurrency, but the schema wait in point 2 takes most of it back.
   - **A global lock** (one publication node, its counter shared) would serialise every tenant's writer and remove points 1 to 3. Every tenant's readers would then see `StoreChanged` on every other tenant's publication: SNAP-02's refusal, with no data changed for them.
   - Measured per tenant: `s1`'s, `s2`'s and `jf`'s publication counters did not move across `a`'s and `b`'s whole concurrent SNAP runs, so their readers were never refused by another tenant's publication.
6. **Wipe, abandon and recovery stay per tenant.** SNAP-03's kills, SNAP-08's abandoned publication cleared by a reader and SNAP-11's writer killed between commit and close all touched only their own tenant.
7. **The guard.**
   - An untenanted `gate_cli --no-load` on the tenanted database exits 2: "this database holds tenants; open it with a tenant (KG_TENANT)".
   - A tenanted writer on a database holding an untenanted store is refused: "this database holds an untenanted store; wipe it before it holds tenants".

## 6. Measurement 5: cost

### 6.1 Load time and transaction memory

Peak transaction memory is `SHOW TRANSACTIONS`' `estimatedUsedHeapMemory`, sampled every 20 ms by tenant.

| Case (`run.py --deterministic`, the whole run one unit) | Wall | Peak transaction heap |
|---|---|---|
| CargoQuote, untenanted, runs 1 and 2 | 8.9 s, 8.4 s | 14, 15 MiB |
| J-F, untenanted | 30.4 s | 78 MiB |
| CargoQuote, one tenant alone, runs 1 and 2 | 10.5 s, 10.6 s | 15, 19 MiB |
| J-F, one tenant alone | 36.6 s | 76 MiB |
| CargoQuote with a J-F tenant resident (3,348 nodes) | 15.3 s | 19 MiB |
| CargoQuote while a J-F run loads in another tenant | 60.8 s | 19 MiB |
| that J-F run | 61.8 s | 76 MiB |

- A lone tenant costs 18–20 % over untenanted. The cause was not separated: the rewritten statements, the composite constraints, or both.
- **A resident tenant costs a further 46 %, because every tenant's reads scan every tenant's nodes.** The plans:
  - the tenant's wipe: `AllNodesScan ← Filter`;
  - `Assertion {key, tenant}` and `Activity {id, tenant}`: `NodeByLabelScan ← Filter`;
  - only `Assertion {id, tenant}` uses the composite index: `NodeUniqueIndexSeek`.
- The cost of a tenant's load therefore grows with the database, not with the tenant. A per-tenant label (`:KgT_<tenant>`) would make the wipe and the scans label scans of the tenant alone. It needs a second rewrite rule, and dynamic labels in statements.
- Each client process peaks at about 200 MB RSS. The server stood at 1,399 MiB RSS after the runs, at the compose heap: the cost of each extra Community container under the alternative.

### 6.2 The load-memory forecast when another tenant is loading

`load_memory.sizing` forecasts:

| Subject | Whole run | One gate load |
|---|---|---|
| CargoQuote | 69.0 MiB | 37.2 MiB |
| J-F | 237.5 MiB | 65.0 MiB |

- The limit `transaction_memory` reads is the smallest of three settings. Here that is the server-wide `dbms.memory.transaction.total.max` (716.8 MiB, 70 % of the heap), which every tenant's units share. The forecast compares one unit against the whole pool.
- Measured with the server restarted at `dbms.memory.transaction.total.max=70m`:
  - five J-F gate loads in five tenants each passed `preflight` alone (65.0 ≤ 70 MiB) and were released together from a barrier;
  - **three published; two failed inside their transactions**: `TransientError: The allocation of an extra 2.0 MiB would use more than the limit 70.0 MiB. Currently using 70.0 MiB. dbms.memory.transaction.total.max threshold reached`;
  - the two failures were not `LoadTooLarge`, and came only after their writes began. Their publications stayed at `begin = end = 0`: nothing partial was visible.
  - three loads in one process (threads) all published, because their peaks did not coincide.
- The forecast stays correct per unit, and the failure stays clean (decision-0014). Its promise, "refused before its first write" (task-0176), does not hold under concurrent tenants. There are three ways to keep it:
  - subtract the other tenants' live usage (`SHOW TRANSACTIONS`), which races;
  - serialise units globally (§5.3 point 5);
  - document the forecast as per unit.

### 6.3 What the change touches

| Surface | Count | What changes |
|---|---|---|
| Cypher (`store_neo4j.py` at `main`) | 257 lines carry a Cypher keyword inside a string; 129 `.run(` call sites; 270 labelled node patterns; 11 publication matches | every labelled pattern gains the tenant; 10 unlabelled forms need a rule (5 `WHERE NOT n:{PUB}`, 2 `MATCH ()-[`, 1 `MATCH (a)-[e]->(b)`, 2 `SET n = r`); by hand: the publication, the fence, the in-unit wipe, `transaction_memory`, the export, two module helpers (`committed_nodes`, `publication`) |
| Port operations | 92 methods on `Store`, 45 in `READS` | **0 signatures change**. `open_store` gains `tenant=` (default None) and `KG_TENANT`; the adapters' constructors gain it; `ReadOnly` carries it. `Store.instance`, documented as "the instance id the adapter may stamp on its writes (a shared store later)", cannot double as the tenant: `run.py` and `check_snapshots.py` already pass `SUBJECT.id`, which would tenant the default path |
| Saved queries (`demo/tools/check_saved_queries.py`) | 16 in the adapter + 4 in CargoQuote's `queries.toml` = 20 | all run per tenant through `console_query`; as Browser text all 20 read every tenant, so the page's guide must emit `:param kg_tenant => '<t>'` or a literal per tenant |
| MCP tools | 17 tools; 10 take `scenario` | 8 are store reads where `scenario` means "the scenario you expect the store to hold; refused if it holds another": `gate_verdict`, `three_valued_answer`, `evidence_bundle`, `register_impact`, `proposal_impact`, `held_keys`, `derived_outputs`, `document_statements`; 2 (`scenario_runs`, `scenario_result`) read the runs folder, not the store. See below |
| Settings | 1 new: `KG_TENANT` | documented, it is a contract (decision-0027, decision-0016 point 3) |
| Tests | 5 fail on the prototype; 59 test files name the store modules, `open_store`, `_KgPublication` or `KG_RDFLIB_FILE` | listed below |
| Check tools | `check_snapshots.py`, 3 lines | plus a per-tenant mode and a SNAP-12 for §5.3 |

The MCP tools' `scenario` has three possible readings under tenancy:
- **keep its meaning**, the tenant fixed per reader process (`KG_TENANT` read once at start, as `as_of` is): no contract change;
- **add an optional `tenant` argument**: additive;
- **let `scenario` select the tenant**: its meaning moves from "expected" to "selected", which is breaking for an agent that relies on the refusal.

The five failing tests:
- `test_docs_code_fixes::test_the_stores_live_where_the_row_says` pins the rdflib constructor's text;
- `test_settings_table::…every_setting…` wants rows for `KG_TENANT`, and for the probe's own switch;
- `test_store::test_adapters_implement_every_port_operation` refuses the new private `_tenancy_guard` as an undeclared operation;
- `test_store_generations::test_the_neo4j_publication_node_stays_out_of_the_evidence` wants every whole-graph statement filtered by `NOT n:_KgPublication`, and the tenant filter is another form;
- `test_store_singles::test_s7_on_neo4j…` builds an adapter by hand, without `tenant`.

New tests a build needs:
- every statement tenanted: a guard in task-0003's style;
- isolation per adapter;
- the guard;
- the settings row;
- SNAP-12, for the fence, the schema wait and the forecast.

## 7. Measurement 6: access

| On 5.26.18 Community | Result |
|---|---|
| `CREATE USER spike SET PASSWORD … CHANGE NOT REQUIRED` | accepted |
| `SHOW USERS` | users listed, `roles` null |
| `CREATE ROLE spike_reader` | "Unsupported administration command" |
| `GRANT MATCH {*} ON GRAPH neo4j NODES Assertion TO spike_reader` | "Unsupported administration command" |
| `SHOW ROLES` | "Unsupported administration command" |
| `CREATE DATABASE tenant_b` | "Unsupported administration command" |
| `SHOW DATABASES` | `neo4j` and `system` only |

Every authenticated user has full read and write on the one database. **Tenancy here separates data, not access.**
- A tenant is a filter in the harness's statements, not a credential.
- Any client with the password reads and writes every tenant: the Browser (§5.1), `cypher-shell`, a second harness with another `KG_TENANT`, or one with none (refused only by knowgov's own guard, not by the server).
- `docs/security.md` "Supported on Neo4j 5 Community with one database; nothing assumes a second database" stays true. "Who may do what" and "Gaps" would each need a line saying so.
- Separation of access needs one database server per tenant: one Community container each, or Enterprise (roles, privileges, several databases).

## 8. What cannot stay identical

- **Untenanted:** one read at every open (the guard) and five shape tests. No output, no D1, no record leaf.
- **Tenanted, against the record:** D1's six constraint texts (`<label>_tenant_id … REQUIRE (n.tenant, n.id) IS UNIQUE`). `accepted` and the three refusals are unchanged.
  - The comparator would compare a tenanted D1 only with a tenanted run, as it already compares D1 only between runs of the same store kind (task-0004). That is a rule added; the record is unchanged.
  - The six single-property constraints cannot stay in a tenanted database.
- **Tenanted, behaviour:**
  - the Browser's saved-query texts need a tenant parameter;
  - a tenanted database refuses untenanted handles;
  - the forecast's "before its first write" holds per unit only;
  - writers of different tenants wait on one another's units (§5.3 point 2) where untenanted there is only ever one writer.

## 9. Opportunity canvas

| Box | Content |
|---|---|
| Problem | One deployment per subject (one store holds one subject's one scenario) multiplies containers when several teams, subjects or scenarios adopt knowgov in one organisation |
| Users | An adopting organisation's platform team running one stack for several delivery teams; the maintainer, who runs CargoQuote and J-F side by side |
| Proposal | A tenant bound at `open_store(tenant=)`: a property on every node and a filter in every statement on Neo4j, a file per tenant on rdflib; untenanted unchanged |
| Unique value | One Neo4j for many subjects, each with its own generations (SNAP-01..11 hold per tenant), its own wipe and its own recovery |
| Cost | Every Cypher statement reviewed (129 call sites, 270 patterns); a per-tenant label to stop scans growing with the database (+46 % measured); D1 measured once per database to lift the schema wait; a fence, a guard and a marker constraint; a SNAP-12; the page's Browser guide parameterised; `KG_TENANT` documented |
| Risk | Data separation mistaken for access separation (Community has no roles); a missed statement reads across tenants; concurrent tenants serialise or deadlock through schema statements; the forecast's promise weakens under concurrency |
| Alternative | One Community container per tenant: zero code, data and access separated, about 1.4 GiB RSS each; rdflib with `KG_RDFLIB_FILE` per team, which already works today with no change |

## 10. Fit/gap

| Must satisfy | Fit | Gap |
|---|---|---|
| decision-0016 point 3: the store port is a contract | no operation's signature changes; `tenant=` is an optional keyword | the port's documented `wipe` ("Delete everything this instance holds") gains a per-tenant reading |
| decision-0016 point 3: the MCP tools' inputs and outputs | one reader per tenant, `KG_TENANT` at start: no change | reusing `scenario` as the selector would change a frozen input's meaning |
| decision-0016 point 3: the documented `KG_*` settings | `KG_TENANT` is additive | in the 0.9.x soak an additive contract change is still 0.10.0 (point 2, A1) |
| decision-0016 point 5: deprecation from 1.0.0 | nothing is deprecated | — |
| decision-0016 point 7: after 1.0.0 SemVer proper | additive, hence a minor: 1.x | — |
| decision-0014 SNAP-01..11 | hold per tenant on both adapters, alone and two at once (§5.2) | only with the fence per tenant; the shared pool, schema statements and the Browser are outside the per-tenant publication (§5.3) |
| D1 | untenanted D1 equal to the record | tenanted D1 differs in six texts; the comparator needs a tenanted-D1 rule |
| The record and the comparator | untenanted 0 differing leaves on both adapters; tenanted differs in D1 alone | — |
| `docs/security.md` | "one database; nothing assumes a second" holds | tenancy adds no access control; "Who may do what" and "Gaps" must say so |
| CLAUDE.md "No other module speaks Cypher" (task-0003) | the filter stays inside the adapter | the Browser texts leave it; a guard test must hold every statement tenanted |

## 11. SWOT

- **Strengths.**
  - The untenanted path is provably unchanged.
  - The port's surface holds.
  - Composite uniqueness works on Community.
  - The publication protocol (decision-0014) partitions cleanly by one id: every SNAP holds per tenant, and bystanders are byte-identical through kills and recoveries.
  - rdflib needs a path derivation and nothing else.
- **Weaknesses.**
  - Every statement is touched.
  - Reads scan every tenant's nodes.
  - Writers of different tenants wait on each other through D1's refused families.
  - A deadlock was seen once.
  - The tenant's presence cannot be enforced by the database.
  - The Browser sees everything.
- **Opportunities.**
  - One stack for several teams of one organisation, at one container's memory.
  - The maintainer's two public subjects side by side on one page.
  - A per-tenant label would also give per-tenant counts and wipes as label scans.
- **Threats.**
  - An adopter reads "tenants" as access control, which Community cannot provide.
  - A statement added later without the filter leaks across tenants.
  - Concurrency failures appear only under load.
  - Building it in the soak restarts the freeze.

## 12. Advice

The drafter's recommendation to the maintainer:

1. **Do not build it in 0.9.x or for 1.0.0.** Any contract change in the soak is 0.10.0 and restarts the freeze (decision-0016 point 2, A1). No adopter has asked for it, and nothing on the 1.0 path needs it.
2. **Offer the alternative first.** If a lighthouse needs several teams on one deployment, offer one Community container per tenant: no code, data and access both separated. A container costs about 1.4 GiB RSS at the compose heap, measured. Or offer rdflib with a store file per team, which works today. Say so in the instance README when the question comes.
3. **Build in-database tenancy only as a 1.x minor, and only if a lighthouse refuses the per-container cost and accepts shared credentials.** Its prerequisites, each from a measurement here:
   - a per-tenant label rather than a property alone (§6.1);
   - D1 measured once per database rather than per writer, so no schema statement runs while another tenant's unit is open (§5.3 point 2);
   - the per-tenant fence (§5.3 point 1);
   - a constrained marker (§5.3 point 4);
   - a stated forecast policy (§6.2);
   - one MCP reader per tenant, `scenario` unchanged (§6.3);
   - the Browser guide parameterised (§5.1);
   - `docs/security.md` saying "data, not access" (§7);
   - SNAP-12 proving the cross-tenant cases.

## 13. Verdict

**Additive 1.x.** It does not need 2.0.0:
- the untenanted path is identical: comparator 0 differing leaves on both adapters, D1 equal to the record, SNAP-01..11 and both `--chain`s holding;
- no port operation's signature changes;
- every new element is opt-in: `tenant=`, `KG_TENANT`, a tenanted database and its D1;
- the one change that would break a frozen contract, `scenario` as a tenant selector, is avoidable.

It is worth building only on demand, after 1.0.0: on Community it buys data separation without access separation, and the container-per-tenant alternative buys both for memory alone.

## 14. Not measured, and why

- **SNAP-03's `--memory-limited` per tenant** needs a server restarted with a small `db.memory.transaction.max`. The shared-pool measurement in §6.2 replaced it.
- **The Docker stack (`demo.yml`), the page under a tenant, and `tools/check_mcp_server.py` per tenant** were not run: the brief named the tarball. The MCP reader was exercised only through SNAP-01's `gate_verdict` per tenant.
- **The deadlock's cause** (§5.3 point 3) was seen once in seven trials and not isolated.
- **A global sequence lock** was not prototyped. Its effect on readers follows from SNAP-02's refusal, by reasoning, not by measurement.
