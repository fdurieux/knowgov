# Changelog

One section per release, newest first. The version in `VERSION` is the top section's
(decision-0003). While the version is 0.x, a change to a contract raises the minor version: the
gate command's exit codes or flags, the JSON shapes under `harness/schemas/`, the instance layout,
the store port, the subject manifest format.

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
