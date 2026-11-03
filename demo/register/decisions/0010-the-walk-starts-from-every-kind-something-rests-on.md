# 0010 — The impact walk starts from every kind something rests on

Date: 2026-11-03. State: approved (fdurieux, by the merge of #14 on 2026-11-03; the line read proposed when merged). Supersedes: nothing;
extends decision 0007's walk, whose rule (approved links only, withdrawn edges reported and not
followed) is unchanged.

## Decision

`tools/impact.py` `FORWARD` gains one row per start kind that had none, each pointing from the
thing changed to what rests on it:

| start taxonomy | steps added | what is reached |
|---|---|---|
| information | `crud`, inverse; `manages`, inverse | the processes that read or write the entity, the applications that manage it |
| capabilities | `requires`, inverse | the products that require the capability |
| products | `concerns`, inverse; `delivers`, inverse | the journeys about the product, the processes that deliver it |
| journeys | `is_supported_by`, forward (added beside `concerns`) | the process that supports a step or a touchpoint |

Applications and processes keep their steps. From any node reached, the walk goes on by that
node's own row, so a change to an application now also reaches, through a process's `realizes`,
the products that require the capability it realises.

Two relationship types stay out of the walk on purpose. `owns` points at the accountable unit,
which a tool shows beside each reached node (who to tell) rather than counting as reached.
`maps_to` leaves the register (`target_external`); it is the join into a knowledge store, which is
that store's to make.

The realiser direction (from a capability to the processes that realise it) answers a different
question, "what implements this", and is not mixed in. It can be a second, named walk if a reader
needs one.

## Why

knowgov measured the walk on this register (its doc-0011, 2026-11-03). From 28 approved
capabilities, information entities, products and journey steps it reached nothing, because only
applications, processes and journeys had a row. Adding every relationship type in both directions
is no answer: every start then reaches the same slice of fifteen nodes, which tells a reader
nothing they did not know. Direction is the decision. With the rows above, 6 of the 28 still reach
nothing: the two capability domains, the two information domains and the two portfolios, which
have no links of their own; the walk does not descend `parent`, and this decision leaves that as
0007 left it. `tests/test_register.py` holds the six, the steps named above, and that starts do
not collapse to one set.

## Not decided here

Whether retiring a parent reaches its children (`parent` is still not walked). Whether a second,
realiser walk is wanted.
