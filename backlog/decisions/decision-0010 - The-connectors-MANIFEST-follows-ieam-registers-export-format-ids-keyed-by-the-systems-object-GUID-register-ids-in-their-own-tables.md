---
id: decision-0010
title: >-
  The connector's MANIFEST follows ieam-register's export format: ids keyed by
  the system's object GUID, register ids in their own tables
date: '2026-11-05T20:07:00Z'
status: accepted
---
## Context

task-0138, the register re-vendored at ieam-register v0.2.10. The register's decision 0017 adds
`unregistered` to `RECONCILE.json`: the MANIFEST `[ids]` keys that no node's `[source]` carries
under the system's `id_field`. Its `exports/README.md` keys `[ids]` the same way: `kit_path` for
`kit`, and `aris_guid` for ARIS (`metamodel/sources.toml`).

`tools/connector.py` (task-0063, task-0121) did not follow that format:
- it keyed `[ids]` by register id (`AT_ID`);
- it kept the object GUIDs in a separate `[guids]` table;
- it dropped every AML object that carries no register id.

So the vendored `reconcile.py` read every connector export against the wrong key: its ids diff,
its `stale_nodes` and `unregistered`, and, on an instance, `check_register.py --report`'s export
counts. The connector worked around this with three extensions:
- an id carried by a GUID counts as carried;
- a node is stale by register id;
- `unknown_ids`.

Measured on the synthetic ARIS fixtures (`tools/fixtures/aris_cargo_quote`), landed in a temporary
example instance, with the vendored `reconcile.py` run unchanged. `first`'s AML holds 41 objects,
every one with a GUID; 14 carry `AT_ID`. `later`'s holds 38, of which 13 carry `AT_ID`. The BPMN
files carry 5 and 4 register ids, all of them also in the AML. No example node carries
`[source] aris_guid`.

| variant | export | `[ids]` | ids diff | `stale_nodes` (register only) | `unregistered` |
|---|---|---|---|---|---|
| before: `[ids]` by register id | first / later | 14 / 13 | by register id | 0 / 0 | 14 / 13 |
| (a1) `[ids]` by GUID, objects with `AT_ID` only; nodes as in the example | first | 14 | +14 | 0 | 14 |
| | later | 13 | renamed PROC-0004's GUID, deleted PROC-0005's | 0 | 13 |
| (a2) as (a1); the 14 nodes given `[source] system = "aris"`, `aris_guid` | first | 14 | +14 | 0 | 0 |
| | later | 13 | as (a1) | PROC-0005 | 0 |
| (a3) `[ids]` every object by GUID; nodes as in (a2) | first | 41 | +41 | 0 | 27 |
| | later | 38 | renamed 1, deleted 3 (PROC-0005's and two events') | PROC-0005 | 25 |

Under (a1), (a2) and (a3), the connector's carried-by-GUID extension has nothing left to do.
Stale-by-register-id is needed while nodes carry no `aris_guid`, and redundant once they do.
`unknown_ids` is still needed, because the register cannot see a typed `AT_ID` it does not hold.

A BPMN file has no GUID, and element ids are not identity (task-0119). `reconcile()` guards both
its stale rule and `unregistered` on a non-empty `[ids]`, so an empty `[ids]` makes neither
misfire.

## Decision

Option (a), the full-object variant (a3). The connector's MANIFEST follows ieam-register's export
format:
- `[ids]` is every AML object with a GUID, keyed by the GUID (the system's `id_field`), with its
  name, whether or not it carries a register id.
- `[register_ids]` maps GUID to register id for the objects that carry one. It replaces `[guids]`.
- `[bpmn_ids]` maps each register id a BPMN file carries to its name. A BPMN part adds nothing to
  `[ids]`, and key spaces are never mixed in `[ids]`.

The extensions:
- carried-by-GUID is dropped;
- `unknown_ids` stays, read from the `[register_ids]` values and the `[bpmn_ids]` keys;
- stale-by-register-id stays, read from the same tables of the previous folder and this one. It is
  documented as redundant once an instance's nodes carry `[source] aris_guid`.

Recorded as: maintainer, 2026-11-05, "(a)", relayed by the coordinating session.

## Consequences

- **Contract change.** The connector's MANIFEST format changes (CHANGELOG, Unreleased, contract
  changes).
- **Older folders.** A folder landed before keeps its bytes (append-only). The first export after
  an upgrade reads every object as added in `ids`. Stale and `unknown_ids` read the register ids of
  both folders, and a folder with `[guids]` gives its `[ids]` keys.
- **What the register computes now.** It runs its own ids diff, `stale_nodes` and `unregistered` on
  the connector's exports. On the example instance, `unregistered` is 41 and then 38.
  - It includes the 27 and then 25 events, rules and step functions that no register id names. They
    read as unregistered until the register's decision 0017 settles whether such an object may be
    excused.
  - With nodes that carry `[source] aris_guid`, it is 27 and then 25, and the register's own
    `stale_nodes` finds PROC-0005.
- **proposal_impact.** Its D2 reads `[register_ids]`, and `[guids]` in an older folder.
- **No record moves.** The fixtures are unchanged, and `tools/aris_export.py --check` holds.
