---
id: doc-0029
title: >-
  Toward 0.9 while decision-0016 is open: the coordinator's plan for the
  2026-11-06 afternoon delegation
type: other
created_date: '2026-11-06T13:02:00Z'
updated_date: '2026-11-06T15:57:00Z'
---
*2026-11-06. Maintainer register. A choice taken under the maintainer's delegation of ~13:00 UTC: "I'll be off again for a few hours; continue unsupervised; use the swot, opportunity canvas, fit/gap, and derive an advise which you then document and execute." Drafted and executed by the coordinating session. It decides no record question: decision-0016 and decision-0011 stay the maintainer's, and nothing here accepts either.*

## Context

- v0.8.0 is published (2026-11-06, tag at `0c629d8`), and B7 (task-0157) waits in Unreleased.
- doc-0028 §4 lists what a 0.9 contract freeze needs (G9-1 to G9-10), and §9 proposes P1 to P4 "for the coordinating session to review and mint". None is minted.
- decision-0016 (0.9 as the freeze, 1.0 at the lighthouse) is proposed and the maintainer's.
- Since doc-0028:
  - G9-4 is met (an image that runs every feature);
  - G9-5 is met in structure (task-0163; the 12-min budget is still unmeasured uncontended);
  - G9-9's two stale claims are fixed (#291).
- **Still open, and not waiting on the maintainer:**
  - G9-2: format versions (P1);
  - G9-3: task-0160, the raw-byte digest of a file artefact;
  - G9-6: the Known limits pass (P3).
- **Found on 2026-11-06:** task-0168 noted that no JSON schema pins the MCP tools' outputs. decision-0016 point 3 lists them among the 1.0 contracts, and the external pass (doc-0012 §9) scored E1 on documentation alone.
- **In flight:** #304 (task-0169), #306 (task-0162), #308 (this file's PR), and a key-check PR (a separate session).

## Opportunity canvas

| Box | Content |
|---|---|
| Problem | 0.8.0 shipped, and the record names what a freeze needs, but nothing is queued for the parts that do not wait on the maintainer. |
| Who, and when | The maintainer on return, deciding decision-0016 against a shorter gap list. Later, the lighthouse pilot's platform team, reading what holds. |
| Today | P1 and P3 unminted; task-0160 To Do; the MCP tools' outputs described in prose only. |
| Solution | Mint P3, and P5 (new: a JSON schema per MCP tool output, checked in the suite like `harness/schemas/`). Dispatch P5 and task-0160 to build. Dispatch P3 as a docs and backlog pass. Mint P1 and dispatch it **as a plan only**, with no format chosen in code, because it is the widest contract change and its scheme is the maintainer's to see first. |
| Measure | Each merged on its whole green matrix, with its evidence. doc-0028's G9-2 (planned), G9-3 (task-0160) and G9-6 (P3) each move one step. |
| Cost | Three sessions for a few hours, and CI minutes. No paid call, no pin change. |
| Risk | Building toward a freeze the maintainer may not choose (decision-0016 options c or d). |

## Fit/gap

| Must satisfy | How the plan meets it | Gap |
|---|---|---|
| decision-0003 §2: a contract change raises the minor | task-0160 and P5 are additive or a fix; they gather in Unreleased for the next minor | none |
| decision-0016 open, the maintainer's | nothing here accepts it, and every item holds under its options (a), (b) and (c) | under (c) the schemas come earlier than strictly needed |
| CLAUDE.md: standard library only; the record and its pins unchanged | the schemas use `harness/schema_check.py`; task-0160's AC #3 stops it if a recorded digest would move | none |
| One record per thing | doc-0028 keeps its gap lists; this doc records the choice; the tasks hold the work | none |
| The coordinator's merge capacity, and CHANGELOG collisions | at most three of these PRs in flight; the coordinator resolves each collision and runs the suite | each collision costs a CI round |

## SWOT

- **Strengths.**
  - Every item is decision-independent, and each closes or advances a named G9 gap.
  - It uses sessions that are idle now.
  - The work is mostly additive.
- **Weaknesses.**
  - task-0160 is a contract change the maintainer has not seen.
  - More CHANGELOG churn and CI minutes.
- **Opportunities.**
  - decision-0016 can be decided against a shorter list.
  - Pinned output schemas give the next external pass firmer E1 evidence than prose.
- **Threats.**
  - A format-version scheme chosen without the maintainer may need a redo, hence P1 as a plan only.
  - P5 and the key-check work both touch `harness/mcp_runs.py`.

## Advice, and what is executed

1. **Mint and build P5 (task-0172)**, pinned JSON schemas for the MCP tools' outputs. It goes to the session that built B7 (session_01HTAA1RV7EhHr9LUbAviLXA). It is additive, and it rebases onto the key-check PR if that lands first.
2. **Build task-0160**, the raw-byte file Version digest. It goes to the security session (session_01HTAA1UsSVF25SBM7XfjnqP). Its AC #3 holds: the change waits if a recorded digest would move.
3. **Mint P3 (task-0173)**, the Known limits pass: each limit in 0.7.0, 0.8.0 and Unreleased is closed, tasked, or proposed as a named 1.0 limit. The doc-0028 drafter takes it (session_01HTAA1TThDg3TA2qJHCemaG), backlog and docs only, and no limit is declared a 1.0 limit without the maintainer.
4. **Mint P1 (task-0174)**, format versions on the instance's inputs, and plan it in the task: the scheme options, each with this doc's four parts, and the drafter's recommendation. No code until the maintainer has read it.
5. **P4** waits for decision-0016's acceptance, as doc-0028 says.
6. **Merge everything on green** (CLAUDE.md, maintainer 2026-11-06), and measure task-0163's budget in a quiet slot.

## Second tranche, 2026-11-06 13:45 UTC

Since this doc was written, the following merged: task-0172's base, task-0160 (#310), task-0171 (#307), task-0169, task-0162 and task-0170. The Known limits pass (task-0173, PR #312) minted four limits with no owner: task-0175 to task-0178.

| Box | Content |
|---|---|
| Problem | Two of the four new limits carry security or availability weight. First, an unbounded response (K9, task-0177), the half of H2 that was left open. Second, a reader wedged behind one killed Neo4j writer until the next writer comes (K3, task-0175). |
| Who, and when | An organisation's instance, once its data is larger than the public subjects', and the lighthouse pilot's operators. |
| Today | Both are only listed as Known limits; neither has a test that fails today. |
| Solution | task-0175 goes to the session that built S2 (session_01HTAA1UsSVF25SBM7XfjnqP) now. task-0177 goes to the session that fixed LIMIT-06 (session_01HTAA1RV7EhHr9LUbAviLXA) once #311 has merged. task-0176 (heap sizing) and task-0178 (the register panel) wait: one needs an instance's scale, and the other is a convenience. |
| Measure | Each merged on its whole green matrix, with the Known limit removed from Unreleased in the same PR. |
| Cost | Two sessions for a few hours. task-0177 adds a new refusal, a contract change gathered in Unreleased. |
| Risk | task-0175 touches the publication code that decision-0014 rests on. |

**Fit/gap.**
- decision-0014 (whole publication) is kept: task-0175's clearing takes the sequence lock, its AC #3 holds both race orders, and SNAP-01 to SNAP-07 must stay green on both adapters.
- H2's settings pattern (bounded, refused with the variable's name) is reused by task-0177. Its defaults sit above the largest measured response; the gap is that the measurement comes first.
- Neither needs decision-0016.

**SWOT.**
- **Strengths:** two named limits close, and each fix reuses an existing pattern.
- **Weaknesses:** task-0177 is a contract change, and task-0175 is delicate code.
- **Opportunities:** 1.0's limits list gets shorter before the maintainer decides decision-0016.
- **Threats:** a regression in publication, which SNAP and the stack job guard.

**Advice, executed:**
- dispatch task-0175 now;
- dispatch task-0177 after #311;
- leave task-0176 and task-0178 To Do.

## Third tranche, 2026-11-06 14:45 UTC

The second tranche merged: task-0175 (#314) and task-0177 (#315). Of the four limits task-0173 minted, task-0176 (the heap a Neo4j load needs) and task-0178 (the register panel) remain. The second tranche held task-0176 back because it "needs an instance's scale". Its AC #1 asks for a synthetic scale-up, so it does not. That reason is withdrawn here.

| Box | Content |
|---|---|
| Problem | An instance's first Neo4j load, larger than the public subjects', fails inside its transaction with no forecast (task-0176). A reviewer on the page cannot see what a register update withdrew (task-0178). |
| Who, and when | The pilot's operators at their first load. Reviewers of a register update on the page. |
| Today | Both are only listed as limits (doc-0028 §10, K4 and K18). |
| Solution | task-0176 goes to the session that built S2 and measured 41 and 64 MiB (session_01HTAA1UsSVF25SBM7XfjnqP). task-0178 goes to the session that built the worker chip on the page (session_01HTAA1UUkk7jJTbGCaLWPnf). |
| Measure | Each merged on its whole green matrix, with its Known limit lifted in Unreleased. |
| Cost | Two sessions for a few hours, plus one local Neo4j for task-0176's measurement. |
| Risk | task-0176's forecast is a model: a forecast too low still fails in the transaction (today's behaviour), and one too high refuses a load that would fit. |

**Fit/gap.**
- decision-0014 is kept: a refused load starts nothing and keeps the previous generation.
- task-0178 reuses `harness/register_change.py`, the gate's own computation, so the page and the gate agree by construction.
- **Gap:** task-0176's forecast must be conservative only by a stated margin. A setting turns the pre-check off, as `KG_KEY_CHECK` does for the key check.
- Neither needs decision-0016.

**SWOT.**
- **Strengths:** both close named limits; task-0178 reuses an existing computation.
- **Weaknesses:** task-0176 adds a refusal, a contract change gathered in Unreleased.
- **Opportunities:** the pilot's first load gets a sizing rule before it starts. The 1.0 limits list shrinks to the thirteen proposed for the maintainer.
- **Threats:** a forecast tuned on synthetic data that misses an instance's shape. AC #1 records the relation with its data, so it can be refitted.

**Advice, executed:**
- dispatch task-0176, with a switch-off setting for the pre-check;
- dispatch task-0178;
- task-0163's AC #2 still waits for a quiet slot.

## Close of the window, 2026-11-06 16:00 UTC

**The three tranches are done.** All merged, on whole green matrices:
- **First tranche:**
  - task-0172, the MCP output schemas (#311);
  - task-0160, the raw-byte file digest (#310);
  - task-0173, the Known limits pass (#312);
  - task-0174's plan, filed (#312).
- **Second tranche:** task-0175, an abandoned Neo4j publication recovered (#314), and task-0177, response sizes bounded (#315).
- **Third tranche:** task-0176, the heap a load needs (#318), and task-0178, the register panel shows what an update withdrew (#317).

All four limits that task-0173 minted are closed. The limits left are the thirteen doc-0028 §10 proposes as 1.0 limits, and naming them is the maintainer's word.

**task-0163's budget, measured.** The measurement was a re-run of #318's PR harness, with 4 other runs active:
- `rdflib-readers` took 10.1 min, under the 12-minute budget;
- `rdflib` took 17.2 min, over it, because today's checks landed in the record half.

AC #2 stays open. task-0180 is minted, not started: the round trip as a third parallel job.

**What next: nothing more is dispatched in this window.**

| Box | Content |
|---|---|
| Problem | What to start in the time left, with the delegation ending at ~17:00. |
| Today | The open To Do tasks are the maintainer's to decide, gated on the pilot, or parked:<br>- the maintainer's: task-0058, the licence; task-0060, the entity; task-0061, the name; task-0174, the format scheme; task-0179, the Claude row's upstream key; task-0180, which adds a required check;<br>- at the pilot: task-0057, task-0103, task-0108 and task-0125;<br>- parked: task-0073, task-0104, task-0153, task-0154 and task-0164;<br>- spikes: task-0008 and task-0053;<br>- task-0074 and task-0123 propose changes to ieam-register and to the source tool. |
| Solution | Start nothing new. Merge what is open, record, and hand over. |
| Cost | Idle sessions for the rest of the window. |
| Risk | None of note: every candidate needs the maintainer's word or the pilot. |

- **Fit/gap.** The delegation says to derive advice and execute it. Here the honest advice is to stop: starting a maintainer-held or pilot-gated task would exceed it. task-0180 needs a ruleset change.
- **SWOT.**
  - Strengths: the record ends clean, with no half-built work.
  - Weaknesses: idle capacity.
  - Opportunities: the maintainer returns to a short, decision-only list.
  - Threats: none.
- **Advice, executed:** stop dispatching. Summarise on the queue page, and leave the maintainer's list as the queue page's "Yours".
