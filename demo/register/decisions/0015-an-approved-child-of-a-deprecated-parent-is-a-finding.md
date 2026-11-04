# 0015 — An approved child of a deprecated or retired parent is a finding

Date: 2026-11-04. State: approved (fdurieux, by the merge of #23 on 2026-11-04; the line read proposed when merged). Supersedes: nothing; extends the lifecycle rule that an
approved link referencing a deprecated or retired node is an error (`tools/check_register.py`;
README.md, "Deprecating a node fails the check on every approved link that still references it"),
whose wording is unchanged.

## Proposal

`tools/check_register.py`, in the node pass beside the existing `parent` checks (exists, same
taxonomy, allowed kind), adds one state check:

| child's state | parent's state | finding |
|---|---|---|
| approved | deprecated or retired | **error** `lifecycle`: "approved node has parent `<id>` in state `<state>`" |
| proposed or draft | deprecated or retired | **warning** `lifecycle`, same text |
| deprecated, retired or rejected | any | none |

So a parent is deprecated only once each approved child has been moved to another parent, or
deprecated in the same pull request, the order the link rule already imposes on links.

## What it would find

On the register as of this pull request (base `2b9e093`): nothing. No node with children is
deprecated or retired; JRN-0008, the one deprecated node, has none.

Had CAP-0001 Freight quoting been deprecated: three errors (CAP-0002, CAP-0003, CAP-0004,
approved) and one warning (CAP-0005, proposed). Today the same pull request passes the checker
with no finding: CAP-0001 has no links of its own, so the link rule never fires, and the `parent`
check reads the parent's existence and kind, never its state.

## Why

A deprecation is how this register says "stop building on this", and the checker is what makes
it visible: "Deprecating a node fails the check on every approved link that still references it;
nothing is fixed automatically" (README.md). For links that holds. For `parent` it does not: a domain can be
deprecated, and then retired, while approved capabilities still sit under it, and nothing in the
working tree says so. The tree would then hold an approved node whose place in the hierarchy is a
retired one, which no reader can resolve.

A warning only for proposed and draft children keeps the rule from blocking work in progress,
the same distinction the walk makes (decision 0007: approved links followed, others reported).

## Not decided here

Whether the impact walk descends `parent`: this decision does not need it, and 0014 proposes it as
an option. Whether a parent may come back: `metamodel/lifecycle.toml` already allows `deprecated` back to
`approved` and `retired` to nothing; nothing changes there.

## If approved

The same pull request, or the next, adds the check, and `tests/test_register.py` holds: the
register as it stands gives no new finding; a working tree with CAP-0001 deprecated gives three
errors and one warning naming CAP-0002 to CAP-0005; a deprecated child of a deprecated parent gives
none. METAMODEL.md **Lifecycle.** gains one sentence.
