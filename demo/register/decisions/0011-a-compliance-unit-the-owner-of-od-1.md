# 0011 — A compliance unit, the owner of the CargoQuote kit's open decision OD-1

Date: 2026-11-03. State: approved (fdurieux, by the merge of #16 on 2026-11-03; the line read proposed when merged). Supersedes: nothing.

## Decision

The organisation taxonomy gains **ORG-0004 "Compliance (stand-in)"**, a business unit, approved
under this record, its source the CargoQuote kit's `kit/requirements.md`. That document declares
REQ-06 "NOT YET SPECIFIED (open decision OD-1, owner: compliance)"; until now the register held
no unit by that name, so nobody the register knows owned the open decision.

`people/handles.toml` gains **`employee-4`** in ORG-0004 with roles `gives`, `approves` and
`closes` (decision 0009), issued 2026-11-03. Like every handle in this test case it is a
synthetic role, with no person behind it.

No link, relationship type or glossary term changes. The unit owns no register node: OD-1 is a
declaration in a document, not a node, and the knowledge store resolves a declaration's named
owner to a unit by name.

## Why

knowgov's review step (its task-0037, under its decision-0002) lets only a declared gap's owner
close it. On this register the close of OD-1 was refused, correctly, because "compliance" matched
no unit; so the CargoQuote scenario S2 could not reach PROCEED by command, which knowgov's
next-milestone measure (its doc-0009) requires. The unit and a `closes` handle make the
owner's act possible; they do not make it happen.

## Not decided here

What compliance would decide for OD-1. Closing the gap supplies no value (knowgov decision-0002);
the key then rests on whatever statements it has.
