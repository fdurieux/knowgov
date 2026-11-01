# knowgov

Governed knowledge for AI-assisted delivery: every statement with its source,
status and verification; a gate that says whether an assistant may build on
it; and impact analysis that shows what a change or a defect reaches, through
the register and the systemic model.

## What is here

The governed-repository demo, moved from pumllint's
[`kg_experiment/`](https://github.com/fdurieux/pumllint/tree/main/kg_experiment)
(decision-0001 in `backlog/decisions/`). Start with [`demo/README.md`](demo/README.md):
one command starts a Neo4j database and the web page that replays the seven recorded
scenarios, re-runs them against the database, and shows the register's impact walk.

| folder | holds | written by |
|---|---|---|
| `harness/` | the pipeline: reading the subject's documents into statements, loading them into the store with their provenance, the seven checking rules, the gate, the two assistant arms | this repository |
| `demo/` | the web page, the vendored Legible model and layout tables, the vendored IEAM register, the comparator, the Dockerfile and compose files | this repository; `demo/register/` by `tools/vendor_register.py` |
| `subjects/<id>/` | a subject: its manifest, scenarios, plants, saved queries, register map and prompts ([`subjects/README.md`](subjects/README.md)); `cargo_quote/` carries pumllint's kit, oracle and record byte for byte under `vendor/`, `minimal/` is the smallest one | this repository; `vendor/` by `tools/vendor_subject.py`, never by hand |
| `runs/` | re-runs, in dated folders; ignored by git, never the record | the page or the harness |
| `backlog/` | the queue, the decisions and the briefs ([Backlog.md](https://github.com/MrLesk/Backlog.md)) | the `backlog` command |
| `tests/` | the checks; `python tests/run_tests.py` needs the standard library only | this repository |

The harness needs Python 3.13 with the pinned packages the Dockerfile installs,
pumllint among them: the sequence-diagram mapper uses pumllint's parser as a
library. The page itself is standard library only.

The record of the proof of concept stays in pumllint:
[`docs/neo4j-governed-knowledge-evaluation.md`](https://github.com/fdurieux/pumllint/blob/main/docs/neo4j-governed-knowledge-evaluation.md).

## Licence

knowgov is published under the GNU General Public License, version 3 or
later (see [`LICENSE`](LICENSE)). For an organisation running it, that means:
you may use and modify it freely within your organisation with no obligation
to publish anything; the obligation to provide source arises only if you
distribute a modified knowgov to third parties; and the content it governs,
your artefacts, your register and your answers, is your data and is never
affected by the licence.
