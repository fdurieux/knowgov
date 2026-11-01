---
id: decision-0001
title: >-
  Move the governed-repository demo out of pumllint into knowgov, under
  GPL-3.0-or-later
date: '2026-11-01T14:27:00Z'
status: accepted
---
## Context

The governed-repository demo lives in pumllint under `kg_experiment/` (harness, page, Neo4j
store, vendored ieam-register) and is lab territory under pumllint's packaging settlement:
nothing of it may ship on pumllint's product path, and the 2026-08-26 never-build list keeps
any store off that path (N1). Serving more than one subject, and private instances of a
client organisation, inside a GPL linter's tree would put private content beside the public
tool and drift toward the product path. pumllint `docs/ieam-register-proposal.md` §5 placed the
register in its own repository for the same reasons. The brief is doc-0001.

## Decision

The platform (harness, page, store port and adapters, register adapter, Dockerfile, compose
files, vendoring tool, comparator, tests) moves to this repository, `fdurieux/knowgov`,
public. The CargoQuote subject and the record of the proof of concept stay in pumllint, where
they were made, and are vendored here at a tag with a SOURCE note and a digest test, as the
register already is. pumllint's ROADMAP records the move on its side; this record is the
platform's.

The licence stays GPL-3.0-or-later, the licence the code carries in pumllint, so nothing is
relicensed. An organisation running knowgov in house has no obligation to publish anything;
the source obligation arises only on distributing a modified knowgov to third parties; the
content it governs is that organisation's data and is never affected. The same licence is to
be added to ieam-register, which has no LICENSE file.

## Consequences

- pumllint's copy of the demo and its `kg-demo` workflow are retired by a pumllint pull
  request once task-0001 is Done; until then pumllint's copy is the running one.
- `pumllint/` imports nothing from this repository and reads no register; this repository
  consumes pumllint's reports, never the reverse.
- The backlog (`backlog/`) is this repository's queue and `backlog/decisions/` its decision
  record; the maintainer's artifact pages quote them and are views.
- A client's instance is created inside the client's repositories and never reaches here.
