---
id: decision-0048
title: >-
  A cut or large MCP result says so: io.knowgov/clipped on what the reader cuts,
  io.knowgov/large over a client budget, nothing truncated
date: '2026-11-27T21:22:24Z'
status: accepted
---
## Context

<!-- SECTION:CONTEXT:BEGIN -->
task-0365 (0.10.0). An assistant reading a private subject's gate report over MCP summarised a report too large to read whole, carried a wrong count forward and inferred a link no tool states. The 156,000-character report was cut by the client, not the server: the reader never truncates, and an answer over KG_MCP_MAX_RESPONSE (16 MiB) is refused whole (task-0177). Only two tools return part of what they hold: register_nodes past its limit (100 by default, at most 1000) and scenario_runs past its limit. A client hands the model a result's content and seldom its _meta, so a mark only in _meta reaches client code, not the assistant.

Taken by the coordinating session under the maintainer's delegation of 2026-11-27 ('0025 + any knowgov task decision'), while the maintainer was away. Drafted by the building session; option B, with three conditions the coordinator set: an unmarked result byte-identical, the budget a bounded contract setting citing no vendor fact, this record.

## Opportunity canvas

- **Problem:** an assistant reads part of a result and generalises from the sample.
- **Who is served:** assistants over MCP, and the people who read their answers.
- **Solution:** the reader marks what it cut and what is large enough for a client to cut, with the full count and the narrower call, in _meta and in words before the answer.
- **What it costs:** one bounded setting, two _meta objects with a schema, a per-tool count and narrower-call table; no structuredContent schema moves.
- **How we know it worked:** check_mcp_server.py holds a clipped, a large and a plain case equal over stdio and HTTP, on rdflib and Neo4j.

## Fit/gap

| it must | fit or gap |
|---|---|
| mark every result cut to fit, with partial, the full count and the narrower call (AC1) | fit: io.knowgov/clipped on register_nodes and scenario_runs past their limits; the over-cap refusal names its size and the narrower call |
| leave an uncut result unmarked (AC2) | fit: an answer that holds everything and fits the budget is byte-identical to before |
| the same on both transports and stores (AC2) | fit: computed from the tool's answer and its text |
| reach the model, not only the client | fit: each mark is a text item before the answer |
| keep task-0177's whole-or-error rule | fit: nothing is truncated; a large answer is whole |
| cover a cut the client makes | gap, partly: the server cannot see it; the large mark names the risk before the client cuts, and a client whose limit is below the budget still cuts unmarked unless the instance lowers KG_MCP_CLIENT_BUDGET |
| keep content[0] readers working | gap, accepted: a marked result's content[0] is the notice; the answer is the last text item, and the CHANGELOG says so |

## SWOT

- **Strengths:** no truncation; the mark reaches the model; unmarked results unchanged; one rule on both transports and stores.
- **Weaknesses:** a new setting; a per-tool count and narrower-call table to keep current; a marked result's content[0] is no longer the answer.
- **Opportunities:** task-0367's reader instructions can tell the assistant to obey the marks; a client can act on _meta in code.
- **Threats:** a client cutting below the budget still cuts unmarked; a client that ignores leading text items sees only the answer.
<!-- SECTION:CONTEXT:END -->

## Decision

<!-- SECTION:DECISION:BEGIN -->
1. **What the reader cuts says so.** register_nodes past its limit and scenario_runs past its limit carry _meta["io.knowgov/clipped"] = {partial: true, what (nodes or runs), returned, total, narrower}. An answer refused over KG_MCP_MAX_RESPONSE carries the same object, what bytes, returned 0 and total its size, and its text names the narrower call.
2. **A large answer is whole and says so.** An answer whose text is over KG_MCP_CLIENT_BUDGET characters carries _meta["io.knowgov/large"] = {partial: false, chars, budget, count: {what, n} or null, narrower}. Nothing is cut: task-0177's whole-or-error rule is kept.
3. **KG_MCP_CLIENT_BUDGET** is a bounded contract setting: an int from 1,000 to 1 GiB, default 100,000, set below the response limits common MCP clients apply. A value outside the bounds exits 2 at start, like the other bounded settings.
4. **Each mark is also a text item, in words, before the answer.** The answer stays the last text item, unchanged, and structuredContent. A result with no mark is byte for byte what it was. A client that parsed content[0] as the answer takes the last text item, or structuredContent.
5. **The fields are pinned** by harness/schemas/result-meta.schema.json. The per-tool count and narrower call live in harness/result_marks.py.

## Advice

Take B, as the coordinator did. It marks every cut the server makes (AC1). It leaves every result that is whole and within the budget untouched (AC2). And it reaches the model in the case that caused the incident, a whole answer too large for the client, without giving up the rule that an answer is whole or an error. C, the server clipping to the budget, would hand the assistant the very partial report the incident warns of. A alone would leave that case unmarked.
<!-- SECTION:DECISION:END -->

## Consequences

<!-- SECTION:CONSEQUENCES:BEGIN -->
- A contract change in 0.10.0. It adds one setting (the settings table: 67 contracts of 107), two _meta objects, a schema and leading text items on marked results.
- In-repo readers that parsed content[0] as the answer now read the last text item.
- task-0367's instructions can rely on the marks.
<!-- SECTION:CONSEQUENCES:END -->

## Alternatives

<!-- SECTION:ALTERNATIVES:BEGIN -->
- **A: mark only the server's own cuts.** Fits the criteria literally, but leaves the incident's case, a whole answer the client cuts, unmarked.
- **C: the server clips to the budget and marks the result partial.** Reverses task-0177. A partial gate report is the hazard itself, and every tool would need its own clipping rule.
<!-- SECTION:ALTERNATIVES:END -->

