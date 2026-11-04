# 0014 — The impact walk descends `parent` on request

Date: 2026-11-04. State: approved (fdurieux, by the merge of #23 on 2026-11-04; the line read proposed when merged). Supersedes: nothing; answers the question decisions 0007, 0010
and 0012 left open ("whether either walk descends `parent`"), whose rows, rule and default are
unchanged.

## Proposal

`tools/impact.py` gains `--children`. With it, the walk starts from the node and from every
descendant reached by `parent`, recursively; without it, the walk is the walk of today.

- **Which descendants.** Approved ones only, as decision 0007 follows approved links only. A
  descendant in any other state is reported, marked withdrawn, and not walked from.
- **Which rows.** Each descendant is walked by its own taxonomy's row of the walk chosen
  (`--walk dependants` or `--walk realisers`); `parent` adds starts, never steps.
- **What is reported.** The descendants under their own heading, apart from what the walk
  reached; what was reached is the union of the start's and each approved descendant's, less the
  start and its descendants. Each reached node keeps its owning unit (who to tell), as today.
- **Default.** Off. `walk(reg, start)` and `walk(reg, start, rows)` keep their meaning; the
  descent is a separate function, so knowgov's register view (`register_view.impact`, vendored at a
  tag) reads the same answer until it chooses the option.

## What it would reach

Measured on the register as of this pull request (base `2b9e093`), `--walk dependants`, by
walking each approved descendant with `tools/impact.py` and taking the union:

| start | kind | descendants (approved) | reaches today | reaches with `--children` |
|---|---|---|---|---|
| CAP-0001 Freight quoting | capability_domain | 4 (3; CAP-0005 proposed) | nothing | 3: PRD-0002, PROC-0001, JRN-0001 |
| CAP-0006 | capability_domain | 2 (2) | nothing | 8 |
| ENT-0001 | information_domain | 4 (3; ENT-0005 draft) | nothing | 11 |
| ENT-0006 | information_domain | 4 (4) | nothing | 16 |
| PRD-0001 | portfolio | 1 (1) | nothing | 2 |
| PRD-0003 | portfolio | 2 (2) | nothing | 6 |
| APP-0001 | application | 3 (3) | nothing | 11 |
| APP-0005 | application | 4 (4) | 8 | 15 |
| PROC-0001 | end_to_end_process | 4 (3; PROC-0005 proposed) | 3 | 7 |
| PROC-0006 | end_to_end_process | 3 (3) | 5 | 11 |
| JRN-0001 | journey | 3 (3) | 3 | 6 |
| JRN-0005 | journey | 6 (5; JRN-0008 deprecated) | 3 | 8 |

Fourteen nodes have children. Seven reach nothing today, because they have no links of their own:
the two capability domains, the two information domains, the two portfolios, and APP-0001. With
the option, every one of the fourteen reaches something. The two rows not shown, JRN-0002 and
PROC-0007, have one child each and reach no more with it than without.

## Why

The question the IEAM asks of the walk is "what is affected if this is retired or changed". For a
node whose meaning is its children, a capability domain above all, the answer today is "nothing",
which reads as "safe to retire" and is not. knowgov met it on 2026-11-04: asked what retiring
CAP-0001 touches, its register view and its saved Cypher both answer zero edges, while every one of
cargo_quote's 36 codegen keys rests on CAP-0001's children or on what they reach.

Descending by default would change every answer a consumer has recorded (knowgov's
`tests/test_register_view.py` holds CAP-0001's empty walk) and mix two questions: what rests on this
node, and what rests on what it groups. An option keeps the first as it is and makes the second
askable, as decision 0012 did for the realiser direction.

## Not decided here

Whether deprecating a parent should require its children to move first: decision 0015. Whether
`parent` is ever walked upwards (from a child to what rests on its parent): not proposed.

## If approved

The same pull request, or the next, adds `--children` and a function beside `walk`, and
`tests/test_register.py` holds: the option is off by default; the fourteen parents and their
reached sets above; CAP-0005, ENT-0005, PROC-0005 and JRN-0008 reported withdrawn and not walked;
the union excludes the start and its descendants. METAMODEL.md "The impact walk" gains one line.
