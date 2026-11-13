---
id: decision-0041
title: >-
  After 1.0.0: the contract-bearing residues of the 0.9.x fixes wait for 1.1.0,
  so the 30-day soak is not restarted (task-0342)
date: '2026-11-13T22:13:00Z'
status: accepted
---
## Context

task-0342 holds the contract-bearing residues of the 0.9.x fixes (task-0311 to task-0315, task-0323, task-0329). The fix-only sessions left them unfixed because each needs a contract change. The re-checks confirmed each. Every one is additive: an optional field, a new reader or a new setting. The exception is B-N9, which would change the output of an existing MCP tool.

decision-0016 point 2 makes any contract change after 0.9.0 a 0.10.0 that restarts the freeze. Amendment A1 condition 2 cuts 1.0.0 only after the 0.9 contracts have held for 30 days from 0.9.0 (2026-11-12), across at least one 0.9.x patch release, with no contract change. Point 7 makes an additive contract change after 1.0.0 an ordinary minor release.

The items:
- **C5-1** (task-0313): no reader lists RECONCILE.json's stale nodes with their owners.
- **B-X2 and R-T1** (task-0314): `register_impact` answers a start whose kind has no step in the walk with no edges and no word, and the schema is closed. Mitigated in 0.9.x: the tool's `walk` description, and the page's panel.
- **B-X8** (task-0314): `store_status` does not name the stage of what it holds, and the schema is closed. Mitigated in 0.9.x: the description points to the gate report's `version`, and code_path's reason names it.
- **B-N9** (task-0329): `register_impact` with `children` repeats an edge once per descendant. That is the vendored register walk's own behaviour (`impact.walk_children`), which the MCP tool, the page and the Browser Cypher hold equal to.
- **B-N2** (task-0329, part): the CI template passes no previous register. `KG_REGISTER_PREVIOUS` is already the page's setting, so giving it an effect in `knowgov-gate.sh` would re-stale keys on every CI run of an instance that set it for the page.
- **C2-7** (task-0315, part): a stale digest names no file it came from, which needs the digest's provenance stored.
- **N-3** (task-0329), a known-limits candidate: plant-derived digests listed in a manifest trigger check_subject's unchanged-code note after an honest relist.

## Options and choice

- **(a) Build them now as 0.10.0.** Every item lands within days, but the freeze and the 30-day soak restart. 1.0.0 then moves to at least 30 days after 0.10.0.
- **(b) Defer the additive items to 1.1.0, after 1.0.0.** Settle B-N9 in the register first, document B-N2, and name N-3 a known limit now. The soak runs on, and each additive item later costs one minor release under point 7.
- **(c) Decline them all.** No cost, but C5-1 and C2-7 are real gaps an adopter will meet.

**Chosen: (b)**, by the maintainer on 2026-11-13: "go with recommendations on task-0342". Per item:
- **C5-1: deferred to 1.1.0.** A reconcile reader (CLI and MCP) listing stale nodes with their owners. A new tool is an additive change.
- **B-X2 and R-T1: deferred to 1.1.0.** An optional `note` on `register_impact`. The 0.9.x mitigations stand meanwhile.
- **B-X8: deferred to 1.1.0.** An optional `stage` on `store_status`. The 0.9.x mitigations stand.
- **B-N9: deferred to ieam-register.** The repetition is the register walk's own, so a fix starts as a register decision there. knowgov follows by re-vendoring. Since that changes an existing tool's output, it comes after 1.0.0 under point 5's deprecation rule if it is breaking, or point 7 if it is not.
- **B-N2: documented; a gate-only setting is deferred to 1.1.0.** instance/README, "After a register update", already says the CI template does not pass a previous register. It also says how to run `gate_cli.py --register-previous DIR` once when an update lands, and when to stop passing it. `KG_REGISTER_PREVIOUS` keeps its single, page-only effect.
- **C2-7: deferred to 1.1.0.** Storing the digest's provenance so that the error names the file a stale digest was last recorded for.
- **N-3: a known limit.** It is named under `## Unreleased`'s Known limits now, and carried into 1.0.0's Known limits.

## Opportunity canvas

| Box | Content |
|---|---|
| Problem | Seven contract-bearing residues wait on a decision, and building any one now restarts the 30-day soak towards 1.0.0 |
| Users | The maintainer, whose 1.0.0 date the soak sets. An adopter, who meets the gaps (no reconcile reader, an unnamed stale file) and gets the 1.0 deprecation promise sooner |
| Proposal | (b): the additive items wait for 1.1.0, B-N9 goes to the register, B-N2 is documented, and N-3 is named a known limit |
| Unique value | 1.0.0 keeps its earliest date, and every residue keeps an owner and a release |
| Cost | Each additive item waits at least 30 days; C5-1's and C2-7's gaps stay open until 1.1.0 |
| Risk | A lighthouse needs one of these before 1.1.0. After 1.0.0 it is one minor release away, not a restarted freeze |

## Fit/gap

| Must satisfy | Fit | Gap |
|---|---|---|
| decision-0016 point 2: 0.9.x carries fixes only | no contract change in 0.9.x | none |
| decision-0016 A1 condition 2: 30 days with no contract change | the soak runs on | it still needs a 0.9.x patch release within the 30 days |
| decision-0016 point 7: after 1.0.0, additive is a minor | the deferred items are additive | B-N9 changes an existing output, so it falls under point 5 if breaking |
| A1 condition 4: Known limits name what is unproven | N-3 is named | none |
| The register owns its walk (ieam-register's decisions) | B-N9 goes there first | a register decision is not yet drafted |

## SWOT

- **Strengths**
  - 1.0.0 keeps its earliest date.
  - No residue is lost: each has an owner and a release.
  - The 0.9.x mitigations already answer the confusion in B-X2, R-T1 and B-X8.
- **Weaknesses**
  - C5-1's and C2-7's gaps stay open for at least a month.
  - 1.1.0 starts with a batch.
- **Opportunities**
  - A lighthouse's first weeks on 1.0 can reorder the batch by what it actually needs.
- **Threats**
  - A lighthouse that needs a reconcile reader at once is asked to wait, or to read RECONCILE.json directly.

## Advice

(b), for three reasons:
- Every item is additive or mitigated, so none blocks an adopter on 0.9.
- Building any of them now buys days on a gap and costs at least 30 days on 1.0.0.
- After 1.0.0 the same changes are ordinary minor releases with a deprecation promise around them, which is what a lighthouse needs.

## Consequences

- task-0342 moves to 1.1.0. Its acceptance criteria now read "built in 1.1.0".
- N-3 joins the Known limits.
- No build is dispatched before 1.0.0.
- A1's soak still needs one 0.9.x patch release within the 30 days. The fixes since 0.9.0 are under `## Unreleased`, ready for 0.9.1.
