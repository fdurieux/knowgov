# 0017 — Reconcile lists the export ids no node carries

Date: 2026-11-04. State: approved (fdurieux, by the merge of #27 on 2026-11-04; the line read proposed when merged). Supersedes: nothing; extends `tools/reconcile.py` and the
`RECONCILE.json` it writes (decision 0001, "Exports are append-only"), whose `files`, `ids` and
`stale_nodes` sections are unchanged.

## Proposal

1. **The field.** `reconcile()` adds one top-level section to `RECONCILE.json`, `unregistered`:
   the export's ids (the keys of `MANIFEST.toml` `[ids]`) that no node's `[source]` carries for that
   system, under the system's `id_field` (`metamodel/sources.toml`), compared on the part before `#`
   as `stale_nodes` already compares. One entry per id, sorted by id:

   ```json
   "unregistered": [
     {"kit_path": "kit/links.toml", "name": "links.toml"}
   ]
   ```

   The id's key is the system's `id_field`, as in `stale_nodes`; `name` is the value `[ids]` gives
   it, verbatim. A system with no `id_field`, or an export with no `[ids]`, gives an empty list.
2. **Additive.** No section is renamed, moved or removed. A reader of an older `RECONCILE.json`
   reads it as before; a reader of the new one that does not know `unregistered` ignores it. A
   `RECONCILE.json` already committed under `exports/` is not rewritten: append-only holds, and the
   section appears in a folder's file when `reconcile.py` next runs on a new export.
3. **The coverage report.** The summary `check_register.py --report` writes at a tag gains, per
   system, the latest export's count: `{"denominator": <ids the export carries>, "registered": <n>,
   "unregistered": <n>}`. It is reported with its denominator, never as a percentage to pass, and
   is not a coverage rule: it raises no error and no warning.

## What it would find

Measured on the register as of this pull request (base `4bb0923`, 57 nodes, 65 links), against the
two exports it holds:

| export | ids carried | held by a node | unregistered |
|---|---|---|---|
| `exports/kit/2026-10-30` | 10 | 8 | 2: `kit/links.toml`, `tests_input/acceptance.feature` |
| `exports/jef_kit/2026-11-01` | 50 | 15 | 35: `CHANGES.md`, 19 under `contracts/`, 12 `features/*.feature`, `requirements.json`, `uml/basis_and_adjustment.puml`, `uml/series_state.puml` |

`stale_nodes` is empty on both today and stays so.

## What it does not do

- **No node minted.** An `unregistered` entry is a finding to triage: register it (a node, an id
  minted here, in its own pull request), or leave it, since not every document an export carries is
  a node. The register mints ids; a tool never writes a node.
- **No deletion, no change to `stale`.** `stale_nodes` keeps its meaning (a node whose external id
  the export no longer carries) and its shape. The two lists are the two sides of one comparison;
  neither acts on the other.
- **No check.** `check_register.py` does not fail or warn on an unregistered id; point 3 reports a
  count only.

## Why

Reconcile today answers one side: which register nodes lost their external id. The other side,
which external ids the register does not hold, is the inventory gap an adopter is asked about
first, and the denominator a coverage claim over an export needs. Without it the count lives in
each consumer.

knowgov's connector (`tools/connector.py`, task-0063/0121) vendors and imports `reconcile.py` and
reports the carried ids the register does not hold as `unknown_ids`, its own extension. With the
register's own field it can drop that extension at its next re-vendor. Whether and when it does is
knowgov's choice.

## Not decided here

Whether an unregistered id may be excused (an entry in `exceptions/`, as for the coverage rules)
or marked as not a node in the export's `MANIFEST.toml`. Whether `reconcile.py` prints the count
on its summary line: the implementation may, as it prints the stale count.

## If approved

The next pull request:

- **Code.** `tools/reconcile.py` `reconcile()` fills `unregistered` as in point 1; the module
  docstring gains one line citing 0017. `tools/check_register.py` `run()` adds point 3's counts to
  the summary.
- **Tests.** `tests/test_register.py`: `test_reconcile_against_no_previous` also holds the kit's
  `unregistered` as the two entries above, each with its `kit_path` and `name`; a new
  `test_reconcile_lists_unregistered_ids` holds, on a temporary copy of the register, the jef_kit
  export's 35 entries, that `stale_nodes` is unchanged on both exports, and that a node removed from the
  copy moves its id into `unregistered`.
- **README.md**, one line in the adopter register beside the export row: reconcile also lists the
  export's ids no node holds, for triage, never created.
