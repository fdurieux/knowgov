# Subjects

A *subject* is what the harness loads and the page shows: a set of documents (the kit), the
code that verified them, the oracle that grades what an assistant writes, the task classes with
their required keys, and, when the subject has been run, its record. The platform names no
subject: everything it knows about one comes from a subject root, the directory `KG_SUBJECT`
points at (default `subjects/cargo_quote`). A second subject is a second directory, with no
change to the harness or the page.

## The files of a subject root

| file | holds | required |
|---|---|---|
| `subject.toml` | the manifest: the artefacts, the reference code, the oracle, the provenance and verification constants, the task classes, the three-valued keys, the rules' subject constants, the register view's constants, the record | yes |
| `scenarios.toml` | the recorded scenarios: the card and the Planted line, the harness's switches per scenario, the measures' keyword sets and targets, the page's extra sentences, the placement on the systemic model | for the gate: `gate_cli.py` runs on a scenario and exits 2 on a subject with a task and none (doc-0018 F3); one with none offers no scenario to replay or re-run |
| `plants.toml` | the mechanical patches a scenario applies to the pristine kit, a stage-2 change, and a model-proposed assertion | no |
| `queries.toml` | saved Cypher that names the subject's keys or scenarios; the page lists them after its generic ones | no |
| `register_map.toml` | the approved map from required keys to register nodes, for the footprint; a row's optional `owner`, one of its nodes' owners, is the one unit the key's questionnaire goes to (task-0043) | no |
| `prompts/` | the arms' task prompts, `<name>_baseline.md` and `<name>_governed.md` per task | for the arms mode |
| `vendor/` | bytes vendored from elsewhere, with their `SOURCE.md`; never edited by hand | no |

`subjects/minimal/` is the smallest subject: a manifest with one task and two keys, one scenario,
no artefacts. Its manifest says `listed = false`, so the page's subject drop-down, which lists every
subject in the folder `KG_SUBJECTS` names, leaves it out; named directly, it still loads. The harness loads it and the gate reports both keys absent and BLOCKED. The CI stack
job runs it. `subjects/cargo_quote/` is the full one: the kit of pumllint's proof of concept, its
record, its seven scenarios. `subjects/jef_data_load/` is the second: the specification kit of
pumllint's recreation experiment (J-F's daily asset load reverse-engineered, 163 requirements
joining five layers), the degradation test's six arms (C, the kit as committed, and D1 to D5) as its scenarios with its patches as the
plants, the platform's own deterministic record, and the kit's own pytest-bdd suite as the
oracle (`oracle/jef_suite.py`, one scenario per feature file, run once per reply and cached).

## `subject.toml`

```toml
[format]
version = 1                   # the format of this subject root (task-0174, decision-0023): subject.toml,
                              # scenarios.toml, plants.toml, queries.toml and the register map; missing reads
                              # as the current one, a newer one is refused, exit 2 (instance/README.md, "Format versions")

[subject]
id = "cargo_quote"            # the directory name by default
name = "CargoQuote"
description = "..."
record_model = "gpt-5.1-2025-11-13"   # the model that answered the record's arms; another is a deviation
record_effort = ""                    # the reasoning effort those arms ran at; "" is the API's default; another is a deviation too

[[artefact]]                  # in the order the baseline arm concatenates the documents
key = "kit/requirements.md"   # the name the harness and the record use for the document
short = "req"                 # the short name assertion ids carry (A:req:...)
family = "requirements"       # the family the store records
format = "markdown"
label = "requirements"        # what the page shows
format_label = "markdown"
path = "vendor/kg_experiment/kit/requirements.md"   # where the bytes are; absent when a plant adds the artefact
                              # a directory makes a directory artefact: one document whose parts are the
                              # files under it, each opened by a "==> <relative path> <==" line
include = ["*.md", "*.toml"]  # directory artefact only: the parts, as relative globs (* never crosses a slash,
                              # ** does); all files when absent
mapper = "requirements"       # the deterministic mapper: requirements, decision_table, spec, openapi,
                              # sequence, containers, bpmn, dmn, gherkin, links (the CargoQuote kit's
                              # conventions), or requirements_json, contracts_markdown, dmn_decisions,
                              # gherkin_tagged, plantuml_realises (a kit whose layers are folders joined
                              # by requirement id); absent for a document the store does not read
store = true                  # false keeps a document out of the store (the arms still read it)

[reference]
code = "vendor/stack_experiment/cargo_quote/reference_impl.py"   # the code the oracle verified; its digest is the execution
                              # evidence; a directory is bundled as its *.py files

[oracle]
script = "vendor/stack_experiment/smoke_test.py"   # the suite runner the measures load: suite_mod.SUITE["scenarios"],
                              # suite_mod.OVERLAYS, build_spec(name), run_child(artifact, spec); absent, the arms stay off
suite_order = ["quoted_low_risk", "..."]           # the oracle's scenarios, in display order
status_scenario = "screening_down_hold"            # the suite scenario whose detail carries the status the code returned

[provenance]                  # the agents the store records
harness_name = "kg_experiment harness"
human = { id = "agent:maintainer", name = "..." }
llm = { id = "agent:llm", name = "..." }
inference_at = "2026-10-27T00:00:00+00:00"
inference_tool = "architecture assistant"

[verification]
map = "vendor/kg_experiment/kit/verification_map.toml"   # suite scenario -> keys it exercises; review -> keys
derive_execution = { from_predicate = "verified_by", key_predicate = "statement", separator = "; " }
                              # instead of a static map: every assertion <req>|verified_by names, in its value, the
                              # suite scenarios that verify <req>|statement, read from the scenario's own kit, so a
                              # scenario the plant removed verifies nothing
execution_scope = "suite scenario {scenario} on reference_impl.py (smoke 2026-10-30)"
review = { at = "2026-08-06", scope = "..." }       # the dated human review; it lapses after its keys' review months (decision-0005)
authored = { at = "2026-10-30", scope = "..." }     # authored statements: reviewed by construction, only when declared
approval = { at = "2026-08-06", record = "..." }    # the owner's approval of every verified assertion, only when declared
                              # decision-0009 (a): no default stands in for a person; without authored, authored
                              # statements stay proposed, and without approval nothing is approved; each needs its
                              # own at and [provenance] human an id, refused otherwise by check_subject and applied
                              # to nothing by the load (task-0199, doc-0030 I9); authored and approval may list in
                              # versions = ["<sha256>", ...] the Versions they attest (decision-0019): an unlisted
                              # Version then reads proposed; without the list they attest per load (the read rule)

[arms]                        # optional; absent means kind = "reply": one JSON reply per run (harness/arms.py)
kind = "agent"                # a loop of turns with tools over a sandbox (harness/agent.py, task-0022)
[arms.agent]
system_prompt = "system_agent"   # prompts/<name>.md for the agent kind
feedback = "features/"           # the artefact that is the scenario's own suite, run by the oracle script's run_feedback
context = "pull"                 # push (default): the bundle or the documents in the first message; pull: an index,
                                 # read_knowledge(key) for G and read_document(path) for B, every read logged as consulted
layout = """..."""               # prose appended to the task prompt: what the oracle grades and where files go

[tasks.codegen]               # one table per task class; the gate resolves a class's keys
keys = ["shipper_id|present", "..."]
verbatim = ["contracts/cli.md"]      # optional: kit files the governed bundle carries as written, after the knowledge
                                     # (an artefact key, or a directory artefact's key plus the part's path inside it);
                                     # for what the task needs byte for byte and an assertion cannot stand in for
block_levels = ["absent", "declared_gap", "disputed", "invalidated"]
max_unverified_share = 0.25          # block_levels a list, never a bare string; a share from 0 to 1. A subject with a
                                     # malformed task class does not load: every gate call exits 2 naming the field (task-0242)
rationale = "..."                    # optional: why these keys; store_status reports it (task-0101)
require_approved = true              # optional, default false: the intended bar (task-0215, decision-0018 point 4).
                                     # A key verified but not approved then reads below the class's bar: an
                                     # "intended" finding (major) names its owner and route (capture.routing),
                                     # and the verdict counts it as the class counts a key below verified
                                     # (QUALIFIED, or BLOCKED past max_unverified_share). A behaviour verified
                                     # by execution on the original is shown to hold, not intended by anyone.
                                     # Such a key never blocks outright: a class that wants it to block lowers
                                     # max_unverified_share (0 blocks on the first one)

[three_valued]
keys = ["S-review|notified", "..."]   # D5, measured on the scenario that asks for it

[rules]
requirement_id_pattern = "JDL-\\d{3}"   # what a requirement id looks like, for the mappers that join on it (default [A-Z]{2,}-\d{2,})
vague_words = ["around", "..."]
declared_gap_id = "gap:declared:OD-1"
declared_gap_text = "{req} is NOT YET SPECIFIED (open decision OD-1, owner: compliance)"
[rules.requirement_keys]
"REQ-06" = "QuoteAPI|on_screening_outage"   # the key a declared-open requirement governs

[register]
map = "register_map.toml"
requirement_anchor = "kit:requirements.md#"          # how the register's links cite a requirement
export_manifest = "exports/kit/2026-10-30/MANIFEST.toml"   # in the vendored register

[record]
dir = "vendor/kg_experiment/results"   # <scenario>/deterministic.json and the arms' run files; never written
as_of = 2026-10-30            # optional: the date the record is read as of (decision-0005); absent, today

[page.reference]              # the no-governance reference the page cites
title = "..."
text = "..."
numbers = { planted = 15, reached_code = 6 }
```

**Conflict gap ids in a record** (decision-0020, task-0223). A conflict between two statements is named
`gap:conflict:<key>:<a>~<b>`, by its two assertion ids sorted, whether a person's statement is one side or
both are documents'. A record written before took `gap:conflict:<key>:<n>` for two documents, numbered in the
store's order: the vendored CargoQuote results keep that form (S4's `:0` to `:3`) and are never edited.
`demo/tools/compare_deterministic.py` reads both forms as one per key, so a run compares equal to such a
record; the page and the gate name a conflict by its statements on every store.

## `scenarios.toml`

A subject that declares a task declares at least one scenario: the gate loads one, and with none
`gate_cli.py` exits 2 ("no scenario ''; the subject declares none"); `tools/check_subject.py`, which
`check_instance.py` runs on every subject, refuses such a subject (doc-0018 F3, task-0135). The
smallest is a pristine scenario, the pattern `subjects/minimal/scenarios.toml` follows: the kit as
committed, nothing planted.

```toml
[[scenario]]
id = "S0"
title = "pristine"
represented = "The documents as committed."
gate = "BLOCKED"              # what the page's card shows as the record's verdict; the gate computes its own
defect = "None planted."
plant = "Nothing was planted: the subject's documents as committed."
plain = "The subject's documents as they are, with nothing planted."
extraction = "pristine"
```

The full set of fields, as CargoQuote's S6 uses them:

```toml
[[scenario]]
id = "S6"
title = "invalidated by change"
represented = "..."           # controlled sentences (GLOSSARY.md): the card
gate = "PROCEED"              # the record's verdict
defect = "..."
plant = "..."                 # the Planted line
plain = "..."                 # the reading, 25 words a sentence
extraction = "pristine"       # or "planted": the activity note
prompts = "task_s6"           # the prompt pair under prompts/ (default task_codegen)
verifications = true          # false loads none (extraction only)
three_valued = false          # true measures D5 here
inferred = false              # true adds plants.toml's [inferred] assertion
flag_words = ["invalidat", "stale"]   # M3: the planted problem is flagged when one appears in the arm's questions or assumptions
co_words = []                 # M3: a second family that must appear too
targets = ["price_exact_heavy"]       # M4: the oracle scenarios the plant aims at
default_source = "rerun"      # which result folder the page opens first
deterministic_record = "d3check/S6"   # the record's deterministic-mode run, what a deterministic re-run is compared with
scored_record_volatile = ["valid_until"]  # leaves the page sets aside, timestamps-like, against the scored record only (say why beside it)

[scenario.page]               # extra sentences for the page, controlled
ingest = ["..."]
oracle = ["S6 asks for the new prices."]
absent_artefacts = ["kit/screening_decision.dmn"]   # listed as absent in the ingest panel

[[scenario.sources]]          # extra result folders under the record
id = "rerun"
label = "..."
dir = "rerun/S6"

[scenario.systemic]           # the placement on the Legible knowledge view
entry = "drift"
family = "..."
[scenario.systemic.G]
path = ["drift"]
stop = "validation"
note = "..."

[scenario.stage2]             # a second stage: the change after verification
artefact = "contract/decision_table.md"
version = "v2"
note = "..."
reverify_keys = ["P2|threshold", "P2|surcharge", "P3|order"]
reverify_scope = "..."
reapproval_record = "..."
at = "2026-10-30"                # the re-verification's day: required with reverify_keys (task-0199)
[scenario.stage2.derived]     # the earlier governed output registered as derived
id = "derived:S1:G:run1"
kind = "python module"
from_scenario = "S1"
file = "run1_G.py"
[scenario.suite_overlays.price_exact_heavy]   # the oracle's recomputed expectations after the change
require_re = "3211"
forbid_re = "3186"
```

## `plants.toml`

```toml
[[plant.S2]]                  # patches in order; a replace must match exactly once
path = "contract/decision_table.md"
within = "glossary.md"        # directory artefact only: the part the match is confined to
op = "replace"                # replace, drop or add
old = "..."
new = "..."

[[stage2.S6]]                 # the stage-2 change, the same shape

[inferred]                    # the model-proposed assertion a scenario with inferred = true adds
id = "A:llm:QuoteAPI|on_screening_outage"
entity = "QuoteAPI"
predicate = "on_screening_outage"
value = "..."
text = "..."
note = "..."
candidate_for = "gap:declared:OD-1"
```

## `queries.toml`

```toml
[[query]]
id = "invalidation"
needs = "S6"                  # "scenario" (any loaded), a scenario id, "register", "register+scenario"
needs_text = "S6 loaded deterministically"
title = "..."
text = "MATCH ..."
```

## The claim

A kit written by reverse engineering (decision-0018, doc-0032 §3) may say, statement by statement, what each
statement is (task-0214):

| claim | what it says | basis it loads with | how far it can rise |
|---|---|---|---|
| `observed` | what the pinned original does | `extracted` | `verified` by execution, then `approved` |
| `inferred` | a proposed explanation or generalised rule | `inferred` | never above `proposed`: nothing verifies it, a ruling may reject or refer it but never approve it (`harness/review.py`, task-0199 I4), and a `verified_by` link it carries derives no execution |
| `intended` | behaviour the responsible authority accepted | `authored` | `approved` only under `[verification] authored` and `approval` (decision-0009) |

A statement with no claim loads as before: `extracted` for `requirements_json`'s statements, `authored` for the
other four mappers' links and structure. The public kits carry no claim, so they and the record do not move.
Where each bundle mapper reads it:

| mapper | where the claim is written | scope |
|---|---|---|
| `requirements_json` | `"claim": "<value>"` on an item (its `basis` field is where the statement was read: code logic, prose or both, not a claim) | the item's statement |
| `contracts_markdown` | a line `Claim: <value>` in a part | the part's citations |
| `dmn_decisions` | `claim: <value>` in a decision's or a rule's `<description>` | the decision's rules, a rule's own winning |
| `gherkin_tagged` | a tag `@claim:<value>` on the Feature, a Rule or a Scenario | the scenarios under it, the nearest winning |
| `plantuml_realises` | a comment line `' claim: <value>` | the diagram's statements |

An assertion resting on statements of different claims, such as a requirement two contract parts cite, takes the
most conservative: `inferred` before `extracted` before `authored`, a statement with no claim counting as the
mapper's own basis. An unknown value (`guessed`) is refused by `tools/check_subject.py` (rule `claim`), and the
load fails on it rather than read the statement as something it did not say. The SHACL shape for an inferred
assertion (`harness/shacl.py`) accepts one that rests on the kit fragment stating it, beside one linked to the gap
it proposes to fill. `tools/fixtures/claim_probe` carries
every mapping, and `tools/check_claim_probe.py` holds it on the store `KG_STORE` names.

## Checking a subject

`tools/check_subject.py <subject root> [--register DIR] [--json]` reads a root before it is loaded,
and `tools/check_instance.py` runs it on every subject of an instance (task-0135, doc-0018 F2 to
F5). It refuses (exit 1) a table or field this file does not document, a task without `keys`,
`block_levels` or `max_unverified_share`, a task setting of the wrong type or out of range (`block_levels`
not a list of gate levels, `keys` not a list of keys, `max_unverified_share` outside 0 to 1, a
`require_approved` that is not true or false; `harness/task_policy.py`, the validator the gate itself uses,
task-0242), a task class named `keys` or outside `[a-z][a-z0-9_-]{0,31}` (rule `task-class`, task-0278), a key that
is not `<entity>|<predicate>`, a task with no
scenario, a `register_map.toml` node the register does not hold or an `owner` of none of its row's
nodes, a mapper that cannot read its document, and a claim that is not `observed`, `inferred` or
`intended` (task-0214). It warns on a required key no document yields
when they yield a near one, the documents' yield taken from the load's own mappers in a child
process, with no store. A register named by `--register` or `KG_REGISTER` that cannot be read is
exit 2, naming the path; with neither, the rows are checked against `demo/register` and are
unchecked only when it cannot be read (task-0279, decision-0033 choice 5). `tools/fixtures/subject_probe`
carries every refusal on purpose; the report is pinned by `harness/schemas/subject-check.schema.json`.

## Vendoring

A subject whose bytes live in pumllint declares them in a `[vendor]` table of `subject.toml`,
and `tools/vendor_subject.py <pumllint checkout> --subject <id>` copies that path set byte for
byte into `vendor/` under the subject and rewrites its `SOURCE.md`; `tests/test_vendor_subject.py`
holds every file of every vendored subject to its digest and the note to the tool's output.
A subject whose bytes are authored in place has no `[vendor]` table and no `vendor/`.

A subject whose scenarios are kept elsewhere as unified diffs against the pristine kit (the
degradation test of pumllint's recreation experiment) writes its `plants.toml` with
`tools/plants_from_patch.py <subject> <scenario>=<patch> ...`: one `replace` per hunk, confined
with `within` to its part of a directory artefact, hunks on files the store does not read
dropped and listed; `tests/test_jef_subject.py` holds the written file to the tool.

```toml
[vendor]
source = "fdurieux/pumllint"               # the repository the note falls back to when the checkout has no origin
title = "Vendored copy of ..."            # the note's heading
paths = ["kg_experiment/kit", "..."]      # the path set, as git ls-files reads it from the checkout
what = "the kit (...), ...; nothing else" # the note's "what is copied" cell
note = """..."""                          # the paragraph under the note's table
dest = "vendor"                           # optional; the copy's root under the subject
```

## What is still the subject's shape in the code

The ten CargoQuote mappers (`harness/extract.py`) read documents in the conventions that kit
uses: the decision table's row names, the entity `QuoteAPI`, the "NOT YET SPECIFIED" phrase.
The five bundle mappers read a kit whose layers are folders and whose documents cite
requirement ids: the id is the join, every layer's link to a requirement is one authored
assertion on it, and only the requirement's own statement is extracted and verified by
execution. A subject whose documents follow other conventions needs a mapper of its own; the
manifest's `mapper` field is where it is named, and the mapper registry is the one place to
add it.
