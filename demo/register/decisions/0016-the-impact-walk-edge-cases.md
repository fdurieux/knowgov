# 0016 — The impact walk's edge cases: descent below a withdrawn descendant, the start, the walk named

Date: 2026-11-04. State: approved (fdurieux, by the merge of #25 on 2026-11-04; the line read proposed when merged). Supersedes: nothing; settles three points decisions 0012 and
0014 left open, whose rows, rule and default are unchanged. Restates one sentence of 0014's "Why"
(point 3); 0014 is not edited.

## Proposal

1. **Descent below a withdrawn descendant.** Under `--children`, a descendant that is not approved
   is reported withdrawn and not walked from (0014). Its own approved descendants are still walked,
   each by its own taxonomy's row: retiring the parent touches them too. `descendants` recurses
   through every state and `walk_children` walks each approved one, so v0.2.8 already does this;
   0016 records it. No node of the register has an approved descendant below a withdrawn one today
   (the four withdrawn descendants, CAP-0005, ENT-0005, PROC-0005 and JRN-0008, have no children),
   so the point has no measured instance.
2. **The start node is never counted among what it reaches.** `walk_children` already excludes the
   start (0014). The plain `walk` counts it when a cycle of approved links leads back to it. Under
   0016 both exclude it. An edge back to the start is still reported; it is not counted.
3. **Consumers state the walk they rely on.** A claim of the form "X rests on the subtree" names
   its walk (`dependants` or `realisers`) and whether `--children` is set.

## Point 2: what changes

Measured with `impact.reached(impact.walk(reg, <id>))` on the register as of this pull request
(base `f8fb17e`, 57 nodes). `--walk dependants`: 19 nodes reach themselves, each through one or
more approved links back to the start. `--walk realisers`: none. Every other node is unchanged.

| start | kind | reaches today | reaches under 0016 | back to the start from |
|---|---|---|---|---|
| JRN-0001 Get a freight quote | journey | 3 | 2 | PRD-0002 |
| JRN-0002 Submit a quote request | step | 6 | 5 | PROC-0002 |
| JRN-0003 Receive the quote, hold or refusal | step | 6 | 5 | PROC-0004 |
| JRN-0005 Daily data refresh | journey | 3 | 2 | PRD-0004 |
| JRN-0006 Sync the store | step | 11 | 10 | PROC-0007 |
| JRN-0007 Check the store's health | step | 8 | 7 | PROC-0008 |
| JRN-0009 Restore the store | step | 5 | 4 | PROC-0006 |
| JRN-0010 Bin the assets | step | 5 | 4 | PROC-0006 |
| JRN-0011 Upload the run | step | 5 | 4 | PROC-0006 |
| PRD-0002 CargoQuote instant quote | product | 3 | 2 | JRN-0001, PROC-0001 |
| PRD-0004 Seam frame | product | 3 | 2 | JRN-0005, PROC-0010 |
| PRD-0005 Daily run outputs | product | 5 | 4 | PROC-0006 |
| PROC-0001 Quote process | end_to_end_process | 3 | 2 | PRD-0002 |
| PROC-0002 Validate the request | activity | 6 | 5 | JRN-0002 |
| PROC-0004 Price the quote | activity | 6 | 5 | JRN-0003 |
| PROC-0006 Daily chain | end_to_end_process | 5 | 4 | JRN-0009, JRN-0010, JRN-0011, PRD-0005 |
| PROC-0007 Sync run | subprocess | 11 | 10 | JRN-0006 |
| PROC-0008 Status run | subprocess | 8 | 7 | JRN-0007 |
| PROC-0010 Seam frame export | end_to_end_process | 3 | 2 | PRD-0004 |

Each cycle is a pair of `FORWARD` rows that point both ways between two taxonomies: a journey
`concerns` a product and the product reaches it back by `concerns` inverse; a step
`is_supported_by` a process and the process reaches it back by `is_supported_by` inverse; a
process `delivers` a product and the product reaches it back by `delivers` inverse. Each start
loses exactly one, itself; no other node leaves or joins a reached set. The number of edges walked
is unchanged. `walk_children`'s answers (0014's table) are unchanged: it already removes the start
and its descendants.

## Point 3: decision 0014's sentence, restated

0014's "Why" says every one of CargoQuote's 36 codegen keys rests on CAP-0001's children or on what
they reach. Measured in knowgov, with `--children`: CAP-0001's dependants walk (PRD-0002,
PROC-0001, JRN-0001 on the register) lands 31 of the 36 keys; its realisers walk (PROC-0002,
PROC-0003, PROC-0004, APP-0002, APP-0003, APP-0004 on the register) lands all 36. The sentence holds
across both walks, not on either alone. Restated: every one of CargoQuote's 36 codegen keys rests on
what CAP-0001's realisers walk with `--children` reaches; 31 of them also on what its dependants walk
with `--children` reaches.

Context, not decided here: a knowgov consumer may also show, flagged, the keys whose rows in its
map name a withdrawn descendant (CAP-0005). That is knowgov's rendering, not the register's walk.

## Why

Point 1: a withdrawn descendant is a link in the hierarchy, not a boundary of it. Stopping the
descent there would make an approved grandchild invisible to the question "what does retiring
this parent touch", the answer 0014 was made to give.

Point 2: "what is affected if this changes" never includes the thing changed. Today the answer
depends on whether the walk happens to close a cycle, so a journey reports itself and a capability
does not, and `walk` and `walk_children` disagree on the same start. One rule for both.

Point 3: the two walks answer two questions (0012). A sentence that rests on their union, cited
as if it rested on one, overstates what either returns; a consumer quoting it should be able to
rerun it.

## Not decided here

Whether `walk_children` reports a descendant below a withdrawn one under a mark of its own. Whether
knowgov's register view (`register_view.impact`, vendored at a tag) adopts point 2 at the next tag
or pins the earlier answer: its choice.

## If approved

The next pull request:

- **Code.** `tools/impact.py` `walk` does not count the start among what it reaches: an edge whose
  far node is the start is still reported, marked so that `reached` skips it; `walk_children`
  unchanged. The module docstring gains one line citing 0016.
- **Tests.** `tests/test_register.py`: `test_the_walk_descends_parent_on_request`'s JRN-0002
  assertion flips (JRN-0002 not reached by its own walk, with or without the option); a new
  `test_the_start_is_never_reached` holds the 19 starts and their counts above, that the realisers
  walk changes no answer, that the edges walked are unchanged, and point 1 on a temporary copy of
  the register (an approved grandchild below a proposed child is walked). The existing assertions
  of decisions 0010 and 0012 hold as they are.
- **METAMODEL.md**, "The impact walk", one line: the start is never among what a walk reaches,
  with or without `--children`; below a withdrawn descendant the descent continues to approved
  ones (decision 0016).
