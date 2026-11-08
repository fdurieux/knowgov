---
id: decision-0026
title: >-
  The licence boundary: the platform stays GPL-3.0-or-later; harness/schemas/,
  instance/ and any future SDK are Apache-2.0 (task-0058; G9-8)
date: '2026-11-08T19:52:00Z'
status: accepted
---
## Context

knowgov is GPL-3.0-or-later (decision-0001). doc-0012 §5 (OpenAI's review) found that this blocks a vendor or integrator from shipping a connector inside their own product, which route B (plugging into the incumbents) depends on. task-0058 asks where the boundary sits for adapters, connectors and any SDK; doc-0028 G9-8 holds 0.9.0 for the decision.

On 2026-11-08 the coordinator read the candidate boundary at `main` `76e1e04`. The hook scripts under `instance/ci/claude/` import only the standard library and their sibling, and run the gate as a separate process.

## Options

- **(a)** Everything stays GPL-3.0-or-later.
- **(b)** The platform stays GPL-3.0-or-later; the interface layer (`harness/schemas/`, `instance/`, any future SDK) is Apache-2.0.
- **(c)** The interface layer under a weaker copyleft (LGPL or MPL).

## Decision

**Accepted: (b)**, on the maintainer's word (2026-11-08: "licence as advised"), to the coordinator's advice. Drafted by the coordinator.
- **The platform** stays GPL-3.0-or-later: `harness/` (but its `schemas/`), `demo/`, `tools/` (connectors included), `subjects/` and `tests/`.
- **Apache-2.0:**
  - `harness/schemas/`, the JSON Schemas that pin the reports, which are 1.0 contracts;
  - `instance/`, the layout, `kinds.toml`, `mappers.toml` and the CI templates, hooks and skills an instance copies into its own repositories;
  - any future client SDK.
- **A connector built for embedding** codes against the schemas and the export format, not against harness code. `tools/connector.py`, which imports harness code, stays GPL.
- **Vendored files** keep their own licences.
- **Counsel first:** as advised, a short check with counsel comes before the files are re-stamped.

## Opportunity canvas

| Element | Content |
|---|---|
| Problem | A vendor cannot embed what route B needs without the GPL reaching their product |
| Users | Vendors and integrators (route B); clients copying `instance/` into private repositories |
| Proposal | (b) |
| Unique value | Route B opens; the platform keeps its copyleft |
| Cost | Headers on the files under the boundary, a licence file for each Apache directory, README's licence section |
| Risk | The boundary drawn too wide gives the platform away; too narrow, vendors still cannot embed |

## Fit/gap

| Must satisfy | (a) | (b) | (c) | Evidence |
|---|---|---|---|---|
| Route B: a vendor ships a connector in a closed product | **Gap** | Fit, against schemas and formats | Partial | doc-0012 §5 |
| The platform keeps its copyleft | Fit | Fit | Fit | decision-0001 |
| A clean boundary in the tree | n/a | Fit: `instance/`'s scripts are stdlib only and call the gate as a process | Fit | read at `76e1e04` |
| Enterprise legal review | Harder | Easier: Apache-2.0's patent grant | Mixed | — |

## SWOT

| | Helpful | Harmful |
|---|---|---|
| **Internal** | **S:** a boundary that already exists in the code | **W:** two licences to explain and stamp |
| **External** | **O:** Apache-2.0 is what enterprise legal teams accept readily | **T:** a later file under `instance/` that imports harness code blurs the boundary, which a test can hold |

## Advice

(b), the drafter's recommendation. It is the narrowest boundary that opens route B, it matches how the code is already split, and it keeps the platform's copyleft. The re-stamp waits on a short counsel check.

## Consequences

- G9-8 is met: the boundary is decided (decision-0016 point 1).
- task-0058's AC #1 is met by this record. AC #2, README's licence section, and AC #3, every file under the boundary carrying `SPDX-License-Identifier: Apache-2.0` with an Apache-2.0 licence text beside it, are built in one PR once the maintainer says counsel has looked, or to go ahead without.
- That PR adds a test refusing an import of `harness/` from any file under the Apache boundary.
