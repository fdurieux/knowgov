---
id: decision-0025
title: >-
  The technical name stays knowgov; the buyer-facing name stays open until the
  lighthouse (task-0061; G9-7)
date: '2026-11-08T19:52:00Z'
status: accepted
---
## Context

doc-0028 G9-7: names, before they freeze. `knowgov` sits in several contracts:
- the image name, `ghcr.io/fdurieux/knowgov`;
- the `KG_` settings prefix;
- `knowgov-gate.sh`;
- the MCP servers' names, `knowgov` and `knowgov-runs`;
- the reports' `tool` strings.

decision-0016 point 3 makes all of these 1.0 contracts. task-0061 asks a wider question: the one name a buyer meets across knowgov, ieam-register, Legible and pumllint (doc-0012). doc-0028 says deciding "the technical name stays knowgov" is enough for G9-7.

## Options

- **(a)** The technical name stays `knowgov`; the buyer-facing name is decided later.
- **(b)** Rename now, before the freeze.
- **(c)** Decide both now.

## Decision

**Accepted: (a)**, on the maintainer's word (2026-11-08: "knowgov stays"), to the coordinator's advice. Drafted by the coordinator.

## Opportunity canvas

| Element | Content |
|---|---|
| Problem | Names in the contracts cannot move after the freeze without a major version |
| Users | Every adopter's configuration, scripts and MCP registrations |
| Proposal | `knowgov` is the technical name at 0.9.0 and 1.0; a buyer-facing name, if any, is prose |
| Unique value | The freeze is safe, and the buyer question stays open for the evidence that should answer it |
| Cost | None |
| Risk | A later buyer name that sits awkwardly beside `knowgov` in the docs |

## Fit/gap

| Must satisfy | (a) | Evidence |
|---|---|---|
| G9-7: names settled before they freeze | Fit | doc-0028 §4 |
| decision-0016 point 3's contracts unchanged | Fit | decision-0016 |
| task-0061's buyer question | Gap, left open on purpose | task-0061 |

## SWOT

| | Helpful | Harmful |
|---|---|---|
| **Internal** | **S:** no churn; one sentence closes G9-7 | **W:** buyers still meet four names |
| **External** | **O:** "Legible" already names the programme on fdurieux.github.io, the natural buyer name when one is wanted | **T:** a clash in the docs, which "Legible, built on knowgov" covers |

## Advice

(a), the drafter's recommendation. The contracts need only the technical name, and the buyer name is best chosen with the lighthouse.

## Consequences

- G9-7 is met.
- task-0061 stays To Do for the buyer-facing name. Its AC #1 asks a record for that name and its relation to each repository; this record settles only the technical name.
- No file changes.
