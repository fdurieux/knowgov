# 0018 — A third named walk, thread; product–journey alignment at warning level

Date: 2026-11-05. State: approved (fdurieux, on 2026-11-05: "approve both parts of decision 0018"; recorded on #29 before its merge). Supersedes: nothing; adds a walk beside decisions 0010 and 0012,
whose rows and default are unchanged, and a rule beside the coverage rules C1 to C3, which are
unchanged. Asked for by knowgov doc-0022 K2 (the initiative-slicing study, fdurieux/knowgov#254).

## Proposal

**(a) The walk.** `tools/impact.py` gains `THREAD`, a third set of walk rows, chosen by
`--walk thread`. `dependants` stays the default.

| start taxonomy | step | what is reached |
|---|---|---|
| journeys | `is_supported_by`, forward | the process that supports the step |
| processes | `realizes`, forward | the capability the process realises |
| processes | `supports`, inverse | the applications that support the process |
| processes | `crud`, forward | the information the process reads or writes |
| applications | `manages`, forward | the information the application manages |

Every step points away from the journey. Capabilities and information have no row, so the walk ends
there and never turns back towards the product. Decision 0007's rule applies unchanged: approved
links only, a withdrawn edge reported and not followed. `owns` and `maps_to` are never walked (0010).
`parent` adds starts under `--children`, never steps (0014); the start is never counted (0016).

**(b) The rule A1.** `tools/check_register.py` `check_alignment`, at warning level, never an error.
Per approved node of kind `product` or `variant`:

1. no approved `concerns` link from a journey element neither deprecated nor retired: one warning,
   *no journey*; the other two parts are not evaluated for it;
2. a capability the product requires (approved `requires` links) that the thread walk with
   `--children` from none of its journeys reaches: one warning per capability, *required not reached*;
3. a capability that walk reaches and the product does not require: one warning per capability,
   *reached not required*.

The summary carries `A1` with its denominator (approved products), the aligned products and the
three lists; the checker prints one line. A1 is not a coverage rule (glossary: a node of one kind
has a link of one type): it compares two paths to the same capabilities. It has no exception;
a warning needs none.

## What it measures

On the register as of this pull request (base `4149e06`, 57 nodes, 53 approved, 65 links).

**A1:** 0 of 3 approved products aligned, 3 warnings, as doc-0022 found:

| product | journey | requires | the journey's steps reach | finding |
|---|---|---|---|---|
| PRD-0002 CargoQuote instant quote | JRN-0001 | CAP-0002, CAP-0003, CAP-0004 | CAP-0002, CAP-0004 | requires CAP-0003, not reached: PROC-0003, which realises it, supports no step |
| PRD-0004 Seam frame | JRN-0005 | CAP-0007 | CAP-0007, CAP-0008 | reaches CAP-0008 (JRN-0007 by PROC-0008), not required |
| PRD-0005 Daily run outputs | none | CAP-0007, CAP-0008 | — | no journey |

**The walk.** Per start, `impact.reached(impact.walk(reg, <id>, THREAD))`, and with `walk_children`:

| start | reaches | with `--children` |
|---|---|---|
| JRN-0002 Submit a quote request | PROC-0002, CAP-0004, APP-0002, ENT-0002, ENT-0003 | same |
| JRN-0003 Receive the quote, hold or refusal | PROC-0004, CAP-0002, APP-0003, ENT-0003, ENT-0004; REL-03003 to PROC-0005 proposed, withdrawn | same |
| JRN-0006 Sync the store | PROC-0007, CAP-0007, APP-0006, APP-0008, ENT-0008, ENT-0009 | same |
| JRN-0007 Check the store's health | PROC-0008, CAP-0008, APP-0007, ENT-0008 | same |
| JRN-0009, JRN-0010, JRN-0011 | PROC-0006, APP-0005, ENT-0007, ENT-0010; REL-07008 (`crud`, PROC-0006 to ENT-0010) deprecated, withdrawn | same |
| JRN-0001 Get a freight quote | nothing | 9: JRN-0002's and JRN-0003's threads |
| JRN-0005 Daily data refresh | nothing | 13 |

**Direction.** knowgov doc-0011 measured that every relationship walked both ways collapses to the
whole slice. Measured here on the 53 approved starts:

- *Zero-reach starts:* 33 reach nothing without `--children`, 30 with it. All 7 approved
  capabilities, 9 information nodes, 5 product nodes and 4 organisation units (the walk's ends and the
  nodes it never enters); JRN-0001 and JRN-0005 (journeys, which reach their steps' threads with
  `--children`); the touchpoint JRN-0004 (no `is_supported_by` link, EXC-0001); APP-0001 (an
  application with no link of its own, which reaches ENT-0002 to ENT-0004 with `--children`); APP-0004,
  APP-0006, APP-0007 and APP-0009 (modules that manage nothing).
- *Slice size:* the largest reach is 6 without `--children` (JRN-0006) and 13 with it (JRN-0005), of
  the J-F slice's 29 nodes; CargoQuote's largest is 9 (JRN-0001 with `--children`) of 28. No start
  reaches its slice.
- *Specificity:* 20 starts reach something, in 17 distinct sets; the three repeats are JRN-0009 to
  JRN-0011 (one process, PROC-0006) and PROC-0006 with PROC-0010 (one application, APP-0005).
- *Both ways, for contrast:* the same five relationship types walked in both directions give each of
  36 starts its whole component, 5 answers in all (12, 11, 8, 3 and 2 nodes). The thread's one
  direction is what keeps the answer to the step's own.

`tests/test_register.py` `test_the_thread_walk_goes_from_a_step_down_to_its_data` holds the rows,
the reached sets, the withdrawn edges, the parent rule and the measure above;
`test_products_and_journeys_align_at_warning_level` holds the three findings, their level, and on a
copy their clearing once PRD-0004 requires CAP-0008, JRN-0002 is supported by PROC-0003 and JRN-0005
concerns PRD-0005.

## Why

(a) The dependants walk answers what rests on a node; the realisers walk what implements a
capability. Neither answers what a journey step uses, down to the data, the question an initiative
sliced by journey asks (doc-0022). Decision 0012 left `manages` and `crud` out of the realisers walk
because what a capability uses is not what implements it; the thread walk is where they belong.

(b) A product's capabilities are recorded twice: by `requires`, and by the path its journey's steps
take through processes. Where the two disagree, either a link is missing or one is wrong; the
register cannot tell which, so it warns and names both sides. An error would fail every merge on the
three findings the approved register carries today.

## What the walk shows beyond A1

A second knowgov study traced CargoQuote journey to step to process to application with
`impact.py`. Re-measured here on the same base, each holds:

- **Processes that support no step.** No approved `is_supported_by` link targets PROC-0001,
  PROC-0003, PROC-0009 or PROC-0010, all approved. PROC-0003 (screening, supported by APP-0004)
  reaches JRN-0001 only through PRD-0002 in the dependants walk; the thread walk from JRN-0001 never
  meets it, which is A1's PRD-0002 finding.
- **A proposed link.** REL-03003, JRN-0003 `is_supported_by` PROC-0005, is `proposed`: the thread
  walk reports it withdrawn and does not follow it.
- **Coarse grain.** JRN-0009, JRN-0010 and JRN-0011 are each supported only by the end-to-end
  PROC-0006, itself supported only by APP-0005: the three steps get one and the same thread. The walk
  is as fine as the links; it cannot tell the steps apart until a link names a finer process.
- **The gap `crud` forward closes.** `FORWARD` walks `crud` only inverse, from an entity to its
  processes; no walk today goes from a process to the information it reads or writes. `THREAD` does.

## Not decided here; left to later records

Which of the three findings is a missing link and which a wrong one: PRD-0002's CAP-0003 (a step
for screening, or PROC-0003 under an existing step), PRD-0004's CAP-0008 (a `requires` link, or
JRN-0007 under another journey), PRD-0005's journey. Each is a content change with its own record.
A link JRN-0003 `is_supported_by` PROC-0003 would be a candidate for its owner, ORG-0001, to author
and approve; the walk never assumes it. Whether the J-F steps get finer processes.
Whether A1 ever becomes an error, or takes exceptions. Whether knowgov's register view adopts the
thread walk at the next tag: its choice.

## Built in this pull request

As decision 0012 was: `THREAD` and `--walk thread` in `tools/impact.py`; `check_alignment` and the
A1 line in `tools/check_register.py`; the two tests above (twenty-five in all); one README line per
part; METAMODEL.md "The impact walk" two lines.
