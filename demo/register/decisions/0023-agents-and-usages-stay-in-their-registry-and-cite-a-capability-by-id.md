# 0023 — Agents and usages stay in their own registry and cite a capability by id

Date: 2026-11-27. State: approved (fdurieux, in the maintainer's chat on 2026-11-27: "approve 0022 and 0023"; recorded on the pull request before its merge; the line read proposed when drafted). Drafted by session_01HTAA1RXdnjtz75m4FvtKDG, dispatched by
session_01HTAA1UV2N6XGtCwCvVnB5t on fdurieux/ieam-register#40; a session never approves (decision 0019).
Supersedes: nothing. Adds one glossary term, *inbound reference*; proposes a system without a taxonomy in
`metamodel/sources.toml`, a `[cites]` table in an export's `MANIFEST.toml` and one warning-level check.
Decisions 0001 (exports append-only), 0004 (one register per organisation), 0017 (`unregistered`) and
0020 (C1 to C4, exceptions) stand.

## The question

An agent-registry framework keeps its own registry as the system of record for AI agents: one agent record
per version of an agent, and one usage record per usage, each usage being one way the agent is put to work. Each has an
opaque identifier its registry owner assigns at registration and never reuses. A usage names the business
capability it serves by identifier, required for some usages and optional for others; where the
organisation keeps a capability register, the framework makes that register authoritative for the
identifier, and a usage citing an id the register does not hold is wrong. Where it keeps none, the framework keeps a
provisional list of its own, mapped to the register's ids once one exists. The framework has its own
lifecycle for a usage (stages and gates, each with named approvers), its own status for an agent version,
and its own completeness check, run by its registry owner, that a usage's capability identifier exists in
the capability register.

This register mints `CAP-` ids and never reuses them. Nothing joins the two: no kind here for an agent or a
usage, no relationship type that reaches one, no export from the agent registry, and the framework's
identifiers are not of the form `<PREFIX>-<4+ digits>`.

## Options

| | What the register holds | How a usage reaches a capability |
|---|---|---|
| **A. Nodes** | A taxonomy `agents`, prefix `AGN`, kinds `agent` and `usage` (`parent` from usage to agent), a `[source]` pointer to the agent registry and a relationship type from a usage to a capability, as ARIS's processes and Archi's applications are held | A link in `relationships/`, minted, owned and approved here |
| **B. Links with an external source** | No node; a relationship type whose source is outside the register, the mirror of `maps_to` (`target_external`): one link per usage, `source_external` the usage's id, target a capability | A link minted and approved here |
| **C. An inbound reference, read from an export** *(advised)* | No node, no link. The agent registry delivers a dated export of its usages and the capability id each cites to `exports/agent_registry/<date>/`; the checker reads the latest and reports | The usage's own field, in its own registry |
| **D. Nothing** | Nothing. The agent registry reads the register's capabilities; the register knows nothing of usages | The usage's own field, unseen here |

ARIS and Archi author content the register holds as nodes: the pointer runs from the register to them
(`[source]`), and their exports are checked against the nodes that point at them. The agent registry
authors records the register does not hold, and the pointer runs the other way: from a usage to a `CAP-`
id. Option C keeps that direction and gives the register sight of it; A and B turn it round.

## Opportunity canvas

| Block | Content |
|---|---|
| Users | Capability owners deprecating or re-parenting a capability; the agent registry's owner, running its completeness check; portfolio leads asking which agents a capability depends on and where two agents serve one capability; a consumer such as knowgov |
| Problem | A usage names a capability by an id the register mints, and the register cannot see it. A deprecation here is silent to every usage that cites the capability; a provisional or mistyped id is found, if at all, by the other registry's check alone; no one can ask the register which usages rest on a capability |
| Solution | The usage's capability id stays where it is authored. The agent registry exports its usages' references, dated and append-only, as any source exports; the checker resolves each against the register's nodes and reports the result with its denominator. The register mints nothing for an agent or a usage and approves nothing of either |
| Value | A capability's deprecation names the usages that cite it in the pull request that makes it. An unknown, unapproved or withdrawn capability id is visible here and fails where it is authored. Overlap (two usages, one capability) and reach (approved capabilities cited by any usage) are counts in the report |
| Metrics | Per export: usages carried, usages citing, citing an approved capability, citing an unapproved or withdrawn one, citing an id that is no node. Approved capabilities cited, out of all approved capabilities, reported and never a rule |
| Cost | One system entry with no taxonomy, one manifest table, one warning-level check and its summary, a `reconcile.py` branch, tests, one glossary term. No node, no relationship type, no id prefix. On the other side, an export on a stated cadence and one word in its check |
| Risks | The export lags the agent registry, so the register reports yesterday's references; the other side's check is not tightened and a usage keeps citing a withdrawn capability; warnings read as noise and are ignored |

## Fit/gap against what it must satisfy

| Contract (CLAUDE.md) | A. Nodes | B. External-source links | C. Inbound reference *(advised)* | D. Nothing |
|---|---|---|---|---|
| **Ids** minted here, never reused, never encoding hierarchy or organisation | **Gap.** The agent registry already mints an agent's and a usage's id. `AGN-` ids would be a second identity for each; adopting the opaque ids instead breaks `ID_RE` | **Fit** for the `REL-` ids; the usage's id stays external | **Fit.** Nothing new is minted. A usage's id lives in an export only, as an ARIS GUID does | **Fit** |
| **A node never copies a tool's attributes** | **Gap.** `state` would copy the usage's stage or the version's status, which `lifecycle.toml` has no states for; `owner` the usage's business owner; the register has one node per id and the framework one record per agent version. Two records the moment it lands | **Gap, smaller.** The link's `state` and `owner` restate the usage's | **Fit.** The manifest carries ids and references, as `[ids]` carries ids and names; no node file changes | **Fit** |
| **Approval is a file-state change**, both owners on a cross-domain link, the approver never the author | **Gap.** A second approval of what the framework's gates already approve, by other approvers, or a copy of theirs | **Gap.** The same, once per link | **Fit.** The register approves nothing of a usage; an export lands by pull request as every export does | **Fit** |
| **Deprecating a node fails every approved link that references it**; nothing is fixed automatically | **Fit**, natively | **Fit**, natively | **Fit, with the failure where the fix is.** The register reports each citing usage at the deprecated capability; the usage fails in its own registry's check (the follow-up below). Nothing is changed automatically on either side | **Gap.** Silent here; found there at its next check, if that check reads state |
| **Coverage is reported with its denominator and its exceptions** | **Fit**, by a new coverage rule | **Fit**, by a new coverage rule | **Fit.** Usages carried, citing, resolving to an approved capability; no rule, so no percentage to pass | **Gap.** No denominator here |
| **Exceptions expire** | A coverage rule on usages needs exceptions for the usages the framework leaves optional: the framework's rule restated here | The same | **Fit, unchanged.** No coverage rule is added and no exception is needed: the register asks nothing of a usage | n/a |
| **Exports are append-only**; a vanished external id is a `stale` finding, never a deletion | **Fit** | **Fit** | **Fit.** A later export is a new folder; a usage that leaves it is a removed reference in `RECONCILE.json`, a finding against no node | n/a |
| Standard library only; synthetic content in this repository | **Fit** | **Fit** | **Fit.** The test case's export, at the build, carries synthetic usages only | **Fit** |

## SWOT (option C)

- **Strengths.** Each fact has one record: the usage's capability in the agent registry, the capability in
  the register. No id form, lifecycle or approval is bent to fit the other system. It uses the register's
  own route for outside content, a dated, append-only export with a manifest, and reports as decision 0017's
  export counts do.
- **Weaknesses.** The register sees the references only as fresh as the last export. A deprecated
  capability raises a warning here, not an error, so a pull request can deprecate a capability that live
  usages cite. The register cannot make the other side tighten its check.
- **Opportunities.** "Which agents does this capability depend on" becomes a count in the report and,
  later, a reach of the impact walk. The same route serves any other registry that cites the register's
  ids without authoring its content.
- **Threats.** Exports stop arriving and the reported references go stale unnoticed; the warning is read as
  noise. *Response:* the summary names the export's date beside its counts, as `export_counts` does; a
  review of the cadence belongs to the agent registry's owner.

## Advice

**Option C. Approve.**

1. **The usage's capability is the agent registry's fact.** It is authored there, approved at that
   framework's gates by its own approvers, and versioned with the usage. A node or a link here would be a
   second record of it, and every contract that A and B break (ids, copied attributes, approval) breaks for
   that one reason.
2. **The framework already points the right way.** It names the capability register authoritative for the
   identifier, and a usage defines no capability of its own. Nothing on its side has to move for that to hold; it
   needs only to deliver the export and to read state as well as existence.
3. **A warning here, an error there.** An error in this register for another registry's content would make
   every merge here wait on that registry's next export, the one thing no pull request here can fix, and
   would refuse an export the register is bound to mirror. The usage fails where its owner can correct it.
   A capability owner sees, in the deprecating pull request, which usages to tell.
4. **D is too little.** It leaves a deprecation silent and gives no denominator; C costs one check more.

## What the checker would hold

Built after approval, in one pull request, as decision 0021 was:

1. **The system.** `metamodel/sources.toml` `[system.agent_registry]`: `id_field = "usage_id"`,
   `authoritative_for = []`, `cites = ["capabilities"]`. An empty `authoritative_for` means no node may
   name the system in `[source]`: `check_nodes` already refuses a source not authoritative for the node's
   taxonomy.
2. **The export.** `exports/agent_registry/<date>/MANIFEST.toml` with the fields every manifest carries,
   `[ids]` mapping each usage the registry has not retired to a label, and `[cites]` mapping a usage's id to
   the one register id it cites. A usage that cites nothing has no `[cites]` row. The manifest carries no
   stage, owner, version or other field of a usage.
3. **`tools/reconcile.py`.** For a system with an empty `authoritative_for`, `stale_nodes` and
   `unregistered` are empty by definition and are not computed. `RECONCILE.json` gains `references`, the
   `[cites]` rows added, changed and removed against the previous folder.
4. **`tools/check_register.py` `check_inbound`**, on the latest export of each system with `cites`:
   - an error for the manifest's own shape only: a `[cites]` key absent from `[ids]`; a `[cites]` table for
     a system without `cites`;
   - a warning, `inbound`, at `capabilities/<id>.toml` where the node exists and at the manifest otherwise:
     a cited id that is no node (a provisional or mistyped id); a node outside the taxonomies `cites`
     lists; a capability `draft`, `proposed` or `rejected` (not yet approved); a capability `deprecated` or
     `retired` (withdrawn). Any kind of the capabilities taxonomy may be cited;
   - a summary `inbound`, per system: the export, its denominator (usages carried), citing, citing an
     approved capability, not yet approved, withdrawn, no node; and the approved capabilities cited, out
     of all approved capabilities. One printed line per system. Not a coverage rule: no exception applies
     and no percentage is a pass.
5. **Tests** for each finding, the denominator, a deprecation on a copy, and a node whose `[source]` names
   the system; README "The checks"; METAMODEL.md, one paragraph; CLAUDE.md's test count.

Illustrated on a synthetic export of four usages against the register as it stands: one cites `CAP-0003`
(approved), one `CAP-0005` (proposed), one an id no node carries, one nothing. Summary: 4 carried, 3 citing,
1 approved, 1 not yet approved, 0 withdrawn, 1 no node; 1 of 7 approved capabilities cited. Two warnings,
no error. `CAP-0003` deprecated on a copy: the first usage moves from approved to withdrawn and its warning
stands at `capabilities/CAP-0003.toml` beside the lifecycle errors of the approved links that reference it.

## Follow-ups, in their own repositories

- **The agent-registry framework.** Two changes, neither a new field nor a new id form:
  1. its completeness check on a usage's capability identifier, where the organisation keeps this
     register: the id is a capability that exists **and is approved** there; a usage whose capability the
     register has deprecated or retired fails the check at its next run, and its owner moves it to the
     replacing capability;
  2. its registry owner delivers the export above (each usage not retired, its id, the capability id it
     cites, nothing else) to the register's `exports/agent_registry/<date>/`, on a cadence the framework
     states. The framework already produces every other description of an agent from its registry;
     the export is one more.

  Its provisional list is unchanged: once mapped to register ids, the export carries register ids.
- **knowgov.** Nothing required. A reader of the `inbound` summary, if knowgov wants the usages that rest
  on a capability beside it in its view; its choice, at a re-vendor of its choosing.

## Not decided here; left to later records

Whether `tools/impact.py` names the usages citing a reached capability beside its owner (who to tell), as
`owns` is shown and not walked. Whether an instance runs the `inbound` warnings as errors. Whether an agent
record, as against a usage, ever cites a register id. Whether a usage's place in a process or a journey is
exported as register ids: the framework names those in the host flow's own terms, not by id. Whether
*agent* and *usage* become glossary terms: they are the framework's, and the register holds neither.

## Built in this pull request

This record and the glossary term *inbound reference* (`glossary/glossary.toml`), with its forbidden
synonyms. No tool, test, node, link or metamodel file changes.
