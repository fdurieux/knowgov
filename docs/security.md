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
| No module of the harness, the page or the tools opens any other outbound connection: the model client and the Neo4j driver are the only clients (apart from one stack-job check, `demo/tools/check_impact_cypher.py`, which asks the local page), and the page loads no script or style from elsewhere | — | the imports of `harness/`, `demo/app/`, `tools/` | `tests/test_security.py::test_nothing_reaches_the_network_but_the_model_client_and_the_store_driver` |
| The MCP server listens on 127.0.0.1 by default, refuses a wider bind without `KG_MCP_TOKEN`, then asks every request for that token, and refuses a request from a non-local web origin | the assistant's process on the same machine (stdio), or a client on the network holding the token | `harness/mcp_server.py` `bind_check`, `Handler._guard` | `tests/test_mcp_server.py::test_it_binds_localhost_unless_told_and_a_wider_bind_needs_a_token`, `tests/test_mcp_server.py::test_http_with_a_token_refuses_a_request_without_it`, `tests/test_mcp_server.py::test_http_answers_on_mcp_refuses_a_foreign_origin_and_pushes_nothing` |
| The MCP server answers with the gate's verdict, the three-valued answer and the evidence bundle. The bundle carries excerpts, so whoever holds the token reads them | the MCP client | `harness/mcp_server.py` `TOOLS` | `tests/test_mcp_server.py::test_four_tools_every_one_marked_read_only` |
| People appear as opaque handles issued by the register, never as names or e-mail addresses | the store, the capture and review files | `harness/capture.py` (handle pattern, issued list), `harness/review.py` `check` (ieam-register decision 0009) | `tests/test_capture.py::test_a_name_a_future_date_a_contradiction_or_nothing_answered_is_refused`, `tests/test_capture.py::test_ingest_refuses_a_handle_the_register_has_not_issued_by_the_answers_date`, `tests/test_review.py::test_refused_the_giver_a_handle_without_approves_a_name_and_a_future_date` |
| A note in an answer must not identify the person: the questionnaire says so, and the reviewer sees each note before ruling | the capture file | `harness/capture.py` | `tests/test_capture.py::test_the_questionnaire_warns_that_a_note_must_not_identify_the_person`; **Practice:** the code warns and does not check the note's words |
| The instance is created in the organisation's repositories and is never pushed to this one | — | — | **Practice.** CI here runs only the public example instance built by `tools/example_instance.py`; nothing in this repository fetches or uploads an instance |

The handle check is a pattern (`^[a-z][a-z0-9-]{1,39}$` by default, or the register's own) and,
once the register lists issued handles, membership of that list. A lowercase handle that happens
to be a person's name (`jdoe`) passes the pattern. **Practice:** the register issues opaque
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
| The images: the base `python:3.12-slim`, `neo4j:5.26-community`, the app image (a release, `ghcr.io/fdurieux/knowgov:v0.1.0`), the LiteLLM gateway, and the GitLab template's `python:3.12` | `demo/Dockerfile`, `demo/docker-compose.yml`, `instance/ci/gitlab/knowgov.gitlab-ci.yml` | tag and SHA-256 index digest (`name:tag@sha256:…`) | `tests/test_pins.py::test_every_image_is_pinned_by_digest_with_its_tag`; **Practice:** an instance names the release it runs, as the compose file does |
| What Dependabot reads: the image's Python pins in `demo/requirements.txt`, the linters' in `instance/ci/package.json` | the two watch-lists; nothing installs from them | equal to the pins that install | `tests/test_pins.py::test_the_pip_watch_list_is_the_images_pins`, `tests/test_pins.py::test_the_npm_watch_list_is_the_linters_pins` |

**How the pins are kept current.** Dependabot (`.github/dependabot.yml`) proposes updates weekly
for pip, npm, Docker, Docker Compose and GitHub Actions (`tests/test_pins.py::test_dependabot_watches_the_four_ecosystems_weekly`).
Each proposal is a pull request, merged as a pin change under the tests above, on the
maintainer's decision. A proposal moves one file: the watch-list, the Dockerfile, the compose file
or `.github/workflows/`. Where the same pin is in other files, the tests stay red until a commit
moves it there too (the CI template's actions, the Dockerfile's and `harness.yml`'s Python pins,
the template's and `harness.yml`'s linters). The image's Python pins are the versions the proof of
concept's record names, so moving one is a change to the record's environment, and the comparator
in the `stack` job must still pass. The compose file's app image is a release: each release moves
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
| A person by role (decision-0002) | yes | yes, with `gives` (an issued handle; see Gaps) | with `approves`, in the owning unit, never their own answer | with `closes`, as the gap's owner | no | no |
| The register approver | yes | in ieam-register, not here | the register's own changes, upstream | no | yes, upstream in ieam-register; here only by re-vendoring a tag | no |
| Anyone who reaches the page's port | yes | no | no | no | no | no; but may start a run (see Gaps) |
<!-- permission matrix: end -->

"Execute a business action: none." knowgov reads documents and answers. It has no connector to
any operational system, and nothing in it acts on one. The agent arm's tools write files into the
run's own folder and run the subject's test suite there. That executes model-written code inside
the run folder, on the machine running the arm. It is not a business action. **Practice:** run the
arms only on a machine or container that holds nothing the run should not touch.

Evidence per row:

| Row | Evidence |
|---|---|
| The model proposes only, as `inferred`, only on empty keys | `tests/test_transcript.py::test_only_empty_keys_are_proposed_so_a_guess_never_lowers_what_the_documents_state`, `tests/test_transcript.py::test_both_adapters_take_a_candidate_for_nothing_and_ci_runs_the_route` |
| The model never verifies, approves or closes: a ruling needs an issued handle, and no verification reaches a model's statement | `tests/test_review.py::test_refused_the_giver_a_handle_without_approves_a_name_and_a_future_date`, `tests/test_capture.py::test_no_verification_reaches_a_captured_or_a_model_statement` |
| An agent over MCP reads only the port's reads and can write nothing | `tests/test_mcp_server.py::test_the_store_view_lets_through_reads_of_the_port_and_nothing_else`, `tests/test_mcp_server.py::test_an_rdflib_file_is_read_and_never_written_back`, `tests/test_mcp_server.py::test_four_tools_every_one_marked_read_only`, `tests/test_mcp_server.py::test_the_scenario_must_be_the_one_the_store_holds_and_nothing_is_ever_loaded` |
| The pipeline proposes only; its gate never rules | `tests/test_gate_cli.py::test_every_record_scenario_gives_a_valid_report_and_the_contracts_exit_codes`, `tests/test_trace.py::test_register_refuses_an_unmapped_file_a_missing_map_and_no_statement` |
| `approves`: an issued, unwithdrawn handle of the owning unit, never the giver | `tests/test_review.py::test_another_handle_with_approves_of_an_owning_unit_approves_what_a_person_gave`, `tests/test_review.py::test_refused_the_giver_a_handle_without_approves_a_name_and_a_future_date`, `tests/test_review.py::test_a_withdrawn_handle_or_one_issued_after_the_review_is_refused`, `tests/test_review.py::test_a_unit_that_does_not_own_the_key_is_refused` |
| Overruling a document or settling a dispute needs `closes`, and a dispute is settled whole | `tests/test_review.py::test_overruling_a_document_needs_closes`, `tests/test_review.py::test_a_dispute_is_settled_only_whole_and_on_one_value` |
| `closes`: only the gap's owner | `tests/test_review.py::test_a_declared_gap_is_closed_only_by_its_owner` |
| An approval lapses six months after the capture | `tests/test_review.py::test_an_approval_of_what_a_person_gave_lapses_six_months_after_the_capture` |
| `gives` | not enforced: see Gaps |
| The register is edited upstream only: here it is a vendored copy at a tag, held file by file to its digest, and the page reads it and never writes it | `tests/test_demo.py::test_vendored_register_matches_its_source_note_and_checks_clean`, `tests/test_vendor_register.py::test_vendor_register_refuses_a_dirty_tree_and_an_untagged_commit`, `tests/test_register_view.py::test_projection_rows_and_statements` |
| An instance's own register is mounted read-only | `tests/test_demo.py::test_compose_files_agree` |
| No business action: no outbound client but the model's and the store's | `tests/test_security.py::test_nothing_reaches_the_network_but_the_model_client_and_the_store_driver` |
| Who may merge a change to this repository, or to an instance's | **Practice:** the repository's branch rules; in an instance, its own (an instance's CI runs the gate on every pull request, `instance/ci/`) |

## Gaps: what the code does not enforce

Each gap is stated so that nobody reads the tables above as claiming more than they do.
`tests/test_security.py::test_the_gaps_named_here_are_still_the_codes` fails when one is closed,
so this list is updated with the fix.

<!-- gaps: begin -->
1. **The page and Neo4j listen on every interface.** `demo/docker-compose.yml` publishes the page
   (8080), Neo4j Browser (7474) and bolt (7687) without a host address, so they listen on every
   interface of the host. The page has no login. Anyone who reaches it reads everything it shows,
   and can start a run (`POST /api/run`): the run reloads the store and, with a key set, calls the
   model at the organisation's cost. Neo4j's password defaults to `kgpoc2026`. **Practice until
   fixed:** run the stack on a machine only its users reach, or behind a firewall, and set
   `KG_NEO4J_PASSWORD`. Proposed fix: publish the three ports on `127.0.0.1` by default, with a
   variable to widen them, and refuse to start with the default password once the bind is wider.
2. **The `gives` role is not checked.** An answer is refused when its handle is not issued or has
   been withdrawn, but not when the handle lacks `gives`. Proposed fix: `capture.check_answers`
   refuses a handle without `gives`, as `review.check` does for `approves` and `closes`.
3. **The store holds excerpts.** "Status and provenance, never content" is true of whole documents
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
- Expose the page, Neo4j Browser and bolt only to the people who should read them, and set
  `KG_NEO4J_PASSWORD` (Gap 1).
- Issue opaque handles, and keep names and identifying details out of answers' notes.
- Leave the model key unset unless the arms or the transcript route are wanted. When they are,
  choose the endpoint with the table above in mind, and confirm where a private endpoint forwards.
- Run the arms only where model-written code may run.
- Pin the app image to a release tag.
- Report vulnerabilities privately ([`SECURITY.md`](../SECURITY.md)).
