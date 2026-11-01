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
  projection need, nothing more) and its first adapter (`store_neo4j.py`: every
  Cypher statement, the constraints, the saved queries); `KG_STORE` picks the
  adapter, `neo4j` by default. No other module speaks Cypher; a test guards it
  (task-0003). `demo/` the page, the vendored model, the vendored
  register, the comparator, the Docker files; `subjects/<id>/` a subject root
  (`subjects/README.md` documents the format): `subject.toml`, `scenarios.toml`,
  `plants.toml`, `queries.toml`, `register_map.toml`, `prompts/`, and under
  `vendor/` the bytes vendored from pumllint in its relative layout; `runs/`
  re-runs, gitignored. `KG_SUBJECT` selects the root; nothing in `harness/` or
  `demo/` names a subject, a document or a scenario (task-0002).
- Re-vendor the register with `python tools/vendor_register.py <checkout>` at
  a tag of ieam-register; the CargoQuote bytes with `python tools/vendor_subject.py
  <checkout>` at a pumllint tag (`--allow-untagged` for a commit, and the
  note says so). Each rewrites its `SOURCE.md`; a test holds every file to
  its digest.
- The record's versions are pinned in `demo/Dockerfile` (neo4j 6.4.1, rdflib
  7.6.0, pyshacl 0.40.2, openai 3.41.0) with pumllint 0.33.0 from PyPI, the
  library the sequence-diagram mapper imports; `tests/test_demo.py` holds them.
- Local proof without Docker: a Neo4j 5.26 community tarball started directly
  (Java 21), a venv with the pins above, `harness/run.py --deterministic --out
  <dir>`, then `demo/tools/compare_deterministic.py <dir>`.

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
for the whole matrix, merge on green, never on red or pending.

## Boundaries

- `pumllint/` imports nothing from here and reads no register; this repository
  consumes pumllint's reports and its parser as a released library, never the
  reverse.
- A client's instance is private, created inside the client's repositories,
  and never pushed here. No bank-related data, ever.
- The model endpoint is instance configuration; arms are off until one is set.


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
