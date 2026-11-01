# 0004 — One register per organisation, every subject of it inside

Date: 2026-11-01. State: approved (fdurieux). Supersedes: none.

## Decision

A register is kept per organisation, and it holds every subject of that organisation. A
subject is a body of artefacts a platform loads and governs (the knowgov stack: a kit of
documents, the code that verified them, an oracle); it enters this register as a source of
record of its own under `metamodel/sources.toml`, with its dated export manifests under
`exports/<system>/<date>/`, and its nodes and links sit beside the others'. Ids are minted
across the whole register, never per subject: a node belongs to the organisation, not to the
subject that first described it. A platform instance reads one register, the instance's own
checkout, and every subject of the instance joins it through its own key-to-node map, kept
with the subject, never here.

This public test case is the maintainer's organisation. The CargoQuote slice (decision 0002)
is its first subject; the J-F data-load kit of pumllint's recreation experiment is to be its
second, as a source system of its own with its own export manifest, named in the decision
record that adds its slice.

One register per subject was considered and refused: impact across an organisation's
artefacts is the question this register exists to answer, and two registers cannot answer it.

## Why

The maintainer's intent, stated on 2026-11-01 for the platform: the register serves all
subjects and all instances. The structure already allowed it, since no node, type or rule
names CargoQuote; what it lacked was the statement that a subject is a source of record and
not a register, and the rule on ids.

## What changes

No node, link, state, relationship type or glossary term. `metamodel/sources.toml` gains
nothing yet: the second source system arrives with its slice and manifest. `README.md` and
`exports/README.md` state the rule.
