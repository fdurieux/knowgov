# Changelog

One section per release, newest first. The version in `VERSION` is the top section's
(decision-0003). While the version is 0.x, a change to a contract raises the minor version: the
gate command's exit codes or flags, the JSON shapes under `harness/schemas/`, the instance layout,
the store port, the subject manifest format.

Between releases, changes merged to `main` gather under `## Unreleased` on top; the release PR
names that section with the version.

## Unreleased

### Contract changes

- **The reader serves prompts: the subject wizard** (task-0148, doc-0018 candidate 4, doc-0021 §8).
  `knowgov` declares the `prompts` capability and serves `new_subject <id> <task>` and
  `add_artefact <subject> [file]` through `prompts/list` and `prompts/get`, in both protocol eras;
  over HTTP a stateless `prompts/get` carries its `Mcp-Name`. Each prompt is the text of the
  Claude Code skill `instance/ci/claude/skills/knowgov-onboard/`, verbatim (`harness/wizard.py`):
  the procedure an assistant follows to scaffold a subject on a branch with its own file tools,
  checked after every write, ending in a pull request; with the never-list (no content drafted, no
  attestation written, no key drawn from the yield), the stop condition, and the kinds table with
  what each mapper reads. `knowgov-runs` declares no prompts.

- **`key_nodes`, `code_path` and `document_links`, three new read-only MCP tools** (task-0143, doc-0020
  C2, additive): the upward joins, from files and with no store, listed on stdio and Streamable HTTP
  alike and admitted by the shipped managed allowlist by server name. `key_nodes` names the register nodes a knowledge key's
  `register_map.toml` rows name, with each row's owner, anchor and note; an unknown key is refused.
  `code_path` takes a path under the instance's `code_map.toml` root and names its application, the
  keys its header cites and its trace ledger entry (derived id, keys, statements, commit, digest,
  drift). `document_links` names the register links whose evidence cites a document of the export
  manifest, with the anchor and the nodes at both ends and their owners, as the Browser's
  `register-cites` joins them. Each `code_path` leg reads `read` or `unchecked` with its reason, never empty. The server takes
  `--instance`/`KG_INSTANCE` and `--ledger`/`KG_LEDGER`, read once at start. Its instructions name the
  chain's two sequences: down by `register_impact walk=realisers` then `evidence_bundle`, up by
  `code_path`, `key_nodes`, `register_impact walk=dependants` and `register_nodes`. Also
  `python harness/upward.py key|code|doc`; reports pinned by `harness/schemas/key-nodes.schema.json`,
  `code-path.schema.json` and `document-links.schema.json`, version 1.
- **The subject check reads a document's yield more honestly** (task-0149, doc-0021 G1, G2, G5).
  `tools/check_subject.py` (and `check_instance.py`, which runs it) now refuses an artefact with a
  mapper and no `short`, naming the file's stem as the fix, where the load failed on a `KeyError`
  blamed on the document. It warns (new rule `zero-yield`) when a mapper reads a document and
  yields nothing, naming what the mapper reads (the new `instance/mappers.toml`) and the kind's
  other mappers. It offers each yielded key once, to its best match, and a match on another entity
  is now a note, not a did-you-mean. The report's shape is unchanged (schema version 1; the rule
  `zero-yield` is added).
- **`register_nodes`, a new read-only MCP tool** (task-0142, doc-0020 C1, additive): the register
  listed from its files, no store, every node by id with its taxonomy, kind, name, state, owner and
  parent, filtered by taxonomy, kind, state, owning unit (the owner field or an approved `owns` link)
  and parent (`null`: the roots), with the total, a limit and an offset; with `node`, that node's
  lineage, every ancestor by `parent` to the root and its children with their states, an annotation
  and never a walk. Also `python harness/register_nodes.py`. Report pinned by
  `harness/schemas/register-nodes.schema.json`, version 1.
- **`subject_check` on the MCP reader** (task-0146, doc-0018 candidate 3). A thirteenth read-only tool:
  the call carries a proposed `subject.toml`, `register_map.toml`, `scenarios.toml` and the
  documents' text, and gets back `tools/check_subject.py`'s report (schema `subject-check`), made
  by that tool's own functions against the served register. The files live in a temporary folder
  removed after the call, the documents' yield runs in a child process, and nothing is stored. A
  call carries at most 64 documents and 1 MB of text; a document path may climb at most `../../`
  from the subject folder.

- **The connector's MANIFEST follows ieam-register's export format** (decision-0010, task-0138).
  `[ids]` now lists every object of the AML, keyed by its GUID (the system's `id_field`,
  `aris_guid` for ARIS), with its name, including objects that carry no register id. Before, it
  was keyed by register id. The register ids move to their own tables: `[register_ids]` (GUID to
  register id, replacing `[guids]`) and `[bpmn_ids]` (the register ids a BPMN file carries).
  `RECONCILE.json`'s `ids` section is now the register's own comparison by GUID: a renamed object
  is its GUID under `renamed`. The connector no longer treats an id carried by a GUID as carried;
  that extension is redundant now. It keeps `unknown_ids` and its stale rule by register id, both
  read from the new tables. A folder landed before keeps its bytes; the first export landed after
  the upgrade reads every object as added in `ids`. `proposal_impact`'s D2 reads `[register_ids]`,
  and `[guids]` in an older folder.

### Changes

- **The store's reads answer in one order on both adapters.** Neo4j's `collect()` answers in its
  traversal order, which a reload can move, so the evidence bundle's suspect line and the gate
  report's stale statements could list the same items differently on two reads of one store. Now
  `suspect_derived` (and its `used_invalidated`), `stale_on_keys` (and its verifications and
  successors) and `key_evidence`'s lists are by id on both adapters, fragments by their fields
  (`store.by_id`, `store.by_content`). The record compares lists as sets: 0 differing leaves on
  both subjects.

- **The page finds a new subject without a restart** (task-0150, doc-0021 G3). The page re-reads
  its subject folders (`KG_SUBJECTS`) when a `subject.toml` is added, edited or removed, on the
  next request. A merged subject is listed and served at once, and a removed one is no longer
  listed. A manifest that does not load is left out and logged; the others stay served. Before, the
  list was read once, at start.

- **The CI scripts check their interpreter first** (task-0141.01). `knowgov-gate.sh`,
  `preload-check.sh` and `proposal-impact.sh` run every step with the interpreter `PYTHON` names
  (default `python3`), by its absolute path. An interpreter that is missing or older than Python
  3.12 now exits 2 (cannot run) with the reason. Before, a step could exit 1, read as a finding,
  or 127. A relative `PYTHON` now works for the gate's core commands. The Claude Code hook passes its
  own interpreter to the gate unless `PYTHON` is set. The test runner counts a test whose
  prerequisite is absent as skipped, never passed, and `KG_TEST_REQUIRE` turns a skip into a
  failure.
- **A second Claude Code hook guards what people attest** (task-0147, doc-0018 candidate 5).
  `instance/ci/claude/attestation_paths.py`, wired by `settings.attestations.json`, blocks an
  assistant's Edit, Write, MultiEdit or NotebookEdit that adds or changes `subject.toml`'s
  `[verification]` or `[provenance]`, or writes under `captures/`, a review file, the verification
  map, `preload-baseline.json` or `register/`. Fail-closed through task-0099's `decide`; it does not
  see a shell command writing the same file.
- **The register at ieam-register v0.2.10** (the register's decision 0017): `RECONCILE.json`
  carries the register's `unregistered` list, the objects no node's `[source]` names. On the
  synthetic ARIS exports, no example node names ARIS as its source, so the list holds 41 objects
  for `first` and 38 for `later`. 27 and 25 of them are events, rules and steps that no register
  id names. A node that carries `[source] aris_guid` leaves the list, and the register's own
  `stale_nodes` then finds a vanished object. `check_register.py --report` gains a per-system
  export count. The record is unchanged on both subjects.

## 0.6.0 — 2026-11-05

An AI assistant can now see what has been run for its subject, read any run's result, and start a
run of its own, while the server it asks for knowledge stays read-only. `scenario_runs` lists each
scenario with what the record holds and its runs, newest first; `scenario_result` returns what the
page's Replay shows for any of them, from files and never the store; and a second server,
`knowgov-runs`, starts and polls a run through the page, deterministic by default, one at a time.
While a run is loading the store, the tools that read knowledge from it refuse and name the run. A proposed
addition (a new product, capability or journey) can be read before approval as if approved, with
the register's own checker and walks, held in the call or taken from a register branch:
`proposal_impact`. The layout check now reads each subject's manifest and keys, so a typo, a
missing scenario or a register-map row the register does not hold is refused before a load. And a
load attests only what the subject declares: an authored document nobody declared reviewed no
longer loads as approved (decision-0009).

### Contract changes (why this is 0.6.0, decision-0003)

- **A load attests only what the subject declares** (decision-0009 (a), task-0136, doc-0018 F1):
  the authored-by-construction review runs only when `subject.toml` declares `[verification]
  authored`, and the approval of verified statements only when it declares `approval`. Before, both
  ran with the loader's defaults (`agent:maintainer`, record `approval`), so an authored document
  nobody had read loaded approved. A subject without the declarations now loads its authored
  statements `proposed` and approves nothing, and the gate reads them below verified. Both public
  subjects declare both tables: the record, the comparator and the example instance are unchanged.
  `tools/check_subject.py` notes a subject with authored documents and no `authored` declaration.
- **A run folder describes itself** (task-0127, additive): the page's Runner writes
  `runs/<subject>/<stamp>/run.json` when a run starts (status `running`) and again when it ends
  (`finished`, `done` or `failed`, `exit_code`); a run whose process cannot start leaves it
  `failed` with an `error`. It names the mode, the model row, the as-of date and who asked
  (`by`: `page`, or `mcp`, which `POST /api/run` now takes as `by`), never a key, a token or the
  environment. `harness/schemas/run.schema.json` pins it (version 1; version 2, task-0128). `/api/runs` carries it as
  `run` where present and is unchanged for a folder without one.
- **A proposal read before approval: `proposal_impact`** (task-0130, task-0131, doc-0017; additive):
  a sixth read-only MCP tool and a command, `harness/proposal_impact.py`, with its report pinned by
  `harness/schemas/proposal-impact.schema.json` (version 1). A proposed addition (new nodes with
  provisional ids, links, the reused register nodes `as_is` or `changed`, proposed exceptions) is
  read by the register's own checker and walks as if approved: placement findings, coverage C1-C3
  before and after with the new gaps, the reach from every reused node before and after, what each
  new node rests on, each reused node's keys as `register_impact` reads them, the new nodes listed
  unmapped, and the approvals per owning unit. Deterministic link candidates D1-D4 carry `authored`
  or `inferred` and never rise above `proposed`; D5, a forbidden synonym, is a placement error.
  Every overlay element is `hypothetical`; nothing is written to the register or the store, and no
  id is minted. Journey reuse shows through shared processes and D3 (decision-0007). The tool-count
  test is renamed `test_every_tool_listed_and_marked_read_only`. The record and the comparator are
  unchanged.
- **`proposal_impact` branch mode** (task-0132, doc-0017 candidate 2; additive): `--register-branch DIR
  --base REF` reads a register checkout's own additions since its merge base with REF (node files
  added, links whose id is new, exception files added; a changed node file is a reused node
  `changed`; anything else listed under `branch.not_read`) as the overlay, against the merge base's
  register taken from git into a temporary directory. The checkout is never written. The report gains
  `branch` (null for a proposal held in the call). `instance/ci/proposal-impact.sh` is an optional,
  advisory step for a register pull request (exit 0 with a report, 2 cannot run), proven in
  `harness.yml` by `tools/check_proposal_branch.py`: on a scratch branch of the public register, the
  report equals the held overlay's, ids aside.
- **`scenario_runs`, and the gate refuses mid-run** (task-0128, doc-0016 item 1; additive): a
  seventh read-only MCP tool. Per scenario of the server's subject: its title and card line, what the
  record holds (the record and each extra source, deterministic or not, the D6 verdict, the arms
  with n, models, decisions and suite) and its runs newest first, from `run.json` or, for a folder
  from before it, inferred (`inferred: true`); the held scenario with its version, stage and
  `loaded_at`; and `run_in_progress`. Replay is reported as the record, never as a run. No path is
  taken. `store_status` gains `loaded_at`; the store port gains a read, `extraction_times`. While a
  `run.json` of the server's subject reads `running` with a heartbeat under 120 s old,
  `gate_verdict`, `three_valued_answer` and `evidence_bundle` refuse and name the run (doc-0016 F2).
  `run.json` moves to version 2: `heartbeat_at`, rewritten every 30 s while the run is under way;
  version 1 is still read, its start standing for the heartbeat. The page closes a stale `running`
  file as `failed` (`error: "page restarted"`) when it starts. `harness/runs_index.py` is the one
  reader of the run folders: the page's `/api/runs` and source lists read through it, unchanged.
  `review.now()` is the reader's clock (`KG_NOW`; refused under `KG_CLOCK=pinned` without it).
- **The layout check reads each subject's manifest and keys** (task-0135, doc-0018 F2 to F5; a layout
  refusal): `tools/check_instance.py` runs the new `tools/check_subject.py` on every subject. It now
  exits 1 on any of these: a table or field `subject.toml` holds that the loader does not read; a
  task missing `keys`, `block_levels` or `max_unverified_share`, or holding a bad value in one; a
  key that is not `<entity>|<predicate>`; a subject with a task and no scenario, which the gate
  exits 2 on; a `register_map.toml` node the register does not hold, or an `owner` that owns none
  of its row's nodes; a mapper that cannot read its document. A required key that no document
  yields, when a document yields one very close to it, is a warning naming that key, so a typo no
  longer reads as absent knowledge. The documents' yield comes from the load's own mappers, run in a
  child process with no store, and is reported unchecked where they cannot run. Its report is pinned
  by `harness/schemas/subject-check.schema.json` (version 1) and carried as each subject's `check`
  in `check_instance.py --json`. Both public subjects and the example instance pass unchanged; the
  record and the comparator are unchanged.
- **`knowgov-runs`: an assistant starts and polls a scenario run** (task-0133, decision-0008;
  additive). A second stdio MCP server, `harness/mcp_runs.py`, a client of the page's
  `POST /api/run` and `GET /api/run` (`KG_PAGE_URL`, `KG_PAGE_TOKEN`, sent and never echoed). Tools:
  `run_options` (read-only), `start_run {scenario, mode, row?, effort?, as_of?}` (n fixed at 1,
  `by: mcp`, refused while a run is under way with the page's message; not read-only, destructive,
  not idempotent) and `run_status {run?}`. `KG_MCP_RUN_MODES` is `deterministic` by default; arms
  only when the operator names it. The reader, `knowgov`, is unchanged and stays read-only; the
  shipped allowlist admits it only. `mcp_server.Server` takes a tool table, server info and
  instructions. The page's banner says when a run was started over MCP.
- **`register_impact` and `proposal_impact` refuse mid-run** (task-0137, additive): while a
  `run.json` of the server's subject reads `running` with a live heartbeat, both refuse and name the
  run on the path where they read key levels from the store, as `gate_verdict` does (task-0128).
  Their register-only answers, with no scenario held or no store, are unchanged.
- **`scenario_result`** (task-0129, doc-0016 item 1 step 3; additive): an eighth read-only MCP tool.
  For a source `scenario_runs` lists (the record, an extra source, a run), what the page's Replay
  shows, as data: the D6 gate as the page's gate view has it, the date read, every required key's
  level, each arm's runs (decision, code, flagged, suite, model) and the stage-2 verdicts. It reads
  the source's files through `harness/runs_index.py`, never the store, and its reply says so. A
  source not listed is refused; no path is taken.

### What this release carries

| what | version |
|---|---|
| pumllint (the sequence-diagram mapper's parser) | 0.33.0, from PyPI |
| the IEAM register, vendored under `demo/register/` | ieam-register `v0.2.9` |
| the record's pins | unchanged from 0.5.0 |
| Python | 3.12 in the image |

The image is `ghcr.io/fdurieux/knowgov:v0.6.0`. The compose file moves to it in a follow-up, once
the Release has published its digest.

### Known limits

- The register stays at `v0.2.9`: its `v0.2.10` (decision 0017, `unregistered` in
  `RECONCILE.json`) comes with a later re-vendor, once that tag is published.
- An attestation is the manifest's declaration and is not bound to a document's version: a later
  edit to a declared document keeps its attestation until decision-0009's follow-up (c) is decided.
- A run folder from before `run.json` is inferred: its status, start and initiator are unknown.
- `proposal_impact`'s branch mode reads a branch's additions only; a deleted node or a link
  changed in place is listed under `branch.not_read`.
- The subject check compares keys with the documents' yield only where the mappers run; elsewhere
  the yield reads unchecked.
- The connector has run only on the synthetic CargoQuote export, not on a real installation.
- A register change is read only when the gate is given the previous register
  (`--register-previous`); the page's register panel does not show what a change withdrew yet.
- The GitLab include is proven by shell, not yet on a GitLab runner (task-0108).
- The hooks see Edit and Write, not a shell command writing the same file.

## 0.5.0 — 2026-11-04

The impact walk is complete, and it now runs both ways. A fifth read-only MCP tool,
`register_impact`, answers what retiring or changing a register node touches: the register's own
walk from that node, every node it reaches with its owning unit, and the knowledge keys that rest
on them, each read as `gate_verdict` reads it. It takes either walk (`dependants` or `realisers`), a
node's children and a task class, and the page's impact panel and the Neo4j Browser offer the same
four walks. In the other direction, a register change now invalidates what rests on it: given the
register as it was before its update, the gate stales the keys a withdrawn node or link lands on,
names the register's decision as the reason, and turns the derived outputs suspect. The register
moves to ieam-register `v0.2.9`, where a walk never counts its start. Hand-written code can cite
the keys it rests on, so a change reaches it as it reaches built code. The MCP server refuses a
scenario that belongs to another subject instead of answering against the wrong graph. A connector
lands a system of record's export (AML, and BPMN in its own dialect and ARIS's) in an instance's
register, append-only: an id that vanished is reported stale, never deleted.

### Contract changes (why this is 0.5.0, decision-0003)

- **The MCP server refuses another subject's scenario** (task-0126, doc-0016 F1, a fix). One
  store serves every subject; before, a CargoQuote server over a store holding J-F's `C` reported
  `scenario: C` and `gate_verdict` answered a well-formed BLOCKED, CargoQuote's keys read against
  J-F's graph. Now `store_status` reports `scenario` null and names the foreign one in a new
  `held_by_other_subject` (null otherwise), and `gate_verdict`, `three_valued_answer`,
  `evidence_bundle` and `register_impact` (where it reads a scenario) refuse with `isError`,
  naming the held scenario and the server's subject, with or without a `scenario` argument.
  `register_impact` with no scenario named and nothing held still answers from the register. The
  tool list, the record and the comparator are unchanged.
- **`register_impact` takes a `task` input** (task-0120, additive): an optional declared task
  class (default `codegen`, as `gate_verdict`'s) under whose block levels, bar and route each
  landed key's level and findings are read, as `gate_verdict --task` reads that key set. For
  CargoQuote, `design` and `codegen` give their own answers. `keys` is a key set, not a class,
  and is refused. With `children`, a map row that names only a withdrawn descendant (one the
  descent lists and does not walk) now lands too, after the others, flagged `withdrawn: true`,
  walked no further; before, it was left out. CAP-0001's `dependants` walk with children lands
  32 keys, the 32nd `QuoteAPI|on_notification_failure` through the proposed CAP-0005; the
  `realisers` walk still lands 36. The record and the comparator are unchanged.
- **The trace report carries a hand-written file's `keys`** (task-0124, additive; schema version
  1): a registered row may name the keys the file was registered on, and `check` has four new
  finding kinds, `unknown_key` and `malformed_citation` (blocker), `uncited` (major) and
  `uncitable` (info). A ledger written before still reads. The record and the comparator are
  unchanged.
- **A register change invalidates** (task-0122, additive): `gate_cli.py --register-previous DIR`
  compares the register as it was before its update (the previous vendored tag, or an instance's
  checkout before its pull) with the register the gate reads (`KG_REGISTER`). Every node that
  became deprecated or retired (or left the register), and every approved link withdrawn, marks
  the live statements on the keys resting on it as stale. The reason is the register's decision
  record: the decision its state line names, else its moved approval record, else the decisions
  the update added. The derived outputs that used those statements turn suspect, and the scenario's
  governed output from the subject's record is registered first. The gate reports them as `stale`
  and `suspect_derived` findings, as it does for a source change, so it exits 1.
  - "Resting on" is the subject's map rows plus the register's own `dependants` walk, on the
    previous register. For a node, the walk descends by `parent` (decision 0014) and never counts
    the start (decision 0016); a row naming only a withdrawn descendant lands too, as in
    `register_impact`. A descendant that the new register re-parented away from the withdrawn node,
    in any state, is skipped along with its subtree: it was moved, not withdrawn, so its keys stay
    as they were (the maintainer's choice, 2026-11-04). A descendant still under the node is
    descended as before. For a link, the rows naming both its ends, and the rows the walk from
    either end lands only through the link.
  - The report gains an optional `register_change` section: what was withdrawn, each item's reason,
    the keys, the statements invalidated and the derived output. The schema stays at version 2.
  - The store port gains one write, `invalidate_keys`. Both adapters implement it and agree, and
    `check_round_trip.py --register-previous` holds the staleness across Turtle hops.
  - Proven on a fixture built from the vendored register, which is never edited
    (`tools/register_fixture.py`): CAP-0001 deprecated, all four of its children moved to
    CAP-0006, and REL-06001 withdrawn. The moved children land nothing, so CAP-0001's deprecation
    stales no key. REL-06001 stales the eight DT-V keys and their 15 statements on CargoQuote's S1,
    the same on Neo4j and rdflib. `derived:S1:G:run1` turns suspect and the gate exits 1. An update with no state change leaves the report as it was.
    `tools/check_register_change.py` runs it on rdflib in `harness.yml` and on Neo4j and rdflib in
    the stack job. The record and the comparator are unchanged.

### Also in this release

- **Hand-written code cites the keys it rests on** (task-0124, doc-0015 §3). A header comment line,
  `# knowgov-keys: K1, K2` in Python or `// knowgov-keys: K1, K2` in Java, names them.
  `knowgov-trace register --keys K1,K2`, or `--cited` to read each file's own header, registers
  the file as a derived output on those keys' current statements. After a change invalidates one,
  `check` reads the file suspect, as it reads a built one. A key the subject does not know is
  refused (exit 2) and, in a file's header, a blocker. An instance turns on the missing-citation
  check with `[citations] require = true` in `code_map.toml`, optionally for some APPs only.
  Proven after S6's change by `tools/check_trace_walkthrough.py`. Citations rot; a file edited
  after its registration is drift, as before, and asks for a new one.
- **The connector for a system of record** (task-0063, decision-0006): `tools/connector.py` lands
  an export in an instance's register as `exports/<system>/<date>/`. The folder holds the files,
  a `MANIFEST.toml` and a `RECONCILE.json` in ieam-register's format. The system and the AML
  attribute that carries the register id (`AT_ID` by default) are instance configuration, in a
  new optional `connectors.toml`.
  - It reads AML, and BPMN 2.0 in its own dialect and ARIS's. Namespaces are matched by URI.
    Register ids come only from the configured attribute, a process `@id` and `<documentation>`.
  - A register node whose id the previous export carried and this one lacks is reported stale.
    Nothing is deleted. A renamed object is an update (`ids.renamed`). An export is never landed
    over another, or with a date before the newest.
  - Proven on the synthetic CargoQuote export, in a temporary example instance: PROC-0005 is
    stale and PROC-0004 renamed. Nothing under `harness/` or `demo/app` names the vendor (a test
    guards it). It has not yet run on a real installation.
  - The synthetic export now carries the real ARIS 10.0 namespace URIs, `exporterVersion` and
    `aris:port` values in place of task-0119's stand-ins.
- **Connector follow-ups** (task-0121):
  - The register's own `tools/reconcile.py` is now vendored with its other tools, still at
    v0.2.8. The connector imports its comparison instead of restating it, and adds only its own
    extensions on top.
  - `tools/check_instance.py` checks `connectors.toml`. Each `[system.<name>]` must be a system of
    the register's `metamodel/sources.toml`, and `id_attribute` must be a non-empty string.
    Anything else is a layout error.
  - The synthetic ARIS BPMN keeps `exporterVersion="10.0.0.320027101"`, but its `exporter` now
    reads `synthetic, mimicking ARIS`. A landed MANIFEST's `source_version` therefore never reads
    as a real ARIS export.
- **A synthetic CargoQuote ARIS export** (task-0119): `tools/aris_export.py` writes, per variant,
  one AML file and the same process in two BPMN 2.0 dialects, from public CargoQuote material only
  (the vendored kit's `quote_process.bpmn` and the vendored register). The fixtures are committed
  under `tools/fixtures/aris_cargo_quote/{first,later}/` for the ARIS connector (task-0063).
  - The AML: every process, capability, application system type and person type carries its
    register id in `AT_ID`, and every object has a uuid5 GUID that stays the same across runs
    and variants.
  - The BPMN: the end-to-end process's register id is the process `@id`, and each activity's is
    its `<documentation>` text. Those are what ARIS 10.0 kept through one import and export of a
    BPMN file. `quote_process.aris.bpmn` mimics the dialect ARIS wrote: the `semantic:` prefix,
    `ID-…` element ids, `isExecutable` dropped, colours and label styles.
  - `later` drops PROC-0005 and renames PROC-0004, for the connector's append-only and stale-id
    cases.
  - Marked synthetic in its headers. The AML's ARIS type names are unverified against any method
    filter. bpmnlint's recommended rules find nothing in the four BPMN files.
- **MCP server, a fifth read-only tool, `register_impact`** (task-0111): what retiring or changing
  a register node touches. It runs the register's own impact walk from a register id
  (`dependants` by default, or `realisers`) on `KG_REGISTER`, and returns the register's tag and
  commit, the node, its children listed but not walked (by default; `children`,
  task-0118, adds the register's descent), every edge with `live`, and what the walk reached by id prefix with each node's
  owning unit. It also returns the `register_map.toml` keys whose rows name the node or what it
  reaches, each with its owner, anchor and the nodes it came through (`via`). With a scenario
  loaded, each key carries its level, stale statements, suspect derived outputs and findings, as
  `gate_verdict` reports that key set on the same `as_of`. It is additive: the store view's reads
  are unchanged and nothing is written.
- **`register_impact` walks a node's children on request** (task-0118): a `children` input
  (default false) runs the register's own descent by `parent` (ieam-register decision 0014,
  `walk_children`). An approved descendant is walked by its own kind's row. Any other is listed
  withdrawn and not walked from. What is reached excludes the start and its descendants. A map row
  lands on the start, a walked descendant or a reached node. Every descendant is listed with its
  parent and state, and `children_walked` says which answer this is. Without `children` the answer
  is unchanged. For CargoQuote, CAP-0001 reaches PRD-0002, PROC-0001 and JRN-0001 and lands 31 keys
  on the `dependants` walk; all 36 `codegen` keys land on the `realisers` walk. The register is
  vendored at ieam-register `v0.2.8`, which also carries decision 0015 (an approved child of a
  deprecated parent is a checker error). The record (as of 2026-10-30) and the comparator are
  unchanged. The page's impact panel still walks without children.
- **The page's impact panel offers both walks and the children option** (task-0112): beside the
  node id, a `dependants`/`realisers` choice and a `children` box; `GET /api/register/impact/<id>`
  takes `?walk=` and `?children=1` (a bad value is a 400). The panel names its walk in its title
  ("What realises CAP-0002"; "…, with its descendants"), lists every descendant with its state and
  whether it was walked, and reaches what `register_impact` reaches on every node, both walks, both
  options. Each variant's Cypher is on the panel with its own Browser guide
  (`/api/register/impact/<id>/<variant>/guide/<form>`; the default walk's paths are unchanged), and
  three saved queries join the list: `register-impact-children`, `register-realisers` and
  `register-realisers-children`. `check_impact_cypher.py` checks all four walks on every node.
  Without the options the panel and its Cypher are unchanged. The record and the comparator are
  unchanged.
- **The register is vendored at ieam-register `v0.2.9`** (task-0122, first half), which carries its
  decision 0016: a walk never counts its start among what it reaches. An edge back to the start is
  still listed, and the register marks it `to_start`. On CargoQuote's register, 19 nodes stop reaching
  themselves on the `dependants` walk; no other node joins or leaves a reached set, and the
  `realisers` walk and the descent by `parent` are unchanged, so `register_impact`'s keys are too.
  The page's impact panel and its Cypher rows form mark such an edge "yes, back to the start, not
  counted", and `check_impact_cypher.py` compares that column too. The record (as of 2026-10-30)
  and the comparator are unchanged.
- `instance/README.md` "Letting an AI assistant ask the gate": connecting Claude Code (`claude mcp add -s user`) and Claude Desktop (config file, absolute paths, the full `docker` path, the log) over the container's stdio, the phone through Remote Control, `KG_SUBJECT` as a path, `scenario` in every call, and a stateless HTTP example with `clientCapabilities` that a test runs against the server, with a guard on every flag the section names (task-0117).

### What this release carries

| what | version |
|---|---|
| pumllint (the sequence-diagram mapper's parser) | 0.33.0, from PyPI |
| the IEAM register, vendored under `demo/register/` | ieam-register `v0.2.9` |
| the record's pins | unchanged from 0.4.0 |
| Python | 3.12 in the image |

The image is `ghcr.io/fdurieux/knowgov:v0.5.0`. The compose file moves to it in a follow-up, once
the Release has published its digest.

### Known limits

- The connector has run only on the synthetic CargoQuote export, not on a real installation
  (task-0063); the AML's ARIS type names are unverified against any method filter.
- A register change is read only when the gate is given the previous register
  (`--register-previous`); the page's register panel does not show what a change withdrew yet.
- Citations are read in Python and Java headers only, and a cited file counts only once it is
  registered.
- The GitLab include is proven by shell, not yet on a GitLab runner (task-0108).
- The hooks see Edit and Write, not a shell command writing the same file.

## 0.4.0 — 2026-11-04

The gate becomes something an AI-native delivery pipeline can rely on. A fail-closed Claude Code
hook runs it at stage transitions and stops the step when it says no or cannot run. Each finding
names the unit that answers for the key and the route to approval, and a declared gap also names
the unit that closes it. The MCP server reads one date per process. A second task class, `design`,
checks a requirements-and-design step. The register moves to ieam-register `v0.2.7`.

### Contract changes (why this is 0.4.0, decision-0003)

- **MCP server, one `as_of` per process** (task-0100, doc-0014 C2): `harness/mcp_server.py` reads
  `KG_AS_OF` (or `--as-of`: `YYYY-MM-DD`, `record` or `today`; default `today`) once at start and
  resolves it once. `gate_verdict` and `evidence_bundle` read review currency on that date unless a
  call names its own; a call's `today` or `record` is also resolved once per process.
  **`evidence_bundle`'s default changes from `record` to the server's date** (today unless
  `KG_AS_OF` says otherwise); `record` stays available as an explicit `as_of`, as
  `tools/check_mcp_server.py` and `tools/lighthouse_evidence.py` pass it. `store_status` carries
  `as_of` and `as_of_from`. A bad `KG_AS_OF`, or a relative date under `KG_CLOCK=pinned` with no
  `KG_TODAY`, stops the server at start (exit 2).
- **Gate report, owner and route on findings** (task-0102, doc-0014 C7): a `key`, `stale` or
  `lapsed` finding carries `owner`, the unit that answers for the key in the subject's
  `register_map.toml`, and `route`, the owner's questionnaire. Additive: `schema_version` stays 2
  and a report from before still validates. The page's gate box names the owner.
- **`knowgov-gate.sh` refuses `KG_TASK=keys`** (task-0102, doc-0014 C4): a mandatory check runs a
  task class, never an agent-chosen key set.
- **Gate report, the closing unit on a declared gap** (task-0110, decision-0002): a `key` finding
  on a declared gap carries `closer`, the unit its declaration names (compliance, ORG-0004, for
  CargoQuote's OD-1), and its `route` ends with the close. Additive: `schema_version` stays 2. The
  hook's summary and the page's gate box name the closing unit.

### Also in this release

- **A fail-closed Claude Code hook for the gate** (task-0099, doc-0014 C1): `instance/ci/claude/`
  runs the gate at stage transitions (plan accepted, spec committed, before push), never on every
  edit. A finding and an unavailable gate both block, with the reason and the route to approval;
  a `keys` report or one for another task is refused. Three settings snippets: repository, managed
  (the mandatory one) and an advisory variant labelled fail-open. Supersedes doc-0004's exit-code
  adapter.
- **Pre-load findings reach the platform's annotations** (task-0106): the `preload` gate writes its
  report under `KG_REPORT`, so `KG_ANNOTATE` turns its findings into GitHub annotations and GitLab
  code quality; a finding the baseline holds is at most a warning.
- **knowgov dogfoods the hook** (task-0105): this repository's `.claude/` blocks hand edits to
  vendored files and to the backlog.
- **The register is vendored at ieam-register `v0.2.7`** (task-0109): decision 0012's realiser walk
  and decision 0013's review months. CargoQuote's three `response|*` keys now lapse after six
  months; as of 2027-02-07, S1, S3 and S6 read QUALIFIED. The record (as of 2026-10-30) is
  unchanged.
- **The MCP allowlist leaves the managed hook fragment** (task-0107): `instance/ci/claude/managed-settings.json`
  carries `allowManagedHooksOnly` and the hook only; `allowManagedMcpServersOnly` and `allowedMcpServers` move to
  `managed-mcp-allowlist.json`, an opt-in whose lists replace lower sources' and must be merged; the hook stays
  mandatory without it.
- **A `design` task class on CargoQuote** (task-0101, doc-0014 C3): `[tasks.design]` names the 36
  keys a requirements-and-design pass rests on (each requirement's text and the component that
  carries it, the screening bands and their outcomes, the failure behaviours, the flow's order, the
  response statuses, the containers' calls), with its `rationale` and the codegen block levels. The
  `codegen` class and the record are unchanged; the comparator stays identical. `store_status`
  reports a class's rationale; the lighthouse rehearsal runs every declared class on each scenario
  and records the classes `store_status` lists. As of the record (2026-10-30), design reads S1
  QUALIFIED, S2 BLOCKED, S3 QUALIFIED, S4 BLOCKED, S5 BLOCKED, S6 QUALIFIED, S7 BLOCKED: the
  structure is extracted and never verified. `docs/lighthouse-evaluation.md` names the class at each
  pilot transition: `design` at the specification's commit, `codegen` at plan acceptance and push.

### What this release carries

| what | version |
|---|---|
| pumllint (the sequence-diagram mapper's parser) | 0.33.0, from PyPI |
| the IEAM register, vendored under `demo/register/` | ieam-register `v0.2.7` |
| the record's pins | unchanged from 0.3.0 |
| Python | 3.12 in the image |

The image is `ghcr.io/fdurieux/knowgov:v0.4.0`. The compose file moves to it in a follow-up, once
the Release has published its digest.

### Known limits

- The GitLab include is proven by shell, not yet on a GitLab runner (task-0108).
- The hooks see Edit and Write, not a shell command writing the same file.

## 0.3.0 — 2026-11-04

A hardening release on top of 0.2.0. The page's writes need a token beyond the local machine. A
code-change registration reads as of a chosen date. A document made of several files keeps a
digest for each of them. The lighthouse evidence reaches the gate the way an agent does, through
the MCP server.

### Contract changes (why this is 0.3.0, decision-0003)

- **The page's write endpoints** (a run, the register projection): when the stack listens beyond
  127.0.0.1, they require `KG_PAGE_TOKEN` as a bearer token. Every bind refuses a request from a
  foreign Origin. Reads stay open (task-0096).
- **`knowgov-trace register --as-of`**: registrations record the date they read. The trace report
  and its ledger carry `as_of`, an additive change in the schema. `KG_AS_OF` reaches `register`
  through all three CI wrappers (task-0093).
- **Store port:** `record_part_digests` / `part_digests`. A directory artefact's Version keeps a
  digest for each file (`part_sha256`), carried through the Turtle round trip. `register-cites`
  compares a cited file by its own digest (task-0094).

### Also in this release

- `tools/lighthouse_evidence.py` reads the evidence bundle through the MCP server's
  `evidence_bundle`, over stdio or `--transport http`. A run fails if the bundle's verdict or date
  differs from the gate's (task-0095).
- The demo's compose file names the release image by digest. The image moved from `v0.1.0` to
  `v0.2.0` after 0.2.0 was published.
- **Process:**
  - a release PR comes with the Release's title and description;
  - a merged PR refreshes the maintainer's two pages.

### What this release carries

| what | version |
|---|---|
| pumllint (the sequence-diagram mapper's parser) | 0.33.0, from PyPI |
| the IEAM register, vendored under `demo/register/` | ieam-register `v0.2.6` |
| the record's pins | unchanged from 0.2.0 |
| Python | 3.12 in the image |

The image is `ghcr.io/fdurieux/knowgov:v0.3.0`. The compose file moves to it in a follow-up, once
the Release has published its digest.

### Known limits

- **The page's reads have no login.** Keep the default localhost bind, or put the page behind your
  own access control.
- **The GitLab template** is proven by shell, not yet on a GitLab runner.
- **The lighthouse pilot** waits on the choice of incumbent.
- **The register's open decisions** are the realiser walk and the review months for CargoQuote's
  `response|*` kinds (ieam-register #18 and #19).

## 0.2.0 — 2026-11-04

The gate now sees change, time and code. A changed document invalidates what rested on it and
marks the code built on it suspect. A review runs out on its kind's cadence. A code change finds the
knowledge it rests on. Knowledge a person gives can move the gate, and only under a person's
review. The gate reaches an AI assistant through a read-only MCP server and a pipeline through
three wrappers. A private instance is checked before it is loaded, and the stack is closed by
default.

### Contract changes (why this is 0.2.0, decision-0003)

- **Gate report schema v2** (`harness/schemas/gate-report.schema.json`): stale statements and
  suspect derived outputs are findings (task-0048). Additive fields: the version and change
  loaded (task-0049), `superseded_by` (task-0071), `lapsed` findings and `as_of`
  (task-0068), and pre-load verdicts at info (task-0064).
- **Gate command flags:** `--stage 2 [--reverify]` loads a scenario's later version (task-0049).
  `--as-of DATE` reads the gate as of a date (task-0068).
- **What a key's level means:**
  - An unreviewed, elicited statement no longer lowers a key that a document holds at validated
    or better. A contradicting one still disputes it (decision-0004, task-0039).
  - A review verification lapses after the review months of its kind (decision-0005,
    task-0068).
- **Store port:** `export_turtle()` / `import_turtle()` (task-0070), and `record_preload` /
  `preload_verdicts` (task-0064).
- **New report schemas:** `trace-report.schema.json` for `knowgov-trace` (task-0051). The gate
  and trace reports are also converted to GitHub annotations, GitLab code quality and SARIF
  (task-0083).
- **Instance layout:** `code_map.toml` maps code paths to register applications (task-0050).
  `preload-report.json` is read at the load (task-0064). The CI wrappers take `KG_AS_OF`
  (task-0089).
- **MCP server:** the tools `store_status`, `gate_verdict`, `three_valued_answer` and
  `evidence_bundle` (tasks 0056, 0080). The server speaks the 2026-07-28 stateless revision beside
  the handshake (task-0079).
- **The stack's defaults:** the page, Neo4j Browser and bolt publish on 127.0.0.1. A wider bind
  (`KG_BIND`) refuses the default Neo4j password (task-0090).

### Capture that moves the gate (m-5)

- A person's answer is weighed against the documents' statements. A contradiction is a dispute
  for review, and an agreement is corroboration (task-0038).
- **Capture routes.** There are three:
  - direct answers;
  - a questionnaire from the reviews falling due, pre-filled with the earlier answer (task-0040);
  - a transcript read by a model, whose candidates land at proposed and are never promoted. Only
    the transcript's digest is kept (task-0041).
- **Checks at ingest.** Capture accepts only handles issued in the register (task-0055), holding
  the `gives` role (task-0091). The questionnaire warns against notes that identify a person, and
  the reviewer reads each note (task-0042). Each key has one answering owner (task-0043).
- The real CargoQuote S2 reaches PROCEED by command once its owner, the compliance unit, closes
  OD-1 (task-0054, register decision 0011).
- Every check that reads the date reads a pinned one (task-0075). The page shows the as-of date
  and each lapsed review (tasks 0076, 0086).

### An adopter can start alone (m-6)

- **The check before the load** runs Spectral, markdownlint, gplint, bpmnlint and dmnlint, all
  pinned (tasks 0066, 0082). It fails only on regression against a committed baseline
  (task-0065). The verdict is recorded on each document's version (task-0064).
- **The impact walk.** The register's walk starts from every kind (task-0044, register decision
  0010). The impact panel names the owning unit of each node it reaches (task-0047). A register
  node reaches its statements through the part of a document it cites, including J-F's directory
  artefacts (tasks 0046, 0077, 0088), with a Browser link for each view (task-0078).
- A provenance crosswalk maps knowgov's bases and statuses to W3C PROV-O (task-0072).

### Code changes reach the knowledge (m-7)

- **The gate's three gaps from doc-0011 are closed:**
  - stale and suspect findings (task-0048);
  - a scenario's later version (task-0049);
  - `knowgov-trace` (task-0051), which takes a code change through `code_map.toml` to the gate.
- **Pipeline wrappers** cover GitHub Actions, GitLab CI and plain shell (task-0052), with
  annotations (task-0083).

### The lighthouse (m-8)

- The read-only MCP server (tasks 0056, 0079, 0080).
- A round trip through Turtle into the other store gives the same gate (tasks 0070, 0085).
- `docs/lighthouse-evaluation.md`, the evaluation protocol, rehearsed on the public subjects
  (task-0069).
- **The security pack:** `docs/security.md` and `SECURITY.md`, with a test for each claim
  (task-0059). Its gaps are closed by localhost binds (task-0090), the `gives` check (task-0091),
  and digest and SHA pins with Dependabot (task-0092). The record's pins are frozen.

### Documentation

The briefs: doc-0013, Palantir Ontology read against knowgov. The decisions: decision-0004 (option
B) and decision-0005 (the review lapse).

### What this release carries

| what | version |
|---|---|
| pumllint (the sequence-diagram mapper's parser) | 0.33.0, from PyPI |
| the IEAM register, vendored under `demo/register/` | ieam-register `v0.2.6` |
| Neo4j driver, rdflib, pyshacl, openai | 6.4.1, 7.6.0, 0.40.2, 3.41.0 (the record's pins, unchanged) |
| Neo4j server in the stack | 5.26 community, by digest |
| the J-F oracle's pins | unchanged from 0.1.0 |
| pre-load linters | pinned in `instance/ci/` (Spectral 6.17.0, gplint 2.6.1 and the rest) |
| Python | 3.12 in the image |

The image is `ghcr.io/fdurieux/knowgov:v0.2.0`. The compose file names the release by digest. It
moves to `v0.2.0` in a follow-up once the Release has published the image and its digest exists.

### Known limits

- **Gaps `docs/security.md` still lists:** the page has no login, and the store keeps short
  excerpts.
- **Not yet proven on a real runner:** the GitLab include. It is proven by shell only (task-0083).
- **The lighthouse** waits on the maintainer's choice of incumbent and pilot (task-0062). Its
  connector and outcome study follow from that choice.
- **The register's open decisions:** the realiser walk and the review months for CargoQuote's
  `response|*` kinds (ieam-register #18 and #19).

## 0.1.0 — 2026-11-03

The first release. knowgov keeps the knowledge an AI assistant builds on as governed statements,
each with its source, its status and its verification. A gate says whether a task's required
knowledge is good enough to build on, and impact analysis shows what a change reaches. It runs on
two public, synthetic subjects, and an organisation can point it at its own private instance.

### The platform

- **It stands alone** (milestone m-0): the demo, its harness and the vendoring tools moved out of
  pumllint (decision-0001), with the CargoQuote record vendored at a tag and checked by digest.
- **Any subject, any store** (m-1): a subject is a manifest under a subject root
  (`subjects/README.md`). The store is a port with two adapters, Neo4j and an in-memory rdflib
  graph (`KG_STORE`). The model endpoint is configuration.
- **Two public subjects:** `cargo_quote`, the proof of concept with seven scenarios and its scored
  record, and `jef_data_load`, the recreation experiment's kit with its own suite as the oracle.
- **The page** serves every subject of its root, with a subject drop-down (`KG_SUBJECTS`), a models
  and efforts drop-down (OpenAI, Google, and Anthropic through a LiteLLM gateway), token counts in
  place of prices, and the register card with its impact panel, footprint and saved Cypher.

### A client's private instance (m-2)

- **The instance layout** (`instance/README.md`): `register/`, `artefacts/<kind>/` with one kind
  per row of the programme's artefact table, `subjects/`, `record/`. It is mounted read-only
  (`demo/docker-compose.instance.yml`). `tools/check_instance.py` reports a document no mapper
  reads as absent, and `tools/example_instance.py` builds a public example that CI mounts
  read-only and finds unchanged afterwards.
- **The check before the load** (`tools/preload_check.py`): each document is checked by its kind's
  linter where one runs here (pumllint). Every other kind is listed as unchecked, never passed.
  There is a CI template an instance copies. It checks form, not knowledge.
- **Capturing what people know** (`harness/capture.py`): a questionnaire per owner from the gate's
  gaps. An answer comes back as a statement *proposed* by a person's issued handle, never a name,
  and "nobody knows" becomes a declared gap.
- **A person's review** (`capture.py review`, decision-0002): an `approves` handle approves what
  another gave, for six months. Only a declared gap's owner closes it. A dispute is settled by
  ruling on every side. Nothing a model writes rises above proposed.

### A programme project (m-3)

- **The gate as a command** (`harness/gate_cli.py`): exit 0, 1 or 2 under the programme's gate
  contract, a severity threshold (`--fail-on`), the record as a ratchet baseline
  (`--baseline record`), and JSON pinned by `harness/schemas/gate-report.schema.json` (version 1).
- **An agentic arm**: a subject's program built over several turns with read, write and run-suite
  tools, the knowledge read through the gate.

### Documentation

`docs/guide.md`, the adopter's guide (what knowgov solves, dropping documents, the dashboard,
impact in Neo4j). The briefs and decisions behind this release are in `backlog/docs/` (doc-0001 to
doc-0012) and `backlog/decisions/` (decision-0001 to decision-0003).

### What this release carries

| what | version |
|---|---|
| pumllint (the sequence-diagram mapper's parser) | 0.33.0, from PyPI |
| the IEAM register, vendored under `demo/register/` | ieam-register `v0.2.4` |
| Neo4j driver, rdflib, pyshacl, openai | 6.4.1, 7.6.0, 0.40.2, 3.41.0 |
| Neo4j server in the stack | 5.26 community |
| the J-F oracle's pins | pandas 3.0.5, numpy 2.4.6, requests 2.34.2, pyarrow 25.0.1, pytest 9.1.1, pytest-bdd 9.0.1 |
| Python | 3.12 in the image |

The image is `ghcr.io/fdurieux/knowgov:v0.1.0`.

### Known limits

- The impact walk starts only from applications, processes and journeys; the register's decision
  0010 (`v0.2.5`) extends it, and knowgov follows in 0.2.0.
- The gate counts stale statements and suspect derived code but does not yet raise them as
  findings (task-0048, 0.2.0).
- A person's answer is not yet compared with the documents' statements in the conflict rule
  (task-0038).
- Real S2 cannot reach PROCEED until the register's compliance unit (decision 0011) is vendored
  (task-0054).
