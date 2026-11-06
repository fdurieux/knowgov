---
id: TASK-0174
title: >-
  Format versions on an instance's inputs: a plan, the scheme options with their
  four parts, no code (doc-0028 P1, G9-2; doc-0029)
status: To Do
assignee: []
created_date: '2026-11-06T13:03:00Z'
updated_date: '2026-11-06T13:26:00Z'
labels:
  - contracts
  - instance
dependencies: []
priority: medium
ordinal: 175000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0028 §9 P1, minted by doc-0029 advice 4 as a plan only. subject.toml, register_map.toml, code_map.toml, connectors.toml, the captures and the review files carry no format version today, so a change to any of them cannot be told from an old file. Plan, in this task's implementation plan: the files in scope (from instance/kinds.toml and instance/README.md), two or three schemes (e.g. a format = N key per file; one instance-level version; a schema URI), each with an opportunity canvas, a fit/gap (decision-0003 contracts, decision-0016 point 3, check_instance.py, the loaders, backward reading of a file without a version as current until 1.0), a SWOT and the drafter's advice. No code until the maintainer has read the plan: the scheme is a contract choice.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The implementation plan names every input file in scope with its reader (module and function)
- [x] #2 Two or three schemes, each with an opportunity canvas, a fit/gap, a SWOT and advice; a recommendation
- [ ] #3 No code change; the task stays To Do with the plan, for the maintainer
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Plan only (doc-0029; doc-0028 G9-2, P1). No code until the maintainer has read it; the task stays To Do. Read at `main` `38ae719`. Drafted by the v1.0 session (session_01HTAA1TThDg3TA2qJHCemaG); filed by the coordinating session under the maintainer's delegation (doc-0029).

## 1. The inputs in scope, and their readers

Only files an organisation writes or keeps in its instance and subjects are in scope. The register is ieam-register's format and its own record (doc-0028 G9-10). `instance/kinds.toml` and `instance/mappers.toml` ship with knowgov, so knowgov moves them with its own version.

| file | written by | read by (module, function) | carries a version today |
|---|---|---|---|
| `subject.toml` | a person, the wizard (`instance/ci/claude/skills/knowgov-onboard/SKILL.md`), `tools/example_instance.py` | `harness/subject.py` `Subject.__init__`; `tools/check_subject.py` `check`; `harness/subject_check.py` (MCP `subject_check`) | no |
| `scenarios.toml` | a person, the wizard | `harness/subject.py` `Subject.__init__`; `tools/check_subject.py` | no |
| `plants.toml` | a person | `harness/subject.py` `Subject.__init__`, `harness/plant.py` | no |
| `queries.toml` | a person | `harness/subject.py` `Subject.__init__` (the page's and the store's saved queries) | no |
| `register_map.toml` (the path in `subject.toml [register] map`) | a person, the wizard | `harness/subject.py` `Subject.register_map`; `harness/capture.py`; `harness/cadence.py`; `harness/upward.py` (`key_nodes`) | no |
| `code_map.toml` | a person | `harness/code_map.py` `code_map`; `tools/check_instance.py` | no |
| `connectors.toml` | a person | `tools/connector.py` (its `CONFIG`); `tools/check_instance.py` `connectors` | no |
| captures (`[capture] dir`, `captures/` by default; one TOML per answered questionnaire) | `harness/capture.py` ingest (`capture_toml`) | `harness/load.py` `load_captures`; `harness/capture.py` `check_answers`, `due_captures` | no |
| review files (append-only, beside the captures) | a reviewer; `harness/review.py` `review_toml` | `harness/load.py` `load_reviews` → `harness/review.py` `check` | no |
| the pre-load report and its baseline (`preload-report.json`, `--baseline FILE`) | `tools/preload_check.py` | `harness/preload.py`; `tools/preload_check.py` | **yes**, `schema_version` (schema `preload-report`) |
| the gate baseline (`gate_cli --baseline FILE`) | `harness/gate_cli.py` `-o` | `harness/gate_cli.py` `_baseline` | **yes**, `schema_version` 2 (schema `gate-report`) |
| the trace ledger (`--ledger`, `KG_LEDGER`) | `harness/trace.py` `register` | `harness/trace.py` `read_ledger` | **yes**, `schema_version` |

**The gap:** nine unversioned inputs. Seven are configuration a person writes once and edits. Two, the captures and the review files, are append-only records that knowgov's own tools write and that outlive the version that wrote them.

## 2. What any scheme must satisfy

1. **A missing version reads as the current one until 1.0** (doc-0028 P1). No instance, subject or fixture breaks on the day the key lands.
2. **A file written for a newer knowgov is refused, not misread,** with an exit 2 ("cannot run") that names the file and both versions. This is the gate contract.
3. **Adding the key is a contract change** (decision-0003 §2). It lands in 0.9.0 if decision-0016 is accepted, and is named in the CHANGELOG.
4. **The attestation hook (task-0147) still blocks a write** that adds or changes `[verification]` or `[provenance]`, and only that. A version key elsewhere in `subject.toml` must not trip it.
5. **Every writer stamps the version it writes:** the wizard skill, `tools/example_instance.py`, `capture_toml`, `review_toml`, and the MCP `subject_check` report.
6. **The public subjects carry the key.** `cargo_quote`, `jef_data_load` and `minimal` are edited in place: their `vendor/` trees are vendored, but their `subject.toml` files are not. A run's `SHA256SUMS` (`harness/run.py`, over `Subject.definition_files` and the harness's own files) lists `subject.toml`, so a new run records the new digest, as it does after any harness change. The comparator compares results, not these sums.

## 3. Schemes

### A. One version per file

Each in-scope TOML carries a top-level `format = N`. Each reader checks its own file.

| Box | Content |
|---|---|
| Problem | Nothing tells a reader which knowgov a file was written for |
| Solution | `format = 1` at the top of every in-scope file; the reader compares it with what it reads |
| Measure | Every reader refuses a newer file in a test; the example instance digests unchanged apart from the key |
| Cost | Nine readers and five writers touched; one key in every file of three public subjects |
| Risk | A subject's files disagree, say `subject.toml` at 2 and `scenarios.toml` at 1, and the combination was never tested |

- **Fit/gap:**
  - Requirement 1: met (missing → current).
  - Requirement 2: met per file.
  - Requirement 4: met; the key sits outside `[verification]`.
  - Requirement 5: five writers to change.
  - Requirement 6: three subjects × up to five files.
  - Gap: no rule for a subject whose files differ.
- **SWOT:**
  - S: each file self-describing; a captured answer carries the version it was written under.
  - W: the most churn; a combination of versions to define.
  - O: the same key later becomes JSON Schema's `$id` version if the TOML inputs get schemas.
  - T: adopters bump one file and not the others.
- **Advice:** right for the append-only records, too fine for a subject's configuration.

### B. One version per root

`subject.toml` carries `[format] version = N`, covering every file in its subject root (`scenarios`, `plants`, `queries`, `register_map`). The instance carries one too, in a new `<instance>/instance.toml` covering `code_map.toml` and `connectors.toml`. The captures and review files inherit their subject's version.

| Box | Content |
|---|---|
| Problem | As A |
| Solution | One number per subject and one per instance, checked at `Subject.__init__` and by `tools/check_instance.py` |
| Measure | As A, with two readers to prove instead of nine |
| Cost | Two checks, one new file, three writers |
| Risk | Captures written under version 1 are read as version 2 after the subject's number moves: the append-only records lose the version they were written in |

- **Fit/gap:**
  - Requirement 1: met.
  - Requirement 2: met per root.
  - Requirement 4: met.
  - Requirement 5: three writers.
  - Requirement 6: one key per subject.
  - Gap: the append-only records, which outlive the root's version. `instance.toml` is also a new file in the instance layout, itself a contract change.
- **SWOT:**
  - S: one number to bump; matches decision-0003's "subject manifest format" contract exactly.
  - W: a new instance file; history of the records lost.
  - O: `check_instance.py` reports one version per subject at a glance.
  - T: an upgrade that changes the capture format silently re-reads old captures.
- **Advice:** right for configuration, wrong for records.

### C. No key; a stated read rule and published schemas

The files carry nothing:
- knowgov states a read rule: a minor version reads every input that the earlier minors of the same major accept;
- knowgov publishes a JSON Schema per TOML input under `harness/schemas/`, validated in `check_instance.py`;
- unknown keys are refused, as `check_subject.py` already does for some tables.

| Box | Content |
|---|---|
| Problem | As A |
| Solution | Compatibility promised by the reader and checked against schemas, never stamped in files |
| Measure | Schema validation of every public subject and the example instance in the suite |
| Cost | Nine schemas to write and keep; a TOML-to-JSON step in the checker |
| Risk | A file written for a newer knowgov is indistinguishable from a malformed one, so requirement 2 holds only as "unknown key refused" |

- **Fit/gap:**
  - Requirement 1: trivially met.
  - Requirement 2: only partly; a newer file reads as "invalid", not "newer".
  - Requirement 4: met.
  - Requirement 5: none.
  - Requirement 6: none.
  - Gap: the "written for a newer version" message, and the records' history.
- **SWOT:**
  - S: no churn in adopters' files; schemas document the formats.
  - W: weakest on downgrade detection; the most new artefacts.
  - O: the schemas are worth having under any scheme (task-0172 does the same for the MCP outputs).
  - T: a refusal that reads as a typo when it is a version mismatch.
- **Advice:** worth doing as a complement, not as the scheme.

## 4. Recommendation (the drafter's, for the maintainer)

**B for configuration, A for records, C's schemas later:**
- `subject.toml` gets `[format] version = 1`, covering its root's configuration files. A version per root fits how a subject is edited and reviewed: in one pull request, as one manifest.
- `code_map.toml` and `connectors.toml` each get a top-level `format = 1`. That is per file (A), so the instance layout gains no new `instance.toml`, which would be another contract change.
- Captures and review files each get `format = 1`, stamped by `capture_toml` and `review_toml`. They are records that outlive the version that wrote them, and must say which one did.
- Missing means the current version until 1.0 (requirement 1). A higher one refuses with exit 2, naming the file, its version and the reader's (requirement 2). A lower one is read, and a migration note follows the first time a version moves.
- JSON Schemas for the TOML inputs (scheme C) follow as their own task once task-0172's MCP schemas show the pattern. They are not needed for the freeze.

**Where it is checked:** `harness/subject.py` `Subject.__init__` (the root's version), `harness/code_map.py` `code_map`, `tools/connector.py`, `harness/load.py` `load_captures` and `load_reviews`; then `tools/check_instance.py` and `tools/check_subject.py` report each version found.

**Tests, when built:**
- per reader: missing reads as current, equal is read, higher is refused with exit 2;
- the writers stamp the key;
- the attestation hook ignores `[format]`;
- the three public subjects carry it;
- the deterministic record's results are unchanged (the comparator).
<!-- SECTION:PLAN:END -->

## Comments

<!-- COMMENTS:BEGIN -->
created: 2026-11-06T13:26:00Z

---

Plan filed by the coordinating session under the maintainer's delegation (doc-0029), drafted by the v1.0 session (session_01HTAA1TThDg3TA2qJHCemaG) at main 38ae719. ACs #1 and #2 are met by the plan; #3 (no code, task stays To Do for the maintainer) holds. Recommendation: B for configuration, A for records, C's schemas later.

---
<!-- COMMENTS:END -->
