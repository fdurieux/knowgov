# Working on knowgov

Governed knowledge for AI-assisted delivery: the platform behind pumllint's
governed-repository demo, moved here by decision-0001. Maintainer register:
terse, dense, symbols cited by name. British English.

## Layout and checks

```bash
python tests/run_tests.py          # stdlib only; imports every tests/test_*.py, calls each test_*
cd demo && docker compose up -d --build --wait   # the stack; CI loads S1 deterministically and runs the comparator
```

- `harness/` the pipeline, with the store port (`store.py`: the operations
  the loader, the rules, the gate, the census, the SHACL reads and the register
  projection need, nothing more) and two adapters: `store_neo4j.py` (every
  Cypher statement, the constraints, the saved queries) and `store_rdflib.py`
  (an rdflib graph in memory, optionally persisted to `KG_RDFLIB_FILE`); `KG_STORE`
  picks one, `neo4j` by default. Every caller names `open_store(access="read"|"write")`: a read handle passes `store.READS` only and never
  publishes; a writer publishes on `commit()`, never `close()`, and on a file locks `<file>.lock` before it loads (task-0141.02). No other module speaks Cypher; a test guards
  it (task-0003). `export_turtle`/`import_turtle` carry a store into a fresh one of either kind in the rdflib
  adapter's form; `tools/check_round_trip.py --chain` holds every scenario's gate reports and three-valued
  answers equal across the hops (rdflib in `harness.yml`, Neo4j to rdflib and back in the stack job; task-0070), and with `--expect-parts` the file digests a directory artefact's Version keeps in `part_sha256` (`record_part_digests`/`part_digests`; `register-cites` compares a cited file by its own; task-0094), and with `--expect-preload` on the example instance with its report every Version's pre-load verdict, the gate's preload bundle and its info findings, both ways through Neo4j (task-0085). The comparator compares D1, the Neo4j edition's constraint
  measurement, only between runs of the same store kind (task-0004). `demo/` the page, the vendored model, the vendored
  register, the comparator, the Docker files; `subjects/<id>/` a subject root
  (`subjects/README.md` documents the format): `subject.toml`, `scenarios.toml`,
  `plants.toml`, `queries.toml`, `register_map.toml`, `prompts/`, and under
  `vendor/` the bytes vendored from pumllint in its relative layout; `runs/`
  re-runs, gitignored. `instance/` an organisation's instance layout (`README.md`, adopter register;
  `kinds.toml`, one kind per row of the site's artefact table and the mappers that read it, every
  mapper in exactly one), checked by `tools/check_instance.py` (each subject's manifest, scenario, register map and keys against the documents' yield by `tools/check_subject.py`, pure, the yield in a child process, no store; schema `subject-check`; fixture `tools/fixtures/subject_probe`; task-0135, doc-0018), with a public example from
  `tools/example_instance.py` that CI mounts read-only and digests before and after (task-0006). Each kind's `lint`
  field is doc-0008 §5's tool and gate column; `tools/preload_check.py` lints an instance's documents
  with the ones that run here (pumllint; Spectral for api-contracts, task-0066; markdownlint, gplint, bpmnlint, dmnlint for prose, Gherkin, BPMN, .dmn, task-0082, proven by `tools/check_preload_linters.py`; `--baseline` fails only on regression, task-0065), lists every other kind's files, and a kind whose linter is not installed, as unchecked, exits under the
  gate contract, JSON under `harness/schemas/preload-report.schema.json`; `instance/ci/` is the
  template an instance copies, its script proven in `harness.yml` (task-0045); `instance/ci/knowgov-gate.sh`
  the three gates as one platform-neutral call (KG_* variables to the core flags; `KG_TASK=keys` exits 2, doc-0014 C4), wrapped by
  `instance/ci/github/action.yml` (run for real in `harness.yml`) and `instance/ci/gitlab/knowgov.gitlab-ci.yml`
  (its script lines run by a shell, `tools/check_ci_wrappers.py`; task-0052). `instance/ci/claude/knowgov_hook.py` the gate as a fail-closed Claude Code hook at stage transitions (plan, spec commit, push; exit 1 and 2 both to the hook's blocking 2, a `keys` report refused; `decide` the mapping another hook imports, with its own `route` and `unavailable_route`; task-0102), with a repository, a managed and an advisory fail-open settings snippet (task-0099; doc-0014 C1, C4). The load records the report's verdict per document version (`harness/preload.py`, `KG_PRELOAD_REPORT` or `<instance>/preload-report.json`; unchecked unless the digest matches) and the gate lists the unchecked or flawed documents behind its keys at info (task-0064). Form, not knowledge. `harness/gate_cli.py`
  the gate as a command (exit 0/1/2, `--fail-on`, `--baseline record|FILE`, JSON pinned by
  `harness/schemas/gate-report.schema.json` through `harness/schema_check.py`; task-0007; version 2: stale statements and suspect derived outputs are findings, task-0048, shown after S6's change by `tools/check_gate_after_change.py`; a key, stale or lapsed finding names its key's `owner` unit from `register_map.toml` and its `route`, the owner's questionnaire, additive, and the page's gate box the owner, task-0102; a declared gap's key finding also its `closer`, the unit its declaration names, and the route the close, task-0110; `--register-previous DIR`, `harness/register_change.py`: what a register update withdrew, deprecated or retired nodes and withdrawn links, stales the keys resting on it, map rows plus the register's dependants walk on the previous register, a descendant re-parented away skipped with its subtree (maintainer, 2026-11-04), the reason its decision record, and their derived outputs suspect, port write `invalidate_keys`, proven on `tools/register_fixture.py` by `tools/check_register_change.py`, task-0122). `--as-of` (decision-0005, task-0068; `harness/cadence.py`): a review verification's `valid_until` is its date plus its key's review months from the register's `lifecycle.toml`, a lapse reads validated and is a `lapsed` finding; today by default, the deterministic run and the comparator as of the subject's `[record] as_of`; `run.py --as-of` and the page's run (`as_of`) name another date, and the page's gate box and panel name the date read and list each lapse with its day and months (task-0076; S6's stage-2 gates too, task-0086).
  The clock (task-0075): `harness/review.py` `today()` is the only wall-clock read that decides an
  outcome (KG_TODAY, else the wall clock); under `KG_CLOCK=pinned` (the test runner, the rdflib job,
  every check tool's commands via `review.pinned`/`cadence.pin_record`) it refuses the wall clock.
  `tests/test_clock.py` names every other read, holds each check tool pinned and each workflow gate
  command to an `--as-of`. `harness/mcp_server.py` the gate, the three-valued answer, the arms' evidence bundle (`evidence_bundle`, task-0080) and what retiring a register node touches (`register_impact`, `harness/register_impact.py`: the register's own walk, the map rows it lands on, each key as `gate_verdict` reports it; task-0111; `children` the register's descent by `parent`, decision 0014, off by default, task-0118), the register listed and one node's lineage (`register_nodes`, `harness/register_nodes.py`, also a CLI: filters taxonomy, kind, state, owning unit, parent, a limit and the total; ancestors by `parent` to the root and children, an annotation never a walk, decisions 0010 and 0014; the register's own loader, no store; schema `register-nodes`; task-0142, doc-0020), and a proposed addition read as if approved without approving it (`proposal_impact`, `harness/proposal_impact.py`, also a CLI: the overlay's nodes, links, reused nodes and exceptions read by the register's own `check_nodes`, `check_relationships`, `check_glossary`, `check_coverage` and walks, every overlay element `hypothetical`, deterministic candidates D1-D4 `authored`/`inferred` never above `proposed`, D5 a placement error, the reused nodes' keys as `register_impact`'s, no id minted, nothing stored, schema `proposal-impact`, the worked example `tools/fixtures/proposal_contract_quote.json`; task-0130, task-0131, doc-0017, decision-0007; branch mode `--register-branch DIR --base REF`, a register checkout's additions since the merge base, read against the merge base's register from `git archive`, the checkout never written, `instance/ci/proposal-impact.sh` the optional advisory step, proven by `tools/check_proposal_branch.py`, task-0132) as a read-only MCP server (one `as_of` per process: `KG_AS_OF` or `--as-of`, today by default, read once at start, the default of both `gate_verdict` and `evidence_bundle` and reported by `store_status`; task-0100) (stdio, or
  Streamable HTTP on 127.0.0.1 with `KG_MCP_TOKEN` for any wider bind; dual-era: the 2026-07-28 stateless revision
  (`server/discover`, per-request `_meta`, header checks) beside the `initialize` handshake, task-0079; standard library; the store behind a
  view that lets the port's reads through and nothing else; `tools/check_mcp_server.py` holds its report equal
  to `gate_cli.py --no-load`'s and its bundle to the arms' `render_bundle` on a live store; task-0056). `harness/trace.py`
  knowgov-trace (task-0051): `register` records built files as derived outputs (store and a JSON
  ledger, since a load wipes the store; `--as-of` as `check`'s, each entry recording the date read, task-0093), `check` reports suspect, drift, missing, unmapped and the
  task's gate under the same exit contract, JSON pinned by `harness/schemas/trace-report.schema.json`;
  the APP comes from the instance's `code_map.toml` (`harness/code_map.py`, task-0050); hand-written code by the keys its header cites (`harness/citation.py`, Python and Java; `register --keys`/`--cited`; `uncited` only where `code_map.toml`'s `[citations]` requires it; task-0124); S6 shown by
  `tools/check_trace_walkthrough.py`. `KG_SUBJECT` selects the root; nothing in `harness/` or
  `demo/` names a subject, a document or a scenario (task-0002). Two public
  subjects: `cargo_quote` (the proof of concept, seven scenarios, the scored
  record; a `design` task class beside the record's `codegen`, task-0101) and `jef_data_load` (the recreation experiment's kit, the degradation
  test's arms as scenarios, a deterministic record, the kit's own suite as oracle; task-0021).
  `docs/lighthouse-evaluation.md` the evaluation protocol (doc-0013's seven criteria; actions out of
  scope); `tools/lighthouse_evidence.py` collects its public evidence on both subjects (task-0069), the bundle by the server's `evidence_bundle`, over stdio or `--transport http` (task-0095).
  `tools/connector.py` lands a system of record's export (AML; BPMN, its own dialect and ARIS's, by URI) in
  `<instance>/register/exports/<system>/<date>/` with MANIFEST.toml and RECONCILE.json in ieam-register's format (decision-0010, task-0138: `[ids]` every AML object by GUID, the system's `id_field`; register ids apart, `[register_ids]` GUID to id, `[bpmn_ids]`; RECONCILE.json's ids diff, `stale_nodes` and `unregistered` the register's own, plus `unknown_ids` and stale-by-register-id, redundant once nodes carry `[source]` GUIDs; `proposal_impact`'s D2 reads `[register_ids]`), the system
  and the id attribute (`AT_ID` by default) from `<instance>/connectors.toml`; the comparison the register's own `tools/reconcile.py`, vendored and imported; `check_instance.py` checks `connectors.toml`'s systems against `metamodel/sources.toml` (task-0121); a vanished id stale, never a deletion; the
  fixtures land only in a temporary example instance; nothing under `harness/` or `demo/app` names the vendor (task-0063).
- The register the page reads is `KG_REGISTER` (default `demo/register`, the public register
  vendored at a tag): one register per organisation, shared by every subject of it; an
  instance mounts its own checkout read-only (`demo/docker-compose.instance.yml`). A subject
  joins it through its own `register_map.toml` and `export_manifest`; no module under
  `demo/app` names a register path or an export folder (`tests/test_subject.py` guards the
  subject's export date as it guards its names).
- Re-vendor the register with `python tools/vendor_register.py <checkout>` at
  a tag of ieam-register; the Legible model with `python tools/vendor_legible_model.py
  <checkout of fdurieux.github.io>` (its note also carries the digest of
  `demo/model/cascade_layout.py`); a subject's bytes with `python
  tools/vendor_subject.py <checkout> --subject <id>` at a pumllint tag (`--allow-untagged`
  for a commit, and the note says so; the path set is the subject's `[vendor]` table).
  Each rewrites its `SOURCE.md`; a test holds every file to its digest. The demo README's "Keeping the demo current"
  section is the adopter-facing walkthrough.
- The record's versions are pinned in `demo/Dockerfile` (neo4j 6.4.1, rdflib
  7.6.0, pyshacl 0.40.2, openai 3.41.0) with pumllint 0.33.0 from PyPI, the
  library the sequence-diagram mapper imports, and the J-F subject's oracle
  pins (pandas 3.0.5, numpy 2.4.6, requests 2.34.2, pyarrow 25.0.1, pytest
  9.1.1, pytest-bdd 9.0.1) on CPython 3.12, the interpreter its kit names;
  `tests/test_demo.py` holds them, `harness.yml` runs the oracle on the
  reference rebuild (258 of 258).
- Local proof without any database: `KG_STORE=rdflib python harness/run.py
  --deterministic --out <dir>` in a venv with the pins, then
  `demo/tools/compare_deterministic.py <dir>` (`harness.yml` does this in CI).
  `demo/tools/check_saved_queries.py` runs every saved query the page lists through the
  store's `console_query` (the stack job does, after the comparator): they are console text
  nothing else executes, so a syntax error in one fails there and not in a viewer's Browser.
  Against Neo4j: a 5.26 community tarball started directly (Java 21), the same
  two commands without `KG_STORE`.

## Record and views

- `backlog/decisions/` is the decision record; `backlog/tasks/` the queue;
  `backlog/docs/` the briefs. Both are written through the `backlog` CLI,
  never by hand, so ids and metadata stay consistent. The maintainer's
  artifact pages quote them: they are views, never the record.
- pumllint's ROADMAP records what concerns pumllint (the move, its trigger);
  ieam-register's `decisions/` records the register's. One record per thing.
- The CargoQuote subject and the proof-of-concept record stay in pumllint and
  are vendored here at a tag with a SOURCE note and a digest test, as the
  register is. Never edit a vendored file or its note by hand.
- `.claude/` holds two fail-closed PreToolUse hooks on Edit, Write, MultiEdit and NotebookEdit
  (`.claude/hooks/protected_paths.py`, task-0105): `vendored` blocks a hand edit to a file or `SOURCE.md`
  under a vendor tool's destination, `backlog` blocks a `backlog/**/*.md` written other than by the CLI;
  both map through task-0099's `decide` and call nothing else, and the knowledge gate is not wired here.

## Pull requests

Every change goes through a pull request once CI exists; until then `main` is
fast-forwarded from the session branch on the owner's say-so. Open a PR, wait
for the whole matrix, merge on green, never on red or pending. The session that
opened a PR merges it itself once the whole matrix is green (a skipped `publish`
counts as green), without asking; a PR the brief says the parent session merges
is left to it.

GitHub auto-merge is on (2026-11-03): the ruleset on `main` requires `tests` and `rdflib`, not
`stack` (path-filtered, so a required `stack` would leave a PR pending forever) and not an
up-to-date branch. So: a PR whose diff touches `stack`'s paths (`demo/`, `harness/`, `subjects/`,
`tools/`, `demo.yml`) gets auto-merge only once `stack` is green on its head, or is merged by hand
then; any other PR gets auto-merge when it opens. A PR that must wait (a proposed decision, an
ordering) gets none. A `stack` red on `main` after a merge is fixed at once.

CI budget (task-0084): a pull request's `rdflib` and `stack` each within 12 minutes on an
uncontended runner; under parallel load the job may run longer, and the record is never subset to
meet it. On a pull
request the J-F round trip, MCP and lighthouse steps run the named subset `KG_JF_SCENARIOS=C,D3` (the kit as
committed and every layer consistently wrong); the full J-F set runs on every push to `main`,
nightly at 03:17 UTC and on a `workflow_dispatch` of `harness.yml` or `demo.yml`, so a red full run
on `main` is fixed like any other. The J-F record comparison and its oracle always run in full. In `harness.yml` CargoQuote's MCP
and lighthouse steps also take a pull-request subset, `KG_CQ_SCENARIOS=S1,S2,S6`; its comparator
and round trip, the scored record, never do.
`tests/test_ci_subset.py` holds the subset the same in both workflows and here.

Releases (decision-0003): SemVer, `VERSION` and `CHANGELOG.md` move together in a release PR
(a test holds them equal); a contract change raises the minor version while 0.x. Between releases,
a PR whose change an adopter would notice (a contract, a feature, a known limit) adds its line under
`CHANGELOG.md`'s `## Unreleased` as it merges, contract changes under their own heading; the release
PR renames that section to the version (maintainer, 2026-11-04; `tests/test_release.py` admits one
leading Unreleased, `release.yml` stays strict at tag time). A hosted
session cannot push a tag: the owner publishes the GitHub Release on the release PR's merge
commit, typing the tag as new, and the tag's `release.yml` publishes `ghcr.io/fdurieux/knowgov:<tag>`.
The session that prepares a release PR also hands the owner, in its reply, the Release's title and
Markdown description, ready to paste, as part of the release. The title is one line, `knowgov X.Y.Z — <what moved>`.
The description is in the adopter register (the README's reader, not this file's). It covers:
- what the release does, in one paragraph;
- a highlights list;
- the contract changes that set the version;
- the `docker pull` line for the image;
- a table of what it carries (pumllint, the register tag, the record's pins);
- the known limits;
- a link to the tag's `CHANGELOG.md`.
The description restates the changelog's top section and never adds a claim it lacks. A step that
waits on the published image, such as the compose pin's digest, is named as a follow-up after the
Release.

Two artifact pages are the maintainer's running view of pumllint, knowgov and ieam-register:
the queue, *Two roadmaps, one queue*
(https://claude.ai/code/artifact/a6e5007e-36f8-4a94-b3de-3ba2690512cc), and the reconciliation,
*Two loops against two roadmaps* (https://claude.ai/code/artifact/c3e39034-e727-430b-8170-8ca152ea9b80).
A merged PR refreshes both pages in the same turn, without being asked:
- in the queue's "done" column, the PR link with a one-line what-and-why, and every queue row
  whose state it changes (a decision answered, a task unblocked);
- in the reconciliation's Record, a line, when the merge bears on the loops or the seam.
The session that refreshes is the coordinating session, when one dispatches the work. Its
sub-sessions report their merges to it and never publish to the pages, so that two writers never
overwrite each other. With no coordinator, the session that merged refreshes. The backlog and the
decision records land first; the pages quote them and are views, never the record. A session that
cannot reach the pages says so and leaves the record as it is.

## Boundaries

- `pumllint/` imports nothing from here and reads no register; this repository
  consumes pumllint's reports and its parser as a released library, never the
  reverse.
- A client's instance is private, created inside the client's repositories,
  and never pushed here. No bank-related data, ever.
- The model endpoint is instance configuration (`KG_MODEL_BASE_URL`,
  `KG_MODEL_API_KEY_VAR`, `KG_ARMS_MODEL`; `harness/arms.py` `endpoint()`); the
  arms are off until the named key variable holds a value (task-0005).


<!-- BACKLOG.MD GUIDELINES START -->
<!-- backlog.md-instructions-version: 1.55.3 -->
<CRITICAL_INSTRUCTION>

## Backlog.md Workflow

This project uses Backlog.md for task and project management.

**At the beginning of each conversation in this project, run `backlog instructions overview` before answering or taking action. Re-read it only if you have not read it yet in the current conversation.**

Use the overview to decide whether to search, read, create, or update Backlog tasks.

Before task lifecycle actions, read the matching detailed guide:
- `backlog instructions task-creation` before creating or splitting tasks
- `backlog instructions task-execution` before planning, changing status or assignee, adding a plan or implementation notes, or implementing task work
- `backlog instructions task-finalization` before checking acceptance criteria, writing final summaries, or moving tasks to terminal statuses

Use `backlog <command> --help` before running unfamiliar commands. Help shows options, fields, and examples.

Do not edit Backlog task, draft, document, decision, or milestone markdown files directly. Use the `backlog` CLI so metadata, relationships, and history stay consistent.

</CRITICAL_INSTRUCTION>
<!-- BACKLOG.MD GUIDELINES END -->
