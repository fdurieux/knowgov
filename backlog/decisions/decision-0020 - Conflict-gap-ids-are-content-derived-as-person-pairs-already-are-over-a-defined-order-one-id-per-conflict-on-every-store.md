---
id: decision-0020
title: >-
  Conflict gap ids are content-derived, as person pairs already are, over a
  defined order: one id per conflict on every store
date: '2026-11-08T11:46:00Z'
status: proposed
---
## Context

task-0202 (doc-0030 question 4, accepted by the maintainer on 2026-11-07: "the renumbering of the record's conflict gap ids is a decision of its own, after the tranche"). The tranche's semantic core has merged: F3, F4, F2 and F5 (#339, #341, #342, #343, #345).

**How conflict gaps are named today (`harness/rules.py` `r_conflict`).** A conflict between a person's statement and a document's already has a content-derived id: `gap:conflict:<key>:<a>~<b>`, from its two assertion ids. A conflict between two documents is numbered `gap:conflict:<key>:<n>` in the order `pairs(st)` returns, which is the order of `candidate_pairs`, and that order is undefined on both adapters (doc-0030 S2).

**What follows from that:**
- On S4, `:0` is the BPMN-against-table conflict on the Neo4j record and the table-against-PlantUML conflict on rdflib.
- Since decision-0017, the default gate computes on an rdflib scratch store while the page and the MCP reader read Neo4j, so one conflict is named by two ids.
- An edit that adds or removes a conflict on a key renumbers the others: root cause 2, "ids name a position, not content" (doc-0030).
- `demo/tools/compare_deterministic.py` normalises `gap:conflict:<key>:<n>` to `:n`, and `check_round_trip`'s canonical sort hides the order, so neither sees it.

**Where the ids are read:**
- the gate report's `conflicts`;
- the gate's two text renderings, which the arms' bundle carries: S4's recorded model outputs quote `:0..3`;
- the page and the MCP reader (`conflict_gaps` in `store.READS`).

A person's ruling settles a dispute by assertion id, bound by content since task-0199, so no act names a conflict gap id. task-0201 ordered `declared_gaps_for_key` only and held this (task-0202 AC #2).

## Options

- **(a) A defined order, numbering kept.** `candidate_pairs` and `conflict_gaps` answer ordered by key, then by the pair's sorted assertion ids, on both adapters, and R-CONFLICT keeps `:<n>`.
  - The set of ids per key is unchanged. Which conflict holds which number may change on one adapter, against the record.
  - The ids stay positional: a new conflict on the key renumbers those after it.
- **(b) Content-derived ids, as person pairs already have.** A conflict between two documents is `gap:conflict:<key>:<a>~<b>`, with its two assertion ids sorted. The id is the same on every store and on every run of the same statements, and a later version's statements, with their new assertion ids, name a new conflict. The order contract is still set, so that lists are stable.
- **(c) No change.** Store order, two names for one conflict.

## Proposed

**(b)**, with (a)'s order contract under it. The maintainer decides; this record is proposed.

## Opportunity canvas

| Element | Content |
|---|---|
| Problem | One conflict has two ids across the two stores that the default gate and the page read, and an id that moves when another conflict appears |
| Users | A person reading a gate report beside the page or the MCP answer; a pipeline comparing reports across runs; the arms' bundle |
| Proposal | (b): every conflict's id names its two statements, as person pairs do already |
| Unique value | One name per conflict on every store and every run, with the last positional gap id gone before the contracts freeze |
| Cost | `r_conflict`'s document branch; the order contract on both adapters; the comparator's normaliser extended to the new form; the bundle's pinned bytes regenerated where a document conflict appears (S4) |
| Risk | Longer ids in reports and bundles; a reader that parsed `:<n>` |

## Fit/gap

| Must satisfy | (a) | (b) | Evidence |
|---|---|---|---|
| One id per conflict on both stores | Fit | Fit | doc-0030 S2 |
| Stable across an edit that adds a conflict | **Gap** | Fit | root cause 2 |
| The scored record unchanged | Fit through the comparator's normaliser; a renumbering on one adapter | Fit through the normaliser extended to both forms; the vendored results are never edited | `compare_deterministic.py`'s `CONFLICT_ID` |
| The arms' bundle bytes | Unchanged unless the order swaps a number | **Changed** for scenarios with a document conflict (S4): a deliberate re-pin, stated | `gate.py` renderings; `test_arms` |
| decision-0016: a contract change gathers for 0.9.0 | A fix (an order) | A contract change: the gate report's conflict id form | doc-0028 G9 |
| One form for every conflict id | Gap: two forms stay | Fit | `rules.py:111` |

## SWOT

| | Helpful | Harmful |
|---|---|---|
| **Internal** | **S (b):** the form exists for person pairs; one rule for every conflict; ids survive a re-run. **S (a):** the smallest change | **W (b):** the bundle's bytes and every report's conflict ids change form; the comparator learns a second pattern. **W (a):** positional ids frozen into 0.9 |
| **External** | **O:** the reverse-engineering process's step 8 compares two runs' findings by id (decision-0018); a pilot's first edit no longer renumbers its conflicts | **T:** a consumer that parsed `:<n>`, though none is shipped; the recorded model outputs quote `:0..3`, which stays true of the record as vendored |

## Advice

(b), for 0.9.0:
- It removes the last positional gap id before the contracts freeze, the class doc-0030's root cause 2 names.
- It is the form person pairs already use.
- The process's re-run step needs ids that survive a re-run.

(a) alone would freeze positional ids into 0.9's contract and leave them to a later 0.10.0. The record stays equal through the comparator, because the vendored results are never edited and the comparator reads both forms. The cost is a deliberate re-pin of the bundle bytes where S4's document conflicts appear, named in its pull request.

## If accepted: what the build does

A task, minted on acceptance:
- **Ids.** `r_conflict` names a document conflict `gap:conflict:<key>:<a>~<b>`, with its assertion ids sorted.
- **Order.** `candidate_pairs` and `conflict_gaps` are ordered by key, then by id, on both adapters.
- **Comparator.** `compare_deterministic.py` normalises both forms per key.
- **Re-pins.** The bundle's pinned bytes and every fixture that names `:<n>` are re-pinned in the same pull request, each named.
- **Tests.** One test holds one id per conflict on rdflib and Neo4j, and one holds the id unchanged when an unrelated conflict is added.
- **CHANGELOG.** A line under Unreleased's contract heading.
- **The record's note.** The vendored results keep `:0..3`. Each is the S4 conflict that the record's own `text` names, and `subjects/README.md` notes the form change. No vendored file is edited.
- **The record.** The scored record, the deterministic run and the comparator stay equal.
