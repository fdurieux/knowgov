# 0012 — A second, named walk: what realises a capability

Date: 2026-11-04. State: approved (fdurieux, by the merge of #18 on 2026-11-04; the line read proposed when merged). Supersedes: nothing;
answers the question decision 0010 left open, whose rows and default are unchanged.

## Decision

`tools/impact.py` gains `REALISERS`, a second set of walk rows, chosen by `--walk realisers`.
`--walk dependants` (`FORWARD`, decisions 0007 and 0010) stays the default; `walk(reg, start)`
called without rows walks it as before.

| start taxonomy | step | what is reached |
|---|---|---|
| capabilities | `realizes`, inverse | the processes that realise the capability |
| processes | `supports`, inverse | the applications that support those processes |

Applications have no row, so the walk ends at the application that supports a realising process
and never turns back towards what rests on the capability. Decision 0007's rule applies unchanged:
approved links only, a withdrawn edge reported and not followed. `owns` and `maps_to` stay out, as
in 0010; `parent` is not descended.

## What it reaches

Measured with `python tools/impact.py --from <id> --walk realisers` on the register as of this
pull request (base `2b95f43`):

| capability | realisers walk reaches | dependants walk reaches |
|---|---|---|
| CAP-0002 Price a shipment | PROC-0004, APP-0003 | PRD-0002, PROC-0001, JRN-0001 |
| CAP-0003 Screen a shipper | PROC-0003, APP-0004 | PRD-0002, PROC-0001, JRN-0001 |
| CAP-0004 Validate a quote request | PROC-0002, APP-0002 | PRD-0002, PROC-0001, JRN-0001 |
| CAP-0005 Notify a shipper (proposed) | nothing; REL-04004 proposed, reported withdrawn | nothing |
| CAP-0007 Acquire end-of-day bars | PROC-0007, APP-0006, APP-0008 | PRD-0004, PRD-0005, PROC-0006, PROC-0010, JRN-0005, JRN-0009, JRN-0010, JRN-0011 |
| CAP-0008 Report store health | PROC-0008, APP-0007 | PRD-0005, PROC-0006, JRN-0009, JRN-0010, JRN-0011 |
| CAP-0001, CAP-0006 (domains) | nothing | nothing |

CargoQuote: CAP-0002 to CAP-0004. J-F data load: CAP-0007, CAP-0008. Each of the 5 approved
capabilities reaches 2 or 3 nodes; the 2 domains have no links of their own and reach nothing.

## How it differs from the dependants walk

- **Direction.** The dependants walk points from the thing changed to what rests on it: `requires`
  inverse to the product, then on to its journeys and delivering processes. The realisers walk
  points from the capability to what implements it: `realizes` inverse, then `supports` inverse.
- **Question.** Dependants: who is affected if this capability changes. Realisers: what must
  change, and which application owner is told, to change it.
- **No overlap.** On every capability of both slices the two reached sets are disjoint.
- **Specificity.** The three CargoQuote capabilities give one and the same dependants answer
  (PRD-0002, PROC-0001, JRN-0001); the realisers walk gives each its own activity and module.

`tests/test_register.py` `test_the_realiser_walk_is_a_second_named_walk` holds the rows, the five
reached sets, the disjointness, CAP-0005's withdrawn edge and the default.

## Why

Decision 0010 refused to add the realiser direction to `FORWARD`: mixed in, it would make every
start reach the same slice. Kept as its own named walk, it answers "what implements this" without
changing what "what is affected" returns. knowgov's TASK-0081 asked for it as a proposal.

## Not decided here

Whether the realisers walk continues from an application to the information it manages, or from a
process to the information it reads or writes (`manages`, `crud`): what a capability uses is not
what implements it. Whether either walk descends `parent`.
