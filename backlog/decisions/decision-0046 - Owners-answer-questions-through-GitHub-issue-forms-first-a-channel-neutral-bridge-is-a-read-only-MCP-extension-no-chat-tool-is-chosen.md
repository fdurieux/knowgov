---
id: decision-0046
title: >-
  Owners answer questions through GitHub issue forms first; a channel-neutral
  bridge is a read-only MCP extension; no chat tool is chosen
date: '2026-11-16T17:41:00Z'
status: proposed
---
*Proposed. Drafted by the coordinating session on the maintainer's word, 2026-11-16: "Github first, but no decision on a chat tool. Could it be as an MCP?", then "redraft decision-0046". Approval is the maintainer's word (ieam-register decision 0019's rule, which knowgov follows).*

## Context

`harness/capture.py questionnaire` writes one TOML file per owner unit; `ingest` takes an answered file back as assertions of basis `elicited`, status `proposed`, attributed to an issued handle. Nothing in knowgov puts a question in front of a person or carries the answer back: today a file goes out and a file comes back.

A private instance has the first such need: two owner units, 197 questions, each now joined to its evidence (the requirement as stated, the code sections it rests on with comments and permalinks, the comments that agree or contradict, the open questions that cite it), every source file held to the register export's digests. A like-for-like comparison of GitHub issue forms, Slack and Teams put GitHub first: the questions' evidence already lives in the repository, an issue form prefills by URL, an answer lands as an issue the repository keeps, and no bot needs a public endpoint. Teams needs an Azure Bot Service endpoint (Office 365 connectors are retired in favour of Workflows); Slack's Socket Mode is outbound only but needs an app in each workspace.

The maintainer chose GitHub first and declined to choose a chat tool, and asked whether the bridge could be an MCP server. knowgov's server (`harness/mcp_server.py`) is read-only by design: the store sits behind a view that lets the port's reads through and nothing else, and the prompts capability is the reader's only. `capture.py`'s rule stands beside it: a model's output can never be ingested, because an answer needs a person's handle.

## Decision

1. **GitHub issue forms are the first route.** A question goes out as a prefilled link to an issue form (the key, the subject, the scenario, the owner unit; a verdict; the statement prefilled for editing in place; a note). The person opens the issue; nothing is opened or posted on their behalf. A reader turns submitted issues into an answered questionnaire that `capture.py ingest` takes unchanged, the giver an issued handle, never a login. The reader and the form live in the instance (its repository, its CI), not in `harness/`, until a pilot shows the route works.
2. **The channel-neutral bridge, when built, is a read-only extension of the MCP server.** Three tools, each under the server's existing contracts (schemas, `inputSchema` refusals, one read handle per call, both transports):
   - `pending_questions(handle)`: a handle's open items, from the questionnaires and the captures already ingested;
   - `question_evidence(key)`: one item's evidence as the instance generated it;
   - `answer_link(key, verdict, statement)`: the prefilled form URL, computed, nothing written.
   Any MCP client can then walk a person through their questions and hand them the link; the person submits in GitHub. The server gains no write tool, and no client records an answer.
3. **No chat tool is chosen.** Claude Desktop and claude.ai already reach the server; Microsoft Copilot Studio can add an MCP server's tools to an agent published to Teams (preview at this date); Slack documents Slackbot as an MCP client. Which of them an organisation uses is its own choice, outside this decision.
4. **Order.** The pilot first (decision 1, in the instance). The MCP tools are minted as a task only once the pilot's answers have gone through `ingest` and the maintainer has read them; the task's schemas follow the pilot's form, not the reverse.

## Consequences

- No contract of knowgov changes now. The MCP tools, when minted, are additive (new tools, new schemas) and land in a minor release.
- An answer's attestation stays the person's own act in a system that records who did it; the MCP side never holds or forwards an answer.
- A remote client needs the server over Streamable HTTP with `KG_MCP_TOKEN` (any bind wider than 127.0.0.1); stdio and the SSH route stay as they are. An organisation's admins decide which MCP tools their clients may call.
- The login-to-handle mapping a reader needs is the instance's, under ieam-register decision 0008's handles; where it lives is the instance's choice, raised by the pilot.
- Answering inside a chat, without the GitHub step, is out of scope: it would need a decision on how a person's answer is proven when a model carries it.

## Opportunity canvas

- **Problem:** owners answer where they already work; a TOML file round trip asks them to work where knowgov does.
- **Who is served:** the owner units of an instance; the maintainer reviewing their answers; an adopter whose staff live in one chat tool.
- **Solution:** a form link per question now; later, read-only MCP tools that any client can present.
- **What it costs:** an issue form, a link generator and a reader in the instance; later three read tools with schemas and tests.
- **How we know it worked:** the pilot's answers pass `ingest` unchanged and read back as `elicited`, `proposed`, under the giver's handle; no answer is ever attributed to a model.

## Fit/gap

| it must | fit or gap |
|---|---|
| keep an answer a person's act under an issued handle | fit: the person submits in GitHub; the reader maps the account to a handle; `ingest` checks the handle |
| keep the MCP server read-only | fit: the three tools read or compute; none writes |
| choose no chat tool | fit: any MCP client; none is named as the route |
| put no name in the record | fit: handles only; gap, open: the login-to-handle mapping holds a login, its place the instance's to settle |
| reach a person outside GitHub | gap, accepted: the person still finishes in GitHub |
| work for a remote client | gap: Streamable HTTP with a token is needed beyond 127.0.0.1; client-side MCP support is preview in one vendor |

## SWOT

- **Strengths:** no new write path; the server, its transports and its tests exist; GitHub keeps who answered and when.
- **Weaknesses:** a context switch from chat to GitHub for the submit; GitHub accounts for every answering person.
- **Opportunities:** the same `answer_link` serves the pilot's static links and every MCP client; a client vendor's change does not touch knowgov.
- **Threats:** pressure to answer "inside the chat" reopens the write question; a client's admin may block the tools; a vendor's preview MCP support may change.

## Advice

Accept it as written. It takes the route the comparison favoured, keeps the one property that matters (a person, under a handle, gives the answer), and defers both the build and the chat tool until a pilot has shown the form route carries answers into `ingest` unchanged.
