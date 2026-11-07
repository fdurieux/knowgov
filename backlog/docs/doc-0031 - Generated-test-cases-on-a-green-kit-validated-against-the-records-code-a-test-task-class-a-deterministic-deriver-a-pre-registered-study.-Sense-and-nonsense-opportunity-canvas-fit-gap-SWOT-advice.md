---
id: doc-0031
title: >-
  Generated test cases on a green kit, validated against the record's code: a
  test task class, a deterministic deriver, a pre-registered study. Sense and
  nonsense, opportunity canvas, fit/gap, SWOT, advice
type: specification
created_date: '2026-11-07T08:45:00Z'
updated_date: '2026-11-07T08:48:00Z'
tags:
  - brief
  - canvas
  - fit-gap
  - swot
  - gate
  - tests
  - evidence
---
*2026-11-07. Maintainer register. A study with three tasks opened on the maintainer's go (task-0210, task-0211, task-0212); steps 4 and 5 are proposals with no ids. Trigger: two asks of this date. First, a Claude CLI session asked the knowgov MCP reader "does knowgov have sufficient information about CargoQuote to be able to create test scenarios?" and answered no; the maintainer asked for the sense and nonsense, an opportunity canvas and a fit/gap of adding a test task class. Second, rephrased: would a knowgov function that generates test cases, provided the subject's artefacts are all green, make sense, with the cases then validated against S1 onwards? Read on `main` at `7de49e1`. Executed: `harness/gate_cli.py --as-of record` on S1-S7 and S6 stage 2 (scratch store, decision-0017), in a scratch copy of the repository whose `subjects/cargo_quote/subject.toml` carried three draft classes (`test`, `test_strict`, `answer_keys`), committed nowhere, in a venv with rdflib 7.6.0, pyshacl 0.40.2, PyYAML 6.0.3 and pumllint 0.33.0 (the image's pins); read-only scripts over the record's `results/S*/run*_?.json`. Not executed: any of the record's code samples (model output: outside the worker it would run uncontained, which X1 refuses by default, decision-0012, task-0141.07's opt-in aside), any model, Neo4j. Synthetic content only.*

## Verdict

**Sense, staged, as a measurement on the public subject; not yet an adopter's generator.** The gate as the precondition answers the failure the record measured: tests written from defective knowledge pass defective code (degradation test: 6 of 15 planted defects reached the code, all 6 concealed by the arm's own suite and caught by the pristine one; the J-F D arms the same). The validation bed exists: `reference_impl.py`, 50 code samples the frozen oracle graded (31 pass, 19 fail), the oracle's scenarios as data that `runner_child.py` drives over code of any interface, and the worker. CargoQuote's keys hold computable values, so the case list needs no model, and a case that cites its assertions goes suspect after a change, which no model-written test can do. Nonsense as phrased in three places: "all green" seldom holds and must be the test class's verdict, not the kit's; "validated against S1 onwards" exists only on a public subject, since `execution_guard` refuses execution where an instance is mounted; the full bundle names every oracle scenario, so a suite generated from it and graded against that oracle is contaminated.

The first question's answer was wrong on the facts (section 1): it read S3, a planted scenario, and gated keys that block the pristine kit too. On S1, the clean kit, the drafted class reads PROCEED on 44 of 44 keys.

## 1. The MCP answer, read against the record

| Claim | Reading |
|---|---|
| "No, not as things stand" | The store held **S3**, planted: the DT-S rows reworded to vague ranges, the symbolic names undefined, the DMN removed (`scenarios.toml`). On S1 the drafted class reads PROCEED 44/44. The four proposed band boundaries are S3's plant. |
| `REQ-05\|verified_by` absent is a blocker | Inverted. The missing scenario is what a test-writing task produces; gating it blocks the work that closes it. Standing in the kit: `kit/links.toml` has seven `[[verifies]]` rows (G1-G7 to REQ-01, 04, 03, 06, 08, 02, 07), none for REQ-05; `harness/rules.py` raises "no verifying scenario" on every scenario; PREREGISTRATION.md X10 records it as the main shape's standing result. The frozen suite does exercise it (`store_down_error` on `QuoteAPI\|on_store_failure`), but the suite is the held-out oracle (`tests_input/oracle_overlap.md`), so it is rightly no `verified_by`. |
| G1-G7 `title` and `expects_status` at proposed | Proposed by construction in every scenario: `acceptance.feature` is "a GENERATION-INPUT artifact ... not executed by any harness"; the Gherkin mapper (`harness/extract.py`, `extract_gherkin`) extracts those two predicates only, and no verification map row covers them. Required, they make tests rest on tests. |
| `held_keys` (94) under codegen's 25% bar reads BLOCKED | A class's bar applied outside its class; no meaning. |
| None of the keys is in `register_map.toml` | True and not specific to tests: the map holds codegen's 36 keys (`keys_expected = 36`); design's `REQ-xx\|text` and C4 keys are unmapped too (S6 design: "owner none in the register map"). |
| Loading S1 wipes the shared store | Not for the command since decision-0017 (accepted 2026-11-06): `gate_cli.py --scenario S1` computes on a scratch store; only `--publish` writes the configured one. The MCP reader cannot load a scenario (decision-0008); the CLI session could have run the command. |

The answer's own key set (`answer_keys`: the 14 G keys and the eight `verified_by`) reads **BLOCKED on S1**: `REQ-05|verified_by` absent, 14 keys proposed.

## 2. Measured: the drafted test class

Keys: `REQ-01|text` to `REQ-08|text` plus codegen's 36 (44). `test`: codegen's block levels and bar. `test_strict`: codegen's block levels plus `proposed`, `max_unverified_share = 0`. As of 2026-10-30, rdflib.

| Scenario | codegen | design | test | test_strict |
|---|---|---|---|---|
| S1 | PROCEED | QUALIFIED (5 C4 calls proposed) | PROCEED 44/44 | PROCEED 44/44 |
| S2 | BLOCKED | BLOCKED | BLOCKED (3 keys) | BLOCKED (3 keys) |
| S3 | QUALIFIED (4 below, 13 flagged) | QUALIFIED | QUALIFIED | **BLOCKED**: `S-accept\|max`, `S-review\|min`, `S-review\|max`, `S-refuse\|min` (proposed) |
| S4 | BLOCKED (outage disputed) | BLOCKED | BLOCKED | BLOCKED |
| S5 | BLOCKED | BLOCKED | BLOCKED (3 keys) | BLOCKED (3 keys) |
| S6 stage 1 | PROCEED | QUALIFIED | PROCEED 44/44 | PROCEED 44/44 |
| S6 stage 2 | BLOCKED (`P2\|threshold`, `P2\|surcharge` invalidated) | QUALIFIED (exit 1 on the suspect derived output) | not run | BLOCKED (the two P2 keys and `P3\|order` proposed) |
| S7 | BLOCKED (36/36 below) | BLOCKED | BLOCKED (44/44 below) | BLOCKED (19 keys at a blocking level, the requirement texts among them proposed) |

`test` differs from codegen nowhere. `test_strict` differs from codegen's verdict on S3 only, exactly on the boundaries behind the record's S3 defect ("the 41-boundary scenario fails in 4 of 5 runs of G and 5 of 5 of B"). task-0210 adopts `test_strict` as `[tasks.test]`.

## 3. What exists to validate generated cases against

**The corpus.** 70 run slots (7 scenarios, 2 arms, 5 runs); 50 carry code the frozen 11-scenario oracle graded; the 20 without code are arm G under BLOCKED (S2, S4, S5, S7).

| Scenario | B | G |
|---|---|---|
| S1 | 5 pass | 5 pass |
| S2 | 5 fail (`screening_down_hold`) | no code |
| S3 | 5 fail (`accept_boundary_41`) | 4 fail (one on `accept_boundary_41` alone; three on 5, 6 and 11 scenarios), 1 pass |
| S4 | 5 pass | no code |
| S5 | 5 fail (`screening_down_hold`) | no code |
| S6 | 5 pass | 5 pass |
| S7 | 5 pass | no code |

31 pass, 19 fail, five failure signatures. 16 of the 19 carry a single fault (10 the outage, 6 the 41 boundary): the corpus is effectively two faults, so mutants of `reference_impl.py` are needed for anything else. S4's arm B passes the oracle after choosing a side by an invented precedence: a pass is not proof of a sound derivation.

**The reference.** `vendor/stack_experiment/cargo_quote/reference_impl.py`, the code the oracle verified (`[reference]`).

**The case shape.** The oracle's scenarios are data, `SUITE["scenarios"]` in `vendor/tools/acceptance/cargo_quote_suite.py`: stubs, request, `expect`, `must_call`, `must_not_call`, `failure_like`, with driver-side `OVERLAYS` (regexes on the serialised outcome). `runner_child.py` takes one scenario's spec as base64 JSON on its argument list and finds the entry point and collaborators of any interface. Cases in that shape need no generated test code.

**Execution.** `harness/execution.py`: the worker's job kinds are `suite`, `suite_dir` and `feedback`, each running the subject's oracle script; none runs a case list. A `cases` kind is new (step 4).

**The values.** Approved key values are computable: `P1|formula` = '0.87 * weight_kg + 1.13 * distance_km', `P2|threshold` = '1244' (S1 `bundle_G.txt`); bounds and band edges are numbers.

**Leakage.** The full bundle names every oracle scenario: 79 lines of `S1/bundle_G.txt` read "suite scenario <name> on reference_impl.py", all eleven names. The `compact` form (task-0140) keeps each assertion's id and value and drops its verification lines; its stale and lapse sections still list verification ids (`ver:exec:price_exact_heavy:...`) in either form, so after S6's change the compact form leaks too. The deriver reads the gate's resolved keys and ignores verifications (task-0212 AC 4).

## 4. Sense and nonsense

Sense:
- **The gate is the right precondition for an oracle.** Code written on a guess fails the oracle; a test written on a guess becomes the oracle and passes the guess. The degradation test measured that concealment; a test class stricter than codegen is the countermeasure, and S3 is where it bites.
- **The validation bed exists and is labelled**: the reference, 50 graded samples, the oracle's per-scenario verdicts, a tolerant runner, a contained worker.
- **No model is needed for the case list on CargoQuote**: bound plus and minus one, band edges 41/42 and 66/67, the P2 threshold, P3's order, each dependency failure, REQ-05.
- **Cases citing their assertions go suspect after a change.** `trace.py register` takes any built file (task-0051) and the suspect walk exists; S6 stage 2 marks `derived:S1:G:run1` suspect today. A case on `P2@v1` would be marked the same way. This is the part no test generator offers.
- **It answers the MCP session's real question** with a declared scope instead of keys an agent chose (doc-0014 C4).

Nonsense, or not yet:
- **"All green" as the kit's state.** S1 is pristine by construction and still reads QUALIFIED for design. The precondition is the test class's verdict: PROCEED derives, QUALIFIED derives with each case on a key below verified marked as an assumption, BLOCKED derives nothing.
- **Validation against S1 onwards as an adopter feature.** `execution_guard` refuses execution where an organisation's instance is mounted, and the worker sees only what ships in the image. An adopter validates generated cases in its own CI. Inside knowgov the loop is a measurement.
- **A generic deriver.** `harness/` names no subject (task-0002); CargoQuote's bounds and bands come from its decision-table mapper; J-F's requirements are prose (`JDL-nnn|statement`). Derivation without a model is per mapper family; prose needs a model, and only the Arms mode calls one.
- **Disagreement with the oracle read as error.** The oracle never stubs a notification failure (G7 "disjoint" in `oracle_overlap.md`). A case failing one of the 31 passing samples may be a defect the oracle misses; a disagreement is settled against the cited keys, by a stated rule.
- **The oracle as the generator's input.** Through the full bundle, it is: see section 3.

## 5. Opportunity canvas

| Element | Content |
|---|---|
| Problem | Tests written from defective knowledge conceal the defect (6 of 6 in the degradation test); tests written from sound knowledge are never marked when that knowledge changes. |
| Users | First the maintainer and the lighthouse evaluation, as a measurement; later an instance's assistant at a tests-first step, through its own CI. |
| Today's alternative | Hand-written Gherkin (G1-G7, which reveal neither REQ-05 nor the band edges, nor the P2 and P3 points); a model writing tests with no gate; an agent choosing its own keys over MCP. |
| Proposal | Gate on `[tasks.test]`; derive cases deterministically from approved key values, each citing its assertions, in the oracle's data shape; run them in the worker against the reference, the 50 graded samples and the mutants; register them as derived outputs. A model arm only after that. |
| Unique value | A case set that is gated, cites its sources and goes suspect on a change. |
| Measures | Pass rate on the reference (100% expected); detection of the 19 faulty samples (the oracle's 19 at least); agreement with the oracle on the 31, each disagreement settled; coverage of the points `oracle_overlap.md` lists as not revealed (every DT-V bound except V2's lower, the band edges 41/42/66/67, P2's threshold and amount, P3's threshold and the P2-then-P3 order, accept-boundary behaviour, storage failure, the refusal path's pricing and notification); mutant kill rate; cases marked suspect after S6's change; under S2-S7 (step 5), cases refused or marked as assumptions against cases that encode the plant. |
| Cost | A content-only class (task-0210); a pre-registration (task-0211); a subject-side deriver, its schema and tests (task-0212); then a worker job kind, the mutants and a report schema (step 4). |
| Risks | Overfitting to CargoQuote; a measurement taken for a feature; work landing during the 0.9 freeze. |
| How it starts | task-0210, then task-0211 before any deriver exists, then task-0212; step 4 when the three are Done; step 5 only on its numbers. |

## 6. Fit/gap

| Must satisfy | Status | Evidence |
|---|---|---|
| A gated precondition | **Fit** once task-0210 lands | section 2: S1 and S6 PROCEED, S3 BLOCKED |
| Expected values from key values, no model | **Fit** on CargoQuote; **gap** on prose subjects | section 3, the values; J-F `JDL-nnn\|statement` |
| Code to run cases against | **Fit** | reference, 50 graded samples, `runner_child.py`, the worker |
| `harness/` names no subject | **Gap**, closed by a deriver under the subject root | task-0002; precedent `subjects/jef_data_load/oracle/` |
| The oracle held out of the generator's input | **Partial** | compact form on S1; stale and lapse sections list verification ids |
| Fault diversity | **Gap** | five failure signatures, 16 of 19 single-fault |
| A worker job that runs a case list | **Gap** | `suite`, `suite_dir`, `feedback` only |
| Cases as derived outputs, suspect after a change | **Partial** | `trace.py register` takes any file; not rehearsed for a case file (task-0212 AC 7) |
| The MCP reader stays read-only | **Fit** if derivation and execution are runs, never reader tools | decision-0008 |
| Adopter execution | **Gap by design** | `execution_guard`; the worker sees only the image |
| A hook stage for tests | **Gap**, not needed for the study | `STAGES = ("plan", "spec", "push")` |
| Value-level coverage of existing tests | **Gap** | the Gherkin mapper reads no Given values; `oracle_overlap.md` is prose |
| The 0.9 freeze | **Fit** for tasks 0210-0212 (subject content, a subject-side tool); **gap** for step 4 | decision-0016: a worker job kind and a report schema are contract additions, in 0.9.0's set or after it |

## 7. SWOT

| | Helpful | Harmful |
|---|---|---|
| **Internal** | **S:** the bed and its labels exist; no model needed on CargoQuote; cases cite assertions and go suspect on a change; the strict class turns S3's recorded defect into a block; cheap first steps (content, a pre-registration, a subject-side tool). | **W:** public subjects only; the corpus is two faults deep; derivation is per mapper family; the bundle leaks the oracle; `test` and `test_strict` read as codegen on six of seven scenarios. |
| **External** | **O:** a second record, for test generation beside codegen's; the playbook's Test stage (doc-0014 section 5); the oracle's blind spots found (G7, REQ-05 in the input set); J-F later, whose own suite is both oracle and feedback. | **T:** read as a test generator, a crowded category where knowgov's edge is governance, not generation; the 0.9 freeze; a model arm spending money and noise before the deterministic half has numbers; a disagreement rule tuned after the fact. |

## 8. Advice

Do it, in order, as a measurement. **task-0210**: the strict class, content only, because it costs about fifty lines, answers the MCP question with a declared scope, and is the precondition of everything after it. **task-0211**: the pre-registration, before any deriver exists, because the corpus is small and visible and a deriver written while looking at it measures nothing. **task-0212**: the deterministic deriver, because CargoQuote's values are computable and the citations are the part only knowgov can give. Hold step 4 (the worker's `cases` job, the mutants, a report schema) until the three are Done and the 0.9 contract set is settled; hold step 5 (a model arm) until step 4 has numbers. Hold anything adopter-facing until the pilot asks, the rule task-0101 set for further classes. Do not gate a test class on `verified_by` or on the G keys, and do not give a generator the full bundle.

Priorities: task-0210 medium, as task-0101 was; tasks 0211 and 0212 low, behind the hardening tranche before 0.9.0 (doc-0028 G9-11, doc-0030).

## 9. Steps

| Step | What | Id |
|---|---|---|
| 1 | `[tasks.test]` on CargoQuote, stricter than codegen, rehearsed on S1-S7 and S6 stage 2 | task-0210 |
| 2 | The pre-registration: hypotheses, corpus by digest, mutants, measures, the disagreement rule, the leakage control, the case families | task-0211 (depends on task-0210) |
| 3 | The deterministic deriver under `subjects/cargo_quote/`: cases in the oracle's shape, each citing its assertions, refused on BLOCKED, registered as a derived output | task-0212 (depends on task-0211) |
| 4 | A worker job kind `cases` running a case list (data) over code through `runner_child.py`; the mutants; the measures reported under a schema | proposed, no id |
| 5 | A model arm writing cases (compact bundle against documents) under S1-S7, measuring concealment against the deterministic set | proposed, no id |

## 10. Limits of this reading

One model's corpus (`gpt-5.1-2025-11-13`, n = 5), synthetic content, toy scale, as the record states of itself. The class verdicts come from a scratch copy, not a committed class. No code sample was run; whether `runner_child.py` drives a derived case over every sample as it drives the oracle's own is step 4's to show. In my earlier chat reply I said "6 distinct failure signatures"; that count included the clean one. The faulty samples carry five.
