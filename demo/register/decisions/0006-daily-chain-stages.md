# 0006 — The daily chain's stages, read from the chain contract

Date: 2026-11-01. State: approved (fdurieux, by the merge of #6 on 2026-11-01; the line read proposed when merged). Supersedes: decision 0005 in
one reading only, the daily chain's; everything else of 0005 stands.

## Decision

Decision 0005 read the daily chain as three steps, sync, check and publish, and had the chain
deliver the seam frame. The chain contract (`jef_kit:contracts/chain.md`, JDL-146 to JDL-158)
and the rebuild's `deploy/daily.sh` say otherwise: the chain's stages are restore the store
from the venue bucket (JDL-154), sync (JDL-155), status (JDL-156), binning per asset
(JDL-157) and, only when every stage passed, upload the store and the run outputs (JDL-158).
The chain never runs the export command; the seam frame is written by `jef-data export` on
demand (`contracts/seam_frame.md`, JDL-071 to JDL-081), outside the chain. The register
now says so:

| change | id | reading |
|---|---|---|
| step deprecated | JRN-0008 Publish the seam frame | no such stage; its link REL-03006 deprecated with it |
| step added | JRN-0009 Restore the store | the chain's first stage (REL-03007, JDL-154) |
| step added | JRN-0010 Bin the assets | the stage after status (REL-03008, JDL-157) |
| step added | JRN-0011 Upload the run | the last stage, on green only (REL-03009, JDL-158) |
| process added | PROC-0010 Seam frame export | the export command run on demand; `jef-data` supports it (REL-06010); it creates the seam frame entity (REL-07009) and delivers the seam frame product (REL-05004) |
| product added | PRD-0005 Daily run outputs | the binning outputs the chain uploads; the chain delivers it (REL-05003); it requires acquiring bars and reporting store health (REL-01008, REL-01007) |
| link deprecated | REL-05002 chain delivers seam frame | false; replaced by REL-05003 and REL-05004 |
| link deprecated | REL-07008 chain creates seam frame | false; replaced by REL-07009 |
| link deprecated | REL-01006 seam frame requires store health | the status gate guards the upload of the run outputs, not the frame; replaced by REL-01007 |

Kept: JRN-0006 Sync the store and JRN-0007 Check the store's health with their links;
REL-02002, the refresh as the operator's path to a current seam frame, since the export reads
the store the refresh keeps current. Ids continue the sequences; nothing is reused. The
deprecated nodes and links keep their files and their 0005 approval, as the lifecycle
provides (`approved -> deprecated`).

## Why

A register link is evidence the knowgov footprint joins on, and a client's instance is created
from this structure. A link that cites a requirement for a stage the program does not have would
be copied into every instance and every footprint. The error surfaced on 2026-11-01 when the
chain requirements no link cites were read against `daily.sh` to place them on a step
(knowgov, `subjects/jef_data_load/register_map.toml`): three of them, restore, binning and
upload, had no step to go to, and the fourth step's name named a stage the script lacks.

## Not decided here

Three citations of 0005 read loosely against the requirement text and are left for the next
review, since they change no node or step: REL-06008 cites JDL-072 (the exported Volume
column's dtype) for the store writing year files; REL-07007 cites JDL-113 (the
classifications file) for the status run reading series; REL-03005 cites JDL-150 (the chain's
timeout re-exec) for the health step. `jef-binning` is a separate program the kit names and
does not specify, so no application node is minted for it; JRN-0010 rests on the chain
process alone.

## What follows

A tag `v0.2.1` on the merge, then knowgov re-vendors `demo/register` at it and places
JDL-154, JDL-157 and JDL-158 on the new steps in the J-F register map.

## Approvals recorded by this decision

Every node and link whose `approval.record` names this file.
