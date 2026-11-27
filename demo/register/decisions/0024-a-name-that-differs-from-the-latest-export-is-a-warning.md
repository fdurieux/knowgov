# 0024 — A name that differs from the latest export is a warning, where the export names concepts

Date: 2026-11-27. State: approved (fdurieux, in the maintainer's chat on 2026-11-27: "approve 0024"; recorded on the pull request before its merge; the line read proposed when drafted). Drafted by session_01HTAA1VMpofzhnMmGA5dXyy, dispatched by
session_01HTAA1UV2N6XGtCwCvVnB5t on fdurieux/ieam-register#39; a session never approves (decision 0019).
Supersedes: nothing. Sets the level and the scope of the name check that CLAUDE.md and METAMODEL.md have
described since decision 0001 and no code ran; adds one field, `export_names`, to every `[system.<name>]` of
`metamodel/sources.toml`. Decisions 0001 (exports append-only, a vanished id `stale`), 0017 (`unregistered`),
0018 (A1, warning, no exception mechanism), 0020 (exceptions excuse coverage rules), 0022 (an `aris` process
node's name is its function definition's) and 0023 (the agent registry, `[cites]`) stand.

## The question

`name` is the one field a node repeats from its source of record, "checked against the latest export, not
authored". `check_register.py` never opened an export's names. #39 asks for the check; the check changes what
passes, so it needs a record: an error or a warning, whether an exception can excuse it, and, as the first
measurement showed, which exports it can mean anything on.

## Decision

1. **What an export names.** Every `[system.<name>]` declares `export_names`: `"concept"` when its export's
   `[ids]` key the thing a node names and give that thing's name (an ARIS function definition, decision
   0022; an Archi element; an EDM entity; an agent registry's usage), `"document"` when they key a file that
   nodes point into and give the file's name. Here `aris`, `archi`, `edm` and `agent_registry` are
   `"concept"`; `kit` and `jef_kit` are `"document"`. A system without the field, or with another value, is a
   `sources` error.
2. **The check.** For each node whose `[source]` names a system with an id and an export, `check_register.py`
   reads the latest export (`exports/<system>/<date>/MANIFEST.toml`, latest by folder date). On a `"concept"`
   system it compares the node's `name` with the name `[ids]` gives the node's id (`aris_guid`, `archi_id`,
   `edm_id`; for `aris`, the definition's, decision 0022).
3. **A difference is a `name` warning,** naming the node, both names, the id and the export folder. It never
   fails the merge. No exception excuses it: `exceptions/` stays scoped to coverage rules, and a warning needs
   no excuse.
4. **A vanished id**, on any system (neither the id nor its document before `#` among the latest export's
   `[ids]`), is a `stale` warning, never a deletion, and gets no `name` finding. `reconcile.py`'s
   `stale_nodes` is unchanged.
5. **Unchecked, and counted by reason.** A node of a `"document"` system; a node whose system has no export
   folder; a node whose id names a part (`<path>#<part>`) of a document a `"concept"` export carries only whole.
   The checker prints matched over checked, the differing and stale counts, and unchecked over every node with
   a `[source]`, with each reason's count, as coverage is printed.
6. **The remedy is by hand, on the side that is wrong.** A rename in the source of record: set `name` to the
   export's in the pull request that lands the export. A wrong name in the source of record: fix it there; the
   next export, a new folder, closes the finding. Neither side is changed by a tool.

## Measured

On `main` at 1b4974c, before this check: 57 nodes, 65 links, 0 errors, 12 warnings. 57 nodes carry a
`[source]` (28 `kit`, 29 `jef_kit`); no node names `aris`, `archi`, `edm` or `agent_registry`.

- **Without `export_names`** (this pull request's first head): 53 differ, 0 match, 0 stale, 4 unchecked as
  parts (CAP-0002, CAP-0003, CAP-0004 and ENT-0004 on `contract/decision_table.md#DT-…`); 12 warnings become
  65. Every difference has one cause: the kit manifests' `[ids]` give each document its file name
  (`"contract/spec.md" = "spec.md"`), and up to eight nodes point at one document (`contracts/chain.md`). A
  document cannot carry eight concepts' names, so no later kit export could resolve them, and no node name is
  wrong. Under an error level, `main` would fail with 53 errors no pull request could fix.
- **With `export_names`**: 57 of 57 unchecked, all as nodes of a `"document"` system; 0 differ, 0 stale; 12
  warnings, 0 errors. The check runs on its first `"concept"` folder: the tests exercise it on a synthetic
  `aris` export.

## Options

- (a) **Error, every system.** The contract's literal reading. Fails `main` on the kit today (53 errors, none
  fixable).
- (b) **Error, excused by an exception.** A new rule id in `COVERAGE_RULES`, 53 approved exceptions renewed at
  each expiry for a difference no one can remove; the exception mechanism (decision 0020) would carry a check
  that is not a coverage rule.
- (c) **Warning, every system, no exception.** As A1 (decision 0018). `main` stays green, but carries 53
  permanent warnings that drown the ones a reviewer must read, and the check fires usefully on nothing.
- (d) **A per-system level** (`name_check = "error" | "warning"`). Chooses how loud the finding is, not whether
  it means anything: the kit at `warning` is (c) again.
- (e) **Warning, no exception, only where the export names concepts**, declared per system (`export_names`).
  The 53 become unchecked with their reason and denominator; every system that can carry a rename is checked.

## Opportunity canvas

- **Problem:** the contract says `name` is checked; nothing checks it. A rename in ARIS would leave the
  register's name, the one field it repeats, silently wrong; decision 0022's measured rename (PROC-0004 in
  knowgov's fixture) would go unreported. Checking an export that names documents reports only noise.
- **Who is served:** a reviewer of a pull request that lands an export; pumllint `trace`, whose inventory
  carries a node's `name` beside its id (`tools/inventory.py`); an adopter adding a system, who says once what
  its export names.
- **Solution:** one comparison per node of a `"concept"` system, a warning with both names and the folder; a
  `stale` warning on any system; the unchecked counted by reason with their denominator.
- **What it costs:** one function, one constant pair and one printed line in `check_register.py`; one field
  on six systems; five tests; a README section. No warning added on `main`.
- **How we know it worked:** a renamed id in a later `"concept"` export prints one `name` warning naming both
  names; a vanished id prints one `stale` warning and no `name` warning; the counts add up to the denominator;
  the warning count on `main` is unchanged.

## Fit/gap

| it must | fit or gap |
|---|---|
| `name` checked against the latest export, not authored | fit for `"concept"` systems, latest folder by date. Gap, accepted: the 57 kit nodes are unchecked, because their exports carry no names to check against |
| a node file never copies a tool's attributes | fit: nothing is written to a node; the check reads only |
| exports append-only | fit: nothing writes an export; a fix is a new folder |
| a vanished id is `stale`, never a deletion | fit: a `stale` warning on every system, no `name` warning, no file touched |
| coverage reported with its denominator and exceptions | fit: matched over checked, unchecked by reason over all with a `[source]`; no exception exists for this check |
| exceptions excuse coverage rules and expire | fit: untouched, (b) refused |
| a metamodel field needs a decision record | fit: this record adds `export_names` and says what each value means |
| the 53 kit differences reported | fit: measured above and counted on every run as unchecked by reason, never as warnings |
| a difference blocks the content it concerns | gap, accepted: a warning does not block; a reviewer reads it. An error is revisited below |
| a part of a document checked | gap, accepted: unchecked and counted |

## SWOT

- **Strengths:** the contract's sentence becomes true where it can be; `main` keeps its 12 warnings; the same
  code serves `aris` from its first folder with decision 0022's name; the kit's 53 stay visible as a count with
  a reason.
- **Weaknesses:** a field a person sets: a system declared `"document"` by mistake is never name-checked; a
  warning can be merged past; a part is never checked.
- **Opportunities:** a kit export that keyed concepts (a new folder, a new manifest shape) would move the kit
  to `"concept"` with one line; once a `"concept"` export lands, an error level becomes measurable.
- **Threats:** reviewers learn to skip `name` lines if a `"concept"` export proves noisy; an export whose names
  come from another field than the one the register treats as `name` would differ on every node.

## Advice

Approve (e): a warning, no exception, on systems whose export names concepts, declared in `export_names`. The
reasons:

- The one measurement says the kit's 53 differences are structural: a document cannot carry the names of the
  up to eight nodes that point into it. Neither side is wrong, and no remedy exists on either.
- (c), the first draft's advice, turns 12 warnings into 65 that fire usefully on nothing and hide the ones a
  reviewer must read. (e) keeps `main` at 12 and reports the 53 as a count with a reason.
- Against the first draft's objection to a metamodel field before it has a use: `export_names` has its use on
  the first run. It is what makes the check mean anything. (d) does not: it sets loudness, not meaning.
- Error and (b) as before: 53 unfixable errors, or exceptions excusing a check that is not a coverage rule.
  A1 (decision 0018) set the precedent for a finding a reviewer reads and the merge does not gate.

Revisit at the first `aris` export: if every difference there is a rename or a typo, supersede this record
with one that makes a `name` difference an error for `"concept"` systems, measured on that export.

## Built in this pull request

- `metamodel/sources.toml`: `export_names` on all six systems.
- `tools/check_register.py`: `check_names` (`NAME_LEVEL = "warning"`, `EXPORT_NAMES`), on the
  `_latest_export` decision 0023 added; `summary["names"]` and one printed line.
- `tests/test_register.py`: `NameCheck`, five tests on synthetic `aris` folders and the register (a match; a
  difference, read from the latest of two folders; a system with no export, then its first folder; a vanished
  id; the kit systems unchecked and a missing `export_names` refused); 40 tests.
- README "The checks", METAMODEL.md "Required fields", CLAUDE.md's test count.
- No node, link, export or exception changes. No matrix row and no relationship type moves.
