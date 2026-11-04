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
  picks one, `neo4j` by default. No other module speaks Cypher; a test guards
  it (task-0003). `export_turtle`/`import_turtle` carry a store into a fresh one of either kind in the rdflib
  adapter's form; `tools/check_round_trip.py --chain` holds every scenario's gate reports and three-valued
  answers equal across the hops (rdflib in `harness.yml`, Neo4j to rdflib and back in the stack job; task-0070). The comparator compares D1, the Neo4j edition's constraint
  measurement, only between runs of the same store kind (task-0004). `demo/` the page, the vendored model, the vendored
  register, the comparator, the Docker files; `subjects/<id>/` a subject root
  (`subjects/README.md` documents the format): `subject.toml`, `scenarios.toml`,
  `plants.toml`, `queries.toml`, `register_map.toml`, `prompts/`, and under
  `vendor/` the bytes vendored from pumllint in its relative layout; `runs/`
  re-runs, gitignored. `instance/` an organisation's instance layout (`README.md`, adopter register;
  `kinds.toml`, one kind per row of the site's artefact table and the mappers that read it, every
  mapper in exactly one), checked by `tools/check_instance.py`, with a public example from
  `tools/example_instance.py` that CI mounts read-only and digests before and after (task-0006). Each kind's `lint`
  field is doc-0008 §5's tool and gate column; `tools/preload_check.py` lints an instance's documents
  with the ones that run here (pumllint; Spectral for api-contracts, task-0066; `--baseline` fails only on regression, task-0065), lists every other kind's files, and a kind whose linter is not installed, as unchecked, exits under the
  gate contract, JSON under `harness/schemas/preload-report.schema.json`; `instance/ci/` is the
  template an instance copies, its script proven in `harness.yml` (task-0045). Form, not knowledge. `harness/gate_cli.py`
  the gate as a command (exit 0/1/2, `--fail-on`, `--baseline record|FILE`, JSON pinned by
  `harness/schemas/gate-report.schema.json` through `harness/schema_check.py`; task-0007; version 2: stale statements and suspect derived outputs are findings, task-0048, shown after S6's change by `tools/check_gate_after_change.py`). `--as-of` (decision-0005, task-0068; `harness/cadence.py`): a review verification's `valid_until` is its date plus its key's review months from the register's `lifecycle.toml`, a lapse reads validated and is a `lapsed` finding; today by default, the deterministic run and the comparator as of the subject's `[record] as_of`; `run.py --as-of` and the page's run (`as_of`) name another date, and the page's gate box and panel name the date read and list each lapse with its day and months (task-0076). `harness/mcp_server.py` the gate and the three-valued answer as a read-only MCP server (stdio, or
  Streamable HTTP on 127.0.0.1 with `KG_MCP_TOKEN` for any wider bind; standard library; the store behind a
  view that lets the port's reads through and nothing else; `tools/check_mcp_server.py` holds its report equal
  to `gate_cli.py --no-load`'s on a live store; task-0056). `harness/trace.py`
  knowgov-trace (task-0051): `register` records built files as derived outputs (store and a JSON
  ledger, since a load wipes the store), `check` reports suspect, drift, missing, unmapped and the
  task's gate under the same exit contract, JSON pinned by `harness/schemas/trace-report.schema.json`;
  the APP comes from the instance's `code_map.toml` (`harness/code_map.py`, task-0050); S6 shown by
  `tools/check_trace_walkthrough.py`. `KG_SUBJECT` selects the root; nothing in `harness/` or
  `demo/` names a subject, a document or a scenario (task-0002). Two public
  subjects: `cargo_quote` (the proof of concept, seven scenarios, the scored
  record) and `jef_data_load` (the recreation experiment's kit, the degradation
  test's arms as scenarios, a deterministic record, the kit's own suite as oracle; task-0021).
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

Releases (decision-0003): SemVer, `VERSION` and `CHANGELOG.md` move together in a release PR
(a test holds them equal); a contract change raises the minor version while 0.x. A hosted
session cannot push a tag: the owner publishes the GitHub Release on the release PR's merge
commit, typing the tag as new, and the tag's `release.yml` publishes `ghcr.io/fdurieux/knowgov:<tag>`.

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
