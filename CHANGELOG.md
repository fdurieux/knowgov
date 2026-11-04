# Changelog

One section per release, newest first. The version in `VERSION` is the top section's
(decision-0003). While the version is 0.x, a change to a contract raises the minor version: the
gate command's exit codes or flags, the JSON shapes under `harness/schemas/`, the instance layout,
the store port, the subject manifest format.

Between releases, changes merged to `main` gather under `## Unreleased` on top; the release PR
names that section with the version.

## Unreleased

### Contract changes (raise the minor version at the next release, decision-0003)

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

### Also since 0.3.0

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

### Known limits

- The GitLab include is proven by shell, not yet on a GitLab runner (task-0108).
- The hooks see Edit and Write, not a shell command writing the same file.

### Also since 0.3.0

- **The register is vendored at ieam-register `v0.2.7`** (task-0109): decision 0012's realiser walk
  and decision 0013's review months. CargoQuote's three `response|*` keys now lapse after six
  months; as of 2027-02-07, S1, S3 and S6 read QUALIFIED. The record (as of 2026-10-30) is
  unchanged.

### Also since 0.3.0

- **The MCP allowlist leaves the managed hook fragment** (task-0107): `instance/ci/claude/managed-settings.json` carries `allowManagedHooksOnly` and the hook only; `allowManagedMcpServersOnly` and `allowedMcpServers` move to `managed-mcp-allowlist.json`, an opt-in whose lists replace lower sources' and must be merged; the hook stays mandatory without it.

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
