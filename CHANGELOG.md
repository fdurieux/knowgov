# Changelog

One section per release, newest first. The version in `VERSION` is the top section's
(decision-0003). While the version is 0.x, a change to a contract raises the minor version: the
gate command's exit codes or flags, the JSON shapes under `harness/schemas/`, the instance layout,
the store port, the subject manifest format.

Between releases, changes merged to `main` gather under `## Unreleased` on top; the release PR
names that section with the version.

## Unreleased

### Contract changes
- **The gate report names the corpus it decided on, and `--baseline` names what differs** (task-0307, decision-0037).
  The report gains `corpus`, the sha256 over the loaded document Versions' digests (one `<artefact>\t<version>\t<sha256>`
  line each, sorted by artefact then version), equal on both stores and through export and import; it is additive,
  schema version 3 unchanged. Before, an in-place edit of a document left `task_profile`, `register` and `knowgov` as
  they were, so a retained report could not show that its corpus had changed. With `--baseline FILE` or `--baseline
  record`, each of `task_profile`, `register`, `knowgov`, `corpus` and `as_of` that differs from the baseline's is now
  named on stderr, one line each; the exit is unchanged. A field the baseline lacks or holds as null reads as unknown,
  never as different, and the record holds only its `as_of`. The record does not move.

- **The key rule refuses every control and format character** (task-0297, decision-0034 Amendment A1). A key's
  sides now hold only Basic Multilingual Plane characters outside Unicode categories Cc, Cf, Zs, Zl, Zp and Cs, and
  no `|`. `harness/key_rule.py` writes this as explicit `\uXXXX` ranges, with no `\s`, so ECMA-262 and Python read
  the `inputSchema` pattern alike. The bidi marks and overrides (U+200E, U+202E), the soft hyphen, U+2061, U+180E,
  NUL and U+001C to U+001F, U+0085 are refused, on the wire as -32602 and in `check_subject` as an error. Before,
  they passed and read absent at the gate, and a JavaScript client's `\s` let U+001C through. Combining marks are
  kept. Keys use characters up to U+FFFF only: one above it is refused by every engine alike (decision-0034). Every public key still matches, and the record
  does not move.

- **Two more settings are contracts, and the settings table reaches every one the code reads** (task-0294,
  decision-0034 choice 1). `KG_REGISTER_PREVIOUS`, which `demo/docker-compose.instance.yml` passes, and `KG_NOW`,
  the instant `KG_CLOCK=pinned` requires for the live-run read, are now contracts. `instance/README.md`'s table
  gains 30 rows, 105 in all and 65 of them contracts: besides those two, every setting a shipped compose file
  passes and every operator-facing knob (the worker's own limits, the servers' boundary limits, the agent ceilings,
  `KG_ARMS_EFFORT`, the demo's ports and folders, `KG_TRACEBACK`), each `no` with its reason.
  `tests/test_settings_table.py` now fails on any `KG_*` the code (`harness/`, `demo/app/`, `tools/`, `instance/`)
  reads or a compose file under `demo/` passes that has neither a row nor an entry, with its reason, on its
  internal list.
- **One rule for a knowledge key, `entity|attribute`** (task-0296, decision-0034 choice 3(a)). `harness/key_rule.py`
  holds it: each side of the `|` is non-empty, with no `|`, no whitespace and no format character (U+200B to U+200D,
  U+2060, U+FEFF). It is `tools/check_subject.py`'s `KEY_RE`, and the `pattern` of the `keys` items of `gate_verdict`
  and `evidence_bundle`. So `keys: ["nonsense"]` now answers -32602 on both transports and in both eras, where it
  used to read BLOCKED with the key absent. A key holding a zero-width space, which passed `check_subject` and read
  absent at the gate, is now a `key-syntax` error there and -32602 on the wire. Every key in the public subjects and
  the record already matches it.
- **A scenario id is `[A-Za-z0-9][A-Za-z0-9_-]{0,31}`, one per scenario** (task-0295, decision-0034 choice 2).
  Before, two scenarios with one id passed the check and the loader kept the last; `id = ""` and `id = "../x"`
  passed and reached the gate's report; and `run.py` wrote `<out>/../x`, outside its `--out`. Now a scenario with
  no id, a duplicate or an id outside the pattern is an error in `tools/check_subject.py` and the MCP
  `subject_check` (rule `scenario-id`, which the subject-check schema adds, version 1, additive). The subject's
  loader refuses it, so `gate_cli`, `run.py`, the MCP reader and the page exit 2 naming the id before they write
  anything. `[[scenario.sources]]` and stage-2 `derived` ids are not scenario ids. Every public id already
  matches, and the record does not move.
- **Every command that reads a register refuses a named one it cannot read** (task-0288, decision-0033 choice 5,
  after task-0279). `harness/run.py`, `harness/trace.py`, `harness/capture.py`, `harness/transcript.py` and
  `harness/step_grid.py` now exit 2 on a `KG_REGISTER` they cannot read, naming the path and what is missing,
  before they read or write anything (`-h` and `--help` still print the usage), and the page refuses to start. Before, `capture ingest` skipped the
  issued-handle check and wrote a capture the register would refuse, `capture due`, `trace check` and
  `run.py --deterministic` went on with exit 0 (`trace` read twelve review months without saying so), and the
  page started and answered `/api/register` with a 404 naming the path. `check_subject` now uses the same test
  as the other readers, the register's own `tools/register.py` included, so a folder with only
  `metamodel/types.toml` is exit 2, not exit 1 with every row's node unknown. An unnamed register reads as before,
  and the record does not move.
- **`KG_CLOCK` takes only `pinned`** (task-0287, decision-0033 choice 2, G9-17). It is read through
  `harness/switches.py`: `pinned`, exactly, refuses the wall clock; empty or unset reads it; any other value exits 2,
  naming the setting. Before, `Pinned`, `pinned ` or `1` silently read the wall clock. No on/off setting is trimmed of
  spaces any more, in Python as in `knowgov-gate.sh`, so `KG_NO_LOAD=' 1'` is refused in both. A misspelt
  `KG_LOAD_MEMORY_CHECK` now exits 2 naming the setting, not as "the store did not answer".
- **`held_keys`' `gate` is the task class's own verdict whatever the store holds** (task-0292, completing task-0283).
  On a store holding no key, minimal S0's, it was null where `gate_verdict` gives BLOCKED; it is now
  `gate_verdict`'s verdict and why there too. The held-keys schema's description no longer promises null; the type
  stays an object or null.
- **`gate_cli --baseline FILE` holds a deterministic.json to the run too** (task-0286, G9-17). A record file of
  another scenario, one outside this subject's own record tree (another subject's, or a copy), or one read under
  another task class or stage than its own (codegen, stage 1, unless the file names them) is refused with exit 2,
  naming the file and what differs. So is a file without the record's whole structure, such as a report with its
  `tool` removed and a `D6_gate` added. A baseline level the gate's ladder lacks, in a report or a record, is named
  the same way, never "the store did not answer". The record's own file for the same run reads as before. The
  record does not move.
- **`gate_cli --baseline FILE` keeps its promise: an earlier report of the same run** (task-0258, G9-17). A report
  baseline of another subject, scenario, task class or stage is refused with exit 2, naming the field and both
  values. So is one whose `schema_version` is above this command's, under decision-0023's rule. Each report is
  validated against the gate-report schema of its own version before it is compared; versions 1 and 2 are frozen
  beside the current one. A malformed baseline names the file and its first error, never "the store did not
  answer". `--baseline record` and a deterministic.json read as before, and the MCP reader still serves no report
  baseline. The record does not move.
- **`held_keys`' `gate` is the task class's own verdict** (task-0283, decision-0033 choice 9). It gated every held
  key under the class's bar as if each were required. On CargoQuote S1 it read "codegen BLOCKED: 34 of 93
  required keys (37%) are below verified" where `gate_verdict` codegen gives PROCEED. It now gives
  `gate_verdict`'s verdict and why for the same store, class and `as_of`, on the class's own required keys. The
  keys' levels are still the held key set's. The tool's description and the held-keys schema say what the
  field is. The record does not move.

- **A task class's name is `[a-z][a-z0-9_-]{0,31}`, and never `keys`** (task-0278, decision-0033 choice 4).
  `[tasks.keys]`, `[tasks.""]` and `[tasks."code gen"]` passed `check_subject` and `check_instance`. `keys` is
  the task a report on an agent-chosen key set names (doc-0014 C4). Now `harness/task_policy.py` refuses them,
  and so does everything built on it:
  - the checker, the instance check and the MCP `subject_check` report an error, rule `task-class`, which
    the subject-check schema adds (version 1, additive);
  - every command that loads the subject's task classes exits 2 naming the class.

  The public subjects' `codegen` and `design` are unchanged, and so is the record.

- **A register that is named and cannot be read exits 2, naming it** (task-0279, decision-0033 choice 5).
  `check_subject --register DIR` with a missing DIR, or a bad `KG_REGISTER`, gave an "unchecked" note and
  exit 0, so a typo dropped the register check. Now a register named by a flag or by `KG_REGISTER` stops
  these with exit 2, naming the path and what is missing, before a store is opened:
  - `check_subject`, `register_nodes`, `upward` and `proposal_impact` (and its `--register-branch`);
  - `gate_cli`, and its `--register-previous`;
  - the MCP reader, which now refuses to start.

  Before, `register_nodes`, `upward` and `proposal_impact` crashed with exit 1, and `gate_cli` reported the
  register as null with exit 0. "Unchecked" stays for `check_subject` when no register is named and the
  default cannot be read. The record does not move.
- **One table says which `KG_*` settings are contracts** (task-0275, decision-0033 choice 1, amending
  decision-0016 point 3). `instance/README.md`'s "The settings an instance may rely on" now has one row for each of
  the 75 settings it or `docs/security.md` names, with its group, what it does, its default, and whether it is a
  contract: 63 are, the settings an instance's CI, compose file or hook sets in order to run, decision-0027's twenty
  among them, and the clock (`KG_CLOCK`, `KG_TODAY`), which the guides advise in a pipeline; 12 are not (two demo
  ports, nine tuning knobs, and `KG_ALLOW_UNCONTAINED_EXECUTION`). The maintainer confirmed the rows (2026-11-09).
  A setting is a contract when the table marks it so; before, the section read as if only the twenty were.
  `tests/test_settings_table.py` fails on a setting either file names without a row, and on a row for one it does not.

- **The GitLab include and the pre-load workflow template run their own release by default** (task-0259, G9-17,
  decision-0032 C5). `instance/ci/gitlab/knowgov.gitlab-ci.yml`'s `KNOWGOV_REF` and `instance/ci/preload-check.yml`'s
  default to `v<VERSION>`, the tag they come from, instead of `main`, so an include taken from a tag no longer clones
  `main`'s harness at run time. To move to a later release, take that tag's include or template; the default
  follows. Against Neo4j, add the driver at `demo/Dockerfile`'s pin to the include's `KNOWGOV_PIP`. The GitHub
  action is unchanged: it already runs the knowgov tag named in `uses:`.
- **Every date is YYYY-MM-DD, and nothing looser** (task-0262, decision-0032, G9-17). One parse,
  `harness/dates.py`, now reads every date knowgov takes:
  - `--as-of` on `gate_cli`, `run`, `trace` and `proposal_impact`;
  - `KG_AS_OF` and the MCP readers' `as_of`;
  - `KG_TODAY`;
  - `capture due --on` and `connector --exported-on`;
  - the page's `POST /api/run` `as_of` and `GET /api/register?today=`.

  Before, Python's `date.fromisoformat` also read the ISO week form and the basic form, so `2026-W45-1` was
  read as 2026-11-02 and `20261105xx` as 2026-11-05, and the MCP runs reader's `\d` let fullwidth digits
  through. Such a value is now refused, naming it: exit 2 on a command, a tool error on MCP, 400 on the page.
  A stored date, such as a verification's `at` or `valid_until`, is read the same way, alone or followed by
  an ISO time. `record`, `today` and valid dates read as before, and the record does not move.

- **The subject-check report's `finding.rule` names three more rules** (task-0257, decision-0032, G9-17).
  `require-approved` and `rationale` (a malformed `[tasks.<class>]` field, task-0242) and `attestation` (an
  attestation with no day or no attester, task-0199) were emitted by `tools/check_subject.py` but missing from
  `harness/schemas/subject-check.schema.json`. A report carrying one failed its own schema, from the CLI's
  `--json` and from the MCP `subject_check`. Schema version 1, additive.

- **A suspect derived output blocks only the task classes whose keys it rests on** (task-0282, decision-0033
  choice 8). Before, any suspect output was a blocker in every class's gate: a register change that invalidated
  15 codegen statements made the `design` gate exit 1 on `derived:S1:G:run1`, though none of them sits on a design
  key. A suspect output now blocks a class's gate only when one of its invalidated or changed statements sits on
  that class's keys. Otherwise its `suspect_derived` finding is `info`, naming the output and the keys it rests on,
  and a `--baseline` does not count it as a regression. A statement whose key cannot be read counts as on the task.
  The codegen gate in that example still exits 1, and the scored record's gates are unchanged.
- **One reading of every on/off setting** (task-0276, decision-0033 choice 2, G9-17). `harness/switches.py` lists
  them and reads each one: a flag (`KG_NO_LOAD`, `KG_PUBLISH`, `KG_ALLOW_UNCONTAINED_EXECUTION`, `KG_TRACEBACK`,
  `KG_THINKING_UNCOUNTED`) is on with `1` and off with `0`, empty or unset; `KG_LOAD_MEMORY_CHECK` and `KG_KEY_CHECK`
  keep their word, `off` in any case. Any other value now exits 2, naming the setting and what it accepts; before,
  `KG_NO_LOAD=true` silently meant off. A behaviour change: `KG_LOAD_MEMORY_CHECK` or `KG_KEY_CHECK` set to `0`,
  `no` or `false`, spellings no document named, turned the check off before and now exit 2; set `off`. `instance/ci/knowgov-gate.sh`
  reads its flags under the same rule. The GitHub action's `publish`, `annotate` and `sarif` take `true` or `false`
  in any case, and any other value fails the step, naming the input. Every documented spelling keeps its meaning.
- **The image's tags, stated once** (task-0277, decision-0033 choice 3, G9-17). The contract is
  `ghcr.io/fdurieux/knowgov:vX.Y.Z` for a release (the tag, `v` included, as `release.yml` publishes it) and
  `:latest` for the last build of `main`. `:<short-sha>`, which `demo.yml` also publishes, is a build of `main`,
  not a contract. The README, `instance/README.md`'s contracts table and the demo's guide say so, and
  `tests/test_image_tags.py` holds them to both workflows.
- **The trace ledger and the proposal overlay carry a format version** (task-0280, decision-0033 choice 6), by
  decision-0023's rule in `harness/formats.py`. The ledger's `schema_version` is its format: missing reads as 1, and a
  newer one is refused by `trace check` and `trace register` (exit 2) and by `code_path` (exit 2 on `upward.py`, an
  error answer from the MCP server); until now a ledger at 99 was read. A proposal takes an optional top-level
  `format`, until now refused as an unknown field: missing reads as 1, a newer one is refused, exit 2 on the CLI and an
  error answer from the MCP `proposal_impact`. `instance/templates/proposal.toml` writes `format = 1`.
- **`register_impact` reports a key's findings as `gate_verdict` does, `intended` and `act` included** (task-0260,
  doc-0032 group 3 CB1). `register_impact` now takes the owned finding kinds from `gate_cli.OWNED`, one
  definition: key, intended, stale, lapsed and act. Before, a key whose review ruling no longer bound showed the
  act finding on `gate_verdict` and none on `register_impact`; the same gap reached `proposal_impact`'s keys and
  slices. `register-impact` schema, additive: a finding's `kind` admits `intended` and `act`, and it carries the
  gate report's `act` object. `tools/check_owned_findings.py` reproduces group 3's case and holds S1, S4 and S6
  equal key for key, on rdflib and Neo4j.
- **The `proposal-impact` schema names no coverage rule** (task-0261, doc-0032 group 3 CB2). `coverage.before`
  and `after` are keyed by the register's rule ids, each a coverage cell, and a new gap's `rule` is a rule id
  (`^C[0-9]+$`). So a register whose checker defines C5 yields a valid report, and every earlier report still
  validates. The schema validator gains `pattern` and `propertyNames`. The register view's output has no schema;
  its coverage reader already follows the checker's rules (task-0241).
- **A slice reads its task class's keys, and the class's keys on no slice are named** (task-0252, doc-0034 D1).
  `proposal_impact` (CLI `--task`, MCP `task`, `codegen` by default) now keeps each slice's keys to the
  `[tasks.<class>]` keys among the register-map rows on its thread. Before, every mapped key was read under
  the class's rule, so a `design` slice could block on a key `design` does not require. The slice's `keys`
  gains `task`, and `of` is the class's key count. The new `slices.task_keys` lists the class's keys on no
  slice, each with `mapped`, and with a scenario held its levels and gate; `in_slices + on_no_slice` is the
  denominator. On CargoQuote S2 under `design`, the slices block on `QuoteAPI|on_screening_outage` and
  `REQ-06|text` (absent, unmapped) sits in `task_keys`; under `codegen` the slices, verdicts and counts are
  unchanged. `register_impact` keeps its reach: every mapped key a change reaches. Schema additive.

- **`proposal_impact` and the register view read every coverage rule the register's checker defines** (task-0241;
  the maintainer, 2026-11-09). At ieam-register v0.2.13 these are C1 to C4, where C4 is the register's decision 0020:
  an approved process that realises an approved capability is supported by an approved application or module.
  - The rules come from the vendored `check_register.py`'s own `COVERAGE_RULES`, in its order, so a later
    register rule needs no knowgov code.
  - A proposal that breaks C4 now reports it under `coverage.new_gaps`, on its hypothetical element, as C1 to C3
    are reported.
  - The register view's coverage summary and lines name C4.
  - `proposal-impact` schema, version 1, additive: `coverage.before` and `after` name C4, and a new gap's `rule`
    may be `C4`. C1 to C3 stay the required keys, so a report on a register from before decision 0020 still
    validates.
  - `tools/fixtures/proposal_c4_gap.json` is the worked case, held by the tests and by
    `tools/check_proposal_branch.py` in branch mode. The vendored register is C4-clean, so nothing in the
    record moves.

- **The gate report names what it decided on: schema version 3** (task-0237, decision-0029; task-0103 AC #3,
  doc-0014 C9). `gate_cli.py -f json` and the MCP reader's `gate_verdict` now carry three required fields.
  - `task_profile`: the sha256 of the canonical JSON (sorted keys, no whitespace) of the subject's
    `[tasks.<class>]` table the gate read. With a key set asked for, the table carries those keys.
  - `register`: `{tag, commit, why}`. These come from the register's `SOURCE.md` when it is vendored, or
    from an instance checkout's own git `HEAD`, read without the network. Otherwise they are null, with
    the reason.
  - `knowgov`: the build that judged, `{version, commit, describe}`, as `store_status` reports it.

  A retained report, a `--baseline` file or the pre-push hook's, thus says which task profile, register and
  knowgov it judged by. `schema_version` is now 3. A version-2 report still reads as a `--baseline`. The
  scored record does not move: the deterministic comparator reads no gate report.

- **Twenty `KG_*` settings are contracts from 1.0** (task-0234, decision-0027, decision-0016 point 3).
  `instance/README.md`'s new section "The settings an instance may rely on" documents fourteen of them,
  each with what it does, its default and who sets it:
  - the CI-template and hook inputs: `KG_GATE`, `KG_TASK`, `KG_STAGE`, `KG_NO_LOAD`, `KG_CODE_REPO`,
    `KG_SUBJECT_IN` and `KG_HOME`;
  - the store: `KG_NEO4J_URI` and `KG_NEO4J_USER`;
  - `KG_SUBJECT_CALL_TIMEOUT`;
  - the model endpoint: `KG_ARMS_MODEL`, `KG_MODEL_API_KEY_VAR`, `KG_MODEL_API_KEY` and `KG_MODELS`.
  `docs/security.md` documents the worker's six limits: `KG_WORKER_CPUS`, `KG_WORKER_MEM`,
  `KG_WORKER_JOB_SECONDS`, `KG_WORKER_JOBS`, `KG_WORKER_WORK` and `KG_WORKERS`.
  None of them changes behaviour; each is now a promise. Nineteen other settings stay out of the contracts,
  and `tests/test_adopter_docs.py` holds both lists.

- **Format versions on an instance's inputs** (task-0174, decision-0023, doc-0028 G9-2). `subject.toml` carries
  `[format] version = 1`, covering its subject root's `scenarios.toml`, `plants.toml`, `queries.toml` and register
  map; `code_map.toml` and `connectors.toml` each a top-level `format = 1`; each capture and review file its own
  `format = 1`, stamped by `harness/capture.py` as it writes them. A file with no number reads as version 1, in
  every release (decision-0023 Amendment A1, task-0236); a file with a newer number is refused by every reader with exit 2, naming the file, its
  version and the one this knowgov reads. The public subjects, the wizard skill and `tools/example_instance.py`
  write the key; `check_subject.py`'s report (and the MCP `subject_check`'s) carries `format`, and
  `check_instance.py` lists it per subject. `capture.py` now exits through the one failure-to-run wrapper.
- **The MCP servers name the knowgov they run** (task-0231, additive). The reader's `store_status` and
  `knowgov-runs`' `run_options` carry `"knowgov": {"version", "commit", "describe"}`, the same values the
  page's `/api/subjects` gives (task-0227): knowgov's version, the commit, and how far it is past the
  release tag when that is known, each `null` when unknown. The server reads them once, at start. Both
  servers' `serverInfo.version`, in the `initialize` reply and in the stateless era's `_meta` stamp, is now
  knowgov's version (`0.8.0` today) instead of `"1"`. To see which knowgov you are using, ask your assistant
  to call `store_status`.
- **The page names the knowgov it runs** (task-0227). A chip in the header gives knowgov's version, the
  build's commit, and how far it is past the release tag when that is known: for example
  `knowgov 0.8.0 + 277 (7e113f0)` from a checkout build, or `knowgov 0.8.0 (v0.8.0)` from a release image.
  A part that cannot be known reads unknown. `GET /api/subjects` carries the same values as
  `"knowgov": {"version", "commit", "describe"}`, each `null` when unknown. The server reads them once, at
  start, from its own files: `VERSION`, a record the image build writes from two optional build arguments
  (`KG_BUILD_COMMIT`, `KG_BUILD_DESCRIBE`; `release.yml` passes the tag's commit and the tag), and `.git`.
  The image now keeps `.git`'s `HEAD`, `refs` and `packed-refs`, but none of its objects. So an image built
  from a checkout without `KG_BUILD_DESCRIBE` names its commit but not its distance from the release.
  `demo/README.md` shows how to compare the chip with `git describe --tags --always`. Additive, and listed
  here because decision-0016 point 3 makes the page's HTTP API a 1.0 contract.
- **The MCP servers refuse any argument outside a tool's input schema** (task-0200, doc-0030 M5; task-0281,
  decision-0033 choice 7(a)). Both servers, `knowgov` and `knowgov-runs`, keep every tool's `inputSchema`
  before anything runs, on stdio and HTTP and in both protocol eras. A call answers the JSON-RPC error
  -32602, naming the property, and runs nothing, when it:
  - names an argument the tool does not list (`additionalProperties: false`);
  - gives a value of the wrong type, outside an `enum`, not matching a `pattern`, below a `minimum` or
    with fewer items than `minItems`;
  - leaves out a `required` one;
  - passes `arguments` that are not an object (`[]` and `""` are no longer read as `{}`).

  A default applies only when the argument is absent. Before, a falsy value fell back to it:
  `gate_verdict {"scenario": ""}` answered for the held scenario past its guard, and `walk: ""` read as
  `dependants`. `gate_verdict {"senario": "S4"}` and `start_run`'s unknown arguments stay refused as
  task-0200 made them. The page's `POST /api/run` refuses a body key outside `scenario`, `mode`, `n`,
  `row`, `effort`, `as_of`, `by` and `subject` with 400, naming the key, so `as-of` no longer runs as of
  the record date in silence. `harness/schema_check.py` gains `pattern` and `minItems`.

- **Under `--baseline`, the gate's held findings are no longer annotated as errors** (task-0207,
  doc-0030 R8). With a baseline the gate exits on a regression only, yet `harness/annotate.py` marked
  every finding at the threshold an error, though the gate exited 0. Each finding of a report with a
  baseline now carries `held`: false for the regression's own findings (a key whose level fell, a derived
  output newly suspect, and with a worse verdict the task finding and every blocker), true for the rest.
  annotate shows a held finding as a warning at most, titled "held by the baseline". Additive and optional in
  `gate-report.schema.json`: not required, absent without `--baseline`.
- **An attestation is bound to the Versions it attests** (task-0221, decision-0019; decision-0009 option (c)).
  Before, `[verification] authored` and `approval` attested whatever the documents held at each load, so an edit
  made after the attestation inherited it.
  - **The subject format.** Each declaration may list, in `versions`, the digest of every artefact Version it
    attests: a file's raw-byte SHA-256 (task-0160) and, for a directory, each of its files' (task-0094; a directory
    is attested when every file is listed). `authored = { at = "...", scope = "...", versions = ["<sha256>", ...] }`.
  - **An unlisted Version is not attested.** Its authored statements read `proposed`, and none of its statements is
    approved by construction. A test's verification of it still counts.
  - **The gate names it.** A new finding kind, `attestation`: each artefact Version a bound declaration does not
    attest, behind the task's keys, at `major`, with the keys' owner and a route (the attester lists its digest, or
    the owner's questionnaire, `capture.routing`). New port write and read `record_attestation` and `attestations`
    (in `store.READS`), on both adapters and through the Turtle round trip; `verify_authored` and `approve_verified`
    take the attested artefacts.
  - **Read rule for declarations written before this change.** A declaration with no `versions` attests per load,
    as decision-0009 (a) has it. The gate lists it at `info` (`attestation`, not bound), and `tools/check_subject.py`
    notes it, naming decision-0019.
  - **The public subjects list their Versions** (the maintainer's approval, 2026-11-08). `cargo_quote` and
    `jef_data_load` list every Version their scenarios load, as vendored at pumllint v0.35.0 and each planted
    text, so no scenario's attestation changes and the scored record is unchanged. CI's subject check fails
    again on any note, so a fall back to the read rule is caught.
  - `tools/check_subject.py` refuses a listed digest that is no Version of the subject (its files, and the texts
    its plants make of them). `tools/check_attestation_binding.py` proves it on both stores.
- **Conflict gap ids name their two statements** (task-0223, decision-0020, doc-0030 S2). A conflict
  between two documents is now `gap:conflict:<key>:<a>~<b>`, by its two assertion ids sorted, the form a
  conflict with a person's statement already had; the positional `gap:conflict:<key>:<n>` is gone. One
  conflict therefore has one id on rdflib and on Neo4j (the default gate's scratch store and the page's
  store no longer disagree), and a new conflict on a key no longer renames the others. `conflict_gaps`
  answers ordered by id, `candidate_pairs` by key then id, on both adapters. The gate report's
  `conflicts`, its text and the arms' bundle carry the new ids. A record written before keeps its
  `:<n>` ids; `compare_deterministic.py` reads both forms as one per key, so the scored record still
  compares equal.
- **The worker attests `write_confined` only from Landlock ABI 3, and `run.py` takes stage 2's derived input
  explicitly** (task-0203, doc-0030 F8: R10, R3). Two contract changes, and a raised platform floor.
  - **The attestation.** The worker's attestation gains `landlock_abi`, the kernel's Landlock version.
    `write_confined` is now true only at ABI 3 or later, Linux 6.2, the first version where Landlock also
    stops a job truncating a file it may only read. Below that, the worker refuses to serve. The page's
    worker chip names the ABI found and the 3 needed.
  - **Known limit: Arms now need Linux 6.2 or later**, where they needed 5.13. On a kernel between the two the
    worker refuses to serve, the page's worker chip reads *Landlock ABI N, 3 needed*, and every Arms run is
    refused; Replay and Deterministic are unaffected.
  - **`harness/run.py --stage2-derived FILE`** names stage 2's derived output, the code an earlier scenario
    built. By default it is the file this invocation wrote, or, under `--resume`, its earlier attempt's.
    It is never a file left in a reused `--out` folder. A deterministic run in a fresh folder is unchanged.
- **A task class may require approved: the intended bar** (task-0215, decision-0018 point 4). A contract
  change to the subject format and the gate report, opt-in.
  - **The field.** `require_approved = true` under `[tasks.<class>]`.
  - **What it does.** A key that reads `verified` but not `approved` then sits below the class's bar.
    That is a behaviour shown to hold, perhaps by execution on the original, that no person has yet
    intended.
  - **The finding.** Each such key gets an `intended` finding, major, naming its owner and route from
    `capture.routing`. The report's `keys` counts them as `unintended`, and `store_status` shows the
    field.
  - **The verdict.** It counts these keys as the class counts a key below verified: QUALIFIED, or
    BLOCKED past `max_unverified_share`. PROCEED then needs every key approved.
  - **Without the field, nothing changes.** Every class reads as before, and the scored record is
    unchanged: no public class declares it. `tools/check_subject.py` refuses a value that is not true
    or false.

- **Each pre-load finding on a loaded document is a gap with an owner and a route** (task-0216, decision-0018
  point 5). A contract change to the store, the gate report, the review file and the pre-load report.
  - **The gap.** The load keeps every finding the pre-load report gave a version's exact bytes as a `LintGap`
    (port write `record_lint_gap`, read `lint_gaps`). Its id is the finding's own, never the store's order. A
    finding the baseline holds is kept, marked `held`.
  - **The finding.** The gate lists the lint gaps on the documents behind the task's keys as findings of kind
    `lint`. The severity is the linter's, at most major. It is info when held or resolved as a choice or an
    exception.
  - **Owner and route.** Each names the document's owner and route from `capture.routing`, over the keys
    behind it. When several units own those keys, it names each one's route.
  - **A key's level never moves for a lint gap.** It is the document's form, not the knowledge, so every
    verdict reads as before. task-0064's info listing stays.
  - **Resolutions.** A review's new `[[resolves]]` (`choice`, `exception`, `open`) is bound to the finding's
    text by digest. Only the document's owners may make it, under the role `closes`. A slip is a new version.
  - **The delta.** `tools/preload_check.py --previous REPORT` reports what a re-lint changed, at the same tool
    versions only: new, gone (a slip when the bytes changed) and kept.
  - **Proof.** `tools/check_lint_gaps.py` proves it on the example instance, on rdflib and on Neo4j.

- **A kit statement says what it is: the claim** (task-0214, decision-0018 point 3, doc-0032 §3). A change to the
  kit format the five bundle mappers read, and an additive rule in the subject check's report.
  - **The field.** A statement may carry `claim`: `observed` (what the pinned original does), `inferred` (a
    proposed explanation or generalised rule) or `intended` (accepted by the responsible authority). They load
    as `extracted`, `inferred` and `authored`. `requirements_json` reads an item's `"claim"`, `contracts_markdown`
    a part's `Claim:` line, `dmn_decisions` `claim:` in a decision's or rule's description, `gherkin_tagged` an
    `@claim:` tag on the Feature, a Rule or a Scenario, and `plantuml_realises` a `' claim:` comment line
    (`subjects/README.md`, "The claim"; `instance/mappers.toml`).
  - **Inferred stays proposed.** Nothing verifies it, a ruling may never approve it (task-0199 I4), and a
    `verified_by` link claimed inferred derives no execution, so it raises no other statement either. An
    assertion resting on statements of different claims takes the most conservative.
  - **No claim, no change.** A statement without one loads as before, so the public kits and the scored record
    do not move.
  - **Refused when unknown.** `tools/check_subject.py` refuses an unknown claim under a new rule, `claim`
    (`harness/schemas/subject-check.schema.json`, additive), and the load fails on it rather than guess.
  - The SHACL shape for an inferred assertion accepts one that rests on the kit fragment stating it, beside one
    linked to the gap it proposes to fill.
  - `tools/fixtures/claim_probe` carries every mapping. `tools/check_claim_probe.py` proves it on both stores, in
    `harness.yml` and the stack.

- **Step 4's checks in the pre-load check** (task-0217, decision-0018 point 1). A contract change to the
  pre-load report, additive.
  - **The checks.** After each kind's linter, `tools/preload_check.py` runs three checks across documents:
    - pumllint's `trace` with `--features`, over diagrams, feature files and requirements;
    - a glossary check: a term in three requirements with no glossary row;
    - a DMN check: gaps, overlaps under `UNIQUE` or `ANY`, and untyped outputs.
  - **The report.** Each finding names its check as `tool`, and a new `checks` block says whether each one
    ran. A document no linter of its kind read, but a check did, is judged by that check alone.
  - **Through the load.** Each finding reaches the load as a lint gap, routed as task-0216 routes them.
  - **The trace needs pumllint 0.35.0 or later**, the harness's pin since task-0224, and the instance's
    requirement-id pattern. Without either, it is listed as unchecked, naming what is missing.
  - **The example instance.** The DMN check finds two minor gaps in its screening table, at 41 to 42 and
    66 to 67 on a `number` input. A lint finding never lowers a key's level, so every verdict reads as
    before.
  - **Found, not fixed.** The two DMN gaps are reported as found. The example is built from CargoQuote's
    vendored kit, which is never edited by hand.
  - **Proof.** `tools/check_preload_linters.py` proves each check on its planted defect, the trace on the
    pinned pumllint.

- **One definition per concept** (task-0201, doc-0030 F5: G3, M4, G8, S4; S2 for `declared_gaps_for_key`). A fix,
  with one additive field.
  - **One successor set (G3).** The gate's level drops an invalidated statement only when its own verified or
    approved successor supersedes it (`superseded_by`), which is how the stale finding, the report's
    `superseded_by` and the bundle already read it. Before, any settled statement on the key dropped it, so the
    gate could read PROCEED beside a major stale finding with no successor. A key whose statement a change
    invalidated with nothing to replace it now reads `invalidated`, on every reader. The scored record is
    unchanged.
  - **A disputed key is not unknown (M4).** `three_valued_answer` and the record's D5 read disputed statements.
    When some are disputed, the answer stays `asserted` or `documented_absent`, and a new field, `disputed`,
    names them, with a `why`. It is additive: present only when a statement is disputed
    (`harness/schemas/three-valued-answer.schema.json`).
  - **One owner and route (G8).** `capture.routing` is the one place a key's answering units and questionnaire
    files come from: the gate's findings, the questionnaires and a register change's resting keys all read it.
    A key with several answering units now routes to each unit's questionnaire, the ones `capture.py
    questionnaire` writes it into, never to an `-unassigned` file nobody writes.
  - **One uniqueness rule (S4).** `store.UNIQUE_IDS` names the labels whose ids are unique. The Neo4j adapter now
    refuses a duplicate `Derived` or `Activity` id at create, as rdflib does, so `export_turtle` never meets one.
    Its constraint list, the record's D1, is unchanged.
  - **`declared_gaps_for_key` answers by id on both adapters (S2's part).** `candidate_pairs` and `conflict_gaps`
    keep the store's order, and so the record's conflict gap ids, until task-0202's decision.
  - `tools/check_one_definition.py` proves it on both stores, in `harness.yml` and the stack.
- **A person's act binds to what it ruled on** (task-0199, doc-0030 F2: H5, I4, I9; doc-0032 §6 items 7 and 8).
  Before, a ruling named only a statement's id, so after an edit the same id carried a new value and still read
  approved; a vanished id refused the whole review on stderr only.
  - **The review file.** `capture.py review` now writes each `[[ruling]]` with the statement's `key`, `value`
    and `sha256`, the digest of its supporting fragments' digests (`review.content_digest`), and each
    `[[closes]]` with the `sha256` of the gap's declaration.
  - **Every load binds each act by content.** A ruling lands on the statement of its key holding its value
    and digest: the one it names, or else the one statement that does, so a reordered table or renumbered
    answers move no act onto another statement. A ruling whose statement changed or vanished is not applied,
    and the rest of its file is. Stage 2 binds the rulings again after the re-extraction, so a ruling is never
    moved onto a successor.
  - **The gate reports each act it did not apply.** The new finding kind is `act`, with an `act` object: the
    file, the act, its author's handle, the value and digest it ruled on, and what the store holds instead.
    Its severity is `major` when the statement changed, vanished or is ambiguous, and `info` for a file refused
    whole or read under the rule below. On a key, it names the owner and the route, as `key` findings do. A
    new port write and read, `record_act_finding` and `act_findings` (in `store.READS`), hold these acts on both
    adapters and through the Turtle round trip.
  - **Read rule for review files written before this change.** A `[[ruling]]` with no `key`, `value` or `sha256`,
    or a `[[closes]]` with no `sha256`, binds by id, as before. It is applied, and the gate lists it at `info` as
    bound by id only. A new review binds it to content. No file is rewritten.
  - **I4.** A ruling other than `rejected` or `referred` on a statement of basis `inferred`, `assumed` or
    `hypothesised` is refused.
  - **I9.** `[verification] authored`, `approval` and `review`, and a stage-2 re-verification, need their own
    `at` and an attester (`[provenance] human` id). `tools/check_subject.py` refuses each without (rule
    `attestation`). The load no longer dates an undated attestation by its own day, and no longer defaults the
    attester: it applies neither, and says so on stderr.
  - `tools/check_act_binding.py` proves it on both stores, in `harness.yml` and the stack.
- **A derived output binds to what it was built on, and one rule reads it suspect** (task-0199, doc-0030 F2:
  H6, R5; doc-0032 §6 item 6). Before, trace's ledger kept statement ids only. A reload re-mints the same id
  for a new value, so code built on the old value read unchanged. The gate also read *suspect* from a flag
  stored at invalidation, while trace read it from the statements' statuses, so one store could give two
  answers.
  - **The ledger.** `trace.py register` writes each entry's `used`: every statement the output was built on,
    with its `id`, `key`, `value` and `sha256`, the content digest of its fragments (`store.content_digest`).
    The store keeps that list on the derived output (`register_derived(..., recorded)`).
  - **One rule, `store.suspicion`.** A derived output is suspect when a statement it used is invalidated.
    Where its registration recorded what it used, it is also suspect when the statement of that id now holds
    another value or digest, or is gone. The port's reads `suspect_derived`, `all_derived` and
    `derived_outputs` all answer by it, and no stored flag decides. So the gate, the MCP reader and
    `trace.py check` read one answer. A suspect row names the changed statements in `used_changed`, present
    only when there are some (the gate's suspect finding, `derived_outputs` and trace's `registered` rows).
    `trace.py check`'s blocker names each statement's old and new value.
  - **Read rule for ledgers written before this change.** An entry with no `used` reads by status, as
    before. `trace.py check` lists it in a new finding, `unbound`, at info. Registering the file again
    binds it.
  - `tools/check_ledger_binding.py` proves it on both stores, in `harness.yml` and the stack.
- **The store records whose load it holds, and no subject answers from another's** (task-0195, doc-0030
  F1, H1 and S5; decision-0013 A1). Before, the store named only the held scenario, so two subjects
  sharing a scenario id answered each other's gates.
  - **The load records its subject.** The extraction activity now records the subject and the scenario it
    loads. Its id stays `act:extract:<scenario>:<version>`, as the record's run files name it, and the
    Turtle round trip carries both.
  - **One port read, `held()`,** returns the subject, the scenario, each artefact's current version and
    the time of the load. The version comes from the artefacts' current versions, no longer from the
    order of the load activities, so a stage-2 change reads as current whatever its tag.
  - **What refuses.** With one subject's load held, another subject's readers refuse it:
    - `gate_cli --no-load` exits 2, naming the subject whose load is held;
    - every store-backed tool of the MCP reader refuses, and `store_status` reports the held scenario
      as another subject's;
    - `proposal_impact` refuses;
    - the page shows the load as its subject's, and serves the other subject no gaps.
  - **A store loaded before this change** recorded no subject. It reads as unknown and is refused to
    every subject, except an instance's only subject when that subject declares the held scenario.
    Reload the scenario to read it.
  - `tools/check_held_subject.py` proves it on both stores, in `harness.yml` and the stack.
- **`harness/step_grid.py`: a grid of steps by scenarios over deterministic run folders** (task-0192,
  doc-0024 J3). A new command and schema, `harness/schemas/step-grid.schema.json`. Additive.
  - **The input.** One or more `run.py --deterministic` folders, or `--record`.
  - **The rows.** The journey steps of `proposal_impact`'s scoped slices (task-0191, `--scope`; by
    default every approved journey on which a step lands a key).
  - **The columns.** The scenarios the folders hold.
  - **Each cell.** The step's keys as that scenario's gate report in the folder has them, never
    recomputed:
    - levels by count, the keys unread, the lowest level, unknown and gaps;
    - the gate's findings on those keys: blocked, below verified, flagged, stale statements,
      suspect derived outputs, lapsed;
    - for S6, the findings of its two later gates.
  - **Conflicts** are counted per column, never keyed by gap id.
  - **The keys on no step** are listed with their nodes, through `key_nodes`.
  - **It never opens a store and never calls knowgov-runs.** A sweep through `start_run` would replace
    what every viewer of the page reads. Facts only, never a score.

- **`proposal_impact` reads a named journey or product on the approved register, with each slice's
  keys** (task-0191, doc-0024 J1). Additive.
  - **The scope.** A new `scope`, on the MCP tool and as `--scope ID` on the command, names an
    approved journey, step, touchpoint or product. The slices are then that scope's own, and with no
    proposal the approved register is read alone. Before, an overlay that added nothing was refused.
  - **The walk.** The slices still come from the register's own `THREAD` walk and its rule A1. knowgov
    adds no walker.
  - **Each slice's keys.** `keys` holds:
    - the register-map rows `register_impact.landed_rows` gives for the slice's nodes, with the
      subject's key count as the denominator;
    - with a scenario held, each row's level as `with_levels` reads it, and the gate over the
      slice's keys;
    - the keys behind an edge the thread does not follow.
  - **The cells.** Counts per level, the keys unread, the lowest level, unknown (the keys at
    `absent`), gaps, lapses. `handoffs` lists the thread's owner changes. Facts only, never a score.
  - On CargoQuote, JRN-0002 lands 22 of 36 keys. On J-F, JRN-0006, JRN-0007 and JRN-0009 land 65,
    66 and 100 of 163.
  - `proposal` is no longer required on the MCP tool, but a call with neither a proposal nor a scope
    is refused. The schema grows additively: `slices.scope`, and per slice `handoffs` and `keys`.

- **The gate command leaves the shared store alone unless asked to publish** (decision-0017, task-0184).
  Before, `harness/gate_cli.py` wiped the store `KG_STORE` names and loaded its scenario into it. On a stack
  that is the Neo4j the page, the runs and the MCP servers read, and the adopter docs told people to run the
  command there.
  - **The default.** The command loads into a private in-memory store of its own (`store.scratch_store`, as
    task-0183's capture commands do), answers from it, and publishes nothing. The verdict, findings, levels
    and exit code are those of the loading command before. The report's `store` names the adapter it computed
    on (`rdflib`), and a new optional field, `published`, reads `false`. Without rdflib it exits 2 and names
    the install.
  - **`--publish`** keeps the old behaviour: load into the configured store, publish once the report is made,
    with the Neo4j load-memory forecast (task-0176). `published` reads `true`. `--publish --no-load` exits 2.
    `--stage 2` and `--register-previous` act on whichever store the load went to.
  - **Pipelines.** A pipeline whose later step reads the store (`trace-check` or `trace-register` after `gate`)
    sets `KG_PUBLISH=1` on the gate step: the action's input `publish: "true"`, the GitLab include's variable
    `KG_PUBLISH`. One that runs only the gate, and the Claude Code hook, need nothing.

- **A Neo4j load that would not fit the server's transaction memory is refused before it starts**
  (task-0176). Before, such a load failed inside its transaction.
  - **The refusal.** The load forecasts its peak transaction memory from the statements it writes and
    those its wipe deletes, and compares it with the smallest of `db.memory.transaction.max`,
    `db.memory.transaction.total.max` and `dbms.memory.transaction.total.max` (70% of the heap by
    default). Over the limit, it refuses before writing anything: `gate_cli` and `harness/run.py` exit
    2, naming the setting and both figures, and the store keeps what it held. `run.py` checks its whole
    run before the first load and the first model call.
  - **The forecast.** Measured on both public subjects and a synthetic scale-up to 48,288 statements
    (`docs/load-memory.json`, `tools/measure_load_memory.py`): about 9.4 KiB a statement written or
    deleted, raised to cover every measured peak, plus `KG_LOAD_MEMORY_MARGIN` (default 25%).
  - **The escape.** `KG_LOAD_MEMORY_CHECK=off` loads anyway, and a unit that does not fit then fails
    inside its transaction as before.
  - **Sizing.** `instance/README.md` ("Sizing the Neo4j heap") states the heap an instance needs as a
    function of its statement count, and `python harness/load_memory.py` prints a subject's.
  - **Known limit.** The forecast is measured on Neo4j 5.26 Community. It over-reads a run of several
    scenarios by up to about two times, and the off switch is the answer when it refuses a load that
    would fit. No record result moves.
- **Both servers cap a response's size** (task-0177). This lifts the 0.7.0 and 0.8.0 known limit
  "Response sizes are not capped".
  - **The page:** a response over `KG_PAGE_MAX_RESPONSE` bytes (default 8 MiB) is refused with a 500
    and a JSON error that names the setting, its limit and the response's size.
  - **The MCP reader and knowgov-runs:** a `tools/call` result over `KG_MCP_MAX_RESPONSE` (default
    16 MiB), on stdio or HTTP, is an error result that names the setting, with no
    `structuredContent`.
  - **Nothing is truncated.** Each default is about twenty times the largest response measured on
    both public subjects: 392 KB for the page (`/api/results/S6`) and 653 KB for MCP
    (`evidence_bundle` on J-F D4). A cap outside 4 KiB to 1 GiB, or one that is not an integer, is
    refused with the variable's name, and the MCP servers then exit 2 at start.

- **A file document's Version digest is over its raw bytes** (task-0160). The SHA-256 a Version
  records for a file artefact is now taken over the file's bytes on disk, as the register's digest of
  a cited file is. Before, it was taken over the text as read, which turns CRLF line ends into LF, so register-cites
  read an unchanged CRLF file as "differs". A planted text, which has no file, and a directory
  artefact's bundle keep their text's digest. The public subjects' files are all LF, so no recorded
  digest moves. 0.8.0's known limit on this is lifted.
- **One reader for every subject, by id** (task-0157, decision-0013 with amendment A1). Every tool of
  the MCP reader and of `knowgov-runs` takes an optional `subject`: the id of a subject under
  `KG_SUBJECTS`, never a path. A path, an unknown id or an id outside `KG_SUBJECTS` is refused. A
  call that names none answers exactly as before. Additive: existing clients see no change.
  - **`list_subjects`** names every subject, the default (`KG_SUBJECT`), the scenario the store holds
    for each, or none, and which tools are store-backed and which read files only.
  - **Store-backed or files-only.** Each tool says which it is in `_meta` (`io.knowgov/storeBacked`).
    A store-backed tool for a subject whose scenario the store does not hold refuses, naming the
    held subject and scenario and the `start_run` that would load the one asked about. The reader
    never loads.
  - **How.** A call naming another subject is answered by a child process with that subject's
    `KG_SUBJECT` and the server's date, equal to what a reader started on that subject answers;
    `tools/check_mcp_server.py` holds this over stdio and HTTP. About 0.4 s a call on Neo4j
    (p95 0.51 s); `KG_SUBJECT_CALL_TIMEOUT` bounds it (300 s).
  - **Onboarding.** The skill and `instance/README.md` no longer relaunch the servers per subject.

### Changes
- **The CI templates read paths and settings one way, and refuse what they cannot follow** (task-0267; security,
  fail-open).
  - **Changed paths.** `instance/ci/knowgov-gate.sh`'s changed-code list, shared by the GitLab include and the
    GitHub action, split `git diff --name-only` on whitespace, and git quoted non-ASCII names. So a merge request
    adding `módulo.py` read "no code changed" (exit 0), and one adding `new module.py` checked `module.py`.
    - Git's path lists are now read NUL-separated and unquoted (`-z`, `core.quotepath=off`). The Python helper
      quotes each path into the argv, and globbing is off, so a space, a glob character or a non-ASCII name is
      that name.
    - The same holds for the Claude Code hook's staged and worktree paths and for `proposal_impact`'s branch mode.
    - `KG_FILES` stays whitespace-separated, never globbed.
  - **`KG_ANNOTATE`.** An empty element, an unknown format or a format with an empty file now exits 2 before the
    core command, naming the setting and its four formats. A file the annotator cannot write stays a warning
    beside the command's exit, without a traceback.
  - **`KG_BASE`.** A base starting with `-` is refused with exit 2. `--end-of-options` goes before every base
    git reads, so `--output=FILE` writes nothing.
  - **`proposal-impact.sh`.** A register branch that adds nothing now exits 0, with a report whose `not_read`
    names what the branch changes.
  - **`preload_check`.**
    - An absolute `--changed` path and one escaping by `..` are now the same refusal, exit 2, naming the path.
    - A directory with no `subjects/` is refused as not an instance.
    - A linter named by `KG_SPECTRAL`, `KG_MARKDOWNLINT`, `KG_GPLINT`, `KG_BPMNLINT` or `KG_DMNLINT` that is not
      an executable file exits 2, naming the setting.
    - `preload-check.sh` takes an absolute `KG_PRELOAD_BASELINE` as given.
- **`subject_check` can no longer alias the register map onto the manifest** (task-0289, decision-0032 point 5). A
  proposed `[register] map = "subject.toml"` (or `scenarios.toml`, `plants.toml`, or a document's path) wrote the
  `register_map_toml` text over that file after the manifest's paths had been confined, so the manifest that landed could
  name server files the yield read. The map's path now joins the call's files, compared normalised, and the loader's own
  files are reserved, passed or not; the text that lands at `subject.toml` is the one confined; and a file that another
  path needs as a folder (`a` beside `a/b`) is refused by name in either order, no longer `FileExistsError`.
- **Numeric settings and tokens are checked at start** (task-0264, decision-0032 group 1 F13 and group 2 F7 to F9;
  a fix, no contract moves). `harness/settings.py` reads every numeric setting, which must parse as its kind, be
  finite and lie within its bounds. Anything else stops `mcp_server`, `mcp_runs`, the page and the worker at
  start with exit 2 and a line naming the setting, not a traceback or a silent default. This covers:
  - `KG_SUBJECT_CALL_TIMEOUT`, `KG_RDFLIB_LOCK_TIMEOUT` and `KG_WORKER_JOB_SECONDS`;
  - the worker's limits;
  - `KG_MCP_PORT`, `KG_DEMO_PORT` and `--port`;
  - each transport's `*_MAX_BODY`, `*_READ_TIMEOUT`, `*_IDLE_TIMEOUT` and `*_MAX_CONNECTIONS`;
  - the port in `KG_NEO4J_URI`.

  Before, `nan` gave a call no timeout, `inf` disabled the absolute read deadline, and `KG_MCP_PORT=abc` crashed
  the server. A `KG_MCP_TOKEN` or `KG_PAGE_TOKEN` that is blank once stripped now reads as unset. So a wide bind
  refuses, and a page published beyond this machine refuses writes. The defaults are unchanged.
- **The servers survive deep nesting and answer JSON-RPC's protocol edge cases** (task-0272, decision-0032 group 2
  F6, F11, F12; fixes, no contract moves).
  - **Deep nesting.** A request nested past the parser's depth is now a parse error, not a `RecursionError`: -32700 on
    both MCP servers (`knowgov`, `knowgov-runs`) and both transports, 400 on the page. The stdio loop answers the next
    request.
  - **Protocol edges.** An `id` that is not a string, a whole number or null is -32600. A `_meta` protocol version that
    is not a string is -32602, rather than being read as the handshake era. Invalid UTF-8 in an HTTP body is -32700,
    not a "replace" decode. The Bearer scheme is compared without regard to case on both servers and the page
    (RFC 7235).
  - **Content edges.** The page's startup line names the store in use (rdflib and its file under `KG_STORE=rdflib`).
    `add_artefact`'s `file` refuses control characters, a backslash, `~`, absolute paths and `..`, as `subject_check`
    confines a manifest's paths.
- **The two Claude Code hooks fail closed on every form they cannot read** (task-0268, decision-0032 F11, F12).
  `knowgov_hook.py` reads a push in backticks, through an alias (inline `-c alias.X=push` or configured) and behind a
  variable (`git${IFS}push`, `x=git; $x push`, failing closed); refuses a non-string `tool_name` or command, a
  repeated `--task-for` stage and a `--timeout` that is not a finite number above 0; resolves `--knowgov` and
  `KG_HOME` to absolute paths. `attestation_paths.py` reads NotebookEdit like every other write tool and compares
  names case-folded, so `Register/`, `Captures/` and `Preload-Baseline.json` are guarded on macOS. Settings unchanged.
- **A Neo4j read never answers a generation before its data has arrived** (SNAP-11, task-0274; decision-0014, amendment
  A1, accepted 2026-11-09). Under racing writers, a reader could pin a newly published generation while Neo4j was still
  applying the writer's commit, and read it with records missing: CI's SNAP-04 saw S2's counts with no
  extraction activity. Neo4j had shown the publication's `end`, written in the same transaction, before the
  transaction's last records. `end` is now set in a transaction of its own once the unit's commit has returned,
  so readers wait until the data is all there. Every open gap is closed forward (`end = begin`): a writer killed
  between its commit and that step is refused while its lease is live, then recovered and read whole. No shape
  changes; the guarantee decision-0014 documents now holds.
- **Prioritisation inputs and refinement planning, and a proposal template** (task-0253, task-0255, doc-0034). `instance/README.md`
  gains "Feeding your prioritisation, and planning refinement": the facts knowgov gives a team's own method (WSJF, cost
  of delay, RICE), with the command that yields each, what it does not supply, and how to turn each slice's keys below
  the bar into refinement items by level. `instance/templates/proposal.toml` is an annotated template of every field
  `harness/proposal_impact.py` reads, pointed to from `demo/README.md`; `tests/test_proposal_template.py` holds it to the reader.
- **No `.env` file reaches the image** (security; task-0245, doc-0033 R4). `demo/Dockerfile.dockerignore` now
  leaves out every `.env` and `.env.*`, at the root and in any folder. Only a values-free `.env.example` is let
  back in. Compose still reads a `.env` beside the compose file to fill in its variables. The compose file's
  comment and `docs/security.md` say both, and `tests/test_demo.py` holds the rule.

- **Four small corrections** (task-0246, doc-0033). None changes behaviour.
  - `tests/test_page_subject.py` pins the `KG_PAGE_LISTEN` its POST checks depend on, so it passes whether the
    variable is unset or `0.0.0.0`.
  - The page loses a dead line.
  - `harness/annotate.py`'s fingerprints say `usedforsecurity=False`, with the same values.
  - `harness/store.py` checks a setting for NaN with `math.isnan`. A test refuses NaN for every float setting.

- **A task policy the gate cannot apply is refused, never read loosely** (task-0242, doc-0033 R1).
  `block_levels = "absent"` became the set of its letters, so nothing blocked and the gate read QUALIFIED,
  exit 0. `block_levels = 7` passed `tools/check_subject.py` and failed only at run time. One validator,
  `harness/task_policy.py`, now serves the checker and every runtime reader of `[tasks.<class>]` (the gate,
  `gate_cli.py`, the MCP reader, `run.py`, the agent-key path), and coerces nothing. `block_levels` is a list
  of gate levels, `keys` a non-empty list of keys, `max_unverified_share` a number from 0 to 1,
  `require_approved` true or false, `rationale` text. A malformed field is a checker error and, unchecked,
  the gate's exit 2 (an error result from the MCP reader), naming the class and the field. A subject with a
  malformed task class does not load: every gate call exits 2 naming the field.
- **A key resting only on inference carries every basis, not one chosen by the hash seed** (task-0244,
  doc-0033 R3). A key whose statements are all inferred, assumed or hypothesised was flagged with one of
  those bases, picked by Python's set order, so the same store could report different flags from run to
  run. Its flags now list every basis among them, sorted. The verdict never depended on it.
- **Two numeric values of a key compare exactly** (task-0243, doc-0033 R2, doc-0028 G9-16). `rules.compatible`,
  which the rules, the review's dispute check, the capture and the load share, compared numbers as floats.
  9007199254740992 and 9007199254740993, or 1e309 and 2e309, read equal: R-CORROBORATE promoted them and
  R-CONFLICT stayed silent. They now compare as `decimal.Decimal`, with no tolerance; 316.00 is still 316. A
  non-finite value (`inf`, `nan` and their spellings) is incomparable, as R-VAGUE reads a vague one. Nothing in
  the record moves.
- **The vendored register moves to ieam-register v0.2.13** (`7980708`, from v0.2.11). It adds the register's
  decision 0019, four eyes: a session that drafted a change is its author and may not approve it. It also adds
  decision 0020, coverage rule C4: an approved process that realises an approved capability is supported by an
  approved application or module. The vendored register is C4-clean (5 of 5 covered). knowgov's register view
  and `proposal_impact` still read coverage C1 to C3 by name, so C4 has no coverage line and no new-gap entry. A
  C4 error in an instance's register still shows in the register view's findings list and its error count,
  which list every checker finding. Nothing in the record moves.

- **The page's store panel links Neo4j Browser to the right bolt port** (task-0235). `GET /api/store`, a route
  that serves the page, gains a `browser_connect` field: the Neo4j Browser link connected to the bolt port the
  stack publishes (`KG_PORT_BOLT`), or `null` for a store with no Browser. It is not a contract: the page's
  HTTP API is the four routes `demo/README.md` names (decision-0030).

- **What stays stable from 1.0, and how a change reaches you** (task-0181, decision-0016, doc-0028 P4).
  `instance/README.md`'s contracts table now says, for each contract, how you are told when it changes. A new
  subsection quotes decision-0016's points 2, 5 and 6: 0.9.x carries fixes only, the deprecation rule from
  1.0.0, and the support window. `tests/test_adopter_docs.py` holds the table to point 3's list, none missing
  and none invented, and holds the quotes to the record.

- **A job's processes can no longer outlast the worker's clean-up under load** (task-0233). After each job the
  worker kills every process the job left. It used to stop at the first look at the process table that found
  none, but a process can fork and exit between the moment the table is listed and the moment it is read, so a
  hostile job's fast chain of processes could be missed and keep running: once in 260 such jobs on a loaded
  machine. In its container the worker now stops only when nothing forked during a look that found none, and
  `tools/check_worker.py` proves it as EXEC-14. If the clean-up still cannot confirm everything gone within its
  10 seconds, the worker now stops serving and exits, which ends every process in its container; the page then
  refuses arms runs until the worker is restarted. Before, it logged the survivors and took the next job.
- **The worker's containment check no longer counts the healthcheck, and a job can no longer hide from it**
  (task-0232). `tools/check_worker.py`'s EXEC-11 counts any process of the worker's user still alive after a
  job. It once counted the container's own healthcheck in the instant that check exits, and failed. It also
  skipped any process with `--attest-only` on its command line, which a job could copy to hide. The check now
  counts a process only when a second scan, a second later, still finds one, and it trusts no command line: it
  leaves out only processes started from outside the container, such as the healthcheck, which a job cannot
  start. Each process it counts is now named in the failure.
- **The adopter docs held against the code** (task-0230, doc-0028 G9-9 and P4). The nine adopter-facing
  documents were checked against the code, and every stale claim found is corrected: commands, flags,
  settings, paths, routes, counts, defaults and described behaviour, in the READMEs, `docs/guide.md`,
  `docs/security.md` and `docs/lighthouse-evaluation.md`. `tests/test_adopter_docs.py` now fails on any
  of the following that the code does not bear out: a `--flag`, a command's options, a `KG_*` setting,
  a repository path or link, a cited test or an `/api` route. `instance/README.md` ends with what stays
  stable from 1.0, quoting decision-0016 point 3. No code, contract or pin changes.
- **Where the docs were right and the code was wrong** (task-0235; task-0230's docs pass). The store panel's
  Neo4j Browser link and the impact guides' links now connect to the bolt port the stack publishes
  (`KG_PORT_BOLT`), so a second stack's links reach its own Neo4j, not the first's. The page no longer says a deterministic run creates no `Derived` node (the
  page's runs give stage 2 the record's output), and its Arms note names the contained worker. The MCP
  reader's instructions say every tool but `list_subjects` takes `subject`. Two `docs/security.md` rows now
  cite tests that prove them: where each store lives, and that the gate never rules.
- **`tools/preload_check.py` exits 2 when it cannot write `-o`** (task-0228, doc-0030 F6). An unwritable
  report path (a missing folder) exited 1, the finding's code, with a traceback; it is now a failure to run,
  exit 2, one `cannot run: -o ...` line and no report. The command exits through the check tools' outcomes
  wrapper, so `KG_OUTCOMES` records its runs, and any other failure escaping it is exit 2 as well.
- **The Claude Code hooks close two gaps** (task-0204, doc-0030 P2, P4). `knowgov_hook.py` reads git from the
  command's tokens, so `/usr/bin/git push`, `git -C dir push` and `bash -c 'git push'` are the push
  transition, and a commit whose own command stages or names a spec file (`git add spec.md && git commit`,
  `git commit -a`, `git add .`) is the spec transition before it runs; a command it cannot read fails closed.
  `attestation_paths.py` blocks a change to `subject.toml`'s `[capture]` table, and capture-shaped TOML
  (`[[answer]]`, `[[unknown]]`, `[capture]`, a signed `[answered]`) written anywhere, as it blocks a review file.

- **A Neo4j writer's close no longer races its own heartbeat** (task-0229). A writer renews its lease from a
  background thread. Closing the writer used to stop that thread without waiting for it, then close the driver,
  so a renewal still being sent could meet the driver's goodbye on the same connection. The close then failed
  with a `BufferError` from the driver; it was rare, and it reddened one stack run on `main`. The close now
  waits for the renewal to finish first. A renewal still running past its own time bound fails the close with
  `HeartbeatAlive` and leaves the driver open, so the lease runs out on its own. `tools/check_snapshots.py`
  proves it as SNAP-10.

- **`--stage 2 --baseline record` is refused, and review months take the default only when no kind is named**
  (task-0209, doc-0030 G9, G11). Two fixes; no record moves.
  - The record keeps stage 2's verdicts but not its keys' levels. So a stage-2 gate ratcheted against it was
    compared with stage 1's levels, and the record's own stage-2 outcome read as a regression, exit 1. The
    combination now exits 2, before any store opens. For stage 2, pass `--baseline FILE`, an earlier stage-2
    report of `gate_cli.py -o FILE`, which compares level for level.
  - A key's review months are the shortest among the kinds of its nodes that the register's
    `[review.kinds]` names, else `[review] default_months`, as decision-0005 point 2 says. Before, a node
    whose kind is not named mixed the default in, so a key on a 24-month kind beside such a node lapsed at
    12. The public register names no kind above its default, so neither subject's dates move.
- **Uniform edges: every failure to run is exit 2, every hook's crash blocks** (task-0200, doc-0030 F6:
  G6, G7, R9, M6, M10, P8, P9, G12).
  - `gate_cli.py`, `trace.py`, `run.py` and `transcript.py` exit through one wrapper
    (`harness/cli_exit.py`). A pinned run reading the wall clock, a malformed or unreadable `--baseline`,
    an unwritable `-o`, a pin not installed and any other unexpected exception now exit 2 with its
    cause in one line, never 1 (a finding's code) with a traceback. `KG_TRACEBACK=1` shows it.
  - `gate_cli.py --publish` checks the report against its schema and writes `-o` before it publishes
    the load, so a command that fails publishes nothing.
  - The MCP servers answer a non-string tool or prompt name with -32602, and any other internal
    failure with -32603, so the stdio loop and the HTTP connection survive it. A port that cannot be
    bound exits 2.
  - **Known limit: the MCP server's HTTP transport binds IPv4 only.** `--host ::1` (or any IPv6 address)
    exits 2 before binding, where it crashed with exit 1. Serving IPv6 would need a named exception to the
    network scan.
  - Claude Code hooks: a gate report that is valid JSON but not an object is refused, and any exception
    in a hook, the gate's, the attestation hook or knowgov's own, blocks in every profile, the advisory
    one included. Before, it exited 1, which Claude Code reads as a non-blocking warning.
  - `instance/ci/knowgov-gate.sh` exits 2 when the knowgov checkout or the instance does not resolve to a
    directory; under a CI shell's `-e` it exited 1.
  - `harness/schema_check.py`'s `enum` and `const` compare type as well as value: `true` is not `1`.

- **Seven store and load fixes** (task-0205, doc-0030 S1, S3, S6, S7, S8, I11, I12). The scored record is
  unchanged.
  - **A document kept out of the store stays out (S1).** An artefact with a `mapper` and `store = false` used
    to have its statements loaded anyway, without a version: they could pair, dispute and block, and the
    fragment count was more than the store held. Now the load, the pristine values and the execution map
    read only the artefacts the store holds, and the counts match the nodes.
  - **The store file keeps its mode (S3).** Every rdflib publication used to reset `KG_RDFLIB_FILE` to 0644,
    undoing an operator's `chmod 600`. A publication now keeps the file's mode; a first one is 0644.
  - **The heap forecast counts stage 2 (S6).** `harness/run.py`'s check before the first load, and
    `harness/load_memory.py`'s sizing, now count each scenario's stage-2 re-load. Before, a run could be
    refused at S7 after six scenarios had run.
  - **A writer that wrote nothing publishes nothing (S7).** On both stores, a writer that only read used to
    publish a new generation, so every reader read the store again. `tools/check_snapshots.py` proves it as
    SNAP-09.
  - **`invalidated_at` has one meaning (S8).** It was epoch seconds on Neo4j and a node counter on rdflib.
    It is now the ISO 8601 instant of the change that invalidated the statement, on both stores.
  - **A subject's mistakes are named before the load (I11).** `tools/check_subject.py` now refuses two
    artefacts with one `short` (the load used to give the first all their statements) and a document with a
    duplicated row (the load used to fail with "the store did not answer"). A document a mapper cannot
    read now fails the load with its own name.
  - **An unchanged CRLF document reads checked (I12).** The load compared the pre-load report's digest of
    the raw bytes with a digest of the text, so a document with Windows line endings always read unchecked.
    It now compares raw bytes. A `knowgov-keys:` citation on line 1 after a byte-order mark is now read.
- **Three fixes to the MCP reader and its check** (task-0208, doc-0030 M7, M9, M11). `code_path`'s ledger
  leg reads `unchecked`, naming why, when the ledger holds an entry for the path but there is no code root to
  read the file from (no instance, or a code map that does not hold); before, it read `drift: false` for a
  file it never looked at. The reader no longer writes `__pycache__` into `KG_REGISTER/tools` when it loads
  the register's own modules, so a register mounted read-only stays unwritten. `tools/check_mcp_server.py`
  builds the arms' bundle from each scenario's prompts, as the runner does, not a fixed `task_codegen`.
- **An agent run stopped by its seconds ceiling reads as the ceiling, not as an API error** (task-0207,
  doc-0030 R6). When the run's deadline cut a model's answer mid-stream, or the client's timeout fired at
  it, the run was recorded as an API error, so `--resume` ran the cell again and paid for it again. It now
  ends with `stopped_by: "ceiling: <n> seconds"`, a `ceiling` turn in its trace, and no `api_error`, so
  `--resume` keeps it. A stream that falls silent for the idle limit before the deadline is still an API
  error.
- **Route (c) records the model that answered** (task-0207, doc-0030 R12). A transcript's proposals file
  named the configured model (`KG_ARMS_MODEL`); it now names the model the endpoint answered with, as the
  stream named it, which a gateway or an alias can make differ.
- **pumllint 0.35.0 is the record's pin** (task-0224, the maintainer, 2026-11-08). The image, both
  `harness.yml` jobs, `demo/requirements.txt` and the CI templates (`instance/ci/preload-check.yml`'s
  `PUMLLINT`, the GitLab include's `KNOWGOV_PIP`) install pumllint 0.35.0 in place of 0.33.0, so the
  pre-load check, the sequence-diagram mappers and the image run one version, the first with
  `pumllint trace --features` (task-0217 builds on it; a CI step runs it on the J-F kit). Nothing a
  reader sees moves: the scored record (S1 to S7) and J-F's run equal under the comparator on rdflib
  and Neo4j; the two mappers that import the parser yield the same statements, value for value; the
  pre-load check's pumllint findings on the example instance and on every `.puml` of both subjects are
  the same. The parser gains a field (`declared_line` on participants) that no mapper reads. Not a
  contract change: an instance that copied the CI template moves its `PUMLLINT` when it moves its
  knowgov tag.
- **What notices a code change, measured: H7's two mutants on the J-F subject** (task-0219, decision-0018 point 8).
  Two planted changes to one file of the public rebuild, each on a temporary copy, pre-registered first:
  - The gate (R-STALE) saw neither change, because no document changed; scenario C still read PROCEED.
  - trace saw both, as `drift` (minor), and could not tell them apart.
  - Only the kit's suite separated them: 2 and 19 of 258 cases failing.
  - A known limit: `trace.py check` fails at `blocker` by default, so a pipeline stops on a changed
    registered file only with `--fail-on minor`. `docs/reverse-engineering.md` step 8 now says so.
  - `subjects/jef_data_load/probes/h7/` (the pre-registration and `RESULTS.md`), `tools/check_h7_probe.py`,
    `tests/test_h7_probe.py`.
- **A guide to reverse-engineering a code base and finding its knowledge gaps** (task-0218, decision-0018
  points 1 and 2). `docs/reverse-engineering.md` walks the eight steps for an adopter, from scoping at a named
  commit to re-running on change. For each step it gives the tool that runs it today, the record it leaves and
  where that record lives. `docs/reverse-engineering-preregistration.md` is step 1's template, with the
  pumllint experiment's first run on J-F filled in as the example. `tests/test_reverse_engineering_guide.py`
  holds every option, path and flag the two pages name to a real one.
- **The page serves an edited subject on the next request, and the connector refuses a clash** (task-0206,
  doc-0030 P3, P10). Before, the page rescanned its subjects when a `subject.toml` moved, but kept each
  subject's tables by folder forever. So an edited name, `listed`, task or id was never served, and an
  edited `scenarios.toml` was not noticed at all. Both manifests are now watched, and a subject is
  rebuilt when either moves. With `KG_SUBJECTS` set and no subject under it loading, the page used to
  fall back to the public CargoQuote. It now serves none: the page and `/api/subjects` load, and every
  other route answers 404 naming `KG_SUBJECTS`. `tools/connector.py` used to keep one of two export files
  landing at the same relative path, such as two files sharing a name, and drop the other silently. It
  now refuses them, naming both, and lands nothing.
- **Stage 2 reads every review file again** (task-0222). A review written for a scenario's later version now
  applies in the same `--stage 2` run, on both stores; before, only the rulings were re-checked and an act stage 1
  could not apply stayed reported. Stage 2 clears the acts stage 1 recorded, then binds every ruling and close to
  what the change left current. A close of a gap stage 1 already closed, on the same declaration (its digest), is a
  no-op; a close whose declaration changed is not applied and is an `act` finding, as at a load (task-0199). New port
  read `gap_brief` and write `clear_act_findings`, on both adapters. `tools/check_stage2_reload.py` holds it (R1 to
  R3). The scored record is unchanged.
- **A model call whose prompt the endpoint cut is marked, never scored** (task-0185, doc-0023). A model
  server with a short context, such as Ollama at its defaults (4,096 tokens), can drop most of a long prompt
  and still answer, with HTTP 200. The OpenAI API has no field for the context length, so knowgov cannot set
  it; only the server can (`OLLAMA_CONTEXT_LENGTH` for Ollama). An Arms call, or a turn of an agent run, whose
  reported prompt tokens are too few for the characters sent (more than 10 characters per token, on a prompt of
  4,000 characters or more) is now recorded as a failed cell with a `prompt_cut` field and the reason. Its reply
  is not graded, and the page's run table shows *prompt cut*. Before, the reply was graded as if the model had
  read the whole prompt.

- **A model reply sent as a list of parts is read as its text** (task-0186, doc-0023). Mistral documents that
  at a high reasoning effort it sends the reply as a list, a thinking part and then the text. Such a reply
  stopped an Arms call or an agent run with an error. The text parts are now joined and the thinking is
  dropped. Replies sent as plain text read as before. Not yet tried against Mistral's own API.

- **Only a temporary failure of a model call is retried** (task-0187, doc-0023). An Arms call used to retry any
  error three times, waiting 5, 10 and 15 seconds: a request the endpoint refuses, such as an effort the model
  does not accept, took 30 seconds to report. Now a 429, a 5xx, a dropped or timed-out connection, or a reply
  that ended early is retried with the same waits, and any other error is reported at once.

- **A key the endpoint never checks is no longer marked accepted** (task-0188, doc-0023). The page checks each
  model row's key by asking its endpoint for the list of models. Some endpoints list their models to anyone:
  OpenRouter answered with an invalid key, and Ollama holds no keys. Such a row read *key accepted*
  whatever its key. The page now asks first with a placeholder that is no key. If the endpoint answers that, the
  row reads *key unchecked* with the reason, and your key is not sent. Otherwise it asks with your key, as
  before. The check stays free; it makes two requests at most.

- **Worker job isolation and a run folder that starts clean** (task-0203, doc-0030 F8: R2, R3, R4, R7).
  - **No process outlives its job.** After each job the worker kills every process below it, at any depth,
    within 10 seconds. A 70-deep chain of processes, each in its own session, used to leave 20 alive; it
    now leaves none.
  - **A job cannot forge its answer.** The job's runner can no longer be reached through `/proc`, and it
    answers on a channel nothing it starts inherits, so model code cannot write a forged answer through it.
  - **A job's own failure no longer ends the run.** A job that runs out of time or is killed at a bound is
    now that arm's failed cell, as on the host, and the run goes on to write its `summary.json`,
    `usage.json` and `SHA256SUMS`.
  - **A reused `--out` folder carries nothing over.** A fresh agent cell starts from an empty sandbox, and
    `usage.json` adds an earlier attempt's only under `--resume`.
  - `tools/check_worker.py` proves the first three on the real worker (EXEC-11 to EXEC-13).

- **One clock: every lapse is decided on the gate's date** (task-0198, doc-0030 F4: H3, G4, G10, M8;
  decision-0005 points 3 and 5).
  - **A person's approval.** Before, its six-month lapse was decided when the store was loaded, against
    today, so one `--as-of` read PROCEED or QUALIFIED by the calendar, and the report named a date it had not
    read. The load now applies the approval with its end date, and the gate decides as of `--as-of`: past its
    six months the statement reads *proposed*, with a *lapsed* finding. One `--as-of` gives one report
    whatever the day.
  - **No verification.** A review-file approval of a statement with no verification now lapses at its date
    plus the key's review months.
  - **After the date.** A review or approval dated after the date read is not counted; the finding says so.
  - **The MCP answer.** `three_valued_answer` marks a statement no longer current as of the server's date
    (`lapsed`, and an `as_of`).
  - **Additive.** A lapse entry names the status it reads (`to`), and an approval its `until`.

  `tools/check_one_clock.py` proves it on both stores. The record is unchanged.

- **Stage 2 re-reads the whole later kit and answers as a fresh load would** (task-0197, doc-0030 F3: H2, H4,
  I5, I6, G5). `--stage 2` and a run's stage 2 used to re-ingest the one changed file alone. Five defects followed:
  - a review's close of a declared gap reopened (H2);
  - a v2 statement contradicting another document read *proposed* where a fresh load reads *disputed* (H4);
  - symbols resolved from that file only, so re-ingesting a diagram flagged `ACCEPT_MAX` undefined, and a
    changed `ACCEPT_MAX` invalidated nothing (I5);
  - a statement that lost one of several fragments got no successor (I6);
  - a declared gap outlived the statement that declared it (G5).

  Now the whole later kit is extracted, and each statement is diffed against the store's by its id stem, on
  value and fragment set. Only changed documents get a version. The rules run across versions. R-REQ never
  reopens a closed gap, and R-STALE withdraws a declared gap whose declaration it invalidated.
  `tools/check_stage2_reload.py` holds a stage-2 gate equal to a fresh load of the later documents plus the
  stale and suspect findings, on both stores. The record (S1 to S7, S6's stage 2 included) is unchanged.

- **Two security fixes on the MCP reader's boundary** (task-0196, doc-0030 H7, M3). `subject_check`
  now refuses a proposed manifest whose `[[artefact]] path`, `include`, `[reference] code`, `[oracle]
  script`, `[verification] map`, `[record] dir` or any other path field is absolute or resolves outside
  the call's temporary instance, before anything is written or read, so its report can no longer say
  whether a server file exists or quote it; and it compares the documents' paths normalised, so
  `x/../subject.toml` can no longer replace the manifest. Over HTTP, every refusal (404, 421, 403,
  401, and the page's own) now closes the connection, so a refused request's body is never read as a
  second request on the same keep-alive socket with a Host of its own.

- **The deterministic comparator counts a scenario the run lacks as a difference** (task-0193, doc-0030 P7).
  Before, `demo/tools/compare_deterministic.py` skipped a named or defaulted scenario with no folder in the run,
  so a run that stopped after S1 matched the record at exit 0. Each missing scenario is now a difference
  (`S2: not in the run`), exit 1. A run of fewer scenarios than the record names them: `--scenarios S1`. With
  it, three of CI's checks now compare by construction: the round trip compares every part it collects
  (`store_reads` included, P5); `demo.yml` and `harness.yml` run every step under `bash -eo pipefail`, so a
  failing saved query fails its step instead of hiding behind `| tee` (P6); and the security test scans
  recursively, `instance/ci` and each subject's oracle included, for more network modules and dynamic imports
  of one (R11).

- **The instance check refuses a scenario id two subjects share** (task-0194, doc-0030 H1's interim). The shared
  store records the scenario it holds by its id alone, so two subjects both declaring `S0` would answer each
  other's gates. `tools/check_instance.py` now exits 1 on a scenario id two subjects declare, naming the id,
  the subjects and why; on an empty `subjects/`; and on two subject folders declaring the same id. The
  onboarding skill and `instance/README.md` tell adopters to rename the copied `S0` to `<id>-S0`.

- **The capture commands no longer reload the shared store** (task-0183). Before, `capture.py questionnaire`,
  `capture.py review` and `harness/transcript.py` wiped the store `KG_STORE` names and loaded their scenario
  into it. On a stack, that is the Neo4j the page and the MCP servers read, so an owner following the gate's
  own route replaced the scenario everyone saw. Each now loads into a private in-memory store of its own
  (`store.scratch_store`) and leaves the shared store as it was. The files they write are the same. They now
  need rdflib, which is pinned in `demo/requirements.txt` and present in the image; without it they exit 2
  and name the install. The onboarding skill no longer sets `KG_STORE=rdflib` for the questionnaire.

- **The road to 1.0 is decided** (decision-0016). 0.9.0 will freeze the contracts an adopter builds on,
  and the contract changes made since 0.8.0 wait for it. After 0.9.0, a 0.9.x release carries only fixes,
  and any contract change becomes 0.10.0. 1.0.0 follows once a pilot organisation has run on the 0.9
  contracts without a change. From 1.0.0 on, a deprecated contract keeps working for at least one
  further minor release and ninety days, and is removed only in a major release. Until a support
  entity exists, the latest minor release is supported on a best-effort basis.

- **The MCP servers when the stack runs on another machine** (docs, task-0182). `instance/README.md`
  shows how Claude Code and Claude Desktop start `knowgov` and `knowgov-runs` over SSH when the stack
  runs on a server such as the EC2 instance of `demo/README.md`: the same `docker compose … exec`
  command behind `ssh -T <alias>`, with the SSH setup it needs (a `~/.ssh/config` alias with
  `BatchMode yes`, the host key accepted once) and a check from a terminal. Nothing new listens and
  no token is needed.

- **The page's Register view shows what a register update withdrew** (task-0178). Set
  `KG_REGISTER_PREVIOUS` to the register as it was before the update, and the view lists the nodes it
  deprecated or retired, the links it withdrew, each with its reason, and the subject's keys that rest
  on them. `GET /api/register` carries it as `register_change`. It is computed by the same code as
  the gate's `--register-previous` block, and `tools/check_register_change.py` holds the two equal.
  The page reads the setting once, at start, and writes to neither register. Without it, the view
  says so in one line; a missing path is shown, not raised. This lifts the page half of 0.8.0's known
  limit on register changes.

- **Every MCP tool's output has a pinned schema** (task-0172). Each tool of the reader and of
  `knowgov-runs` names the schema of its `structuredContent` at the end of its description. Ten are
  new: `store-status`, `three-valued-answer`, `evidence-bundle`, `register-impact`, `list-subjects`,
  `scenario-runs`, `scenario-result`, `run-options` (with `execution`, `worker` and each model row's
  `key_check`), `run-started` and `run-status`. The others
  were already pinned (the gate report, `register-nodes`, `key-nodes`, `code-path`,
  `document-links`, `held-keys`, `derived-outputs`, `document-statements`, `proposal-impact`,
  `subject-check`). No output changes shape. A test calls every tool on both public subjects and
  validates each answer, and `tools/check_mcp_server.py` validates every answer it reads, over
  stdio and HTTP. A field a schema does not name fails.

- **A reader recovers from an abandoned Neo4j publication** (task-0175). Before, a writer killed between
  raising the publication counter and committing left reads waiting `KG_NEO4J_READ_WAIT`, then
  refusing, until the next writer took the lease.
  - Now, once that writer's lease has run out, the next reader clears the raised counter under the
    sequence lock and answers from the last committed generation, with no writer needed.
  - The publication node records the abandoning writer (`abandoned_owner`, `abandoned_epoch`).
  - While the lease is live, reads wait and refuse as before.
  - `tools/check_snapshots.py` proves it as SNAP-08, on both stores: both orders of a reader and a writer,
    and a race between them.
  - This lifts 0.8.0's known limit on a writer killed mid-publication.
- **The compose file runs the v0.8.0 release** (decision-0003). `demo/docker-compose.yml`'s `app` and
  `worker` pin `ghcr.io/fdurieux/knowgov:v0.8.0` by its index digest, the first release image that carries
  the worker, so `docker compose --profile arms up -d --wait` from the published compose now serves arms
  runs, on Linux with Landlock. `docs/security.md`'s pins row names the release.
- **The Arms mode on an EC2 instance, from a Mac** (task-0162). `demo/README.md` walks through running
  the stack, the worker included, on an EC2 `t3.large` with Ubuntu Server 24.04 LTS and Ubuntu's own
  Docker, the page reached through an SSH tunnel with the default `127.0.0.1` bind. The worker's
  self-check attested every check true there on a real machine (kernel `7.0.0-1014-aws`, with Landlock),
  and S1's arms runs completed there on the Claude row and on the record's model, the oracle 11/11 for each arm;
  Docker Desktop for Mac 4.48.0 still refuses it (no Landlock). `docs/security.md` names that host and no
  other.
- **The demo README looks after the stack and the keys** (task-0162). *Looking after the stack on the
  instance*: status, the worker's self-check, keys after a reconnect, changing a key, updating, stopping,
  disk, the instance's address and the tunnel's port. *API keys: questions and answers*: which variable
  each model row reads, setting a key at a silent prompt, recreating the container after a change, a
  free check that a key works, reading a 401, and getting, limiting and revoking keys at OpenAI,
  Anthropic and Google.

- **The Arms chip and button say whether an Arms run can start** (task-0167). Before, the page showed
  "arms enabled" whenever a model key was set, even with no contained worker running, and the run was
  then refused. Now `GET /api/scenarios` carries `"execution": {"ok", "why"}`, the refusal an Arms run
  would get, beside the unchanged `arms_enabled`. With a key and no confined worker, the chip reads
  "arms: no contained worker" and the Arms buttons stay greyed, with the reason and the fix
  (`--profile arms`, on Linux with Landlock). `demo/README.md` gives the one-command worker self-check.
- **knowgov-runs says whether an Arms run would start** (task-0168). `run_options` passes the page's
  `execution` through (`{"ok", "why"}`, task-0167) and adds `arms_ready`: true only when a model key is
  set, the operator allows arms, and model output may run. `arms_enabled` and `arms_on_page` are
  unchanged. A page older than task-0167, which does not report `execution`, reads as refused.
- **"What this shows" speaks for the run on screen** (task-0170). The plain-English box ends with the
  record's conclusion only for the record, and for a run whose every arm outcome the record also had.
  A run whose model calls failed now says so, quoting the first error, and that the record's conclusion
  does not apply. A run that did not reproduce the record says what happened instead.

- **The page shows where Arms code runs** (task-0169). A new header chip reads, for example,
  "worker: attested · Docker · Linux 7.0.0-1014-aws (x86_64) · AWS (from the kernel release)", or
  "worker: not attested" with the reason. The facts come only from the worker's own attestation, which
  now carries a `host` block (`system`, `kernel`, `machine`, `engine`) read inside its container;
  no check and no verdict changes. A cloud is a reading of the kernel release's suffix (`-aws`,
  `-azure`, `-gcp`, `-oracle`), labelled as such, never asked of a metadata service. `GET /api/scenarios`
  and knowgov-runs' `run_options` carry it as `worker`, additively.

- **Model keys are checked before the Arms drop-down offers a row** (task-0171). When the page starts,
  it asks each row's endpoint for its model listing (`GET {base_url}/models`), which spends no tokens.
  Each row then reads key accepted, key refused (401 or 403), endpoint unreachable, or key unchecked.
  A refused row is greyed with the HTTP status and the variable to fix, and a run on it is refused at
  once instead of failing after the first call. Rows on the same endpoint and key are checked once.
  *re-check keys* asks again (`POST /api/models/check`, behind the page's token). Only the verdict, the
  status and the time are kept, never the key or the provider's message. `KG_KEY_CHECK=off` turns the
  check off. The Claude row reads "gateway key accepted, upstream unchecked": the gateway's listing
  proves its own key only, and LiteLLM's `/health` would make a paid call, so the Anthropic key is first
  tested by a run. Each row in `GET /api/scenarios` and knowgov-runs' `run_options` carries
  `key_check`, and `demo/models.toml` gains an optional `gateway` field. Both are additive.

## 0.8.0 — 2026-11-06

Code a model writes now runs contained, and a reader never sees a half-built store. The arms'
grading and the agent's suites run in a sibling `worker` container of the same image: no network, a
read-only root, no capabilities, uid 65534, bounded memory, processes and CPU, no secret, and
Landlock letting a job write only beneath its own folder. The worker attests that confinement at
start (no interface up but loopback, no route out, no network-admin capability, no socket that could
leave the namespace, a read-only root, its uid, no engine socket, and Landlock's write confinement),
and the app refuses a job without a fresh attestation. The worker starts only with
`--profile arms`, so the default `docker compose up --wait` is green on every engine. On Neo4j a
writer's whole unit is one transaction under a lease, published under a sequence lock that every
read checks, so the page, the MCP server and `gate_cli --no-load` see a run's load only once it
commits; a reader that cannot get one whole generation refuses rather than answer from a mix. The
pre-load report carries the instance layout check's problems, so they annotate; the GitHub action
can send its findings to code scanning; the owner's questionnaire names who closes a declared gap;
a directory artefact's part digests hash each file's raw bytes; and the MCP server reuses one parse
of an rdflib store per publication.
The CI gate script now refuses an instance it cannot name a subject for: in 0.7.0 and earlier, an
instance with no subject or several, and no `KG_SUBJECT`, ran the gate on the default subject and
could pass. The adopter guide now describes the review step as built, the READMEs name Python 3.12,
the image's interpreter, and the rdflib CI job runs as two parallel jobs.

### Contract changes (why this is 0.8.0, decision-0003)

- **A store publishes whole generations, and every read answers from one** (task-0141.06,
  decision-0014). On Neo4j a writer's whole unit is now one transaction under a lease in the
  database, published under a sequence lock that every read call checks.
  - **Visibility.** The page, the MCP server and `gate_cli --no-load` see a run's load only once it
    commits, never half of it. A run that fails or is killed leaves the previous generation.
  - **The port.** `StoreChanged` is a publication during a read, `StoreFenced` a writer whose ownership
    was taken over. `store.read(fn)` runs a logical read again on a fresh handle.
  - **Compatibility.**
    - The page's register projection answers 409 while another writer holds the store.
    - A Neo4j database gains one `_KgPublication` node and its uniqueness constraint; neither is in
      the exported Turtle, the census or D1.
    - On rdflib a writer whose lock file was removed or replaced publishes nothing.
    - New settings, each refused outside its bounds with the variable's name: `KG_NEO4J_LOCK_TIMEOUT`
      (0 to 86400 s, default 60), `KG_NEO4J_LEASE_SECONDS` (1 to 3600 s, default 60),
      `KG_NEO4J_READ_WAIT` (0 to 600 s, default 10), `KG_STORE_READ_ATTEMPTS` (1 to 10, default 3).
  - **A new refusal.** A reader whose every attempt met a publication, or that waited out an
    interrupted one, refuses:
    - `gate_cli --no-load` exits 2 ("cannot run");
    - the MCP server answers an error result;
    - the page's `/api/store` and `/api/gaps` answer 503 with `Retry-After: 1` and `"busy": true`.
  - **A known limit.** On Neo4j a writer's unit is bounded by the server's transaction memory. A larger
    one fails and keeps the previous generation (docs/security.md).

- **The pre-load report carries the layout check's problems** (task-0115, additive): `tools/preload_check.py
  --layout` runs `tools/check_instance.py` on the same instance and adds an optional `layout` block
  (`holds`, `exit_code`, `problems`, each with a severity, a kind, the file it concerns and `fails`)
  to `harness/schemas/preload-report.schema.json`, version 1. `instance/ci/preload-check.sh` passes it
  whenever `KG_REPORT` is set, so `KG_ANNOTATE` shows them: a layout error as an error at the file it
  names or the subject's `subject.toml`; an unread or absent document, a subject's warning or note, an
  unmapped code file or an unmatched code-map row as a warning or notice, never an error. The report's
  `exit_code` stays the lint's, and the step's exit is unchanged: the layout's is still
  `check_instance.py`'s.

- **Model-written code runs in a contained worker, or not at all** (task-0141.05, decision-0012). The
  arms' single-reply grading, the agent's feedback suite and its final grading go through
  `harness/execution.py` to the `worker` service, a sibling container of the same image with:
  - no network and a read-only root;
  - no capabilities and no privilege escalation, as uid 65534;
  - bounded memory, processes and CPU, and no secret in its environment.

  Each job runs as a killed-whole process group with an allowlisted environment and resource
  limits. Landlock lets it write only to its own folder. The worker attests its confinement and
  refuses to serve when a check fails; the app refuses a job without a fresh attestation, and reads
  results as untrusted, capped data. The agent's sandbox writes refuse symlinks at any step. One
  monotonic deadline bounds a run, the model's stream included, with an idle limit
  (`KG_AGENT_IDLE_SECONDS`, 120 s). Compatibility: without a worker (`KG_WORKER_JOBS`), an arms run
  refuses (exit 2; the page answers 400) instead of running on the host. `KG_ALLOW_UNCONTAINED_EXECUTION=1`
  is the only escape. The published 0.7.0 image predates the worker, so arms run only from an image
  that carries it. Limits: `KG_WORKER_MEMORY`, `KG_WORKER_PROCESSES`, `KG_WORKER_FILE_BYTES`,
  `KG_WORKER_MAX_JOB_SECONDS` and `KG_WORKER_JOB_SECONDS`, and compose's `KG_WORKER_MEM` and
  `KG_WORKER_CPUS`.

- **The worker starts only with `--profile arms`** (decision-0015). The default `docker compose up
  -d --build --wait` now starts the app and Neo4j (and the gateway with `--profile claude`), green on
  every engine; it no longer starts the worker. An arms run without a served worker is refused, as
  before. To run arms: `docker compose --profile arms up -d --build --wait`, on Linux with Landlock
  (kernel 5.13 or later, enabled). A known limit: Docker Desktop for Mac 4.48.0's kernel
  (6.10.14-linuxkit) is built without Landlock, so there the worker refuses to serve and exits 3,
  and arms are refused; a later version may differ, unverified (task-0162).

### Changes

- **The CI gate script refuses an instance it cannot name a subject for** (security; 0.7.0 and
  earlier affected). With `KG_SUBJECT` unset, `instance/ci/knowgov-gate.sh` is meant to exit 2 for
  `gate` and `trace-*` unless the instance holds exactly one subject. Its refusal ran inside
  `$(...)`, so it ended only a subshell, and an empty `subjects/` folder counted as one subject. So
  an instance with no subject, or several, ran the gate on the harness's default subject, and could
  pass when it should have refused. Now nothing runs and the exit is 2. Set `KG_SUBJECT` to keep
  any other behaviour.

- **Two corrections to the adopter documentation.** `docs/guide.md` §6 said the review step was
  not built and that no command took S2 to PROCEED. It is built (task-0037): the section now says
  what a review does, that S2 reaches PROCEED once its answers are reviewed and its open decision
  is closed by its owner, and that an approval lapses after six months, with `instance/README.md`
  for the detail. `README.md` and `demo/README.md` named Python 3.13 for the harness and the app
  image; the image runs Python 3.12 (`demo/Dockerfile`), and that is the version to install for the
  harness. The standard-library tests still run on 3.13 in CI too.

- **The rdflib CI job runs as two parallel jobs** (task-0163). `rdflib` keeps the record and its round
  trip, and `rdflib-readers` runs the readers (the MCP server, the lighthouse, the gate, the wrappers,
  review, capture, transcript). Nothing is dropped or subset: a test holds that every step of the old job
  runs in exactly one. `rdflib-readers` gates once it joins the ruleset's required checks.

- **The worker attests that it cannot open AF_VSOCK or AF_PACKET sockets or reach an outside address**
  (`no_socket_escape`, task-0165; decision-0012, decision-0015). No network namespace confines AF_VSOCK,
  and on Docker Desktop the VM's host side answers on it; the engine's default seccomp profile refuses it,
  and the worker now proves that at start rather than assume it. It tries both families and a connect to
  `192.0.2.1:9` (TEST-NET-1, never routed); any that opens or reaches fails the check, and the app refuses
  jobs from a worker whose attestation lacks it. The attestation carries each probe's outcome under
  `sockets`. On Docker Desktop for Mac 4.48.0 all three are refused (EPERM, EPERM, ENETUNREACH).

- **The worker's network check accepts the down tunnel devices Docker Desktop creates** (task-0161,
  decision-0015). `loopback_only` held only when `/sys/class/net` listed `lo` alone. A kernel with
  tunnel modules loaded puts `tunl0`, `gre0`, `sit0` and others, down, in every network namespace,
  and the bonding driver adds its `bonding_masters` file. The check now holds when no interface but
  `lo` is up, no route leaves `lo`, and `CAP_NET_ADMIN` is in neither the effective nor the bounding
  set; anything unreadable counts against it. The attestation's `interfaces` is now a map from each
  interface to `up` or `down`, beside `routes` and `cap_net_admin`.

- **The MCP server's rdflib reads reuse one parse per publication** (task-0097). A read handle on a
  file-backed rdflib store now reuses the process's parse of the published file while it is the same
  publication (keyed by the file's device, inode, size and times), and parses again after a publication,
  so a read never answers from a retired generation; one read handle per call and Neo4j are unchanged.
  The rdflib MCP step took 430 s and now 259 s locally on the pull-request subset. The process keeps the
  latest parse: about 15 MB for CargoQuote S1 and 82 MB for J-F C.

- **A directory artefact's file digests are the file's bytes** (task-0098, a fix to task-0094). `part_sha256`
  hashed each part as bundled, and the bundle adds a newline to a file that lacks one and reads CRLF as LF,
  so such a file's digest disagreed with the register's, which `register-cites` compares it with. The load now
  hashes each file's raw bytes; a part a scenario's plant changed keeps its text's digest. Every file of the
  public subjects' directory artefacts (J-F's 47) already ends in a newline with LF line ends, so no recorded
  digest moves; an instance's file without one now matches its register.

- **CI hygiene, the review's V1 completed** (task-0159).
  - **Timeouts.** Every job of `tests.yml`, `harness.yml` and `demo.yml` has a timeout, each above the worst run seen, so a slow, honest run
    is not killed: tests 20 min, rdflib 120, stack 60, publish 30.
  - **The stack job's paths.** A change under `instance/` now runs it.
  - **Outcomes, machine-readable.** `tests/run_tests.py` writes a JSON report when `KG_TEST_REPORT` names a
    file. Every check tool appends its exit and, where it reports them, each check's pass, fail or skip with
    the skip's reason, when `KG_OUTCOMES` names one (`tools/_outcomes.py`). Each job's summary lists them, one
    line per tool (`tools/outcomes_summary.py`), and keeps the outcome JSON for 14 days as an artifact
    (`actions/upload-artifact`, pinned by commit), whatever the job's result.
  - **Coverage.** `tools/coverage_stdlib.py` measures the suite's statement and branch coverage with
    the standard library alone (CPython 3.12+), against a declared denominator. It counts the suite's own
    process only, so it claims no integration coverage. The tests job reports it.

- **The hook's settings snippets read the spec commit under `design`** (task-0114, after task-0101).
  The three snippets under `instance/ci/claude/` (repository, managed, advisory) add
  `--task-for spec=design`, as the pilot protocol does; the plan and the push stay `codegen`. Keep it
  only where every gated subject declares `[tasks.design]`; elsewhere the spec commit's gate exits 2,
  which the mandatory hook blocks and the advisory one lets through, so drop the two arguments
  (instance README).

- **The owner's questionnaire names who closes a declared gap** (task-0113, after task-0110). An item
  on a declared gap carries `gap`, `closed_by` and `closed_by_name`, the unit its declaration names, as
  the gate's finding names it in `closer`, and a comment line saying an answer does not close it: S2's
  questionnaire for ORG-0002 names ORG-0004 as closing OD-1. Ingest reads none of them; a questionnaire
  written before still ingests to the same capture.

- **The GitHub action can upload its findings to code scanning** (task-0116, after task-0106). A new
  optional input, `sarif` (off by default), writes the report as SARIF 2.1.0 and uploads it with
  `github/codeql-action/upload-sarif`, pinned by commit, whatever the gate's exit; `sarif-category`
  names the analysis (default `knowgov-<gate>`) and the output `sarif-id` the upload. The instance's
  job needs `security-events: write` and code scanning available (instance README). The exit code
  stays the gate's.

### What this release carries

| what | version |
|---|---|
| pumllint (the sequence-diagram mapper's parser) | 0.33.0, from PyPI |
| the IEAM register, vendored under `demo/register/` | ieam-register `v0.2.11` |
| the record's pins | unchanged from 0.7.0 |
| Python | 3.12 in the image |

The image is `ghcr.io/fdurieux/knowgov:v0.8.0`, the first release image that carries the worker. The
compose file moves to it in a follow-up, once the Release has published its digest; until then the
published compose runs v0.7.0, whose image has no worker, so an arms run refuses there.

### Known limits

- Contained execution needs Linux with Landlock (kernel 5.13 or later, enabled) and a container
  engine that runs the compose `worker` service under `--profile arms`. Docker Desktop for Mac
  4.48.0's kernel (6.10.14-linuxkit) is built without Landlock: there the worker refuses to serve
  and every arms run is refused, while the page, deterministic runs, the gate and the MCP server are
  unaffected. A later Docker Desktop may differ; unverified (task-0162).
  `KG_ALLOW_UNCONTAINED_EXECUTION=1` is the only escape, and it runs the code on the host.
- Neo4j keeps no earlier generation: a reader open across a publication is refused and read again,
  and one that cannot get a whole generation within `KG_STORE_READ_ATTEMPTS` refuses (`gate_cli`
  exit 2, an MCP error result, 503 on the page).
- A writer killed between raising the publication counter and committing makes reads wait up to
  `KG_NEO4J_READ_WAIT` seconds, then refuse, until the next writer takes the lease.
- The server's transaction memory bounds a Neo4j load: measured peaks about 41 MiB for CargoQuote's
  whole run and 64 MiB for J-F's, against 70% of the compose's 1 GiB heap. Size the heap for a much
  larger instance.
- Terminating a stale writer's transaction needs a role allowed to run `TERMINATE TRANSACTIONS`;
  without it the epoch check still refuses that writer's commit, but its open transaction holds its
  locks until its connection ends.
- One MCP process holds one parsed rdflib store, the latest publication only: about 15 MB for
  CargoQuote S1 and 82 MB for J-F C.
- A file artefact's Version digest hashes its text, so a file with CRLF line endings has a different
  digest from a register citation over its raw bytes (task-0160). A directory artefact's parts hash
  their raw bytes.
- A file-backed store supports its writers on POSIX with `flock`, on a local disk.
- Response sizes are not capped by the HTTP limits; request framing, bodies, deadlines and
  connections are.
- Claude Desktop's role is asking the gate until the maintainer's own test shows the prompts listed
  there and `subject_check` running; onboarding is Claude Code's.
- A proposal's slices are as fine as the register's links: steps supported only by one end-to-end
  process share one thread.
- An attestation is the manifest's declaration and is not bound to a document's version.
- A run folder from before `run.json` is inferred: its status, start and initiator are unknown.
- `proposal_impact`'s branch mode reads a branch's additions only.
- The subject check compares keys with the documents' yield only where the mappers run.
- The connector has run only on the synthetic CargoQuote export, not on a real installation.
- A register change is read only when the gate is given the previous register; the page's register
  panel does not show what a change withdrew yet.
- The GitLab include is proven by shell, not yet on a GitLab runner (task-0108).
- The hooks see Edit and Write, not a shell command writing the same file.

## 0.7.0 — 2026-11-06

The store, the HTTP boundary and code execution are hardened for an organisation's own instance,
and an assistant can now travel the whole chain from strategy to code and back. A read handle never
writes the store back, and a writer publishes atomically under a lock, so a stale reader can no
longer overwrite a newer run and two writers no longer lose an update. Both servers check every
request's authority and origin, on reads as well as writes, and bound what a request may send and
how long it may take. Until code a model writes runs contained, it is refused beside a mounted
instance. On the reading side, the MCP server lists the register (`register_nodes`), climbs from a
key, a code file or a document back to the register (`key_nodes`, `code_path`, `document_links`),
reads what the store holds and what was built on it (`held_keys`, `derived_outputs`,
`document_statements`), and names the down, up, store and intake sequences in its instructions.
`proposal_impact` groups a proposed addition into slices along the register's own thread walk. A
subject wizard (two prompts and a Claude Code skill), `subject_check` in the call and a franker
subject check make onboarding a subject an assistant's procedure, ending in a pull request a person
reviews.

### Contract changes (why this is 0.7.0, decision-0003)

- **Both servers bound what a request may cost** (task-0141.04). The framing is checked before any
  of the body is read:
  - one `Content-Length` of digits, else 400;
  - none, or a `Transfer-Encoding`, 411;
  - a `Content-Encoding`, or a `Content-Type` other than JSON, 415;
  - above the body limit, 413.

  A request must arrive whole within an absolute deadline, however slowly it is sent; an idle
  timeout also bounds each silent wait. At most a fixed number of connections are served at once,
  and the next is answered 503 with `Retry-After`, with no thread started. The limits: the page's
  `KG_PAGE_MAX_BODY` (64 KiB), `KG_PAGE_READ_TIMEOUT` (10 s), `KG_PAGE_IDLE_TIMEOUT` (5 s) and
  `KG_PAGE_MAX_CONNECTIONS` (32); the MCP server's `KG_MCP_*` likewise, with a 4 MiB body for
  `subject_check`. A page body must be a JSON object with typed fields. A run's `n` must be an integer
  from 1 to `KG_PAGE_MAX_RUNS` (5, the record's count). Compatibility: `true`, `2.5` and `"3"` were
  coerced before and are now refused (400), as is any `n` above the maximum, which before was
  unbounded. Before, a negative or unfinished `Content-Length` held a worker indefinitely, a
  non-numeric one dropped the connection, and connections were unbounded.

- **`held_keys`, `derived_outputs` and `document_statements`, three new read-only MCP tools, on three
  new reads of the store port** (task-0144, doc-0020 C3, additive). The port gains `held_keys`,
  `derived_outputs` and `artefact_assertions`, on Neo4j and rdflib, in `store.READS`, answering by id
  (`store.by_id`).
  - `held_keys`: every key the held scenario holds, with its count by status, its level as
    `gate_verdict` reads that key set, the task classes requiring it (a key no class asks for, which
    `store_status` never showed, reads `required_by: []`) and the required keys it lacks.
  - `derived_outputs`: with `key`, every derived output built on it, any state; with `derived`, that
    one. Each used statement reads `live`, `stale`, `superseded` (with `superseded_by`) or `rejected`.
  - `document_statements`: the statements a document yields, by version, and the outputs built on them.
  - One read handle per call; refused mid-run and on another subject's scenario. Listed on stdio and
    HTTP. Schemas `held-keys`, `derived-outputs`, `document-statements`, version 1;
    `check_mcp_server.py` holds each equal to the port's read, `check_round_trip.py` across store kinds.

- **Both servers check the request's authority and origin on every request** (task-0141.03). A
  request whose Host names an authority the server does not answer for gets 421, and a malformed or
  repeated Host 400. An Origin that is not one of the server's own gets 403, `null` included, on
  reads as well as writes. Each check stands on its own and apart from the bearer token. The page
  answers for the loopback names and `KG_DEMO_HOST` on its published port (compose passes
  `KG_PORT_APP` as `KG_PUBLIC_PORT`), plus `KG_PAGE_AUTHORITIES`. Its origins are those authorities
  over `http://`, plus `KG_PAGE_ORIGINS`. The impact guides also admit Neo4j Browser's origin
  (`KG_BROWSER_URL`). The MCP server answers for the loopback names on its port, or its bind
  address, plus `KG_MCP_AUTHORITIES` and `KG_MCP_ORIGINS`. Forwarded headers are never read: behind
  a proxy, list the public authority and its `https://` origin. Before, the page compared Origin
  with the request's own Host, so a rebound name sending both passed. The MCP server took any
  loopback origin on any port. Compatibility: the MCP Inspector (`http://localhost:6274`) now needs
  `KG_MCP_ORIGINS=http://localhost:6274`. A client reaching the page by a name other than
  `localhost`, `127.0.0.1`, `[::1]` or `KG_DEMO_HOST` needs it in `KG_PAGE_AUTHORITIES`.

- **`proposal_impact`'s report gains a slice map** (task-0152, doc-0022 K1, additive: `slices`,
  required, in `harness/schemas/proposal-impact.schema.json`, version 1). One vertical slice per
  approved journey step of each product the proposal touches, or per delivering process for a
  product no journey concerns: the register's own thread walk (ieam-register decision 0018, at
  v0.2.11) from step to process, capability, application and information, each node new, reused or
  changed, with its owner, the layers the thread leaves empty and the edges it reports withdrawn.
  The capabilities a product requires and no slice reaches are the register's rule A1. Every
  overlay node, link and exception sits in exactly one slice or one named remainder (shared,
  required_not_reached, frame, exceptions, outside), with the denominator. Facts only: no label,
  estimate or rank. The CLI's text output and the MCP tool give the same section.

- **The store port names its access; a read never publishes** (task-0141.02). `open_store()` takes
  `access="read"` or `access="write"`. A read handle lets through the port's reads (`store.READS`)
  and refuses any other operation with `StoreReadOnly`. A write handle publishes on `commit()`,
  which the context manager calls when its block ends cleanly, and never on `close()`, which now
  only releases it. With `KG_RDFLIB_FILE`, a writer locks `<file>.lock` before it loads, waits at most
  `KG_RDFLIB_LOCK_TIMEOUT` seconds (default 60) for another writer, then fails with `StoreBusy`. It
  publishes through a synced temporary file and an atomic replacement. A file that does not parse
  fails with `StoreCorrupt` and is left as it is. Before, closing any handle, a read included,
  serialised its snapshot over the file. A page or MCP read could restore an older store over a
  newer run, and two writers could lose an update. Neo4j read handles run in read access mode.
  Supported for a file-backed writer: POSIX with `flock`.

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

- **The MCP server's instructions name the intake sequence** (task-0156, doc-0022 K5). Beside the down and
  up sequences, on both transports: `proposal_impact` on a proposed initiative, its `slices` as the story
  map's backbone, then `gate_verdict` per slice's keys under one task class and one `as_of`. They say
  knowgov writes no work item and ranks nothing, and that a backlog coverage check is parked to the
  pilot. Text only; no tool or schema changes.

- **Arms runs refuse beside a mounted instance until X1** (task-0141.07, a stopgap). Code a model
  writes still runs uncontained, with the process's environment and files; task-0141.05 contains it.
  Until then, when `KG_SUBJECT`, `KG_SUBJECTS` or `KG_REGISTER` names a folder outside the knowgov
  checkout, as `docker-compose.instance.yml` sets them, every path that runs model output refuses.
  Those paths are the single-reply grading, the agent's feedback suite and its final grading.
  `run.py` exits 2 before its first model call, and the page refuses to start an arms run.
  `KG_ALLOW_UNCONTAINED_EXECUTION=1` lifts the refusal and accepts the risk. The public demo runs
  as before. Do not set a model key where an organisation's data is mounted. For the public demo,
  use a project key with a spending cap.

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
- **The register at ieam-register v0.2.11** (the register's decision 0018). The vendored
  `impact.py` gains a third named walk, `--walk thread`, from a journey step down to the data it
  uses. The checker gains A1, a warning when a product's `requires` links and the capabilities its
  journeys' steps reach disagree. The register view lists 10 warnings, 7 before plus A1's three
  (PRD-0002, PRD-0004, PRD-0005), with no coverage line for A1, which is not a coverage rule.
  `proposal_impact`'s `slices` (task-0152) reads it; knowgov composes no walk of its own.

### What this release carries

| what | version |
|---|---|
| pumllint (the sequence-diagram mapper's parser) | 0.33.0, from PyPI |
| the IEAM register, vendored under `demo/register/` | ieam-register `v0.2.11` |
| the record's pins | unchanged from 0.6.0 |
| Python | 3.12 in the image |

The image is `ghcr.io/fdurieux/knowgov:v0.7.0`. The compose file moves to it in a follow-up, once
the Release has published its digest.

### Known limits

- Code a model writes is not yet contained (task-0141.05, decision-0012). The guard refuses it beside
  a mounted instance or register; with `KG_ALLOW_UNCONTAINED_EXECUTION=1`, or on the public demo, it
  still runs with the process's environment and files.
- A load is not yet published whole on Neo4j (task-0141.06): the adapter writes each statement as it
  runs, so a reader can see a store part-way through a rebuild. The MCP tools that read knowledge
  refuse while a run is loading.
- A file-backed store supports its writers on POSIX with `flock`, on a local disk.
- Response sizes are not capped by the HTTP limits; request framing, bodies, deadlines and
  connections are.
- Claude Desktop's role is asking the gate until the maintainer's own test shows the prompts listed
  there and `subject_check` running; onboarding is Claude Code's.
- A proposal's slices are as fine as the register's links: steps supported only by one end-to-end
  process share one thread.
- An attestation is the manifest's declaration and is not bound to a document's version.
- A run folder from before `run.json` is inferred: its status, start and initiator are unknown.
- `proposal_impact`'s branch mode reads a branch's additions only.
- The subject check compares keys with the documents' yield only where the mappers run.
- The connector has run only on the synthetic CargoQuote export, not on a real installation.
- A register change is read only when the gate is given the previous register; the page's register
  panel does not show what a change withdrew yet.
- The GitLab include is proven by shell, not yet on a GitLab runner (task-0108).
- The hooks see Edit and Write, not a shell command writing the same file.

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
