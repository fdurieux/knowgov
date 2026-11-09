---
id: decision-0029
title: >-
  The gate report names what it decided on: the task profile's digest, the
  register's tag and the knowgov build, in 0.9.0 (task-0103 AC 3, doc-0014 C9)
date: '2026-11-08T23:45:00Z'
status: proposed
---
## Context

doc-0014 C9 decided (option B) that the stage-to-stage decision record is the gate report and the trace ledger: "the gate report and the trace ledger carry what was relied on: verdict, threshold, task-profile digest, register tag, subject digest, `assertion_ids`, `as_of`". task-0103 AC #3 builds the report's half: "the report carries the two digests and the round trip holds them".

At `main` `4c7fcb0`, `harness/schemas/gate-report.schema.json` has `additionalProperties: false`. It carries the verdict, threshold and `as_of`, but neither the task profile's digest nor the register's tag. task-0103 sits at m-8 with the lighthouse, and its AC #1 and #2 are pilot work.

After the 0.9.0 cut, adding a field is a contract change: 0.10.0, and a restarted freeze (decision-0016 point 2). Before the cut it gathers for 0.9.0.

Raised by the reconciliation of the v1.0 scope handover against `main` `4c7fcb0` (its D3; A04, A09).

*Drafted by the coordinating session during the maintainer's overnight delegation (2026-11-08) and **parked for the maintainer**: it adds to 0.9.0's scope an item doc-0028 G1-6 placed at the pilot, and every addition to 0.9.0 this cycle (G9-11 to G9-15) was the maintainer's word. The advice below is the drafter's recommendation; the maintainer's word decides.*

## Options

- **(a) AC #3 in 0.9.0.** AC #1 and #2 stay with the pilot.
- **(b) All of task-0103 at the pilot.** AC #3 is then 0.10.0.
- **(c) Not built.** A retained report stays without its identity.

## Decision (proposed)

**(a)**, the drafter's recommendation. The gate report gains, additively:
- **`task_profile`**: the sha256 of the canonical JSON of the subject's `[tasks.<class>]` table the gate read.
- **`register`**: the register's tag and commit, read from `KG_REGISTER`'s `SOURCE.md` when it is vendored. For an instance's own checkout, they come from its git `HEAD` read without the network, or are `null` with the reason.
- **`knowgov`**: the build identity task-0231 already reports (`version`, `commit`, `describe`).

The schema's version moves under the project's convention. The round trip and `check_mcp_server.py` hold the fields, and the CHANGELOG names them under Unreleased › Contract changes.

The scored record does not move. If the comparator cannot pass without re-freezing the record, the build stops and the question comes back as a DECIDE.

## Opportunity canvas

| Element | Content |
|---|---|
| Problem | A retained gate report cannot say which task profile or register it judged, so it cannot be the stage's decision record (doc-0014 C9) |
| Users | The lighthouse's auditors and owners; an instance keeping reports as evidence (`--baseline`, the pre-push hook) |
| Proposal | (a) |
| Unique value | A report is self-describing: what was asked, against which register, by which knowgov |
| Cost | Three fields from data the gate already reads, a schema bump, round-trip and MCP coverage |
| Risk | Scope added before the cut; the comparator if it compares whole reports |

## Fit/gap

| Must satisfy | (a) | (b) | (c) |
|---|---|---|---|
| doc-0014 C9, B: the report carries what was relied on | Fit | Fit, later | **Gap** |
| decision-0016 point 4: no contract change between 0.9.0 and 1.0.0 | Fit | **Gap**: the pilot's first audit forces 0.10.0 mid-pilot | Fit, with a gap in the record |
| The record does not move | Fit, under the stop condition | Fit | Fit |
| The cut's timing | Fit: the cut waits on G9-3 (2026-11-09) anyway | Fit | Fit |

## SWOT (of a)

| | Helpful | Harmful |
|---|---|---|
| **Internal** | **S:** closes A04 and A09's identity leg with no new store or folder; reuses task-0231 | **W:** a contract change late in 0.9 |
| **External** | **O:** the trace report could carry the same fields later | **T:** if left out, the first audit request breaks point 4 when it matters most |

## Advice

(a). It is small, additive, and the kind of change decision-0016 makes expensive after the cut. The cut already waits on the maintainer's Desktop test, so it costs no time. It is parked because 0.9.0's scope is the maintainer's to widen.

## Consequences

- **If accepted**, task-0237 builds it, depending on task-0103. The build is prepared overnight, and its pull request waits for the maintainer's word. task-0103 AC #3 is checked when it merges, and AC #1 and #2 stay at m-8.
- **If not**, task-0237 is archived, and AC #3 stays at the pilot, as a 0.10.0 when it is built.
- **doc-0028**: "Left before the cut" lists it as the maintainer's.
