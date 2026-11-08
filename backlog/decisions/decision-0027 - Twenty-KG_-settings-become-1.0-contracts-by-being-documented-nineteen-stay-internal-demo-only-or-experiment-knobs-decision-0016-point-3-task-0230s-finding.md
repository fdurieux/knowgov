---
id: decision-0027
title: >-
  Twenty KG_* settings become 1.0 contracts by being documented; nineteen stay
  internal, demo-only or experiment knobs (decision-0016 point 3; task-0230's
  finding)
date: '2026-11-08T20:56:00Z'
status: accepted
---
## Context

decision-0016 point 3: the `KG_*` settings that `instance/README.md` or `docs/security.md` documents are 1.0 contracts, and an undocumented setting is not. task-0230's adopter-docs pass (#384) held every setting the docs name against the code, and found two lists:
- 28 settings the code reads that no adopter doc names;
- 11 named only in `demo/README.md`, which is not a contract document.

It changed none of them and put the choice to the maintainer. On 2026-11-08 the coordinator grouped the 39 and advised documenting five groups.

## Options

- **(a) Document the five groups an instance relies on**, and keep the rest out.
- **(b) Document all 39.**
- **(c) Document none**, and leave instance settings uncontracted.

## Decision

**Accepted: (a)**, on the maintainer's word (2026-11-08: "settings as advised"). Drafted by the coordinator.

**Twenty become 1.0 contracts**, each documented in `instance/README.md`, or in `docs/security.md` for the worker limits:

| Group | Settings | Why |
|---|---|---|
| CI-template and hook inputs | `KG_TASK`, `KG_STAGE`, `KG_NO_LOAD`, `KG_GATE`, `KG_CODE_REPO`, `KG_SUBJECT_IN`, `KG_HOME` | decision-0016 point 3 already makes `instance/ci/`'s inputs contracts; undocumented, they were a gap |
| The store | `KG_NEO4J_URI`, `KG_NEO4J_USER` | Every Neo4j instance sets them |
| Worker limits | `KG_WORKERS`, `KG_WORKER_CPUS`, `KG_WORKER_MEM`, `KG_WORKER_JOBS`, `KG_WORKER_JOB_SECONDS`, `KG_WORKER_WORK` | They bound contained code, so their place is `docs/security.md` |
| Cross-subject calls | `KG_SUBJECT_CALL_TIMEOUT` | The named 1.0 limit U2 cites it |
| The model endpoint | `KG_ARMS_MODEL`, `KG_MODEL_API_KEY_VAR`, `KG_MODEL_API_KEY`, `KG_MODELS` | CLAUDE.md calls the model endpoint instance configuration |

**Nineteen stay out:**
- Test and tool internals: `KG_MUTANT`, `KG_ROOT`, `KG_NOW`, `KG_TRACEBACK`, `KG_OUTCOMES`, `KG_DEMO_URL`.
- Demo-stack knobs, kept in `demo/README.md`: `KG_DEMO_PORT`, `KG_DEMO_RUNS`, `KG_PAGE_LISTEN`, `KG_PORT_BOLT`, `KG_PORT_BROWSER`, `KG_ANTHROPIC_KEY`.
- Arms experiment knobs: `KG_ARMS_EFFORT`, `KG_THINKING_UNCOUNTED`, `KG_AGENT_IDLE_SECONDS`, `KG_AGENT_MAX_CALLS`, `KG_AGENT_MAX_SECONDS`, `KG_AGENT_MAX_TOKENS`, `KG_ARMS_MAX_TOKENS`.

## Opportunity canvas

| Element | Content |
|---|---|
| Problem | An operator cannot tell which settings will hold across releases |
| Users | The lighthouse's operator first; any instance running the stack or the CI templates |
| Proposal | (a) |
| Unique value | One list of the settings an instance may rely on, under 1.0's deprecation rule |
| Cost | A docs-only pull request; a test holding the twenty documented and read |
| Risk | A knob frozen before it is understood |

## Fit/gap

| Must satisfy | (a) | Evidence |
|---|---|---|
| decision-0016 point 3: documented means contract | Fit | decision-0016 |
| `instance/ci/`'s inputs are contracts already | Fit: their seven settings are now written down | decision-0016 point 3 |
| Experiment and demo knobs stay free to change | Fit: kept out | task-0230's lists |
| A deprecation costs a minor and ninety days | Accepted for the twenty | decision-0016 point 5 |

## SWOT

| | Helpful | Harmful |
|---|---|---|
| **Internal** | **S:** every setting an instance needs is promised | **W:** twenty more names to keep stable |
| **External** | **O:** `docs/security.md` gets the full list of worker limits | **T:** a setting frozen before the lighthouse shows it is needed, which is why the arms knobs stay out |

## Advice

(a), the drafter's recommendation:
- It documents what an instance must set.
- It closes a gap decision-0016 already implied for `instance/ci/`.
- It keeps the experiment free to move.

## Consequences

- A docs-only task documents the twenty, with what each does and its default:
  - in `instance/README.md`, and `docs/security.md` for the worker limits;
  - each as `tests/test_adopter_docs.py` holds it, extended to require the twenty documented and read in code.
- It is a contract change for 0.9.0, named under Unreleased › Contract changes.
- The nineteen stay where they are.
