---
id: decision-0024
title: >-
  The thirteen proposed Known limits are named 1.0 limits (doc-0028 section 10;
  G9-6)
date: '2026-11-08T19:52:00Z'
status: accepted
---
## Context

decision-0016 point 1 cuts 0.9.0 only when each Known limit is closed, tasked or named a 1.0 limit (doc-0028 G9-6). task-0173's pass (doc-0028 §10) classed every limit of 0.7.0, 0.8.0 and Unreleased.

On 2026-11-08 the coordinator set out, in plain English, the thirteen still to be named:
- K1, the Landlock floor, which task-0162 settled: Docker Desktop for Mac 4.48.0 has none, and the EC2 route works;
- the twelve the pass proposed: K2, K5, K6, K8, K11, K13, K14, K15, K17, K20, U2, U3.

The rest of the table is already settled:
- K21 is a 1.0 limit by decision-0021;
- K10 waits on the maintainer's Desktop test (G9-3);
- K16, K19 and U1 are tasked;
- K3, K4, K7, K9, K18, K-a and K-b are closed;
- K12 is decided for 0.9.0.

## Options

- **(a)** Name all thirteen.
- **(b)** Name all but K8 (no Windows or network file store) and K20 (the hooks do not see shell writes), and task those two.
- **(c)** Task each.

## Decision

**Accepted: (a)**, on the maintainer's word (2026-11-08: "name all"), to the coordinator's advice. Drafted by the coordinator.

## Opportunity canvas

| Element | Content |
|---|---|
| Problem | 0.9.0 cannot be cut while limits are neither closed, tasked nor named |
| Users | An adopter reading 1.0's Known limits; the maintainer, for the cut |
| Proposal | The thirteen are named as 1.0 limits, each with the sentence §10 gives it |
| Unique value | 1.0 states what it does not do, measured, before anyone relies on it |
| Cost | None in code; one Known limits list in the release that freezes |
| Risk | A named limit an adopter needed gone |

## Fit/gap

| Must satisfy | (a) | Evidence |
|---|---|---|
| decision-0016 point 1: each limit closed, tasked or named | Fit | doc-0028 §10 |
| A limit is a fact or a boundary, not an unfixed defect 1.0 promises against | Fit: each row's reason says by design or measured | §10 |
| Nothing the lighthouse needs is left as a limit | Fit, but K8 and K20 are the two to watch | §10 |

## SWOT

| | Helpful | Harmful |
|---|---|---|
| **Internal** | **S:** no code; each limit stated with its measure | **W:** a list of thirteen to keep true |
| **External** | **O:** the lighthouse shows which limits matter, and a later minor can lift one | **T:** K8 for a Windows adopter, K20 for one who relies on the hooks alone |

## Advice

(a), the drafter's recommendation:
- Each limit is measured or deliberate.
- Naming costs nothing.
- None blocks the lighthouse.

K8 and K20 are worth a second look if a Windows adopter or hook-only reliance appears.

## Consequences

- doc-0028 §10 reads **1.0 limit (decision-0024)** for the thirteen.
- 0.9.0's release section carries them under its Known limits.
- G9-6 is met, apart from K10, which G9-3 settles.
