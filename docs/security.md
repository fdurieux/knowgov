# knowgov's security description

This document is for a reviewer whose organisation has been asked to let knowgov near its systems:
a procurement or security team, or the architect who answers to one. It says what a private
instance reads, what it stores and what it sends, and where each of those goes. It says what
leaves the organisation's network under each model-endpoint setting, how the dependencies are
pinned and kept current, and who may do what.

Each claim names its evidence. That is either a test (`tests/<file>.py::<test>`, run by
`python tests/run_tests.py`), a CI step, or the word **Practice**. Practice means the code does not
enforce the claim and the operator must. Where this document found that the code does not hold
something an adopter might assume, it says so under [Gaps](#gaps-what-the-code-does-not-enforce).
`tests/test_security.py` holds the document to the code. Every test it cites must exist, every
row must name its evidence, and the gaps listed here must still be the code's. When one is fixed,
that test fails until this document is updated.

The vulnerability-reporting route is in [`SECURITY.md`](../SECURITY.md).

## The parts and where they run

A private instance runs on the organisation's own machines, from a folder inside the organisation's
own repositories (`instance/README.md`). The parts are:

- **the harness** (`harness/`): reads documents, extracts statements, loads them into the store,
  and runs the gate;
- **the store**: Neo4j in a container (`KG_STORE=neo4j`, the default), or an rdflib graph held in
  memory and optionally saved to the file `KG_RDFLIB_FILE` (`KG_STORE=rdflib`);
- **the page** (`demo/app/server.py`), the web view;
- **the MCP server** (`harness/mcp_server.py`), the read-only interface an AI assistant uses;
- **the gate command** (`harness/gate_cli.py`) and **knowgov-trace** (`harness/trace.py`), run
  from the instance's CI (`instance/ci/`);
- **optionally a model endpoint**, used only by the arms (the measured comparison runs) and by the
  transcript route.

No knowgov service is hosted by the maintainer. Nothing in the code reports to this repository or
to anyone else.

## Data flows

### What is read

| Flow | Where it goes | Enforced by | Evidence |
|---|---|---|---|
| The instance folder (documents and the register checkout) is mounted into the app container read-only | the app container, at `/instance` | `demo/docker-compose.instance.yml` (`:/instance:ro`) | `tests/test_demo.py::test_compose_files_agree`; CI: `demo.yml` mounts the example instance, fails if `touch /instance/probe` succeeds, and compares its digest before and after |
| The harness reads the instance and writes nothing into it | inside the process | `harness/load.py`, `tools/check_instance.py` | `tests/test_instance.py::test_the_example_instance_holds_and_its_sources_are_untouched`; CI: `harness.yml` digests the example instance before and after S1–S7 |
| The register is read from `KG_REGISTER`. The page's projection of it goes into the store under its own `Reg` labels and never touches a harness label; a run wipes it | the store | `demo/app/register_project.py`, `harness/store_neo4j.py` `project_register` | `tests/test_register_view.py::test_register_root_comes_from_the_environment_and_a_checkout_has_no_note`, `tests/test_register_view.py::test_projection_rows_and_statements` |
| The pre-load linters run in the instance's own CI, on the instance's documents | the instance's CI runner | `instance/ci/preload-check.yml`, `tools/preload_check.py` | `tests/test_preload.py::test_every_runner_names_the_tool_its_kind_names_and_the_ci_template_runs_the_script` |

### What is stored

| Flow | Where it goes | Enforced by | Evidence |
|---|---|---|---|
| For each document version: its path, kind, a SHA-256 digest and its size in bytes, never the whole text | the store | `harness/load.py` (`upsert_artefact_version`), the port `harness/store.py` | `tests/test_security.py::test_the_store_gets_a_documents_digest_and_size_never_its_text` |
| For each statement: the **excerpt** it was read from (the fragment's text and digest), the value and a one-line text of the statement, its status, its basis, the activity and agent that produced it, and its verifications. The store holds status and provenance and these excerpts. It does not hold whole documents. | the store | `harness/load.py` (`create_fragment`, `create_assertion`) | `tests/test_security.py::test_the_store_gets_a_documents_digest_and_size_never_its_text` (it also holds that excerpts are stored, so this row stays true) |
| A person's answer is stored as their handle, the date, the value and their note | the store, and the capture file in the instance | `harness/load.py` (`load_captures`), `harness/capture.py` | `tests/test_capture.py::test_an_answered_questionnaire_is_normalised_with_the_registers_three_fields` |
| The Neo4j store lives in the `neo4j-data` volume on the host; the rdflib store lives in memory, or in `KG_RDFLIB_FILE` when set | the host's disk | `demo/docker-compose.yml`, `harness/store_rdflib.py` | `tests/test_store.py::test_the_rdflib_adapter_speaks_no_cypher_and_the_port_names_both` |
| A run's outputs (reports, and the prompts and bundles an arm sent) are written under `runs/`, which git ignores, or under the `demo-runs` volume | the host's disk | `.gitignore`, `harness/run.py` | `tests/test_security.py::test_runs_are_ignored_by_git_and_security_md_points_here` |
| The transcript route keeps the transcript's SHA-256, the model and the date, never the transcript | the instance's capture folder, `inferred/` | `harness/transcript.py` | `tests/test_transcript.py::test_the_file_keeps_the_digest_and_never_the_transcript` |
| knowgov-trace keeps a JSON ledger of the files it registered as derived outputs, beside the store | the path the caller names | `harness/trace.py` (`register`) | `tests/test_trace.py::test_register_records_the_file_its_app_and_the_statements_and_supersedes_by_path` |

The file-backed store's integrity (task-0141.02): every caller opens the store for `read` or
`write`. A read handle refuses every change and never publishes, so the page and the MCP server
cannot write a stale snapshot back over a newer one. A writer takes an exclusive lock on
`KG_RDFLIB_FILE.lock` before it loads the snapshot it starts from, so a second writer waits (at most
`KG_RDFLIB_LOCK_TIMEOUT` seconds, default 60, then cannot run) and starts from the first one's
publication. It publishes only on commit, through a synced temporary file in the same directory and
an atomic replacement. A failure or an exception publishes nothing and releases the lock. A file that
does not parse is reported and left as it is, never read as an empty store. Supported on POSIX
filesystems with `flock` (Linux, macOS), on a local disk; a platform without it refuses a writer.

Store generations (task-0141.06, decision-0014): on both stores a writer builds its unit privately and
publishes it whole, and a read answers from one published generation or refuses.
- **rdflib.** The lock above, held from load to the atomic replacement. A reader keeps the snapshot it
  loaded for as long as it is open. A writer publishes only while the lock file at the path is still
  the one it locked, so a writer whose lock was cleared publishes nothing.
- **Neo4j.** A writer holds a lease in the database, a `_KgPublication` node outside every evidence
  label, from open to close: `KG_NEO4J_LEASE_SECONDS` long (default 60), renewed while it runs. A
  second writer waits `KG_NEO4J_LOCK_TIMEOUT` seconds (default 60), then cannot run. The writer's whole
  unit, the wipe, the load, the rules and the reviews, is one transaction, so nothing of it is visible
  before it commits and a failure leaves nothing behind.
  - It publishes under a sequence lock: a counter raised in its own transaction before the unit
    commits, and matched inside it.
  - A read handle pins the counter when it opens and checks it after every read. A publication during
    a read refuses it (`StoreChanged`); the page and the MCP server read again, up to
    `KG_STORE_READ_ATTEMPTS` times (default 3).
  - A writer whose lease ran out cannot publish: its epoch is gone, and the writer that took the lease
    over terminates its transaction. Recovery is automatic.
  - Supported on Neo4j 5 Community with one database; nothing assumes a second database.
- **Retirement.** Neo4j keeps no earlier generation: a reader open across a publication is refused,
  never answered from a retired one. A writer killed between raising the counter and committing makes
  reads wait up to `KG_NEO4J_READ_WAIT` seconds (default 10), then refuse, until the next writer takes
  the lease.
- **Coordination.** The page decides a register projection under the same lock that starts a run, and
  a projection that finds another writer holding the store answers 409.
- **When the retries run out.** A reader that meets a publication on every attempt, or a writer's
  publication interrupted past `KG_NEO4J_READ_WAIT`, answers a refusal, never a mixed result:
  - `gate_cli --no-load` exits 2, "cannot run";
  - the MCP server answers an error result naming the republished store;
  - the page's `/api/store` and `/api/gaps` answer 503 with `Retry-After: 1` and `"busy": true`;
  - `/api/scenarios`, which the page boots from, keeps 200 and carries the same `busy` and `error` in
    its `store`.
- **Settings.** Each is a number within bounds, and anything else is refused with the variable's name:
  - `KG_STORE_READ_ATTEMPTS`: a whole number, 1 to 10;
  - `KG_NEO4J_LEASE_SECONDS`: 1 to 3600, with a heartbeat every third of it;
  - `KG_NEO4J_LOCK_TIMEOUT`: 0 to 86400;
  - `KG_NEO4J_READ_WAIT`: 0 to 600.
- **Transaction memory bounds a Neo4j unit.** A writer's whole unit is one transaction, so the
  server's transaction memory limits a load.
  - The bounds: `db.memory.transaction.max` per transaction (unset, so unlimited on its own) and
    `db.memory.transaction.total.max` (by default 70% of the heap; the compose heap is 1 GiB).
  - Measured peaks of the estimated heap: CargoQuote's whole seven-scenario deterministic run about
    41 MiB; J-F's whole run about 64 MiB.
  - A unit over the limit fails with `MemoryPoolOutOfMemoryError` and publishes nothing; the previous
    generation is read whole. `tools/check_snapshots.py --memory-limited` checks this on a server
    started with a small `db.memory.transaction.max`, and passed with 2 MiB.
  - **Practice:** size the heap for an instance whose documents are much larger.
- **The server-side fence.** It was seen working on Neo4j 5.26 Community: right after a takeover, the
  former owner's unit transaction reads `Terminated` in `SHOW TRANSACTIONS`, and its commit raises
  `StoreFenced` (SNAP-05).

| Property | Evidence |
|---|---|
| A reader's close never publishes, so a newer write survives it | `tests/test_store_persistence.py::test_st_01_closing_a_stale_reader_cannot_restore_its_snapshot_over_a_newer_write`, `tests/test_store_persistence.py::test_st_02_the_page_and_the_mcp_server_read_and_never_publish` |
| A read handle refuses every change | `tests/test_store_persistence.py::test_st_03_a_read_handle_refuses_every_change_and_the_file_is_untouched` |
| Writers are serialised from load to publication; no update is lost | `tests/test_store_persistence.py::test_st_04_a_second_writer_waits_for_the_first_and_starts_from_its_publication` |
| A reader sees the whole old file or the whole new one; a failure keeps the old file | `tests/test_store_persistence.py::test_st_05_a_reader_during_a_publication_gets_the_whole_old_file_or_the_whole_new_one`, `tests/test_store_persistence.py::test_st_06_a_failed_serialisation_sync_or_replacement_keeps_the_previous_file_and_releases_the_lock`, `tests/test_store_persistence.py::test_st_07_a_writer_that_raises_publishes_nothing` |
| A killed writer leaves the last publication and a recoverable lock; a corrupt file fails explicitly | `tests/test_store_persistence.py::test_st_08_a_writer_killed_before_publication_leaves_the_last_snapshot_and_a_recoverable_lock`, `tests/test_store_persistence.py::test_st_09_a_corrupt_file_fails_explicitly_and_is_never_replaced` |
| A read answers from one published generation or refuses, on both stores; a half-staged load, a killed or failed publication, racing writers and a recovered lease never show a partial or mixed graph (SNAP-01 to SNAP-07) | CI: `tools/check_snapshots.py` in `harness.yml` (rdflib) and `demo.yml` (Neo4j); `tests/test_store_generations.py::test_a_read_handle_refuses_the_read_after_a_publication_and_never_answers_from_two_generations`, `tests/test_store_generations.py::test_snap_05_a_file_writer_whose_lock_file_was_replaced_publishes_nothing` |

Because the store holds excerpts, treat it, its volume, `KG_RDFLIB_FILE` and `runs/` as being
as sensitive as the documents they came from. **Practice:** keep them on the instance's
machines, under the same access controls as the documents, and delete them when the pilot ends.

### What is sent

| Flow | Where it goes | Enforced by | Evidence |
|---|---|---|---|
| Nothing is sent to a model until the named key variable holds a value (and the subject declares an oracle) | nowhere | `harness/arms.py` `endpoint()`, `enabled()` | `tests/test_arms.py::test_defaults_are_openai_and_the_records_model_and_arms_are_off_without_a_key`, `tests/test_arms.py::test_a_private_gateway_without_its_key_is_off_even_with_an_openai_key_present` |
| The model client is imported only when a call is made | — | `harness/arms.py` `call()` | `tests/test_arms.py::test_the_client_is_imported_only_when_a_call_is_made` |
| With a key, the baseline arm sends the task prompt and the **whole text** of the subject's documents | `KG_MODEL_BASE_URL` (default `https://api.openai.com/v1`) | `harness/run.py`, `harness/arms.py` `baseline_documents` | `tests/test_security.py::test_the_baseline_arm_sends_whole_documents` |
| With a key, the governed arm sends the task prompt and the evidence bundle: statements, values, excerpts, gaps, and the documents the task names, word for word | `KG_MODEL_BASE_URL` | `harness/gate.py` `render_bundle` | `tests/test_arms.py::test_bundle_carries_the_documents_the_task_names_verbatim_after_the_knowledge` |
| With a key, the agent arm sends the same, and the model's tool calls write files into the run's folder only and run the subject's own test suite there | `KG_MODEL_BASE_URL`; the run folder | `harness/agent.py` (the safe-path check) | `tests/test_agent.py::test_safe_rel_and_the_tools_are_what_the_prompt_says` |
| With a key, the transcript route sends the transcript's text and the keys asked about; without one it exits 2 | `KG_MODEL_BASE_URL` | `harness/transcript.py` | `tests/test_transcript.py::test_with_no_model_key_it_refuses_with_exit_2` |
| The key is passed through the environment, never written into the image or the models table; the page names the variable, never the key | — | `demo/docker-compose.yml`, `demo/models.toml` | `tests/test_demo.py::test_compose_files_agree`, `tests/test_demo.py::test_models_table_rows_resolve_to_the_harness_variables_and_never_carry_a_key`, `tests/test_arms.py::test_the_page_names_the_endpoint_and_the_key_variable_never_the_key` |
| With a key set, the page checks it when it starts (and on a re-check) by asking the row's own endpoint for its model listing, `GET {base_url}/models`, through the model client: no prompt, no document, no tokens. Only the verdict (accepted, refused, unreachable, unchecked), the HTTP status, the time and the listed model names are kept; never the key, never the provider's message (OpenAI's 401 quotes part of the key). The cache is keyed by an HMAC of the key under a secret drawn for the process. A refused row is unavailable, so a run on it is refused before anything is sent. `KG_KEY_CHECK=off` sends nothing (task-0171) | each row's `base_url`, the endpoint its runs call | `harness/key_check.py` (`probe`, `Checker`), `demo/app/server.py` `check_keys`, `demo/app/models.py` `rows` | `tests/test_key_check.py::test_the_check_is_the_model_clients_listing_and_nothing_else`, `tests/test_key_check.py::test_no_key_and_no_provider_message_leaves_the_check`, `tests/test_security.py::test_nothing_reaches_the_network_but_the_model_client_and_the_store_driver` |
| No module of the harness, the page or the tools opens any other outbound connection: the model client and the Neo4j driver are the only clients (the model client's key check, `harness/key_check.py`, included: it asks the row's own endpoint for its listing; apart from two checks that ask only a local server: `demo/tools/check_impact_cypher.py`, the stack job's page, and `tools/check_mcp_server.py`'s HTTP client, the MCP server it started on loopback; and the worker's attestation probe, `harness/worker.py` `sockets`, which tries `192.0.2.1:9`, TEST-NET-1 and never routed, to prove that it cannot connect), and the page loads no script or style from elsewhere | — | the imports of `harness/`, `demo/app/`, `tools/` | `tests/test_security.py::test_nothing_reaches_the_network_but_the_model_client_and_the_store_driver` |
| The page, Neo4j Browser and bolt are published on `127.0.0.1` unless `KG_BIND` widens the bind; on a wider bind the stack refuses to start while the Neo4j password is the default | this machine only, by default | `demo/docker-compose.yml` (`${KG_BIND:-127.0.0.1}` on every published port), `demo/neo4j/bind-guard.sh` | `tests/test_demo.py::test_the_ports_bind_loopback_and_a_wider_bind_refuses_the_default_password`; CI: `demo.yml` reaches the stack on `localhost` from the runner |
| Every request to the page or the MCP server names, in its Host, an authority the server answers for (from its configuration and listener, never the request: 421 otherwise), and an Origin, when sent, is one of the server's own (403 otherwise); each is checked on its own and apart from the token, and forwarded headers are never read (task-0141.03) | the configured authorities only | `harness/http_boundary.py`, `demo/app/server.py` `page_policy` and `Handler._boundary`, `harness/mcp_server.py` `http_policy` and `Handler._guard` | `tests/test_http_boundary.py::test_http_01_a_foreign_host_with_a_matching_foreign_origin_changes_nothing`, `tests/test_http_boundary.py::test_http_03_scheme_port_opaque_malformed_duplicate_and_deceptive_values_are_refused`, `tests/test_http_boundary.py::test_http_05_the_token_and_the_authority_are_independent_and_the_token_never_echoed`, `tests/test_http_boundary.py::test_http_06_forwarded_headers_never_stand_in_for_the_host` |
| Both servers bound what a request may cost (task-0141.04): its framing is checked before a byte of the body is read (one Content-Length of digits, else 400; none, or a transfer encoding, 411; a content encoding or a type other than JSON, 415; above the body limit, 413), it must arrive whole within an absolute deadline however it is paced, the connections served at once are capped (more get 503 with Retry-After, no thread started), a page body is a JSON object with typed fields, and a run's `n` an integer from 1 to `KG_PAGE_MAX_RUNS` (5) | each server's own limits | `harness/http_boundary.py` (`Limits`, `read_body`, `BoundedServer`, `BoundedMixin`), `demo/app/server.py` `page_limits` and `run_request`, `harness/mcp_server.py` `mcp_limits` | `tests/test_http_limits.py::test_limit_01_framing_is_checked_before_a_byte_of_the_body_is_read`, `tests/test_http_limits.py::test_limit_04_a_body_that_never_completes_or_trickles_is_cut_at_the_absolute_deadline`, `tests/test_http_limits.py::test_limit_05_connections_over_capacity_get_503_without_a_thread_and_recover` |
| The page's state-changing requests (a run, which reloads the store and may call the model, and the register's projection) are refused from another web origin; with `KG_PAGE_TOKEN` set each must carry it as a bearer token; without it, a page published beyond this machine refuses them. Its read-only requests stay open | this machine only, unless `KG_BIND` widens the bind and the token is set | `demo/app/server.py` `write_guard`, `demo/docker-compose.yml` (passes `KG_BIND` and `KG_PAGE_TOKEN` to the app) | `tests/test_security.py::test_the_pages_writes_need_its_token_and_a_wider_bind_without_one_refuses_them`, `tests/test_security.py::test_the_page_sends_its_token_and_the_stack_passes_the_bind_and_the_token`; CI: `demo.yml` starts runs on `localhost` with no token |
| The MCP server listens on 127.0.0.1 by default, refuses a wider bind without `KG_MCP_TOKEN`, then asks every request for that token, and refuses a request naming another authority or coming from another web origin; the MCP Inspector's origin (`http://localhost:6274`) is admitted only when `KG_MCP_ORIGINS` names it | the assistant's process on the same machine (stdio), or a client on the network holding the token | `harness/mcp_server.py` `bind_check`, `Handler._guard` | `tests/test_mcp_server.py::test_it_binds_localhost_unless_told_and_a_wider_bind_needs_a_token`, `tests/test_mcp_server.py::test_http_with_a_token_refuses_a_request_without_it`, `tests/test_mcp_server.py::test_http_answers_on_mcp_refuses_a_foreign_origin_and_pushes_nothing` |
| The MCP server answers with the gate's verdict, the three-valued answer, the evidence bundle, the register impact walk with its keys and a proposal read as if approved (nothing stored). The bundle carries excerpts, so whoever holds the token reads them | the MCP client | `harness/mcp_server.py` `TOOLS` | `tests/test_mcp_server.py::test_every_tool_listed_and_marked_read_only` |
| People appear as opaque handles issued by the register, never as names or e-mail addresses | the store, the capture and review files | `harness/capture.py` (handle pattern, issued list), `harness/review.py` `check` (ieam-register decision 0009) | `tests/test_capture.py::test_a_name_a_future_date_a_contradiction_or_nothing_answered_is_refused`, `tests/test_capture.py::test_ingest_refuses_a_handle_the_register_has_not_issued_by_the_answers_date`, `tests/test_capture.py::test_ingest_refuses_a_handle_without_gives`, `tests/test_review.py::test_refused_the_giver_a_handle_without_approves_a_name_and_a_future_date` |
| A note in an answer must not identify the person: the questionnaire says so, and the reviewer sees each note before ruling | the capture file | `harness/capture.py` | `tests/test_capture.py::test_the_questionnaire_warns_that_a_note_must_not_identify_the_person`; **Practice:** the code warns and does not check the note's words |
| The instance is created in the organisation's repositories and is never pushed to this one | — | — | **Practice.** CI here runs only the public example instance built by `tools/example_instance.py`; nothing in this repository fetches or uploads an instance |

The handle check is a pattern (`^[a-z][a-z0-9-]{1,39}$` by default, or the register's own) and,
once the register lists issued handles, membership of that list, in date, with the role `gives`
(task-0091). A lowercase handle that happens to be a person's name (`jdoe`) passes the pattern. **Practice:** the register issues opaque
handles (`employee-1`, not initials), as ieam-register decision 0009 asks.

## What leaves the network, per model-endpoint setting

The table covers the running stack. Building or pulling the image fetches packages and base images
from PyPI, npm, Docker Hub and ghcr.io. That happens at build time and carries no instance content.

| Setting | What leaves the organisation's network | Evidence |
|---|---|---|
| **No key** (the named variable empty; the default, and every CI run here) | Nothing. The harness, the page and the MCP server talk only to the store, inside the compose network or on the same machine | `tests/test_arms.py::test_defaults_are_openai_and_the_records_model_and_arms_are_off_without_a_key`, `tests/test_security.py::test_nothing_reaches_the_network_but_the_model_client_and_the_store_driver` |
| **A key, `KG_MODEL_BASE_URL` unset** | Prompts, whole documents (baseline arm), evidence bundles with excerpts and named documents (governed arm), and transcripts (transcript route) go to `api.openai.com` | `tests/test_arms.py::test_openai_case_needs_only_the_key` |
| **A key and a hosted compatible endpoint** (for example Google's, `demo/models.toml`) | The same content goes to that provider's host | `tests/test_arms.py::test_a_compatible_endpoint_with_its_own_key_variable_and_model` |
| **The Claude row** (`--profile claude`) | The same content goes from the app to the LiteLLM gateway inside the stack, and from there to Anthropic. The gateway starts only with its profile, is pinned by digest, and fetches no price list at start | `tests/test_demo.py::test_the_claude_row_goes_through_a_pinned_gateway_started_only_by_its_profile` |
| **A key and a private endpoint** (vLLM, Ollama, LiteLLM or a gateway inside the network) | Nothing, provided the endpoint is inside the network and itself forwards nothing | `tests/test_arms.py::test_a_compatible_endpoint_with_its_own_key_variable_and_model`; **Practice:** confirm where the endpoint's host resolves and what it forwards to |

The arms and the transcript route are optional. The gate, the MCP server, knowgov-trace and the
pre-load check never call a model. A pilot can run with no key at all.

## Dependencies and pins

| What | Pinned where | Pinned how | Evidence |
|---|---|---|---|
| Python packages of the image (pumllint 0.33.0, neo4j 6.4.1, pyyaml 6.0.3, rdflib 7.6.0, pyshacl 0.40.2, openai 3.41.0; the J-F oracle's pandas 3.0.5, numpy 2.4.6, requests 2.34.2, pyarrow 25.0.1, pytest 9.1.1, pytest-bdd 9.0.1) | `demo/Dockerfile`, `.github/workflows/harness.yml` | exact versions | `tests/test_demo.py::test_image_pins_the_versions_the_record_names` |
| The MCP server adds no package | `harness/mcp_server.py` | standard library only | `tests/test_demo.py::test_the_mcp_server_adds_no_dependency_to_the_image` |
| The pre-load linters (Spectral 6.17.0, markdownlint-cli2 0.24.0, gplint 2.6.1, bpmnlint 12.0.0, dmnlint 2.0.0, pumllint 0.33.0) | `instance/ci/preload-check.yml`, `.github/workflows/harness.yml` | exact versions, the same in both | `tests/test_preload.py::test_every_runner_names_the_tool_its_kind_names_and_the_ci_template_runs_the_script` |
| The LiteLLM gateway image | `demo/docker-compose.yml` | tag and SHA-256 digest | `tests/test_demo.py::test_the_claude_row_goes_through_a_pinned_gateway_started_only_by_its_profile` |
| The vendored register, the Legible model and the subjects' bytes | `demo/register/SOURCE.md`, `demo/model/SOURCE.md`, each subject's `vendor/SOURCE.md` | an upstream tag and a digest per file | `tests/test_demo.py::test_vendored_register_matches_its_source_note_and_checks_clean`, `tests/test_demo.py::test_vendored_model_matches_its_source_note`, `tests/test_vendor_subject.py::test_every_vendored_subject_matches_its_note` |
| GitHub Actions | `.github/workflows/`, `instance/ci/preload-check.yml` | by full commit SHA, the version in a comment, one SHA per action across every file | `tests/test_pins.py::test_every_remote_action_is_pinned_by_commit_sha_with_its_version`, `tests/test_pins.py::test_each_action_and_image_has_one_pin_everywhere` |
| The images: the base `python:3.12-slim`, `neo4j:5.26-community`, the app image (a release, `ghcr.io/fdurieux/knowgov:v0.8.0`), the LiteLLM gateway, and the GitLab template's `python:3.12` | `demo/Dockerfile`, `demo/docker-compose.yml`, `instance/ci/gitlab/knowgov.gitlab-ci.yml` | tag and SHA-256 index digest (`name:tag@sha256:…`) | `tests/test_pins.py::test_every_image_is_pinned_by_digest_with_its_tag`; **Practice:** an instance names the release it runs, as the compose file does |
| What Dependabot reads: the image's Python pins in `demo/requirements.txt`, the linters' in `instance/ci/package.json` | the two watch-lists; nothing installs from them | equal to the pins that install | `tests/test_pins.py::test_the_pip_watch_list_is_the_images_pins`, `tests/test_pins.py::test_the_npm_watch_list_is_the_linters_pins` |

**How the pins are kept current.** Dependabot (`.github/dependabot.yml`) proposes updates weekly
for pip, npm, Docker, Docker Compose and GitHub Actions (`tests/test_pins.py::test_dependabot_watches_the_four_ecosystems_weekly`).
The pins are of two kinds. **Tool pins** (the actions, the pre-load linters, the images and
pyyaml) move through these proposals: each is a pull request, merged as a pin change under the
tests above on a green matrix. A proposal moves one file: the watch-list, the Dockerfile, the
compose file or `.github/workflows/`. Where the same pin is in other files, the tests stay red
until a commit moves it there too (the CI template's actions, the template's and `harness.yml`'s
linters). **Record pins** (pumllint, neo4j, rdflib, pyshacl, openai, and the J-F oracle's pandas,
numpy, requests, pyarrow, pytest, pytest-bdd) are the versions the scored record and the J-F kit's
oracle name. They are frozen on purpose: Dependabot ignores them
(`tests/test_pins.py::test_dependabot_ignores_the_record_pins`), they are watched by hand, and one
moves only by a deliberate re-record, the comparator in the `stack` job and the oracle's 258 of 258
still passing. A routine bump can break the record (pytest 9.2.0 breaks pytest-bdd 9.0.x). The compose file's app image is a release: each release moves
it, and a merge to main does not. The vendored copies move only through `tools/vendor_register.py`,
`tools/vendor_legible_model.py` and `tools/vendor_subject.py`, at an upstream tag. Each release
(decision-0003) lists what moved in `CHANGELOG.md`.

**Reporting a vulnerability:** privately, as [`SECURITY.md`](../SECURITY.md) says.

## Who may do what

The six actions:

- **read** knowledge;
- **propose** a statement;
- **approve** a statement a person gave, or settle a dispute;
- **close** a declared gap;
- **edit the model**, meaning the register and its taxonomy, which the store and the gate take as given;
- **execute a business action**.

The actors are the ones doc-0013 P7 names, and one more the code shows must be named: anyone who
can reach the page.

<!-- permission matrix: begin -->
| Actor | Read | Propose | Approve | Close | Edit the model | Execute a business action |
|---|---|---|---|---|---|---|
| The model (arms, transcript route) | only what it is sent: documents, bundle, transcript | yes, as basis `inferred` at status `proposed`, only on keys with no value | no | no | no | no |
| An agent over MCP | the port's reads only (`READS` in `harness/mcp_server.py`) | no | no | no | no | no |
| The pipeline (load, `gate_cli`, knowgov-trace) | yes | yes: extracted and authored statements at `proposed`; trace records derived outputs | no | no | no | no |
| A person by role (decision-0002) | yes | yes, with `gives`, under an issued handle in date | with `approves`, in the owning unit, never their own answer | with `closes`, as the gap's owner | no | no |
| The register approver | yes | in ieam-register, not here | the register's own changes, upstream | no | yes, upstream in ieam-register; here only by re-vendoring a tag | no |
| Anyone who reaches the page's port (this machine only, unless `KG_BIND` widens it) | yes (see Gaps) | no | no | no | no | no; starts a run or a projection on this machine, and beyond it only with `KG_PAGE_TOKEN` |
<!-- permission matrix: end -->

"Execute a business action: none." knowgov reads documents and answers. It has no connector to
any operational system, and nothing in it acts on one. The agent arm's tools write files into the
run's own folder and run the subject's test suite there. That executes model-written code inside
the run folder, on the machine running the arm. It is not a business action. **Practice:** run the
arms only on a machine or container that holds nothing the run should not touch.

That code runs contained (task-0141.05, decision-0012). Every path that runs model output, the
single-reply grading, the agent's feedback suite and its final grading, goes through one route,
`harness/execution.py`, to the worker: a sibling container of the same image (`worker` in
`demo/docker-compose.yml`) with no network, a read-only root, no capabilities, no privilege escalation,
uid 65534, bounded memory, processes and CPU, and no secret in its environment. It sees only what ships
in the image and a jobs folder. Its work folder is a tmpfs mounted `exec`, since the oracle runs the launchers it
writes there; `noexec` would bound nothing, as a job can run any Python. Each job runs as its own process group with an allowlisted environment,
resource limits, a wall time (the whole group killed and reaped at it, a process that left the group
included), and Linux Landlock rules that let it write only beneath its own folder, so it cannot forge a
result or the worker's attestation. At start the worker attests its confinement (no interface but
loopback up, no route beyond it and no `CAP_NET_ADMIN` to bring one up, decision-0015; no AF_VSOCK or
AF_PACKET socket and no outside address reachable, which no network namespace confines and the engine's
default seccomp profile refuses; no secret-shaped variable, read-only root, uid 65534, no engine socket,
Landlock) and refuses to serve when any check fails; the app refuses a job without a fresh attestation, and reads the result as untrusted
data, capped and checked against its shape. The attestation also carries the worker's host as it reads it
inside its container (`os.uname()`'s system, kernel release and machine, and the engine by its marker file;
task-0169): facts, never a check, shown on the page's worker chip and in knowgov-runs' `run_options` only
from an attestation that holds, as untrusted strings (printable, capped). A cloud there is the app's reading
of the kernel release's suffix (`-aws` and the like), labelled as a reading; nothing asks a metadata
service, and the worker has no network to ask. Without a worker nothing runs: there is no fall back to
the host. The only escape is `KG_ALLOW_UNCONTAINED_EXECUTION=1`, which runs the code on the host,
uncontained, as before. With an organisation's instance mounted, the interim guard (task-0141.07,
`harness/execution_guard.py`) still refuses first: the worker sees only the public subjects. Supported:
Linux with Landlock (kernel 5.13 or later, enabled) and a container engine that runs the compose
service; elsewhere the worker refuses to serve and model output does not run. That sentence was the
fail-closed design, proven on GitHub's Ubuntu runners and a Linux kernel with Landlock only; the first
evidence on another engine is the maintainer's Mac (2026-11-06), below. The worker starts only
with `--profile arms` (decision-0015): the default `docker compose up` runs the rest of the stack, and
every arms run is refused. Docker Desktop for Mac 4.48.0's kernel (6.10.14-linuxkit) is built without
Landlock (`CONFIG_SECURITY_LANDLOCK` not set), so there the worker refuses to serve and exits 3; a later version may differ, unverified
(task-0162). The one machine besides CI where the worker has attested every check true is an EC2
`t3.large` on Ubuntu Server 24.04 LTS (x86_64) with Ubuntu's `docker.io` 29.1.3 and `docker-compose-v2`
2.40.3, kernel `7.0.0-1014-aws`, Landlock listed in `/sys/kernel/security/lsm` (2026-11-06, at `5ce8262`,
task-0162), and arms runs completed there the same day, on the Claude row and on the record's model (S1, the oracle's suite run in the worker, 11/11 for each arm); `demo/README.md` walks through it with the default `127.0.0.1` bind and an SSH tunnel. No other
host is claimed. On Docker Desktop, in the worker container under compose's settings, AF_VSOCK and AF_PACKET are refused
(EPERM) and an outside address is unreachable (ENETUNREACH). Evidence: `tests/test_worker.py` (the network
check on a fake sysfs and procfs, the Mac's listing included; the socket probes with stand-in sockets),
`tests/test_execution.py::test_exec_07_no_backend_refuses_and_never_falls_back_to_the_host`,
`tests/test_execution.py::test_exec_07_an_absent_stale_loosened_or_malformed_attestation_refuses_the_job`,
`tests/test_execution.py::test_a_job_cannot_write_the_jobs_folder_so_it_cannot_forge_a_result_or_the_attestation`,
`tests/test_execution.py::test_exec_04_a_symlink_at_any_step_of_an_agent_write_is_refused_and_the_target_untouched`,
`tests/test_execution.py::test_exec_08_a_stalled_or_trickling_stream_stops_at_the_monotonic_deadline`; on the real
container, `tools/check_worker.py` in `demo.yml` (EXEC-01 to EXEC-10, and loosened workers refusing: network on,
a key in its environment, and the seccomp profile off where the runner's kernel has vsock).
**Practice:** for the public demo, use a project key with a spending cap; keep the worker service as
compose defines it, since loosening it makes it refuse.

Evidence per row:

| Row | Evidence |
|---|---|
| The model proposes only, as `inferred`, only on empty keys | `tests/test_transcript.py::test_only_empty_keys_are_proposed_so_a_guess_never_lowers_what_the_documents_state`, `tests/test_transcript.py::test_both_adapters_take_a_candidate_for_nothing_and_ci_runs_the_route` |
| The model never verifies, approves or closes: a ruling needs an issued handle, and no verification reaches a model's statement | `tests/test_review.py::test_refused_the_giver_a_handle_without_approves_a_name_and_a_future_date`, `tests/test_capture.py::test_no_verification_reaches_a_captured_or_a_model_statement` |
| An agent over MCP reads only the port's reads and can write nothing | `tests/test_mcp_server.py::test_the_store_view_lets_through_reads_of_the_port_and_nothing_else`, `tests/test_mcp_server.py::test_the_server_opens_the_ports_read_handle_which_never_publishes`, `tests/test_mcp_server.py::test_every_tool_listed_and_marked_read_only`, `tests/test_mcp_server.py::test_the_scenario_must_be_the_one_the_store_holds_and_nothing_is_ever_loaded` |
| The pipeline proposes only; its gate never rules | `tests/test_gate_cli.py::test_every_record_scenario_gives_a_valid_report_and_the_contracts_exit_codes`, `tests/test_trace.py::test_register_refuses_an_unmapped_file_a_missing_map_and_no_statement` |
| `approves`: an issued, unwithdrawn handle of the owning unit, never the giver | `tests/test_review.py::test_another_handle_with_approves_of_an_owning_unit_approves_what_a_person_gave`, `tests/test_review.py::test_refused_the_giver_a_handle_without_approves_a_name_and_a_future_date`, `tests/test_review.py::test_a_withdrawn_handle_or_one_issued_after_the_review_is_refused`, `tests/test_review.py::test_a_unit_that_does_not_own_the_key_is_refused` |
| Overruling a document or settling a dispute needs `closes`, and a dispute is settled whole | `tests/test_review.py::test_overruling_a_document_needs_closes`, `tests/test_review.py::test_a_dispute_is_settled_only_whole_and_on_one_value` |
| `closes`: only the gap's owner | `tests/test_review.py::test_a_declared_gap_is_closed_only_by_its_owner` |
| An approval lapses six months after the capture | `tests/test_review.py::test_an_approval_of_what_a_person_gave_lapses_six_months_after_the_capture` |
| `gives`: an answer's handle is issued, not withdrawn by the answer's date, and holds `gives` (task-0091) | `tests/test_capture.py::test_ingest_refuses_a_handle_without_gives`, `tests/test_capture.py::test_ingest_refuses_a_handle_the_register_has_not_issued_by_the_answers_date` |
| The register is edited upstream only: here it is a vendored copy at a tag, held file by file to its digest, and the page reads it and never writes it | `tests/test_demo.py::test_vendored_register_matches_its_source_note_and_checks_clean`, `tests/test_vendor_register.py::test_vendor_register_refuses_a_dirty_tree_and_an_untagged_commit`, `tests/test_register_view.py::test_projection_rows_and_statements` |
| An instance's own register is mounted read-only | `tests/test_demo.py::test_compose_files_agree` |
| The page reads for anyone who reaches it; it starts a run or a projection beyond this machine only for a request carrying `KG_PAGE_TOKEN`, and never for another web origin | `tests/test_security.py::test_the_pages_writes_need_its_token_and_a_wider_bind_without_one_refuses_them` |
| No business action: no outbound client but the model's and the store's | `tests/test_security.py::test_nothing_reaches_the_network_but_the_model_client_and_the_store_driver` |
| Who may merge a change to this repository, or to an instance's | **Practice:** the repository's branch rules; in an instance, its own (an instance's CI runs the gate on every pull request, `instance/ci/`) |

## Gaps: what the code does not enforce

Each gap is stated so that nobody reads the tables above as claiming more than they do.
`tests/test_security.py::test_the_gaps_named_here_are_still_the_codes` fails when one is closed,
so this list is updated with the fix.

<!-- gaps: begin -->
1. **The page's reads have no login.** The compose stack publishes the page (8080), Neo4j Browser
   (7474) and bolt (7687) on `127.0.0.1` only, unless `KG_BIND` names a wider address (task-0090).
   Its writes are closed (task-0096): a run (`POST /api/run`, which reloads the store and, with a
   key set, calls the model at the organisation's cost) and the register's projection need
   `KG_PAGE_TOKEN` beyond this machine, and are refused from another web origin. Its reads are not:
   anyone who reaches the page reads everything it shows, excerpts included (Gap 2), as the demo
   is meant to be shown. On this machine a write needs no token, so every local user of the host
   can start a run; and on the default bind Neo4j's password may stay `kgpoc2026`, so every local
   user reaches the store. On a wider bind the stack refuses to start until `KG_NEO4J_PASSWORD` is set.
   **Practice:** widen the bind only behind a firewall, or a reverse proxy that authenticates,
   that admits the people who should read the page; set `KG_PAGE_TOKEN` and `KG_NEO4J_PASSWORD` on
   any host with other users; the page serves no TLS, so beyond a trusted network put it behind a
   proxy that does, or the token crosses the network in clear.
   **Wider bind and reverse proxy (task-0141.03).** The page answers only for the loopback names and
   `KG_DEMO_HOST` on the published port (`KG_PORT_APP`, passed as `KG_PUBLIC_PORT`), and the MCP server
   for the loopback names on its port, or its bind address; any other Host gets 421 before anything
   runs. Name the address people use in `KG_PAGE_AUTHORITIES` (or `KG_MCP_AUTHORITIES`), and, when
   it is served over TLS, its `https://` origin in `KG_PAGE_ORIGINS` (or `KG_MCP_ORIGINS`). Forwarded
   headers are never read: the proxy passes the public Host through unchanged (nginx:
   `proxy_set_header Host $host;`). Example, the page as `https://kg.example.org` behind nginx on 443:
   `KG_PAGE_AUTHORITIES=kg.example.org:443 KG_PAGE_ORIGINS=https://kg.example.org`. Neo4j Browser's
   origin (`KG_BROWSER_URL`) reads the impact guides and nothing else.
2. **The store holds excerpts.** "Status and provenance, never content" is true of whole documents
   only: fragments, statement values and their one-line texts are stored (see What is stored). This
   is by design, since the gate's evidence is the excerpt. An adopter must protect the store as they
   protect the documents.
<!-- gaps: end -->

## Operator practices, in one list

Collected from the rows above; each is the operator's to follow, because the code does not
enforce it:

- Create the instance in the organisation's own repositories, and never push it, its store, its
  `runs/` or its keys to this repository.
- Keep the store, its volume, `KG_RDFLIB_FILE` and `runs/` under the same access controls as the
  documents.
- Leave `KG_BIND` unset unless other machines must reach the page; when it is widened, set
  `KG_PAGE_TOKEN` so runs can start, admit only the people who should read the page, serve it over
  TLS beyond a trusted network, and set `KG_NEO4J_PASSWORD` on any shared host (Gap 1).
- Issue opaque handles, and keep names and identifying details out of answers' notes.
- Leave the model key unset unless the arms or the transcript route are wanted. When they are,
  choose the endpoint with the table above in mind, and confirm where a private endpoint forwards.
- Run the arms only where model-written code may run.
- Pin the app image to a release tag.
- Report vulnerabilities privately ([`SECURITY.md`](../SECURITY.md)).
