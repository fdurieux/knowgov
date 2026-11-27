# 0022 — A process node points at its function's definition, and the register id rides on it

Date: 2026-11-27. State: approved (fdurieux, in the maintainer's chat on 2026-11-27: "approve 0022 and 0023"; recorded on the pull request before its merge; the line read proposed when drafted). Drafted by a session, which never approves, decision 0019; raised by #38.
Supersedes: nothing. Settles what `metamodel/sources.toml` `[system.aris]` `id_field = "aris_guid"` names for a
`process` node, which the file has left open since decision 0001. The name check (#39) waits for it.

## Decision

1. **The definition.** A `processes` node whose `[source]` `system` is `aris` points at exactly one function
   definition (AML `ObjDef` of type `OT_FUNC`; report API `ObjDef`). `aris_guid` is that definition's GUID: never
   an occurrence (`<guid>#<index>`), never a model's GUID. The same holds for every process kind (`process_domain`,
   `end_to_end_process`, `subprocess`, `activity`). One node, one definition. One definition carries at most one
   register id.
2. **The model is the diagram.** The EPC model that details a process is its diagram of record. `[source]`
   `diagram` is that model's GUID. For a definition with an assigned model (report API `ObjDef.AssignedModels`;
   AML `LinkedModels.IdRefs` in knowgov's fixture), it is that model. For an activity, it is its parent's model of
   record. A model's own attributes, its name and any `AT_ID`, are not identity, and no consumer reads a register
   id from a model.
3. **The attribute.** The register id is written into ARIS on that definition, in the attribute that `sources.toml`
   `[system.aris]` `register_id_attribute` names. In this test case that is `AT_ID`. An organisation's instance may
   name another, as knowgov's `connectors.toml` `id_attribute` already allows. The value is copied from the register,
   never minted in ARIS. The GUID stays the join the register keys on. The attribute lets a consumer that reads ARIS
   without the register carry the id: the diagram footer, or a BPMN export. Both records of the join must agree. A
   definition whose attribute names a register id other than that of the node whose `aris_guid` is its GUID is a
   finding, fixed by hand, never automatically.
4. **What each consumer reads.**

   | consumer | reads | today |
   |---|---|---|
   | aris2puml, footer `ARIS process <id>` | the attribute of the function definition the EPC is assigned to; else that definition's GUID | the model's `AT_ID`, else the model's GUID (`aris/export_epc.js:135`) |
   | aris2puml, footer `interfaces:` | the attribute of the interface occurrence's own definition; else its GUID | the assigned model's `AT_ID`, else its GUID (`:89-90`) |
   | knowgov `tools/connector.py` | the attribute on every `ObjDef`; `[ids]` keyed by `ObjDef` GUID | the same: no change of identity |
   | `tools/reconcile.py` | `[ids]` by `aris_guid`, as for every system | the same: no change of identity |
   | the name check (#39) | the name the latest `aris` export's `[ids]` gives the node's `aris_guid`: the definition's name | no check exists |

5. **Unverified.** No row of `mapping/matrix.toml` moves; `processes` stays `unverified`. No node carries
   `system = "aris"` until an export route is tested on a target installation (`exports/README.md`).

## What the sources say, and what they do not

Every ARIS fact below cites a file in aris2puml (at `566cf6f`), knowgov (`b1e98d3`) or pumllint (`9205390`). None
is asserted from elsewhere.

- **aris2puml's report script has never run in ARIS.** The header of `aris/export_epc.js` says so (lines 4-17),
  and so do ROADMAP A1 and A1b (adopter-gated, open). The header lists `ObjDef.AssignedModels` as confirmed
  statically against the ARIS Report Scripting guide (docs.aris.com, 10.0.27) and `AT_ID` as unconfirmed.
  - The process id is `attr(model, AT_ID) || model.GUID()` (`:135`). `emit.py:213` writes it as
    `footer … — ARIS process <id>` (README "What comes out", the row "process name, id, owner").
  - An interface's `ref` is the `AT_ID` of the first model its definition is assigned to, else that model's GUID
    (`:89-90`). ROADMAP B4 put these refs in the footer for `pumllint trace --fail-on-unknown-ref`.
  - The script's own node ids are `<ObjDef GUID>#<n>` (`:72`): definitions, with the occurrence as an index.
- **knowgov's connector reads definitions only.** `read_aml` (`tools/connector.py:108-135`) reads the configured
  attribute (default `AT_ID`, `:59`, `:98`) on every `ObjDef`. Its MANIFEST keys `[ids]` by `ObjDef` GUID, knowgov
  decision-0010 (a3). It never reads a `Model` element's GUID or attributes.
- **knowgov's fixture is synthetic.** `tools/aris_export.py` says its type names are "UNVERIFIED against any ARIS
  method filter or installation". Its contents, read from `tools/fixtures/aris_cargo_quote/first/cargo_quote.aml`:
  - one `MT_EEPC`, "Quote process" (`5493b5d5-…`), with no `AT_ID`;
  - PROC-0001 on an `OT_FUNC` definition (`9d515a4c-…`) whose `LinkedModels.IdRefs` names that model;
  - PROC-0002 to PROC-0005 on step functions inside it.

  It follows point 1 already. Read against `export_epc.js:135`, the script would write `5493b5d5-…` in the footer
  where the connector reads PROC-0001. That is #38's divergence, shown in code. It has not been measured in ARIS.
- **One observation exists on a real ARIS, for BPMN only** (knowgov task-0119, the maintainer's round trip of
  2026-11-04, ARIS 10.0, once):
  - process ids and element `<documentation>` survived an import and export;
  - every other element id was replaced;
  - two exports of the imported model were byte-identical;
  - a re-import or a copied model was not tested.

  Nothing was observed about AML, report scripts, the GUIDs of definitions or models, or `AT_ID`.
- **pumllint.** `trace` reads ids by the requirement-link pattern from the diagram name and its title, header,
  footer, caption and notes (`pumllint/cli.py:161-170`). The proposal says `aris_guid` is "the definition GUID; an
  occurrence is `<guid>#<index>`" (`docs/ieam-register-proposal.md:152-153`, §2.2). It also says "the register
  points at definitions" (`:374`, §6).
- **Unverifiable from these sources:**
  - whether the target installation assigns every EPC to a function definition;
  - whether one EPC can be assigned to more than one definition. The API returns a list and the script takes the
    first (`:89-90`); the converse is not documented here;
  - which report call reaches a model's definition from the model: none of the script's confirmed names does;
  - whether `AT_ID` is free in the target installation, or already holds the organisation's own numbering;
  - whether copying a definition copies its attributes;
  - whether a GUID survives a re-import, a consolidation or a move to another database.

## Measured

The two choices were compared on a temporary copy of the register at `be01dfc`. PROC-0001 to PROC-0005 were given
`[source] system = "aris"`. Two manifests were written from knowgov's `first` and `later` AML in its decision-0010
(a3) shape: every `ObjDef` by GUID, with its `AT_NAME`. `tools/reconcile.py` ran unchanged. Under (a), only
PROC-0001 takes the model's GUID. The activities have no model, so they take their function's GUID under both.

| choice | export | ids | `stale_nodes` | `unregistered` |
|---|---|---|---|---|
| (a) the model | first | +41 | PROC-0001 | 37 |
| | later | ~1 −3 | PROC-0001, PROC-0005 | 35 |
| (b) the definition | first | +41 | none | 36 |
| | later | ~1 −3 | PROC-0005 | 34 |

Under (b), the only stale node is the one `later` deletes. Under (a), PROC-0001 is stale on every export, a false
finding: the connector's `[ids]` carries no model. The renamed id (~1) is PROC-0004, "Price the quote" in `first`
and "Calculate the quote price" in `later`. That is the case #39's check will report, and it reads the definition's
name.

## Options

- **Where `[source]` points.**
  - (a) The EPC model: what aris2puml reads today. An activity has no model of its own, so (a) needs the
    definition for activities anyway, and becomes (c).
  - (b) The function definition, for every process kind: what knowgov reads, and what the proposal's §2.2 states.
  - (c) Either one, named per node by a new `[source]` field. That puts two key spaces under one `id_field`, so
    every consumer must carry models and definitions in `[ids]`, and the name check must branch.
- **Where the register id sits.**
  - (i) `AT_ID`: what both tools read, and an unconfirmed name.
  - (ii) An attribute of the organisation's own: avoids a clash with an `AT_ID` already in use.
  - (iii) GUID only, no register id in ARIS. The footer is written inside ARIS by the report script, which cannot
    read the register, and `trace` matches `PROC-\d{4}`, not a GUID. The one carrier observed to survive ARIS
    (BPMN `@id` and `<documentation>`, task-0119) carries only what is typed into ARIS.

The decision is (b), with the attribute named per instance: (i) by default, (ii) where the organisation chooses.

## Opportunity canvas

- **Problem:** one process carries two ids depending on which tool read the export: the model's for aris2puml and
  pumllint `trace`, the function definition's for knowgov. The divergence surfaces as false stale findings and an
  unchecked name as soon as `exports/aris/` holds a folder.
- **Who is served:**
  - pumllint `trace` users, whose footer id must be the register's;
  - knowgov, whose connector already keys definitions;
  - the register's reconciliation and the name check (#39);
  - an adopter's ARIS administrator, who gets one attribute on one kind of definition to fill.
- **Solution:**
  - one pointer per process node, the function definition's GUID;
  - the model as the process's diagram;
  - the register id copied onto the definition in a named attribute, checked against the register.
- **What it costs:**
  - two keys in `sources.toml` and a METAMODEL.md sentence, here;
  - follow-ups in aris2puml (one call to confirm at A1b), in `reconcile.py` (an agreement section, with its own
    record) and in #39;
  - in each organisation: the attribute filled by hand on each process definition, and kept in step.
- **How we know it worked:** on one target-installation export, every process node's `aris_guid` is among
  `[ids]`. The footer of each converted EPC carries the same register id as the connector reads for its definition.
  `stale_nodes` names only definitions that vanished.

## Fit/gap

| it must | fit or gap |
|---|---|
| ids minted here, never reused, never encoding hierarchy or organisation | fit: the attribute holds the bare register id, copied from the register; ARIS mints GUIDs, never register ids |
| a node file never copies a tool's attributes; `name` the one repeated field, checked against the latest export | fit: `aris_guid` and `diagram` are pointers; ARIS holds a copy of the register's id, not the reverse; `name` is checked against the definition's name |
| one concept, one external record (proposal §2.2) | fit: one definition per node. Gap, accepted: the model's name and the definition's name may differ. The footer's `title` is the model's name (`export_epc.js`, `name: model.Name(-1)`); the check reads the definition's |
| exports append-only | fit: nothing here writes or rewrites a folder |
| a vanished external id is `stale`, never a deletion | fit, measured: under (b) only a deleted definition is stale; under (a) the model reads stale on every export |
| support status starts and stays `unverified` | fit: no matrix row and no relationship type moves |
| the footer carries the register id `trace` reads | gap until aris2puml's follow-up: today it carries the model's `AT_ID`, else the model's GUID |
| every consumer reads one id per process (#38) | fit once the follow-ups land; the connector and `reconcile.py` already do |
| an EPC that no definition has assigned | gap, accepted and unverified: such a process has no pointer under (b); the target-installation test is to count them |
| the two records of the join (`aris_guid` here, the attribute in ARIS) agree | gap: no check yet; `reconcile.py`'s follow-up reports a disagreement |

## SWOT

- **Strengths:**
  - one key space for every ARIS process kind, the one `[ids]` already uses;
  - activities need no special case;
  - knowgov's connector and fixture already conform;
  - it says what the proposal's §2.2 already said;
  - the measured stale list is correct.
- **Weaknesses:**
  - the attribute is hand-filled and can be mistyped or duplicated;
  - aris2puml must reach a model's definition through a call not yet confirmed;
  - the footer's title (the model's name) and the checked name (the definition's) can drift apart.
- **Opportunities:**
  - the same rule can extend to capabilities, applications and units, which knowgov's fixture already places on
    definitions (`OT_FUNC`, `OT_APPL_SYS_TYPE`, `OT_PERS_TYPE`, synthetic);
  - the agreement check makes "which ARIS definition is PROC-nnnn" answerable in one read.
- **Threats:**
  - the target installation may keep EPCs unassigned, or reuse one model under several definitions, which (b) does
    not cover; the remedy is a superseding decision, not a per-node field;
  - `AT_ID` may already be in use there, which is why the attribute is the instance's to name.

## Advice

Approve (b), with the attribute named per instance and `AT_ID` by default. The reasons:

- An activity has no model, so (a) needs definitions anyway and becomes (c). (c) doubles the key spaces in every
  consumer for a flexibility no one has asked for.
- The connector already keys definitions, and the proposal already said so. (b) changes one script and no record.
- The measurement shows (a) giving a false stale finding on every export.
- (iii) cannot feed a footer that is written inside ARIS.

Revisit when A1b runs on the target installation. If unassigned EPCs or shared models turn out to be the norm there,
supersede this decision with a record that measures them.

## Follow-ups, not made in this pull request

- **aris2puml** (`aris/export_epc.js`):
  - `process.id` becomes the register id attribute of the function definition the selected EPC is assigned to,
    else that definition's GUID. Where no definition has the model assigned, it stays the model's GUID as today,
    with a warning, so GEN007 still fires.
  - An interface's `ref` becomes `attr(def, …) || def.GUID()` on the interface occurrence's own definition, a
    confirmed call.
  - The attribute becomes a constant at the top of the script, not a hard-coded `Constants.AT_ID`.
  - The call that reaches a model's definition from the model is unconfirmed: one more name for A1b.
  - The JSON contract and the footer format `ARIS process <id>` are unchanged, so the golden diagram does not move;
    the README row says where the id now comes from.
- **knowgov's connector:**
  - Identity is unchanged.
  - Its stale-by-register-id extension is redundant once an instance's nodes carry `aris_guid`, as knowgov
    decision-0010 already records.
  - Checking `diagram` needs the export's model GUIDs. Those go in a table of the connector's own, never in
    `[ids]`; whether to add one is knowgov's choice.
  - The connector re-vendors at the tag that carries this decision.
- **`tools/reconcile.py`:**
  - `[ids]` by `aris_guid` is unchanged.
  - An additive section, in its own decision record as 0017 was, would report two things. First, each node whose
    `aris_guid` an export maps to another register id. Second, each register id an export carries on a GUID that no
    node holds. Both are read from a GUID-to-register-id table (knowgov's `[register_ids]`).
  - Whether the register's export format adopts that table, and the findings' severity, belong to that record.
- **The name check (#39):**
  - An `aris` process node's `name` is compared with the name the latest `aris` export's `[ids]` gives its
    `aris_guid` (the definition's name), never with the model's name.
  - Until `exports/aris/` holds a folder, `aris` nodes are unchecked and counted with their denominator, as #39
    says.

## Not decided here

- The ARIS pointer of a capability, an application, a unit, a product or a journey. The proposal's §6 leaves
  journeys open.
- Links at occurrence level (`#<index>`).
- Whether `diagram` is checked against an export.
- What a disagreement under point 3 is: an error or a warning. That belongs to `reconcile.py`'s follow-up record.

## Built in this pull request

- `metamodel/sources.toml` `[system.aris]` gains `process_definition` (point 1's rule, in a sentence) and
  `register_id_attribute = "AT_ID"`. No tool reads either yet.
- METAMODEL.md gains one sentence under "Required fields".
- No node, link, test or tool changes. No matrix row and no relationship type moves.
