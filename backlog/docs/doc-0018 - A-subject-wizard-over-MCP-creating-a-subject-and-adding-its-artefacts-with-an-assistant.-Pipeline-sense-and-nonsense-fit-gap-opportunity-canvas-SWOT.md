---
id: doc-0018
title: >-
  A subject wizard over MCP: creating a subject and adding its artefacts with an
  assistant. Pipeline, sense and nonsense, fit/gap, opportunity canvas, SWOT
type: specification
created_date: '2026-11-04T22:34:00Z'
updated_date: '2026-11-04T22:36:00Z'
tags:
  - canvas
  - swot
  - fit-gap
  - brief
  - mcp
  - subject
---
*2026-11-04. Maintainer register. A study: nothing is built, and no task is created before the maintainer's go. Trigger: the maintainer's ask of this date to use knowgov's MCP to create new subjects and add their artefacts, as a guided process run by the AI model against the MCP, "an AI version of a wizard". The pipeline was asked for first: it was shown in the session, it is §1 here, and it is on the maintainer's page knowgov Subject Pipeline (https://claude.ai/artifact/1xFNC4hA3Z9j7sy8jXAcTZ). Evidence: knowgov `main` at `8f375cc` (after #216). Probes were run in the session on rdflib with the record's pins (rdflib 7.6.0, pyshacl 0.40.2, pyyaml 6.0.3, pumllint 0.33.0): a scratch subject `probe` and an example instance from `tools/example_instance.py`, both in the session's scratch space and committed nowhere. Read beside decision-0008 (the reader stays read-only), doc-0016 (runs over MCP), doc-0017 (a proposal held in the call; task-0130) and task-0041 (a model's output ends in a questionnaire, never in an ingest).*

## Verdict

**The ask makes sense in a narrower shape than it was put.** The value is real. A subject today is a hand-written manifest: `subjects/README.md` documents sixteen tables for `subject.toml` alone, plus four companion files. Its mistakes either pass every check or surface late, dressed as knowledge findings (§2, F2 to F4). A guided process that proposes, checks after each step and explains the findings is worth having. Three parts of the ask are nonsense as stated:

1. **The MCP as the write path.** decision-0008 (accepted today): "No tool on it loads, runs or writes." The instance is mounted read-only, and an instance's record changes by pull request under four eyes. The wizard therefore writes nothing through knowgov. It writes with the assistant's own file tools into the instance checkout, on a branch, and ends in a pull request. knowgov's MCP contributes reads: what exists, and a check of what is proposed.
2. **The model writing the artefacts.** F1: a document that a mapper reads as `authored` loads as reviewed and approved by the subject's human agent, by construction, with no manifest table needed. Probe P2: an assistant-drafted requirement reads `approved`, agent `maintainer`, review scope `authored`, approval record `approval`, the loader's defaults. A model that drafts requirements, links, contracts or decision tables therefore launders its output into the top of the ladder. The wizard places, names and checks documents that people of record wrote. Where knowledge is missing, its exit is the capture route: a questionnaire to the owner (task-0041's rule).
3. **The model choosing the required keys from what the documents yield.** A task's keys are what the task needs, not what the documents happen to say. Keys derived from the extraction make `absent` impossible and the gate a tautology. The wizard proposes keys from the task's own sources (the oracle's scenarios, the register nodes the task touches, the owner) and shows the documents' yield beside them, never as the list.

The `[verification]` and `[provenance]` tables, the verification map's review keys, `captures/` answers, review files and the pre-load baseline are attestations by people. The wizard never fills them. It leaves them absent and says what that costs at the gate.

**Build, in order** (§6):
- a deterministic subject check, pure and with no store, as a CLI folded into `check_instance.py` (candidate 1);
- the F1 fix: a load verifies and approves only what the manifest declares (candidate 2; a decision first);
- the same check as a read-only MCP tool, the proposal held in the call (candidate 3);
- the wizard itself as a client-side procedure: an MCP prompt on the reader and a Claude Code skill, writing nothing through knowgov (candidate 4);
- a fail-closed hook on the attestation paths (candidate 5).

Park a server-side dry-run gate. Reject write tools on `knowgov`, model-drafted documents and model-written mappers. F1 and F3 hold whether or not a wizard is built.

## 1. The pipeline today

| # | Stage | What a person writes | Check: what it refuses | What it only reports |
|---|---|---|---|---|
| 0 | Register | nodes (`CAP-`, `PROC-`, `APP-`, `ORG-`...), owners, approved links; an export via `tools/connector.py` | ieam-register `check_register.py [--previous]`: ids, lifecycle steps against the base, approvals. The connector refuses an overwrite or an earlier date | stale ids, in `RECONCILE.json` |
| 1 | Artefacts | a file under `artefacts/<kind>/`, the kind one row of `instance/kinds.toml` | `tools/preload_check.py`: a linter finding at or above `--fail-on` (major), or one the `--baseline` does not hold. Six linters: pumllint, Spectral, markdownlint, gplint, bpmnlint, dmnlint | UNCHECKED: the 14 kinds with no linter here, `.md` decision tables, a linter not installed |
| 2 | Subject root | `subject.toml` (`[[artefact]]`, `[tasks.<class>]`, optional `[verification]`, `[reference]`, `[oracle]`, `[rules]`, `[register]`, `[record]`), `register_map.toml`, `scenarios.toml` | `tools/check_instance.py`: a subject that does not load, a missing path, a mapper in no kind, a mapper that does not read that kind's folder, a `code_map` row with an unknown APP or an overlap, a connector system missing from `sources.toml` | ABSENT, UNREAD, UNMAPPED, UNMATCHED |
| 3 | Load | nothing | `harness/run.py` stage 1: a document a mapper cannot parse fails the run | assertions enter as `proposed`. Verification by execution (oracle on `[reference]`, its digest kept), by dated review (lapses, decision-0005), as authored, then approval. Rules R-STRUCT, R-CORROBORATE, R-CONFLICT, R-VAGUE, R-REQ; SHACL (D4) |
| 4 | Gate | nothing | `harness/gate_cli.py`: BLOCKED when a key sits at a `block_levels` level, or when the share below verified exceeds `max_unverified_share`. Exit 0/1/2 | QUALIFIED; stale, suspect and lapsed findings with owner and route; pre-load info |
| 5 | Capture | the owner's answer (handle, date); then a second person's review file | `capture.py ingest`: a name for a handle, a handle not issued or withdrawn or without `gives`, a future date, an answer together with "nobody knows" | decision-0004: an unreviewed answer does not lower a validated key; a contradicting one disputes it |
| 6 | Consume | nothing | `instance/ci/claude/knowgov_hook.py` blocks at plan, spec commit and push on exit 1 or 2 | the reader's five tools at `8f375cc`: `store_status`, `gate_verdict`, `three_valued_answer`, `evidence_bundle`, `register_impact`; #211 adds `proposal_impact` (task-0130) as a sixth |
| 7 | Code | code, `code_map.toml`, `# knowgov-keys:` | `harness/trace.py check`: suspect (blocker); missing, unmapped, uncited (major) | drift (minor) |

Stage 4 loops back through 5 to 3 when a key is `absent` or a `declared_gap`. A public subject in this repository adds: a `[vendor]` table and `tools/vendor_subject.py` at a pumllint tag with its digest test; `tests/test_subject.py`'s guards; `listed` and `KG_SUBJECTS`; the register slice in ieam-register re-vendored at a tag (TASK-0021.04 for J-F); and a deterministic record held by `compare_deterministic.py`.

## 2. Findings that hold before anything is built

The probes ran on rdflib with `KG_TODAY=2026-11-04` and `--as-of 2026-11-04`. Subject `probe` has one artefact, `requirements.md`, with two rows, `REQ-01` *A quote request carries a shipper id.* and `REQ-02` *A quote is valid for 14 days.*, read by mapper `requirements`. It has one task, `keys = ["REQ-01|text", "REQ-02|txt"]`, the second misspelt, and no `[verification]` or `[provenance]` table. P1: `gate_cli.py` on it with no `scenarios.toml`. P2: the same with `subjects/minimal/`'s pristine `S0`. P3: the subject added to an example instance (`tools/example_instance.py`), its document under `artefacts/textual-requirements/`, with a `register_map.toml` row naming `CAP-9999`, then `check_instance.py` and the gate. P4: the mappers on the kit with no store.

- **F1. Authored is approved by construction, by default.** `load_verifications` calls `verify_authored(authored.get("at", ts), authored.get("scope", "authored"), HUMAN["id"])` and then `approve_verified(approval.get("at", ts), approval.get("record", "approval"), ...)` whatever the manifest declares. `HUMAN` defaults to `agent:maintainer`. The mappers mark `basis="authored"` on requirement text, links, the bundle mappers' citations, DMN rule counts, Gherkin scenario counts and PlantUML elements (`harness/extract.py`). P2: `REQ-01|text` reads `approved`, with verification `review` scope `authored` and approval record `approval`, and no person named anywhere in the subject. Both public subjects declare `authored` and `approval` explicitly (`subjects/cargo_quote/subject.toml:154`, `subjects/jef_data_load/subject.toml:101`), so requiring the declaration moves no record. An adopter who drafts a requirements file with an assistant meets F1 today, wizard or not.
- **F2. A misspelt key is reported as missing knowledge and routed to an owner.** P2: `REQ-02|txt` is `absent`, a blocker, and the finding's route sends it to `questionnaire-probe-S0-unassigned.toml` for an owner to answer. The documents yield `REQ-02|text`. Nothing compares a required key with what the documents yield, and nothing lists the yield before a load. P4: `extract.extract_all(kit_for("S0"), "")` returns `['REQ-01|text', 'REQ-02|text']` with no store, so the comparison is computable read-only.
- **F3. The layout check passes a subject the gate cannot run.** P1 and P3: with no `scenarios.toml`, `check_instance.py` exits 0 ("subject probe: 1 artefacts, record empty", the artefact `read`), and `gate_cli.py` exits 2: "probe: no scenario ''; the subject declares none" (`gate_cli.py:309`). `subjects/README.md` lists `scenarios.toml` as not required. An instance subject needs at least the pristine scenario `subjects/minimal/` declares (`S0`).
- **F4. `register_map.toml` is not checked against the register.** P3: a row naming `CAP-9999` passes `check_instance.py` (exit 0). `capture.owners_of` skips a node the register does not hold, and `answering_owners` ignores, silently, an `owner` that is not one of its nodes' owners. The key then goes `unassigned`. Only `tools/lighthouse_evidence.py` and the page's footprint ("not in the register copy") say so.
- **F5. Nothing checks the manifest's fields.** `Subject()` reads the tables it knows and ignores the rest. A bare manifest loads (`test_a_bare_manifest_loads_and_a_missing_one_is_refused`), and a misspelt table name (`[task.codegen]`, `[[artefacts]]`) is dropped without a word. The consequence surfaces later: a task the gate does not know is its exit 2, an artefact list that did not load is an empty load and every key absent.
- **F6. One subject per process, bound at import.** `load`, `extract` and `rules` take `SUBJECT` at import (`from subject import SUBJECT`; `extract._SHORT`, `_REQ_ID`, `extract_all`'s `SUBJECT.mappers`). The served MCP process cannot check a second, proposed subject root in-process without the mappers taking the subject as a value, as the page's modules did (TASK-0032.01), or a subprocess.
- **F7. The served store never shows the wizard's branch.** The reader serves the store the page loaded, from the mounted instance's merged tree. A subject on a branch in the user's checkout is invisible to it until merged and loaded. In Claude Code the assistant can run the gate on the branch locally (`KG_STORE=rdflib python harness/gate_cli.py --subject <dir>`), which is how P2 and P3 ran. In Claude Desktop, with no shell, it cannot.
- **F8. The reader has no prompts.** `harness/mcp_server.py` offers tools only: no `prompts/list`, no elicitation. A server's prompts are text the client shows as a starting message. Claude Code lists them as slash commands, per its documentation; not tried here.

## 3. Sense and nonsense, part by part

| Part of the ask | Reading | Why |
|---|---|---|
| A guided process | **Sense** | Sixteen manifest tables, four companions, twenty kinds, fifteen mappers. F2 to F5 are exactly the mistakes a guide prevents |
| An AI version of a wizard | **Sense, if the steps and stops stay deterministic** | The model's part is the dialogue: asking, proposing a kind, a mapper or a candidate key, and reading findings back in plain English. Pass or fail is the checks'. A model that judges whether a step is done becomes a second, softer gate |
| Interacting with the MCP | **Sense for reads, nonsense for writes** | decision-0008. Reads that help: `register_impact` and doc-0017's `proposal_impact` (task-0130) for the nodes a subject's task touches, `gate_verdict` after the merge and load, and a new `subject_check` (candidate 3) |
| Create new subjects | **Sense as scaffolding on a branch** | The manifest, the pristine `S0`, `register_map.toml` rows, written by the client's file tools, checked by candidate 1 after each write, ending in a pull request a person reviews |
| Add their artefacts | **Sense as placing; nonsense as authoring** | Placing means: the kind folder, the `[[artefact]]` entry, the mapper, the pre-load check, the yield. Authoring launders model output into `approved` (F1). A document the organisation lacks is a gap for its owner, not a draft for the model |
| Quality checks | **Sense; the wizard ends where the gate's findings are only knowledge** | Done means: `check_instance.py` exits 0, `preload_check.py` exits 0 or every finding is HELD, the gate exits 0 or 1 (never 2), and every remaining finding is knowledge with an owner and a route. It does not mean the files exist |
| The model deciding the keys | **Nonsense** | It makes `absent` impossible. The yield is shown beside the keys, as the did-you-mean of F2, never as the source |
| The model filling verification or review | **Nonsense** | They are people's attestations: decision-0002 and decision-0004 for reviews; `[verification]` dates and records name a human act |
| Generating a mapper for a new convention | **Nonsense here** | A mapper is code in `harness/extract.py`, reviewed in this repository. The wizard names the kind as ABSENT and the convention as a mapper request |

## 4. Fit/gap per wizard step

| Wizard step | Today | Fit/gap |
|---|---|---|
| 1. Name the subject and its task class | hand-written `[subject]`, `[tasks.<class>]` | Gap: scaffold, by the client's file tools, from `subjects/minimal/` |
| 2. The pristine scenario | not in the README's required set; the gate needs one | **Gap, F3**: the scaffold writes `S0`; candidate 1 refuses its absence |
| 3. Place each document: kind, mapper | `instance/kinds.toml`; `check_instance.py` checks mapper against kind | Fit |
| 4. The document's form | `preload_check.py` on six kinds | Fit; the baseline is the owner's commit, never the wizard's |
| 5. What each document yields | nothing before a load | **Gap, F2**: the yield preview, pure (P4) |
| 6. The task's keys | hand-written; a typo reads `absent` | **Gap, F2**: proposed from the task's sources; checked against the yield with a did-you-mean |
| 7. The register map | hand-written; unchecked (F4) | **Gap**: every node in the register, every `owner` one of its nodes' owners; candidates from `register_impact` |
| 8. Verification and approval | read from the manifest; authored and approved by default (F1) | **Gap, F1**: left to people; candidate 2 makes absence honest |
| 9. A dry run of the gate | the CLI on the branch, in Claude Code (F7) | Fit in Claude Code; gap in Claude Desktop (candidate 3 answers statically; candidate 6 parked) |
| 10. Gaps to owners | `capture.py questionnaire` | Fit: the pull request carries the questionnaires; ingest and review stay people's |
| 11. The pull request | the instance's `preload-check.yml` and gate wrappers | Fit; candidate 1 joins `check_instance.py`, which the template already runs |
| Guard rails on what the assistant writes | knowgov's own `.claude/hooks/protected_paths.py` (task-0105) | Gap: candidate 5 for an instance |

## 5. Opportunity canvas and SWOT

| Block | Content |
|---|---|
| Users and customers | The platform team that onboards an organisation's first subjects (the lighthouse, m-8, decision-0006); architects and analysts adding a document to an existing subject; a subject's owners, who receive the questionnaires; the maintainer adding a public subject (rare: three so far, one a fixture) |
| Problem | A subject is authored by hand against a field-by-field README. Some mistakes pass every check (F3, F4, F5). Others reach owners as knowledge they are asked to supply (F2). Mapper fit is discovered at the load. And the one shortcut an assistant offers, drafting the missing document, loads as approved (F1) |
| Solution | A client-side wizard that writes the scaffold on a branch with the assistant's own tools. After every step it calls a deterministic subject check (CLI in Claude Code, read-only MCP tool in Claude Desktop). It shows each document's yield beside the task's keys, and it runs the gate on the branch where a shell exists. It ends in a pull request carrying the check's report and the owners' questionnaires. knowgov writes nothing |
| Value | Time to the first gate run that exits 0 or 1, not 2. No questionnaire caused by a typo. Every document placed in a kind: read by a mapper or listed ABSENT. Every gap routed to a named owner. And, by F1's fix, no statement approved by nobody |
| Metrics | Days from an empty instance to the first honest gate. Share of blocker findings that were spelling, not knowledge (target 0). Subjects passing `check_instance.py` that the gate cannot run (target 0). Review rounds per subject pull request. Documents named but ABSENT, by kind, as mapper demand |
| Channels | Claude Code in the instance checkout (a skill under `instance/ci/claude/`, beside the hook); Claude Desktop through the reader (task-0117), the prompt and `subject_check`; the CLI in the instance's CI through `check_instance.py` |
| Cost | One check module with a CLI and a report schema; folding it into `check_instance.py`; the F1 change and its decision; one read-only tool, beside #211's `proposal_impact` and task-0128's `scenario_runs`, so the test that counts the tools (`test_five_tools_every_one_marked_read_only` at `8f375cc`) and the allowlist move; one prompt; a skill text; a hook; the adopter docs. The check's refusals and the tool are contract changes, a minor version while 0.x (decision-0003), with lines under `## Unreleased` |
| Risks | The model drafting content: answered by F1's fix, the skill's never-list and candidate 5. The model filling attestations: answered by candidate 5. Keys drawn from the yield: answered by showing the yield as a check, never as a source. The wizard read as approval: it ends in a pull request a person merges. Drift into a modelling tool: the wizard writes only the subject root and moves files people name |
| Unfair advantage | The wizard has an honest stop condition. An import wizard stops when the files are in. This one stops when every remaining finding is knowledge with an owner and a route, decided by the same gate that later blocks the build |

- **Strengths.** Every check the wizard needs exists, or is a pure function away (P4). The capture route already turns a gap into an owner's question. The reader's read-only contract and doc-0017's "held in the call" pattern give the MCP side its shape. The hook pattern (task-0099, task-0105) gives the guard. *Response:* build the check first. The wizard is then mostly text.
- **Weaknesses.** Fifteen mappers in two kits' conventions: a real organisation's documents will mostly be ABSENT at first, so the wizard's first honest answer is often "nothing here is read yet". `SUBJECT` is bound at import (F6). One maintainer. *Response:* report ABSENT as mapper demand, by kind; take F6 by a subprocess in the CLI and the subject-as-value change only if the tool needs it.
- **Opportunities.** Subject onboarding is the lighthouse's first hour: a guided route from an ARIS export (`connector.py`) and a few documents to a first gate is a demonstration in itself. F1's fix strengthens the record's claim for every adopter, wizard or not. *Response:* fix F1 and F3 first, whatever is decided about the wizard. Offer the wizard as the m-8 onboarding path once candidate 1 runs on the example instance.
- **Threats.** The wizard makes it easy to create many shallow subjects, and the gate's BLOCKED becomes noise. An assistant's convenience can win over the four-eyes rule. Client support for MCP prompts varies. *Response:* one subject per pull request. The report carries the denominators, ABSENT counted. The skill works without the prompt, and the prompt without the skill.

## 6. Candidates

| # | Candidate | Disposition |
|---|---|---|
| 1 | `tools/check_subject.py`: pure, no store. Manifest fields against what `Subject` reads (unknown tables named, F5); artefact fields; mapper names in the registry; at least one scenario when a task is declared (F3); key syntax; the documents' yield per artefact with a did-you-mean for each required key the yield lacks (F2); `register_map.toml` nodes in the register and `owner` among their owners (F4). Its refusals join `check_instance.py` (exit 1). JSON under a schema; F6 by a subprocess | **Build**, medium, first |
| 2 | F1: a load verifies authored statements by construction, and approves verified ones, only when the manifest declares `[verification] authored` and `approval`. Otherwise authored statements stay `proposed`, so a new subject is BLOCKED by `max_unverified_share` until a person attests. Both public subjects declare both tables, so no record moves | **Decision first** (who may attest, in the manifest or in a review file), then build, small. High: independent of the wizard |
| 3 | `subject_check` on the reader: the proposed manifest, map and documents' text held in the call, checked against the served register and kinds by candidate 1's functions; never stored, `readOnlyHint: true` | **Build**, small, after 1 |
| 4 | The wizard as procedure: a `new_subject` and an `add_artefact` prompt on the reader (text only, read-only by nature), and a Claude Code skill under `instance/ci/claude/`. The steps of §4, the never-list (no content drafting, no attestation, no keys from the yield), the stop condition of §3 and the exits: a pull request, questionnaires | **Build**, small, after 1 and 2 |
| 5 | An instance hook, task-0105's pattern through task-0099's `decide`: fail-closed on assistant writes to `[verification]` and `[provenance]`, `captures/`, review files, `preload-baseline.json` and `register/` | **Build**, small, with 4 |
| 6 | A server-side dry-run gate: the proposal written to a temporary root, `KG_STORE=rdflib` in a subprocess, never the shared store. It races nothing, so decision-0008's objection to option C does not apply, but it runs the subject's oracle, which is code | **Park**. Claude Code has the CLI. If revisited: no execution verification, and a decision of its own |
| 7 | Write tools on `knowgov` (`scaffold_subject`, `add_artefact`), or a second writing server | **Reject**: decision-0008 for the first. For the second, the instance's write path is git and a pull request, which the client already has |
| 8 | The model drafting a missing document; a mapper written by the model for a new convention | **Reject**: F1, task-0041's rule; a mapper is reviewed code here |
| 9 | `subjects/README.md` and `instance/README.md`: the gate needs a scenario; F1's behaviour until candidate 2 lands | **Document**, tiny, now |

Order: 9 and 2's decision now; 1; 3, 4, 5 together; 6 only on an adopter's ask. doc-0017's `proposal_impact` (task-0130) is the natural first read of the wizard for a subject about a new product: its reused nodes' keys seed step 6, and its unmapped new elements are the questionnaire's first page.
