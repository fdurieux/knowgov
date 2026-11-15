---
id: decision-0043
title: >-
  After 1.0.0, audit and identity come before a connector and suggested map
  rows, writes wait for a lighthouse, and incumbent adapters live under
  Apache-2.0
date: '2026-11-15T14:27:00Z'
status: accepted
---

## Context

On 2026-11-15 the maintainer wrote two drafts: a quadrant assessment, and a competitor research pass. A read-only investigation re-checked them against `main`. It was run by a sub-session of the coordinating session and changed nothing.

The investigation proposed an approach (P1–P16) and put eight questions to the maintainer. The maintainer answered five of them on 2026-11-15: "4 as proposed, 5 after lighthouse, 6 as proposed, 7 as proposed, 8 yes". This record carries the three answers that set knowgov's direction after 1.0.0: questions 4, 5 and 6.
- **Question 7** concerns the maintainer's own drafts. They are corrected outside the record, which keeps doc-0012's placement, 14 · 2.5.
- **Question 8** is a targeted check of whether a reviewer can review their own answer. Its result is recorded separately.
- **Questions 1–3 are still open:** the AI-governance quadrant as a target, subject content under the freeze, and the design-class owners.

What the investigation found and the record already holds:
- **Route B** (doc-0012 §6) is the record's choice: plug in first, borrowing execution from the incumbents.
- **decision-0041** queues the reconcile reader C5-1 and three other residues for 1.1.0.
- **decision-0008** keeps the MCP reader read-only.
- **decision-0026** puts adapters under Apache-2.0.
- **The gaps** that every incumbent the drafts name has already closed: an audit of who asked for a verdict, and per-user identity on the HTTP transport. knowgov's reader takes one bearer token, `KG_MCP_TOKEN`, and keeps no log of calls.
- **Under decision-0016 point 7**, an additive change after 1.0.0 is a minor release. Before 1.0.0, any contract change is a 0.10.0 and restarts the soak.

## Options and choice

- **(a) The order of the integration and enterprise items after 1.0.0.** After C5-1, three orders were offered: audit and identity first; a connector first; or suggested register-map rows first.
- **(b) A governed write path.** The choice was between "not before a lighthouse asks" and "plan it for 1.x".
- **(c) Where connectors to incumbent tools live.** The choice was between an Apache-2.0 adapter area under decision-0026 and `tools/connector.py` alone.

**Chosen by the maintainer, 2026-11-15:**
1. **Order after 1.0.0:**
   1. C5-1, the reconcile reader, already decided by decision-0041.
   2. The verdict audit log and per-user identity on the HTTP transport, taken as one decision before either is built.
   3. One connector that reads an incumbent's MCP server, tested on public sample data only.
   4. Suggested register-map rows.

   Store isolation stays a decision plus the tenancy spike's measurements, and is not built until a lighthouse with several teams asks for it.
2. **A governed write path waits for the lighthouse.** It is not pursued before a lighthouse asks for one. If it is built, it is a second server, as `knowgov-runs` is, and the reader stays read-only (decision-0008).
3. **Incumbent adapters live in an Apache-2.0 adapter area** under decision-0026's boundary, so an integrator can embed them. `tools/connector.py` stays the landing step into `<instance>/register/exports/<system>/<date>/`. Only public sample exports enter this repository; real incumbent data never does.

Nothing is minted by this record. Each item gets its task, and where it changes a contract its own decision, when its turn comes after 1.0.0.

## Opportunity canvas

| Box | Content |
|---|---|
| Problem | The drafts list a dozen enterprise and integration gaps with no order. Building any of them before 1.0.0 restarts the soak, so the order after it decides what an adopter meets first. |
| Users | The lighthouse, and an integrator embedding knowgov above an incumbent; an AI-governance or security reviewer asking who was allowed to build what. |
| Proposal | C5-1, then audit and identity together, then one MCP-reading connector, then suggested map rows. Writes wait for the lighthouse. Adapters under Apache-2.0. |
| Unique value | The two gaps every named incumbent has already closed are closed first. The read-only reader stays the security strength it is. Integration arrives as an embeddable add-on rather than a replacement. |
| Cost | Four 1.x minor releases' worth of work, each additive. A decision on identity, covering the standard-library-only constraint and the threat model in `docs/security.md`, and one on the audit log's format and retention. |
| Risk | A lighthouse needs a connector before audit and identity; the order is a default and the lighthouse can reorder it. An incumbent's MCP server changes under the connector. |

## Fit/gap

| Must satisfy | Fit | Gap |
|---|---|---|
| decision-0016 A1: no contract change before 1.0.0 | every item is after 1.0.0 | none |
| decision-0016 point 7: after 1.0.0, additive is a minor | audit log, identity, connector and map-row suggestions are additive | store isolation may break the store port (point 3), so point 5's deprecation rule applies; it stays unbuilt |
| decision-0041: the 1.1.0 queue | C5-1 stays first | the batch grows; the new items join or follow it |
| decision-0008: the reader stays read-only | writes wait, and come as a second server if ever built | none |
| decision-0026: adapters under Apache-2.0 | adapters land there | task-0058 (the licence split) is still To Do; the first adapter waits on it |
| CLAUDE.md Boundaries: no client data, no bank-related data | public sample exports only; real data stays in the client's instance | a connector's tests need public samples from the incumbent |
| doc-0012 §6 route B | this is route B in order | none |

## SWOT

- **Strengths**
  - It closes the gaps reviewers ask about first.
  - It keeps the read-only reader.
  - Integration is embeddable.
  - Every item is additive.
- **Weaknesses**
  - Nothing moves before 1.0.0.
  - Identity needs either a library or a careful standard-library implementation.
  - Only one connector is planned.
- **Opportunities**
  - Incumbents' MCP servers make reading them cheaper than exports.
  - An audit log answers the AI-governance buyer's "why was the agent allowed to build this?".
- **Threats**
  - An incumbent adds verification levels first.
  - The first connector's incumbent changes its server.
  - A lighthouse that asks for writes early.

## Advice

As chosen, for three reasons:
- Audit and identity are what every named incumbent already has and what a security review asks for first.
- One connector proves the route B pattern before a second is built.
- Keeping writes out until a lighthouse asks preserves decision-0008's strength in the same review.

## Consequences

- **After 1.0.0:** C5-1 (decision-0041), then a decision on audit and identity, then one connector task, then a suggested-rows task. None is minted now.
- **Store isolation:** a decision with the tenancy spike's measurements; no build until a lighthouse asks.
- **Writes:** none until a lighthouse asks.
- **Adapters:** under decision-0026's Apache-2.0 boundary; `tools/connector.py` stays the landing step.
