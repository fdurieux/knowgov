---
id: doc-0020
title: >-
  The full chain up and down over MCP: what travels both ways today, the missing
  hops, opportunity canvas, fit with the backlog, priority
type: specification
created_date: '2026-11-05T20:44:00Z'
updated_date: '2026-11-05T20:53:00Z'
tags:
  - brief
  - mcp
  - impact
  - canvas
  - swot
  - fit-gap
---
*2026-11-05. Maintainer register. A study with a decision on priority. Asked in a side session ("can the knowgov MCP already answer: list all entities, what depends on X?"), taken over by the coordinating session with the maintainer's question: "I asked for the possibility to travel up and down throughout the full chain; what about it?" Read on `main` at `a994095`, register v0.2.9 vendored. Executed: `demo/register/tools/impact.py` from APP-0002 (dependants) and CAP-0002 (realisers). Read only: `harness/mcp_server.py` (TOOLS, READS), `harness/trace.py`, `harness/code_map.py`, `harness/citation.py`, `subjects/cargo_quote/register_map.toml`, the saved queries in `harness/store_neo4j.py`. Public synthetic content only.*

## Verdict

**Half of the chain travels both ways today; the other half travels down only, and the code end is reachable from the CLI but not from the MCP server.**

- **The register leg goes both ways.**
  - `register_impact` walks `dependants`, which goes up from the technical layer towards the business layer. Measured: APP-0002 reaches PROC-0001/0002, CAP-0004, PRD-0002, JRN-0001/0002 (10 edges).
  - `realisers` goes down from a capability to what implements it. Measured: CAP-0002 reaches PROC-0004, then APP-0003.
  - `children` descends the hierarchy.
- **Climbing the hierarchy is missing.** The walk never climbs `parent`, so CAP-0002 does not say it sits under CAP-0001. `register_impact` names the node's parent (one level) and no further.
- **The knowledge leg goes down only.**
  - Node to keys: `register_impact` lists the `register_map.toml` keys on what it reached, with their levels.
  - Keys to statements, documents and verifications: `evidence_bundle` or `gate_verdict` with `keys`.
  - Statements to derived outputs: only the *suspect* ones.
  - Nothing goes back up: a key to the register nodes it concerns, a derived output to the statements it used, a document to its keys.
- **The code end is CLI only.**
  - `harness/trace.py` maps a code path to its application (`code_map.toml`), the keys its header cites (`citation.py`) and its ledger entry (keys used, commit, digest).
  - No MCP tool takes a code path.
- **There is no listing to start from.**
  - The register: none over MCP (the page's register card lists it).
  - The store: `store_status` gives declared keys only, and `census` gives counts only.
  - Unit ORG-x reaching nothing is the register's decision 0010 (`owns` is shown, never walked). "What does ORG-x own" is a listing, not a walk.

## The chain, hop by hop

| Hop | Down (strategy → code) | Up (code → strategy) |
|---|---|---|
| Hierarchy: domain, capability, sub-capability | `register_impact children` (MCP) | **none**: `parent` is never climbed; one level is named |
| Register layers: CAP, PRD, JRN, PROC, APP, ENT | `register_impact walk=realisers` (MCP) | `register_impact walk=dependants` (MCP) |
| Register node and knowledge key | `register_impact` lists the keys on reached nodes (MCP) | **none**: key → nodes is `register_map.toml` read in reverse, used only for a finding's owner |
| Key, statements, documents | `evidence_bundle keys`, `three_valued_answer` (MCP) | **none** over MCP; the `register-cites` saved query (Browser) joins documents to the register |
| Statement and derived output | suspect only (`gate_verdict`, `register_impact`, `evidence_bundle`) | **none** over MCP |
| Derived output, code file, application | the trace ledger (CLI) | `trace.py check`, code path → application and cited keys (CLI) |
| Where to start | **none**: no register listing over MCP, no store listing beyond declared keys | |

## Why not one tool that walks everything both ways

doc-0011 §1 measured it. Under its ALL row (every relationship in both directions), every CargoQuote start reached the same 15 nodes, ORG-0001 included. The answer becomes "the slice this node is in", which the reader already knows. The walks work because each names its direction:
- `dependants`: what rests on X;
- `realisers`: what implements X;
- `children`: what sits under X.

The full chain both ways is therefore **named hops an assistant composes**, never one undirected flood:
- **Down**, from a capability to code: `register_impact walk=realisers`, then `evidence_bundle keys=…` for the keys it lands on, then the outputs built on those keys.
- **Up**, from a code file to the business: the file's application and cited keys, then the register nodes those keys concern, then `register_impact walk=dependants` from them, then the node's ancestors.

Each missing hop is one small read-only tool. The composition is written once in the server's instructions.

## Opportunity canvas

| Box | Content |
|---|---|
| Problem | An assistant (or an architect through one) can go down from a capability to the keys and their evidence, and up from an application to the business. It cannot start from a code file, a key or a document and climb back, cannot climb the hierarchy, cannot see every output built on a key, and has nowhere to start without knowing an id. |
| Who | The architect asking "what does this capability rest on, down to code". The developer asking "which business process does this file serve, and under which capability". The data owner asking "what is built on this key". The lighthouse pilot's architects (task-0062), through doc-0008's impact mapping. |
| Today | Two named register walks and descent (MCP); node → keys → statements (MCP); suspect outputs only; code ↔ application ↔ keys in `trace.py` (CLI); a register listing on the page only; the Browser's saved queries (console text, one start each). |
| Solution | C1 `register_nodes`: the register's nodes listed and filtered, with lineage (ancestors to the root, children) as annotation. C2 upward joins with no store: key → register nodes (`register_map.toml`), code path → application, cited keys and ledger entry. C3 store reads on both adapters: every key the held scenario holds with its level, and every derived output built on a key (any state) with the statements it used. Plus the server's instructions naming the down and up sequences. Rejected: C5, one tool that walks everything both ways (doc-0011's ALL row). |
| Measure | From the example instance, a code file climbs to its capability and the capability's ancestors in at most four calls, and a capability descends to its keys, statements and outputs in at most three. `register_nodes` returns all 8 vendored capabilities, and CAP-0002's lineage reads CAP-0001. For C3, `check_mcp_server.py` holds the new reads equal on Neo4j and rdflib. |
| Cost | C1: small (the register's own loader, no store). C2: small to medium (code_map, citation and the ledger are built; the server needs the instance and ledger paths as configuration). C3: medium (one read per adapter, `READS`, the parity check). All three are new read-only tools: a minor version at the next release, with lines under CHANGELOG's Unreleased. |
| Risk | C3 adds store reads while task-0141 S1 (read-only handles) and S2 (generation-pinned reads) rework the adapters and the MCP lifecycle: built first, they would be built twice. A real register's size calls for a limit and a total on C1. Lineage must stay an annotation; showing ancestors as reached nodes would reopen decision 0014 ("parent adds starts, never steps"). |

## SWOT

- **S.** Every hop's logic exists: the register's walks, `register_map.toml`, the store's `USED_ASSERTION`, `code_map.app_of`, `citation.read`, the trace ledger. The work is exposure, not invention.
- **W.** The code end depends on an instance's `code_map.toml` and on a ledger being written (`trace.py register`). Without either, C2's code leg says unchecked. The register's application → repository link is still a proposal (task-0125, at the pilot).
- **O.** It turns the MCP server from "may I build on this" into the impact-mapping surface doc-0008 promises an adopter, and it gives the pilot's architects the question they ask first.
- **T.** Drift between a composed MCP answer and the page's impact panel or the Browser's saved queries. Mitigation: the hops reuse the register's `impact.py` and the port's reads, never a second walker.

## Fit with the backlog

| Item | Relation |
|---|---|
| task-0141 (HIGH, critical fixes) | **C3 waits on task-0141.02 (S1).** S1 changes how the MCP server opens the store (read-only handles); a new store read lands on that contract. C1 and C2 open no store and can proceed alongside. |
| task-0097 (LOW, one read-only store handle per process) | Overtaken in part by S1. Re-read it when S1 merges; C3 does not depend on it. |
| task-0125 (LOW, parked, `implemented_by` application → repository) | C2 reads the instance's `code_map.toml` now. The register's link, once approved at the pilot, would be a second source for the same hop. No conflict. |
| task-0062, task-0063 (HIGH, lighthouse) | The pilot's architects are the readers. Not blocking; C1 and C2 make the pilot's demonstration of impact mapping possible over MCP. |
| task-0139, task-0140 (spikes) | Independent. |
| doc-0011 §1, decisions 0010, 0012, 0014 (register) | C1 to C3 add no walk and no relationship. Lineage is annotation, like the owner. Nothing goes to ieam-register. |

## Decision

Taken by the coordinating session on the maintainer's ask to "decide on a priority":
- **C1 and C2: MEDIUM, now**, in one session, two tasks and two PRs, alongside task-0141. They touch the MCP server's tool table and new modules, not the store or the HTTP handler.
- **C3: MEDIUM, after task-0141.02 (S1) merges.** Recorded as a dependency.
- **C5 (one bidirectional walk): rejected** on doc-0011's measurement.
- Each new tool adds its line under CHANGELOG's `## Unreleased`. Together they set the next minor version (0.7.0) at the release.

**2026-11-05, the maintainer: "make these functionalities available via the MCP".** All three tasks are tools on the read-only `knowgov` server. The shipped `managed-mcp-allowlist.json` admits that server by name, so a new tool reaches every configured client with no client change. Each task now says so in an acceptance criterion. One hop in the table above had no task: a document up to its keys and register links. It is added in two halves:
- **task-0143:** the register links whose evidence cites a document, from the register's files;
- **task-0144:** the statements a document yields in the held scenario, and the outputs that used them.

With the three tasks built, every hop in the table is reachable over MCP. Two features stay outside it by design:
- `trace.py check`, the CI hook over a change's files. Its lookup half is task-0143's; the check itself runs on a diff in CI.
- The page's own panels, which these tools answer read for read.
