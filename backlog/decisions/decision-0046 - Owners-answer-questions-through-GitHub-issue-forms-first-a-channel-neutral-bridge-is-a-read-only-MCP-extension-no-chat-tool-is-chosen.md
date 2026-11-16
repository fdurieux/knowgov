---
id: decision-0046
title: >-
  Owners answer questions through GitHub issue forms first; a channel-neutral
  bridge is a read-only MCP extension; no chat tool is chosen
date: '2026-11-16T17:41:00Z'
status: proposed
---
*Proposed. Drafted by the coordinating session on the maintainer's word, 2026-11-16: "Github first, but no decision on a chat tool. Could it be as an MCP?", then "redraft decision-0046", on the login-to-handle mapping "(a), keep the mapping outside git; add the point to 0046", then "draft the [private instance's] decision and adjust 0046" (the instance's name elided: it is private), and, once ieam-register decision 0021 was approved, "approve decision 0021, then align 0046 and 0003". Approval is the maintainer's word (ieam-register decision 0019's rule, which knowgov follows).*

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
5. **Who holds a handle follows the register (ieam-register decision 0021, approved 2026-11-16).** A handle is one person in one role; who holds it is recorded and never anonymised, in the organisation's own private register (the handle's `person`, its directory identifier) or in its directory, as that register decides; knowgov and any public repository never hold it. The reader resolves an issue's author to a handle through that record: from the register's `person` where the instance keeps it there, else from a file passed at run time. Either way the giver written into the answer is the handle, and the holder is read from the register, not copied into the capture. Fixtures carry invented accounts only. This replaces the earlier wording of this point, which kept the key outside git by default under ieam-register decision 0009 §1, now superseded.
6. **The issue itself names its author.** A submitted issue shows the account that opened it, so the issue tracker is a second record of who answered what, beside the register's. Under decision 0021 that attribution is intended and kept, under the basis the organisation records before its first capture (purpose, lawful basis, notice, retention, its data-protection officer's approval). An organisation whose answerers are its staff collects answers in systems its directory governs (its own GitHub Enterprise with directory sign-in, or its own forms), so that the account on the issue is the directory's; its retention period covers the issues as it covers the register.

## Consequences

- No contract of knowgov changes now. The MCP tools, when minted, are additive (new tools, new schemas) and land in a minor release.
- An answer's attestation stays the person's own act in a system that records who did it; the MCP side never holds or forwards an answer.
- A remote client needs the server over Streamable HTTP with `KG_MCP_TOKEN` (any bind wider than 127.0.0.1); stdio and the SSH route stay as they are. An organisation's admins decide which MCP tools their clients may call.
- The reader resolves an author to a handle through the register's record of who holds it, or a file passed at run time where the organisation keeps holders in its directory (decision 5); an author it cannot resolve is refused, never misattributed.
- The issues hold the answerer's account until they are deleted (decision 6); deleting them after ingest is the instance's retention choice, and the capture keeps only the handle.
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
| attribute every answer to the person who gave it | fit: the handle names one person in one role, its holder recorded where the register decides (decision 5, ieam-register 0021) |
| keep attribution lawful | gap, accepted: each organisation records its basis before its first capture (ieam-register 0021 §4); knowgov cannot check it |
| reach a person outside GitHub | gap, accepted: the person still finishes in GitHub |
| work for a remote client | gap: Streamable HTTP with a token is needed beyond 127.0.0.1; client-side MCP support is preview in one vendor |

## SWOT

- **Strengths:** no new write path; the server, its transports and its tests exist; GitHub keeps who answered and when.
- **Weaknesses:** a context switch from chat to GitHub for the submit; GitHub accounts for every answering person.
- **Opportunities:** the same `answer_link` serves the pilot's static links and every MCP client; a client vendor's change does not touch knowgov.
- **Threats:** an organisation going live without its recorded basis (ieam-register 0021 §4); issues on accounts outside the directory, which the register cannot resolve; pressure to answer "inside the chat" reopens the write question; a client's admin may block the tools; a vendor's preview MCP support may change.

## Advice

Accept it as written. It takes the route the comparison favoured, keeps the one property that matters (a person, under a handle, gives the answer), and defers both the build and the chat tool until a pilot has shown the form route carries answers into `ingest` unchanged.
