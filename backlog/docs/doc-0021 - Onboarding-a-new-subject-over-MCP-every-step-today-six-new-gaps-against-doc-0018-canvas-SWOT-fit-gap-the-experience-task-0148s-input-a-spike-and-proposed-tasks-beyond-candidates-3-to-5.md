---
id: doc-0021
title: >-
  Onboarding a new subject over MCP: every step today, six new gaps against
  doc-0018, canvas, SWOT, fit/gap, the experience; task-0148's input; a spike
  and proposed tasks beyond candidates 3 to 5
type: specification
created_date: '2026-11-05T21:26:00Z'
updated_date: '2026-11-05T21:30:00Z'
tags:
  - canvas
  - swot
  - fit-gap
  - brief
  - mcp
  - subject
  - spike
---
*2026-11-05. Maintainer register. A study read against doc-0018: nothing is built, and the plan below is proposed tasks with no ids. The coordinating session mints them on the maintainer's go. Trigger: the maintainer's ask of this date: "investigate what it would take to onboard a new subject via the MCP, i.e. every single step"; an opportunity canvas, a SWOT and a fit/gap first; then the optimal user experience (frictionless, lean, clear); a plan (spike?) if the case is positive. The session's view: Subject Onboarding over MCP (https://claude.ai/artifact/RJkD5PNdC6uhTdhprriZsU). Evidence: knowgov `main` at `4bc8cfc`, and `5a0037c` checked for drift (task-0140 only). Probes ran in the session on rdflib with the record's pins (rdflib 7.6.0, pyshacl 0.40.2, PyYAML 6.0.3, pumllint 0.33.0): an example instance from `tools/example_instance.py`, a new subject `renewal` added to it, the page started on it (`KG_SUBJECTS`, port 8091), and both MCP servers driven over stdio. All of it lived in the session's scratch space and was committed nowhere. Read beside doc-0018 (its candidates 1, 2 and 9 built: task-0135, decision-0009 with task-0136, task-0134), decision-0008, decision-0009, doc-0016, doc-0017, and the work in flight: task-0141 (H1, H2 change the servers' HTTP handling; X1 contains code execution), task-0142 `register_nodes` (#238) and task-0143's upward joins, both from doc-0020 (#236). Updated the same evening, on the coordinating session's word that the maintainer said go on doc-0018's candidates 3 to 5: task-0146 (`subject_check`), task-0147 (the instance hook) and task-0148 (the `new_subject` and `add_artefact` prompts with a Claude Code skill), in build. This doc is task-0148's user-experience input (§8), and its plan is aimed past those three (§9).*

## Verdict

**Positive, in doc-0018's shape: the MCP guides, informs and checks, and answers for a new subject without reconfiguration. It never writes.** decision-0008 keeps `knowgov` read-only; decision-0009 keeps attestation a person's act; keys come from the task, never from the yield. Against doc-0018, what changed:

- **Built since:**
  - candidate 1, the subject check (task-0135);
  - candidate 2, the attestation rule (decision-0009, task-0136);
  - candidate 9, the README lines (task-0134).
- **Hold on the probe:** F1 to F5. A missing `scenarios.toml` is refused, a misspelt key gets the right did-you-mean, and the missing attestation is a NOTE naming decision-0009.
- **Still open:** F6 (one subject per process), F7 (the branch is invisible to the served store) and F8 (no prompts: `prompts/list` answers `-32601`).
- **New: six findings, G1 to G6 (§2).** Four are small fixes to the check, the page and one mapper. **G4 is structural.** Both MCP servers answer for one subject per process, so every new subject means re-registering two servers in every client.

**Baseline, as enumerated in §3:**
- 27 steps per instance subject, 4 of them reachable through the MCP;
- 3 restarts or re-registrations before the MCP answers for the new subject;
- 3 silent or misleading outcomes on one small probe (G1, G2, G5).

**Two conditions:**
- G4's design is decided by a decision record before it is built: it changes every tool's input schema and the "one subject per process" contract instance/README.md documents.
- The Claude Desktop route is verified, or stated as a limit ("check and ask, no dry run").

**Three of the ten proposals are now in build:** B6 is task-0146, B8 is task-0148 and B9 is task-0147, and B10 is folded into task-0148 (§7). §8 lists what the study changes in task-0148: the leanest flow, MRTR elicitation and the Claude Desktop test. §9 is what lies beyond: a spike and six proposed tasks, two of them (B1, B2) independent of everything.

**Unchanged from doc-0018:**
- **Rejected:** write tools on `knowgov` or a second writing server (decision-0008); model-drafted documents and mappers (decision-0009, task-0041's rule); keys from the yield.
- **Parked:** the server-side dry run (candidate 6). It now also depends on task-0141's X1, since it runs the subject's oracle.

## 1. What the probes ran

The subject `renewal`:
- one requirements file, three rows;
- one task, `codegen`, with four keys: two right, one misspelt (`REQ-03|txt`), one for a requirement nobody wrote (`REQ-04|text`);
- no `[verification]`, no register map.

What came back:

- **`tools/check_subject.py`**
  - With no `scenarios.toml`: ERROR, exit 1 (F3 holds).
  - With `minimal`'s `S0`: exit 0. Two WARNINGs (one wrong, G2), a NOTE `[verification]` (decision-0009), 0.14 s.
  - On `cargo_quote`: 0.19 s.
- **The gate**, `KG_STORE=rdflib gate_cli.py --subject … --scenario S0`: BLOCKED, exit 1, 2 blockers (absent), 2 majors (proposed), each `[owner none in the register map]`, 0.23 s.
- **The reader**, with `KG_SUBJECT` set to the new root:
  - `store_status` lists `S0` and `codegen`;
  - `gate_verdict` reads BLOCKED, exit 1;
  - `three_valued_answer REQ-01|text` reads asserted (proposed, authored);
  - `prompts/list` answers `-32601`;
  - a cold call (process start, subject, store, gate) took 0.17 to 0.27 s on the probe's small store.
- **The page**, started on the instance, then the subject added: `/api/subjects` was unchanged and `/api/scenarios?subject=renewal` answered 404 (`no subject 'renewal' here`). After a restart the subject was listed (G3).
- **`knowgov-runs`**, with `KG_SUBJECT` set and `KG_PAGE_URL` pointing at the page:
  - `run_options` listed the subject;
  - `start_run S0 deterministic` ended `done`, exit 0, `by: mcp`, in under a second, logging "S0: gate BLOCKED — 2 required key(s) at a blocking level".
- **`capture.py questionnaire --scenario S0`**: one file for `unassigned`, 4 of 4 keys (G6).

## 2. New findings

- **G1. A document a mapper reads can yield nothing, and nothing says so.**
  - The cause: `requirements` matches only `| REQ-nn | … |` rows (`harness/extract.py:128`, a literal `REQ-\d+`). It ignores `[rules] requirement_id_pattern`, which only the bundle mappers read (`extract.py:618`).
  - On the probe: with ids `RNW-01` to `RNW-03`, the check printed `yield: 0 key(s) from 1 artefact(s)` and four NOTEs. The report's `yield.artefacts["renewal.md"]` was 0, with no finding on the document itself.
  - Why it matters: an adopter's first document in its own conventions is the likely case, and the check reads it as no knowledge rather than the wrong convention.
- **G2. One yielded key is offered as the did-you-mean of two required keys.**
  - `check_subject.py:314` compares each unyielded required key with `yielded − required` (difflib, 0.8).
  - On the probe: `REQ-03|text` was offered for `REQ-03|txt` (right) and for `REQ-04|text` (wrong: another requirement), both as WARNINGs. Following the second turns a real gap into a duplicate.
  - The fix: a yielded key goes once, to its best match; a match with a different entity is a NOTE at most.
- **G3. The page lists subjects once, at start.**
  - The cause: `demo/app/server.py:101` sets `SUBJECTS = _load_subjects()` at import. The read-only mount is live, but the list is stale until the app restarts.
  - The consequence: until then, `knowgov-runs` cannot run the new subject either (the page answers 404 for its id).
- **G4. Both MCP servers answer for one subject per process.**
  - The cause: both servers take `KG_SUBJECT` at start, and the harness binds `SUBJECT` at import (F6).
  - The cost: a new subject means relaunching both with `-e KG_SUBJECT=/instance/subjects/<id>`, or registering a second pair, and reconnecting the client (`/mcp` in Claude Code, quit and reopen in Claude Desktop). *n* subjects mean *2n* registrations.
  - Why it is fixable: a cold call costs 0.17 to 0.27 s on rdflib, which makes a child process per call with `KG_SUBJECT` set credible. That is how the page already runs the harness, and it is to be measured on CargoQuote and on Neo4j.
- **G5. `short` is required in practice, and its absence is blamed on the document.**
  - The check: `ARTEFACT_REQUIRED = ("key", "family", "format")`, while `extract.short()` indexes `SUBJECT.shorts[key]`.
  - Without `short`, the check says `its mapper cannot read it: KeyError: 'renewal.md' … Fix: fix the document, or give the artefact the mapper of its convention`, and the gate says `cannot run: the store did not answer: KeyError: 'renewal.md'`.
  - Of the artefact's ten fields, three (`family`, `format`, `short`) follow from the kind and the mapper yet must be typed.
- **G6. The questionnaire asks owners for what an attestation would give.**
  - On the probe, it asked for `REQ-01|text` and `REQ-02|text`, which the document states and nobody has attested, and for the misspelt `REQ-03|txt`.
  - This is not a defect: a capture can corroborate a key.
  - It is an ordering rule for the wizard: spelling, then mapper fit, then attestation. Owners are asked only what no document and no attestation can answer.

## 3. Every step today, for an instance subject

The adopter's route (m-8, decision-0006): from an empty subject folder to a gate whose remaining findings are all knowledge with an owner. Phase 0 happens once per organisation:
- an instance repository with `register/`;
- the stack with `docker-compose.instance.yml`;
- the reader and `knowgov-runs` registered, one subject each (G4);
- the managed hook.

| # | Step | By, with | MCP today | Friction |
|---|---|---|---|---|
| 1 | Which register nodes the task touches | assistant | `register_impact` | needs an id to start from; task-0142's `register_nodes` gives the listing |
| 2 | Missing nodes or links: proposal, then a register pull request the owners approve | assistant reads; people approve | `proposal_impact` | a second repository, a second review |
| 3 | Optional: an export landed, `tools/connector.py` | person, CLI | none | |
| 4 | Each document into `artefacts/<kind>/` (twenty kinds, `instance/kinds.toml`) | file tools | none | the kind is a lookup |
| 5 | Its mapper: zero to three per kind, conventions written down nowhere an adopter reads | person or assistant | none | G1 |
| 6 | Form: `preload_check.py` | CLI | none | fourteen kinds unchecked |
| 7 | `[subject]` | hand | none | |
| 8 | `[[artefact]]` per document, up to ten fields | hand | none | G5 |
| 9 | `[tasks.<class>]`: keys, block levels, bar | person, from the task's sources | none | G2 |
| 10 | `[rules] requirement_id_pattern` | hand | none | G1 |
| 11 | `scenarios.toml` with `S0` | copied | none | refused when missing (task-0135) |
| 12 | `register_map.toml` rows | hand | none | checked (task-0135); task-0143's key-to-nodes join helps |
| 13 | `[record] as_of` | hand, optional | none | |
| 14 | Optional: `[reference]`, `[oracle]`, verification map, `prompts/`, `plants.toml`, `queries.toml`, `code_map.toml` rows | hand | none | |
| 15 | Attestation: `[provenance] human`, `[verification] authored`, `approval` | person only (decision-0009) | none | |
| 16 | `check_subject.py` | CLI | none | candidate 3 open |
| 17 | `check_instance.py` | CLI | none | |
| 18 | Dry-run gate on private rdflib | CLI, Claude Code only | none | F7 |
| 19 | Pull request; `instance/ci`; four eyes; merge | people, CI | none | |
| 20 | Restart the page | person | none | G3 |
| 21 | Relaunch `knowgov-runs` for the subject | person | none | G4 |
| 22 | Load `S0`; it wipes the one shared store | page or assistant | `start_run` | displaces what others read |
| 23 | Relaunch the reader; reconnect the client | person | none | G4 |
| 24 | `gate_verdict`, `evidence_bundle`, `three_valued_answer` | assistant | reader | |
| 25 | `capture.py questionnaire` | CLI | none | G6 |
| 26 | Owners answer; `capture.py ingest`; a second person's review | people only (decision-0002, decision-0004) | none | |
| 27 | Reload and gate again | assistant | `start_run`, reader | |

**The public-subject route is heavier, and out of scope for a wizard.** It adds:
- a `[vendor]` table and `tools/vendor_subject.py` at a pumllint tag, with its digest test;
- a register slice in ieam-register at a tag;
- a deterministic record held by the comparator;
- `tests/test_subject.py`'s guards and the CI subsets (`jef_data_load` is named in 18 test files and three workflows).

Three public subjects exist, one of them a fixture.

## 4. Opportunity canvas and SWOT

| Block | Content |
|---|---|
| Users and customers | The platform engineer onboarding the lighthouse's first subjects (m-8, task-0062), in Claude Code in the instance checkout. An analyst adding one document, often in Claude Desktop (no shell). People who receive work from it: the attester, the reviewer, the owners. Not the maintainer adding a public subject |
| Problem | 27 steps, 4 on the MCP; 3 restarts or re-registrations; 3 silent or misleading outcomes after doc-0018's fixes; no check before merge for a Desktop user (F7) |
| Solution | One prompt carries the procedure. Resources carry the conventions: kinds, each mapper's input with an example, the manifest's fields. `subject_check` reads the live mount. A `subject` argument goes on every tool, and the page rescans its subjects. Defaults keep the scaffold to two fields per document. The assistant's own file tools write onto a branch, and a pull request carries the readiness card, the dry-run report and the questionnaires |
| Value | The first honest gate (exit 0 or 1, never 2) the same day. No silent zero yield and no typo sent to an owner. No reconfiguration after the merge. Every gap names an owner and a route |
| Metrics (today → target) | Person actions per subject: 27 steps → 10 or fewer. Steps the MCP reaches: 4 → 15 or more. Restarts: 3 → 0. Silent outcomes on the probe: 3 → 0. Fields per artefact: up to 10 → 2. Spelling blockers: 0. Time to the first honest gate: measured in S6 |
| Channels | Claude Code: `/mcp__knowgov__new_subject`, `@knowgov:` resources, the CLI dry run. A skill with the same text for clients without prompts. Claude Desktop through the reader (S1). The instance's CI through `check_instance.py` |
| Cost | Ten small-to-medium proposals, three now in build (task-0146 to task-0148) and one folded in; B7 (G4) medium-to-large, behind a decision. Contract changes: one layout refusal, one tool, the `subject` argument, prompts and resources in the capabilities. Each additive or minor while 0.x (decision-0003), under `## Unreleased` |
| Risks | The model drafting content: decision-0009, the never-list, the hook. A `subject` argument as a confused deputy: ids resolved under `KG_SUBJECTS` only, never a path, as `baseline` already refuses one. The shared store: a load displaces what others read, so the dry run stays on private rdflib. Spec churn: in 2026-07-28, elicitation moved to multi-round-trip results |
| Unfair advantage | An honest stop condition, decided by the same gate that blocks the build later, and the yield shown before anything is loaded |

- **Strengths.**
  - Every check exists and is fast: 0.14 to 0.27 s.
  - The read-only contract and doc-0017's held-in-call pattern shape the MCP side.
  - decision-0009 removes the laundering.
  - The server already speaks 2026-07-28 (task-0079), where multi-round-trip results fit.
  - The capture route and the hook pattern exist (task-0099, task-0105).
  - *Response:* the wizard is mostly text over the check.
- **Weaknesses.**
  - Fifteen mappers in two kits' conventions (G1).
  - One subject per process (G4, F6); a stale page list (G3).
  - One shared store; no shell in Desktop (F7); no prompts (F8).
  - One maintainer.
  - *Response:* report a zero yield as mapper demand, by kind; take G4 by a child process per call if S3's numbers allow it.
- **Opportunities.**
  - The lighthouse's first hour: an ARIS export through aris2puml into PlantUML, then a subject.
  - Claude Code documents MCP prompts as slash commands with positional arguments (code.claude.com/docs/en/mcp), resources as `@server:uri` mentions, and elicitation in form and URL modes with `Elicitation` and `ElicitationResult` hooks.
  - task-0008's aris2puml pilot corpus is a ready dogfood subject.
  - *Response:* S6 on real content where it can.
- **Threats.**
  - Shallow subjects, until BLOCKED becomes noise.
  - Convenience against four eyes.
  - Desktop support for local servers' prompts and resources is unconfirmed on any official page.
  - A multi-subject reader as a confused deputy.
  - The protocol moving: in 2026-07-28, server-to-client requests such as `elicitation/create` go through MRTR. `resultType: "input_required"` comes from `prompts/get`, `resources/read` or `tools/call`, with a `requestState` the client echoes (modelcontextprotocol.io/specification/2026-07-28/basic/patterns/mrtr).
  - *Response:* one subject per pull request; denominators in the report; ids under `KG_SUBJECTS` only; elicitation optional and last.

## 5. Fit/gap

| Steps | Fit/gap | Target | Proposed |
|---|---|---|---|
| Phase 0 registrations | gap G4 | registered once; `list_subjects`, and `subject` on every tool | B7 |
| 1–2 | fit | the prompt calls `register_nodes` (task-0142), `register_impact` and `proposal_impact` first; unmapped nodes seed the map | task-0148 |
| 4 | gap | the folder proposed from the kinds table in the prompt, confirmed by the person | B3, task-0148 |
| 5 | gap G1 | each mapper of the kind tried deterministically, each yield shown, one above zero chosen; a zero yield a WARNING naming the convention | B1, B3, B5 |
| 6 | fit | the assistant runs it; the baseline stays the owner's commit | |
| 7–8 | gap G5 | scaffolded; `path` and `mapper` only, the rest defaulted | B1, B4 |
| 9 | gap G2 | keys proposed from the task's sources, the yield shown beside, never as the list | B1, task-0148 |
| 10 | gap G1 | set from the document's ids; the mapper honours it | B5 |
| 11–14 | gap | `S0`, `as_of` and map rows scaffolded (map rows through task-0143's join); optional tables named, left out | task-0148 |
| 15 | fit | person only; the stanza written commented out, with what its absence costs; the hook refuses an assistant edit | task-0147 |
| 16–17 | gap | after every write: `subject_check` (MCP, held in the call) or the CLI | task-0146 |
| 18 | gap F7 | Claude Code on private rdflib; Desktop stated as a limit | parked |
| 19 | fit | the PR body carries the readiness card | task-0148 |
| 20 | gap G3 | the page rescans | B2 |
| 21, 23 | gap G4 | the `subject` argument | B7 |
| 22, 24, 27 | fit | the prompt's last step, saying the load displaces the shared store | |
| 25 | gap G6 | after spelling, mapper fit and attestation | task-0148 |
| 26 | fit | people only | |

## 6. The experience

1. **One way in.**
   - In Claude Code: `/mcp__knowgov__new_subject <id> <task>` (positional arguments, split on whitespace).
   - Elsewhere: the same text as a skill (`.claude/skills/knowgov-onboard/SKILL.md` in the instance, or in a plugin), or in plain words, since the server's instructions name the prompt.
2. **At most five questions, only what only a person knows:**
   - what the subject is for;
   - the task and what it builds;
   - which documents;
   - which owning units, picked from the register's candidates;
   - who attests, or "nobody yet", costed.

   Everything else is derived: the kind folder, the mapper by trial yield, the artefact fields, `S0`, and the block levels and bar from `subjects/minimal/`.
3. **Show before writing.**
   - Per document: its kind, its mapper, what it yields, its form check.
   - Per key: yielded or not, the did-you-mean, the owner.
   - In plain words, each finding with its fix.
4. **Check after every write, deterministically.** The check decides, never the model. A model that judges a step done becomes a second, softer gate (doc-0018 §3).
5. **Never write what a person must vouch for.** The attestation stanza goes in commented out, with a placeholder handle. The cost of its absence is stated ("BLOCKED by `max_unverified_share` until employee-2 attests"), and the hook refuses an assistant edit there.
6. **Fix in order:** spelling, then mapper fit, then attestation, then questionnaires (G6).
7. **The stop condition, said out loud:**
   - the check exits 0 with no WARNING;
   - the dry run exits 0 or 1, never 2;
   - every remaining finding is knowledge with an owner and a route.

   Then the pull request.
8. **Nothing to reconfigure after the merge.** The page rescans and the servers take `subject`. "Load `S0` and ask the gate" is the prompt's last step, with the warning that the load displaces the store others read.

**Seven person actions in place of 27 steps:**
1. invoke;
2. answer;
3. confirm the card;
4. attest;
5. approve and merge;
6. answer as owner;
7. review the captures.

Writes stay with the client and git. The MCP side reads, except the announced load through `knowgov-runs`, which decision-0008 admits.

**The manifest an assistant writes:** one artefact as `path` and `mapper`.
- `key` and `short` come from the file name, unique in the subject.
- `family`, `format` and the labels come from the kind's row and the mapper.
- Both public subjects declare every field, so no record moves; S4 proves it.

| Client | Writes files | Prompt, resources | Check | Dry run | After the merge |
|---|---|---|---|---|---|
| Claude Code with the stack | own tools, git | documented | tool or CLI | CLI, rdflib | runs, reader |
| Claude Desktop, chat | only with a file extension; not verified | unconfirmed (the Desktop test, §8) | `subject_check`, held in the call | none (F7) | runs, reader |
| Cloud session | own tools, git | no local stack | CLI | CLI, rdflib | stack unreachable |

## 7. What task-0146, task-0147 and task-0148 cover

The maintainer's go of 2026-11-05 on doc-0018's candidates 3 to 5 put three of this study's proposals in build. The rest of the plan is aimed past them.

| Proposed here | In build | Departure |
|---|---|---|
| B6: `subject_check` reading a subject by id from the live mount | task-0146: the proposed files and the documents' text held in the call, checked in a temporary directory, the call's size bounded | none to record. Held in the call works in every client, mount or not. Reading by id (S2) is an optional later mode once `subject` exists (B7): it spares the client sending documents' text |
| B8: prompts and resources on the reader, the same text as a skill | task-0148: `new_subject` and `add_artefact` prompts, a Claude Code skill; no resources | resources optional; §8 item 12 carries what they would hold inside `prompts/get` |
| B9: the instance hook | task-0147 | none |
| B10: the adopter walkthrough | task-0148 AC #3 | folded in; B10 is withdrawn |

Still proposed, with no ids: B1, B2, B3, B4, B5 and B7 (§9).

## 8. For task-0148: what the study changes

The leanest flow, as the prompt's and the skill's text. Every item applies today, without waiting for B1 to B7:

1. **Two arguments, each one token: `new_subject <id> <task>`.** Claude Code splits a prompt's arguments on whitespace, so no free-text argument (a description, a path with spaces). The rest is asked in chat.
2. **At most five questions** (§6 rule 2). Everything else is derived and shown, never asked.
3. **Order:**
   1. the register: `register_nodes` (task-0142) and `register_impact`; `proposal_impact` first for a new product;
   2. the documents into their kinds;
   3. the manifest;
   4. the keys;
   5. the attestation stanza;
   6. the questionnaires, last (G6).
4. **Mapper fit by the check's own numbers.** Read `yield.artefacts` in the report. A document at 0 is the wrong convention, never "no knowledge here" (G1, until B1). Try the kind's other mappers before concluding.
5. **`requirements` reads only `| REQ-nn | text |` rows** (G1, until B5). Say so when a document's ids have another prefix. Never rewrite the organisation's ids: the person decides.
6. **Always write `short`** for a mapped artefact, derived from the file stem (G5, until B1 or B4).
7. **A did-you-mean whose entity differs from the required key's is not a typo** (G2, until B1). Present it as "no document states `<key>`": a question for its owner.
8. **The attestation stanza commented out**, with what its absence costs. task-0147's hook backs it.
9. **The stop condition verbatim** (§6 rule 7), as the last check, with the readiness card in the pull request's body:
   - per document: kind, mapper, yield, form;
   - per key: yielded or not, did-you-mean, owner, level at the dry run.
10. **After the merge, the manual steps named with their commands**, until B2 and B7 land:
    - restart the page;
    - relaunch or re-register both servers with `-e KG_SUBJECT=/instance/subjects/<id>`;
    - reconnect the client;
    - then `start_run S0`, saying the load replaces what others view.
11. **One text, two carriers.** The prompt's messages and the skill come from one source, held equal by a test (task-0148 AC #1 already pins the text).
12. **Embed what resources would carry inside `prompts/get`'s messages:** the kinds table and each mapper's input convention. A client that shows prompts but not resources then has it.

**Multi-round-trip (MRTR) elicitation should not drive the wizard's questions in task-0148.**
- **Open questions.** The questions are open (what the subject is for, which documents). Chat answers them, and the model needs the answers to propose anything. Elicitation's forms suit closed answers.
- **The one closed candidate.** It is the readiness card's confirmation. The write it would confirm is the client's own, and the client already asks the person: the permission prompt, then the pull request's review.
- **Support.** Claude Code documents elicitation in form and URL modes, with `Elicitation` and `ElicitationResult` hooks. Its documentation does not say it serves 2026-07-28's `input_required` result on `prompts/get`, and Claude Desktop is unconfirmed. A wizard built on it would need a chat fallback, and that fallback is the whole wizard.
- **S7 stays for later:** one closed question, measured against chat.

**The Claude Desktop test.** The maintainer runs it on macOS, about 15 minutes, on task-0148's branch or after its merge:
1. Register the reader as instance/README.md's "Connecting Claude Desktop" says; quit and reopen.
2. In a Chat conversation, open the attach menu. Is knowgov's `new_subject` listed? Record yes or no, with a screenshot.
3. If listed, choose it. Does it ask for `id` and `task`, and does the conversation open with the prompt's text?
4. Ask the assistant to check a small subject held in the call. Does `subject_check` (task-0146) run, behind the permission prompt?
5. Record the three answers (prompt, arguments, tool). Desktop's role in onboarding follows (§10, decision 2).

## 9. Beyond candidates 3 to 5: the spike and the proposed tasks

**Spike.** One working session, run once task-0146 to task-0148 have merged. The prototype code stays on a spike branch and is never merged. The spike's outputs:
- its note, as a backlog doc with the numbers;
- one proposed decision: the `subject` argument;
- these tasks, minted on the maintainer's go.

| # | Question | Method | Passes when |
|---|---|---|---|
| S1 | Does Claude Desktop show the prompts and run the tool? | The Desktop test above, by the maintainer | The answers are recorded; Desktop's role decided |
| S2 | Is a by-id mode of `subject_check` worth having? | The reader on the host against an instance folder (no Docker daemon in a hosted session): an edit, then a call by id, beside the held-in-call payload size for CargoQuote's ten artefacts | The edit shows with no restart, an id outside `KG_SUBJECTS` is refused, and the size saved is stated |
| S3 | Which design for G4? | (a) a child process per call, the page's pattern; (b) a lazy pool, one child per subject; (c) the subject as a value through the harness (F6, as TASK-0032.01 did for the page). Latency on rdflib and Neo4j for `cargo_quote`, lines touched, tests moved | One option chosen with its numbers. The proposed decision: `subject` resolved by id under `KG_SUBJECTS`, never a path, defaulting to `KG_SUBJECT` so today's clients see no change |
| S4 | Which artefact fields can default? | Strip `key`, `short`, `family`, `format` and the labels from both public subjects in a scratch copy, derive them, run the comparator | 0 differing leaves over CargoQuote's 7 scenarios and J-F's 6, or the field that moves named and kept |
| S5 | Can `requirements` honour the id pattern? | Read `[rules] requirement_id_pattern` (default `[A-Z]{2,}-\d{2,}`); comparator; the probe with `RNW-` ids | Records unchanged; `renewal.md` yields 3 |
| S6 | Does the built wizard meet the targets? | Onboard a fresh subject with task-0146 to task-0148, plus B1 and B2 if merged: task-0008's aris2puml pilot corpus if that repository is attached, else a synthetic subject on the example instance | 10 or fewer person actions, 0 silent outcomes, the stop condition reached, the restarts counted (0 once B2 and B7 land), time to the first honest gate recorded |
| S7 | Optional: is elicitation worth it for one closed question? | The readiness card's confirmation as an `input_required` result, against chat | Kept only if it removes a step or a model guess |

**Proposed tasks (no ids).** Each goes in its own PR on m-8.

| # | Proposed task | Closes | Size | After | Contract |
|---|---|---|---|---|---|
| B1 | `check_subject`: a zero yield is a WARNING naming the mapper's convention; `short` refused or defaulted when a mapper is set, with the right fix; a yielded key offered once, to its best match; a different-entity match a NOTE | G1, G2, G5 | S | none | one layout refusal (minor) |
| B2 | The page rescans `KG_SUBJECTS` on an unknown id, or by modification time | G3 | S | none | none |
| B3 | Mapper cards: each mapper's input convention with a minimal example, each example held to a yield above zero by a test; task-0148's prompt text quotes them | G1 | S–M | none | none |
| B4 | `[[artefact]]` defaults from the kind's row, the mapper and the path | G5 | S–M | S4 | additive |
| B5 | `requirements` honours `requirement_id_pattern` | G1 | S | S5 | more statements for non-`REQ` ids |
| B7 | `subject` on every reader and `knowgov-runs` tool, and `list_subjects`, per the proposed decision; optionally `subject_check` by id (S2) | G4 | M–L | S3, the decision; after task-0141's H1, H2 and 0.7.0 | tool schemas (minor) |

**Order:**
1. B1 and B2 now: each misleads a person working by hand today, and each removes a workaround from task-0148's text (§8 items 4, 6, 7, 10).
2. B5 after S5, and B3 beside task-0148.
3. S1 when task-0148 is on a branch.
4. S3 to S6 once task-0146 to task-0148 have merged.
5. B4 after S4.
6. B7 last, behind its decision and after knowgov 0.7.0 (task-0141's note), so the reader is not changed under that release's H1 and H2.

When a B-task lands, the matching §8 workaround leaves the prompt's text in the same pull request.

## 10. For the maintainer to decide

1. **B1 and B2 now**, beside task-0146 to task-0148. Recommended: yes. Both are small, independent and remove workarounds from task-0148's text.
2. **Claude Desktop's role:** onboarding, or asking the gate only. Recommended: asking only, until the Desktop test shows prompts listed and `subject_check` running there. Onboarding is Claude Code's job, with a shell, git and the dry run.
3. **G4's direction**, set by the proposed decision after S3. Recommended: (a), a child process per call, if S3 measures under a second per call on Neo4j for CargoQuote; (c) only if not.
4. **Elicitation.** Recommended: not in task-0148; S7 later, for one closed question at most.
