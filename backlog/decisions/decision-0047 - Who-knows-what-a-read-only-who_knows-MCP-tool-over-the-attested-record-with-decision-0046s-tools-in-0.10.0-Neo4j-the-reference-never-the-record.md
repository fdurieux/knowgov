---
id: decision-0047
title: >-
  Who knows what: a read-only who_knows MCP tool over the attested record, with
  decision-0046's tools in 0.10.0; Neo4j the reference, never the record
date: '2026-11-16T19:15:00Z'
status: accepted
---
*Accepted. The maintainer, 2026-11-16: "accept decisions 0046 and 0047". Drafted by the coordinating session on the maintainer's words, 2026-11-16: "I would like to be able to find the people who have certain knowledge (as they answered one or more questions … or because they have contributed to code, or...) via the knowgov MCP"; on the store, "Neo4j is never the record, however it is the reference", then "Agreed" to the wording of point 1; on timing, "why not do it now? I would like to have this fixed before the lighthouse", then "(A), draft 0047 and dispatch the builds". Approval is the maintainer's word (ieam-register decision 0019's rule, which knowgov follows). The builds it names were dispatched on that word; their pull requests merge once this record and decision-0046 were accepted, which they are.*

## Context

ieam-register decision 0021 (approved 2026-11-16) makes a handle one person in one role and records who holds it, never anonymised, in the organisation's register (`people/handles.toml` `person`) or its directory. knowgov already holds who said what under a handle: a capture's `from` (an answer, or "nobody knows"), a review's ruling, a declared gap's closer. A key maps through `register_map.toml` to register nodes, and a node to its owner unit. Nothing lets a reader ask who knows about a node, a key or a code path.

knowgov's store is a projection: a load wipes it (Neo4j Community serves one database), it holds one scenario of one subject at a time (decision-0013), and every read must answer the same on both adapters. 0.9.0 froze the contracts on 2026-11-12; any contract change in 0.9.x is 0.10.0 and restarts the 30-day soak (decision-0016 point 2, amendment A1). No lighthouse is confirmed.

## Decision

1. **The record and the reference** (the maintainer, 2026-11-16, "Agreed"). The capture files, the register and git are the record. Neo4j is the reference: the graph people and tools query, and the deployment the record runs on. Anything the reference answers, rdflib answers the same.
2. **`who_knows`, a read-only MCP tool.** Input: exactly one of a register node id, a key, or a code path under `code_map.toml`'s root. Output, per handle whose evidence touches it: the handle, its unit and roles, its holder (the register's `person`, or null with `why` when none is recorded), and its evidence, each item one of:
   - `answered`: a captured answer or "nobody knows" on a key resolving to it (the key, the subject, the capture id, `on`);
   - `approved` or `rejected`: a review's ruling by the handle (the review id, `on`);
   - `closed`: a declared gap the handle's unit closed;
   - `owns`: the handle's unit owns the node.
   Items sorted by kind, then key, then date; handles by id. No count used as a rank, no weight, no score. It reads the subjects the reader serves (decision-0013's `KG_SUBJECTS`), their capture folders and reviews, and the one register they share, from files, as `register_nodes` and `key_nodes` do, so it answers the same on either store. A schema `who-knows`, both transports, `check_mcp_server.py` holding its report.
3. **decision-0046's three tools come forward into the same release.** `pending_questions`, `question_evidence` and `answer_link` are built now, beside `who_knows`. This amends decision-0046's point 4, which gated them on the pilot: their schemas follow the issue form already built in the pilot instance (its verdicts and fields), and the pilot's five answers, when given, are their first real input.
4. **0.10.0 carries the four tools** (the maintainer's option (A)), **and the contract changes that waited only for the soak** (the maintainer, 2026-11-16: "Yes"): decision-0041's items deferred to 1.1.0 (task-0342: C5-1, B-X2 and R-T1, B-X8, C2-7, B-N2's gate-only setting), R in the header-citation convention (task-0354) and the reader extensions of tasks 0355 to 0357. Their reason to wait, the unbroken soak, falls with 0.10.0; what each chooses is unchanged. decision-0045's 1.1.0 row, task-0347 and task-0359 stay at 1.1.0: each needs a decision first. Under decision-0016 point 2 it restarts the 30-day soak: 1.0.0 is cut 30 days after 0.10.0 at the earliest, with A1's other conditions unchanged. `CHANGELOG.md`'s Unreleased takes each under its contract-change heading as it merges.
5. **Later steps, named and not in 0.10.0:**
   - **Activity:** git changes mapped through `code_map.toml`, labelled `changed`, never mixed with attested evidence, only where the organisation's recorded basis (ieam-register 0021 §4) names code history, and with its own mapping of git authors to holders.
   - **Walks:** the people around a node (its capability's neighbours, its process thread) by the register's walks; the store's walks may serve them, on both adapters.
6. **Never:** a score or ranking of people; a query across organisations' registers; the store treated as the record.
7. **Holders need the register's `person`.** ieam-register builds decision 0021 and tags it; knowgov re-vendors the register at that tag. Until then `who_knows` returns handles with `holder` null and its `why`.

## Consequences

- Four additive MCP tools and their schemas, decision-0041's deferred items, R citations and three reader extensions: contract changes, 0.10.0, the soak restarted once for all of them.
- The demo register is re-vendored at the ieam-register tag that carries `person`.
- An organisation that serves `who_knows` holders has recorded its basis (ieam-register 0021 §4); the adopter docs say so.
- decision-0046 is accepted with this record; point 3 above amends its point 4.

## Opportunity canvas

- **Problem:** knowledge is captured under handles that now resolve to people, but finding who knows about a capability, a key or a file means reading TOML by hand.
- **Who is served:** a newcomer looking for the expert; a reviewer choosing who approves; an owner seeing whose knowledge a leaver takes; an assistant routing a question.
- **Solution:** `who_knows`, evidence by kind per handle and holder, over the attested record; decision-0046's tools beside it, so a question can be routed and answered through the same server.
- **What it costs:** four tools with schemas and checks; a restarted soak (1.0.0 about a week later than 2026-12-12); the register's `person` build and a re-vendor.
- **How we know it worked:** on the example instance and on a pilot instance after its answers, `who_knows` on a capability returns the handle that answered its keys, its holder resolved, the same report on Neo4j and rdflib and over both transports.

## Fit/gap

| it must | fit or gap |
|---|---|
| answer from the attested record | fit: captures, reviews, gap closes and the register; activity is a later, labelled step |
| keep the MCP server read-only | fit: four read tools; none writes |
| answer the same on both stores | fit: step 1 reads files, as `register_nodes` does |
| resolve a handle to a person | gap, planned: point 7; null with `why` until the re-vendor |
| cover an organisation's subjects | fit: the reader's subjects and their one register; never across registers |
| keep the freeze's promise | gap, accepted: 0.10.0 restarts the soak (decision-0016 point 2), by the maintainer's choice |
| stay lawful | fit where the organisation recorded its basis (ieam-register 0021 §4); knowgov cannot check it |

## SWOT

- **Strengths:** built on attested, dated, owned records; deterministic; no new write path; routes to people, not only units.
- **Weaknesses:** sparse until answers accumulate; holders wait on the register's build; the soak restarts.
- **Opportunities:** a "knowledge at risk" view (keys whose only answerer left); the lighthouse demonstration of routing and finding the expert; activity and walks as later minors.
- **Threats:** a later wish for counts or scores turns a directory into a performance tool; commit activity read as expertise; holders served where no basis was recorded.

## Advice

Accept it with decision-0046. A week's slip of 1.0.0 buys a release that already routes questions to people and finds who knows, which is what the lighthouse will be shown, and the rest of the soak's promise stands.
