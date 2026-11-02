# 0007 — Three citations of 0005 re-read against the requirement text, and the impact walk follows approved links only

Date: 2026-11-02. State: approved (fdurieux, by the merge of #8 on 2026-11-02; the line read proposed when merged). Supersedes: decision 0006 in
its "Not decided here" paragraph; nothing else.

## Decision

Two corrections, both to the register's reading, neither to its content: no node, state,
relationship type or glossary term changes.

**1. Three evidence anchors.** Each of these links cited a requirement that does not say what
the link's rationale claims; each now cites one that does, and its approval is renewed against
this record.

| link | rationale | cited | the cited text says | now cites |
|---|---|---|---|---|
| REL-06008 (`supports`, APP-0008 store → PROC-0007 sync run) | the store writes each leg's bars, adjusted, into year files | JDL-057, JDL-072 | JDL-072: the *exported* Volume column's dtype, the seam frame's concern | JDL-057, JDL-058 (a year file is written as `.tmp` and renamed atomically, under the series lock), JDL-069 (a re-adjustment rewrites every year file) |
| REL-07007 (`crud`, PROC-0008 status run reads ENT-0008 series) | a status run reads every series and the actions stamps | JDL-107, JDL-113 | JDL-113: the packaged `classifications.toml` file's grammar, not series | JDL-107, JDL-108 (the status checks read the store and the actions store only; no key, no network, no writes) |
| REL-03005 (`is_supported_by`, JRN-0007 health step ← PROC-0008 status run) | checking health is the status run | JDL-150 | JDL-150: the chain re-executes itself under a one-hour `timeout`, a wrapper rule | JDL-156 (the status stage runs `jef-data status`; a requirement may back several links, as JDL-107 does) |

**2. The impact walk follows approved links only.** `tools/impact.py` `walk()` reports every edge
it meets, as before, and marks each `live`: true when the link is approved and the far node is
neither deprecated nor retired. A withdrawn edge is reported, marked, not followed and not
counted among what was reached; `reached()` is the far ends of live edges. Before, the walk
followed every link whatever its state and counted a deprecated node as reached: from
`jef-data` (APP-0005) it listed the deprecated step JRN-0008 "Publish the seam frame" among four
journey elements where the live reading is three. The checker's own finding, an approved link
into a deprecated node, stays visible: such an edge is reported with its states. `draft` and
`proposed` links are not followed either: impact is a question about the architecture as
approved. `tests/test_register.py` pins both: JRN-0008 is not reached and its edge is reported
withdrawn.

## Why

A link's evidence is what the knowgov demo joins on: its register footprint colours a
requirement gap "cited by a link" or not, and its J-F register map names a link's endpoints on
every key the link cites. A loose citation therefore shows a gap as carried by the wrong link
and lights nodes the requirement does not concern. The three were named by decision 0006 and
re-read against `requirements.json` on 2026-11-02; the replacements were cited by no link before
(JDL-058, JDL-108) or already carry the stage by name (JDL-156). The walk's rule surfaced the
same day when the walk from `jef-data` listed the stage 0006 withdrew. The checker does not read
evidence and the walk is not a check: both corrections are the register's reading, recorded.

## What follows

A tag `v0.2.2` on the merge; knowgov re-vendors `demo/register` at it (the copy carries
`impact.py`), revises the three map rows (JDL-072, JDL-113, JDL-150 lose the link endpoints;
JDL-058, JDL-108, JDL-069 gain them), and changes the walk's Cypher and the impact panel's
counts to the same rule, in one pull request.

## Not decided here

A sentence in `METAMODEL.md` saying what a sound citation is: the rationale's outcome is the
cited requirement's statement. Worth its own line when the next slice is cut.

## Approvals recorded by this decision

REL-06008, REL-07007 and REL-03005, whose `approval.record` names this file.
