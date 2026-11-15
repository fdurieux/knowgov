---
id: decision-0044
title: >-
  The AI-governance quadrant is not a target before the lighthouse; a public
  subject's content may change in 0.9.x with the record untouched; the design
  class's 21 keys get owners
date: '2026-11-15T14:36:00Z'
status: accepted
---

## Context

The market investigation of 2026-11-15 put eight questions to the maintainer; decision-0043 recorded questions 4–6. On 2026-11-15 the maintainer answered the last three: "1. No, as proposed; 2. Yes, explicitly; 3. Yes, as proposed".

- **Question 1:** should knowgov aim for the AI-governance-platforms Magic Quadrant now? The drafts proposed it as the most plausible quadrant. The record's own external pass (doc-0012 §9) already put ServiceNow, an AI-governance Leader by vendor report, in knowgov's governed-context corner. decision-0025 leaves the buyer-facing name open until the lighthouse (task-0061).
- **Question 2:** does a change to a public subject's content fall outside the 0.9 freeze, when the scored record and its comparator are untouched? The public subjects are `subjects/cargo_quote` and `subjects/jef_data_load`; subject content is a `[tasks.*]` table or `register_map.toml` rows, for example. decision-0016 point 2 makes 0.9.x fixes only, and point 3 lists the contracts. A subject's content is none of them, but the freeze did not say so.
- **Question 3:** should the design task class's unowned keys get owners now? In CargoQuote's `register_map.toml`, 21 of `[tasks.design]`'s 36 keys have no row, so a design sign-off routes to no owner:
  - `REQ-01..08|text`;
  - `REQ-01..08|implemented_by`;
  - five `|uses:` links.

## Options and choice

- **Question 1:**
  - (a) No: keep the quadrant as one of two buyer framings to test at the lighthouse, beside the EA framing;
  - (b) yes, as the target now;
  - (c) drop the framing.
- **Question 2:**
  - (a) yes, explicitly, with the record and the comparator untouched;
  - (b) no, wait for 1.0.x.
- **Question 3:**
  - (a) yes: ORG-0001 owns the `REQ-*` keys and ORG-0002 owns the `uses:` links, following the map's existing convention for the API's behaviour;
  - (b) yes, with other owners;
  - (c) not now.

**Chosen by the maintainer, 2026-11-15: 1 (a), 2 (a), 3 (a).**

1. **The AI-governance quadrant is not a target now.** It is one of two buyer framings to test with the lighthouse's buyer, beside the EA framing ("Before an AI agent builds on what your architecture says, know whether it is true", doc-0012). decision-0025's sequencing stands. The outcome lands as a reopen trigger in doc-0012 §7 when the lighthouse reports. The integration half, route B, is decision-0043's.
2. **A public subject's content may change in 0.9.x**, under three conditions:
   - the scored record is untouched: the deterministic run's comparator shows no differing leaf on either store;
   - the comparator and its record are not edited;
   - no contract under decision-0016 point 3 moves.

   A change that would move the record still needs the maintainer's word, as before. This applies to `subjects/cargo_quote` and `subjects/jef_data_load`. It does not extend to a subject's format version, the manifest's schema or any `KG_*` setting.
3. **The 21 design-class keys get owners now:** ORG-0001 for `REQ-01..08|text` and `REQ-01..08|implemented_by`, and ORG-0002 for the five `|uses:` links. The maintainer approves the rows by these words. The map's approval fields name them as this record's.

## Opportunity canvas

| Box | Content |
|---|---|
| Problem | The drafts proposed a quadrant before any adopter. The freeze's reach over subject content was unstated, which blocked task-0210 (the `test` class) and the design-class owners. A design sign-off routes to no owner for 21 keys. |
| Users | The lighthouse's buyer, who picks the category; a squad running design tasks on CargoQuote, which needs an owner to route to; the maintainer, keeping the soak intact. |
| Proposal | No quadrant target. Subject content allowed in 0.9.x with the record untouched. Owners for the 21 keys now. |
| Unique value | task-0210 and the owner rows can land before 1.0.0 without restarting the soak. The category is chosen with a buyer, not before one. |
| Cost | One register-map change and its test; task-0210 when dispatched; proving the record unchanged on both stores for each change. |
| Risk | A subject change that moves the record unnoticed. The comparator on both stores is the guard, and a change that moves it stops. A stand-in owner (ORG-0001, ORG-0002) reads as real. The units are marked stand-in in the register already. |

## Fit/gap

| Must satisfy | Fit | Gap |
|---|---|---|
| decision-0016 point 2: 0.9.x carries fixes only | subject content is not a point 3 contract; this states it | none, now that it is stated |
| decision-0016 A1 condition 2: no contract change in the soak | the record, the comparator and every point 3 contract are untouched | each subject change must prove it on both stores |
| decision-0025: buyer-facing name open until the lighthouse | question 1 keeps it open | none |
| The scored record | comparator 0 differing leaves is the condition | **unverified until built:** an owner row may change a finding's `owner`/`route` in the deterministic output; if it does, the change stops and comes back |
| `register_map.toml`'s approval and `keys_expected` | rows approved by this record; `keys_expected` moves with its test | none |
| CLAUDE.md Boundaries | public demo content only | none |

## SWOT

- **Strengths**
  - Unblocks two pre-1.0 improvements at no contract cost.
  - Keeps the category decision with the buyer.
  - Owners make the design sign-off routable.
- **Weaknesses**
  - Every subject change carries a two-store proof.
  - The owners are stand-ins.
- **Opportunities**
  - task-0210's `test` class in 0.9.x.
  - A cleaner design walkthrough for the lighthouse.
- **Threats**
  - A record change slipping through.
  - The AI-governance quadrant forming its definition without knowgov in it.

## Advice

As chosen, for three reasons:
- The quadrant is out of reach before an adopter and is the buyer's choice.
- Subject content is not a contract, and saying so costs nothing while the comparator guards the record.
- An unowned design key routes nowhere, which is the gap a squad meets first.

## Consequences

- **Question 1:** no quadrant work. The lighthouse tests both framings, and doc-0012 §7 gains the trigger when it reports.
- **Question 2:** task-0210 may land in 0.9.x under these conditions; it is not dispatched by this record.
- **Question 3:** a build adds the 21 rows to `subjects/cargo_quote/register_map.toml` and moves `keys_expected` and its test. It proves the comparator shows 0 differing leaves on rdflib and Neo4j. If it does not, it stops and reports.
