---
id: doc-0021
title: >-
  Onboarding a new subject over MCP: every step today, six new gaps against
  doc-0018, opportunity canvas, SWOT, fit/gap, the experience, a spike and
  proposed tasks
type: specification
created_date: '2026-11-05T21:26:00Z'
updated_date: '2026-11-05T21:26:00Z'
tags:
  - canvas
  - swot
  - fit-gap
  - brief
  - mcp
  - subject
  - spike
---
*2026-11-05. Maintainer register. A study read against doc-0018: nothing is built, and the plan below is proposed tasks with no ids. The coordinating session mints them on the maintainer's go. Trigger: the maintainer's ask of this date: "investigate what it would take to onboard a new subject via the MCP, i.e. every single step"; an opportunity canvas, a SWOT and a fit/gap first; then the optimal user experience (frictionless, lean, clear); a plan (spike?) if the case is positive. The session's view: Subject Onboarding over MCP (https://claude.ai/artifact/RJkD5PNdC6uhTdhprriZsU). Evidence: knowgov `main` at `4bc8cfc`, and `5a0037c` checked for drift (task-0140 only). Probes ran in the session on rdflib with the record's pins (rdflib 7.6.0, pyshacl 0.40.2, PyYAML 6.0.3, pumllint 0.33.0): an example instance from `tools/example_instance.py`, a new subject `renewal` added to it, the page started on it (`KG_SUBJECTS`, port 8091), and both MCP servers driven over stdio. All of it lived in the session's scratch space and was committed nowhere. Read beside doc-0018 (its candidates 1, 2 and 9 built: task-0135, decision-0009 with task-0136, task-0134), decision-0008, decision-0009, doc-0016, doc-0017, and the work in flight: task-0141 (H1, H2 change the servers' HTTP handling; X1 contains code execution), task-0142 `register_nodes` (#238) and task-0143's upward joins, both from doc-0020 (#236).*

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

**A spike first** (§7), then ten proposed tasks. Three are independent of the spike: B1, B2 and B5.

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
| Channels | Claude Code: `/mcp__knowgov__onboard_subject`, `@knowgov:` resources, the CLI dry run. A skill with the same text for clients without prompts. Claude Desktop through the reader (S1). The instance's CI through `check_instance.py` |
| Cost | Ten small-to-medium proposed tasks; B7 (G4) medium-to-large, behind a decision. Contract changes: one layout refusal, one tool, the `subject` argument, prompts and resources in the capabilities. Each additive or minor while 0.x (decision-0003), under `## Unreleased` |
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
| 1–2 | fit | the prompt calls `register_nodes` (task-0142), `register_impact` and `proposal_impact` first; unmapped nodes seed the map | B8 |
| 4 | gap | the folder proposed from the kinds resource, confirmed by the person | B3, B8 |
| 5 | gap G1 | each mapper of the kind tried deterministically, each yield shown, one above zero chosen; a zero yield a WARNING naming the convention | B1, B3, B5 |
| 6 | fit | the assistant runs it; the baseline stays the owner's commit | |
| 7–8 | gap G5 | scaffolded; `path` and `mapper` only, the rest defaulted | B1, B4 |
| 9 | gap G2 | keys proposed from the task's sources, the yield shown beside, never as the list | B1, B8 |
| 10 | gap G1 | set from the document's ids; the mapper honours it | B5 |
| 11–14 | gap | `S0`, `as_of` and map rows scaffolded (map rows through task-0143's join); optional tables named, left out | B8 |
| 15 | fit | person only; the stanza written commented out, with what its absence costs; the hook refuses an assistant edit | B9 |
| 16–17 | gap | after every write: `subject_check` (MCP) or the CLI | B6 |
| 18 | gap F7 | Claude Code on private rdflib; Desktop stated as a limit | parked |
| 19 | fit | the PR body carries the readiness card | B8 |
| 20 | gap G3 | the page rescans | B2 |
| 21, 23 | gap G4 | the `subject` argument | B7 |
| 22, 24, 27 | fit | the prompt's last step, saying the load displaces the shared store | |
| 25 | gap G6 | after spelling, mapper fit and attestation | B8 |
| 26 | fit | people only | |

## 6. The experience

1. **One way in.**
   - In Claude Code: `/mcp__knowgov__onboard_subject <id> <task>` (positional arguments, split on whitespace).
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
| Claude Desktop, chat | only with a file extension; not verified | unconfirmed (S1) | tool on the live mount | none (F7) | runs, reader |
| Cloud session | own tools, git | no local stack | CLI | CLI, rdflib | stack unreachable |

## 7. Plan: a spike, then proposed tasks

**Spike.** One working session, plus the maintainer's Claude Desktop test (about 15 minutes, macOS). The prototype code stays on a spike branch and is never merged. The spike's outputs:
- its note, as a backlog doc with the numbers;
- one proposed decision: the `subject` argument;
- these tasks, minted on the maintainer's go.

| # | Question | Method | Passes when |
|---|---|---|---|
| S1 | Which surfaces do the clients show? | Throwaway `prompts/list`, `prompts/get` (`onboard_subject`, `add_artefact`) and `resources/list`, `resources/read` (kinds, mapper cards, fields) on the reader, both eras. Claude Code by the session; Desktop by the maintainer | The prompt runs as a slash command with arguments, and a resource resolves by mention, in Claude Code; Desktop's result recorded either way |
| S2 | Does `subject_check` read the working tree live? | The reader on the host against an instance folder (no Docker daemon in a hosted session). Edit, call again | The edit shows with no restart; an id outside `KG_SUBJECTS` is refused |
| S3 | Which design for G4? | (a) a child process per call, the page's pattern; (b) a lazy pool, one child per subject; (c) the subject as a value through the harness (F6, as TASK-0032.01 did for the page). Latency on rdflib and Neo4j for `cargo_quote`, lines touched, tests moved | One option chosen with its numbers. The proposed decision: `subject` resolved by id under `KG_SUBJECTS`, never a path, defaulting to `KG_SUBJECT` so today's clients see no change |
| S4 | Which artefact fields can default? | Strip `key`, `short`, `family`, `format` and the labels from both public subjects in a scratch copy, derive them, run the comparator | 0 differing leaves over CargoQuote's 7 scenarios and J-F's 6, or the field that moves named and kept |
| S5 | Can `requirements` honour the id pattern? | Read `[rules] requirement_id_pattern` (default `[A-Z]{2,}-\d{2,}`); comparator; the probe with `RNW-` ids | Records unchanged; `renewal.md` yields 3 |
| S6 | Does it meet the targets? | Onboard a fresh subject with S1 to S5's prototypes: task-0008's aris2puml pilot corpus if that repository is attached, else a synthetic subject on the example instance | 10 or fewer person actions, 0 restarts, 0 silent outcomes, the stop condition reached, time to the first honest gate recorded |
| S7 | Optional: is elicitation worth it? | The five questions as an `input_required` result from `prompts/get`, against the same questions in chat | Kept only if it removes a step or a model guess; expected: not in the first build |

**Proposed tasks (no ids).** Each goes in its own PR on m-8.

| # | Proposed task | Closes | Size | After | Contract |
|---|---|---|---|---|---|
| B1 | `check_subject`: a zero yield is a WARNING naming the mapper's convention; `short` refused or defaulted when a mapper is set, with the right fix; a yielded key offered once, to its best match; a different-entity match a NOTE | G1, G2, G5 | S | none | one layout refusal (minor) |
| B2 | The page rescans `KG_SUBJECTS` on an unknown id, or by modification time | G3 | S | none | none |
| B3 | Mapper cards: each mapper's input convention with a minimal example, each example held to a yield above zero by a test | G1 | S–M | none | none |
| B4 | `[[artefact]]` defaults from the kind's row, the mapper and the path | G5 | S–M | S4 | additive |
| B5 | `requirements` honours `requirement_id_pattern` | G1 | S | S5 | more statements for non-`REQ` ids |
| B6 | `subject_check` as a read-only reader tool on the live mount, by id (doc-0018 candidate 3) | steps 16–17 in Desktop | S–M | B1; after task-0142, task-0143 | a new tool |
| B7 | `subject` on every reader and `knowgov-runs` tool, and `list_subjects`, per the proposed decision | G4 | M–L | S3, the decision; after task-0141's H1, H2 | tool schemas (minor) |
| B8 | Prompts and resources on the reader (`onboard_subject`, `add_artefact`; kinds, mapper cards, fields), and the same text as a skill under `instance/ci/claude/` (doc-0018 candidate 4) | F8, G6 | M | B3, B6; B7 optional | capabilities (additive) |
| B9 | The instance hook: fail-closed on assistant writes to `[provenance]`, `[verification]`, `captures/`, review files, the pre-load baseline and `register/` (doc-0018 candidate 5) | rule 5 | S | with B8 | none |
| B10 | Adopter docs: "Onboarding a subject with an assistant" in instance/README.md, with a plain-English walkthrough beside the commands, held by a docs-flags guard | all | S | last | none |

**Order:**
1. B1, B2 and B5 (after S5) need no other answer and can run beside the spike.
2. Then S1 to S6.
3. Then B3 and B4.
4. Then, once knowgov 0.7.0 has shipped with task-0141.01–.04, 0142 and 0143 (task-0141's note), the server changes B6, B7 and B8 together with B9.
5. B10 last.

The server changes wait so that the reader is not changed under that release's H1 and H2.

## 8. For the maintainer to decide

1. **Whether to run the spike**, or to start with B1 and B2 alone. Recommended: B1 and B2 now, as each misleads a person working by hand today, and the spike beside them.
2. **Whether Claude Desktop is a target for onboarding**, or only for asking the gate. Recommended: asking only, until S1 shows prompts and resources there. Onboarding is Claude Code's job, with a shell, git and the dry run.
3. **G4's direction**, to be set by the proposed decision after S3. Recommended: (a), a child process per call, if S3 measures under a second per call on Neo4j for CargoQuote; (c) only if not.
4. **Elicitation.** Recommended: no in the first build (S7 optional).
