---
id: decision-0032
title: >-
  A contract validation pass before the 0.9.0 cut: every contract surface probed
  once with a fixed battery and combination probes, a bounded re-probe of what
  fixes touch, one independent spot check; only contract-bearing findings hold
  the cut
date: '2026-11-09T08:54:00Z'
status: accepted
---
## Context

In the 36 hours before 2026-11-09, every review or study of knowgov found at least one defect or gap that touched a contract. None came from the record or CI; each came from a fresh reader.
- decision-0023 A1: the missing-version rule would have changed meaning at 1.0.
- decision-0029: the gate report could not say what it judged.
- task-0241: `proposal_impact` ignored coverage rule C4.
- task-0252: slices read the wrong keys for any class but `codegen`.
- doc-0033 R1 to R4.
- A SNAP-04 partial-generation read on Neo4j in #401's stack job, under investigation.

decision-0016 point 2 makes a contract change after the 0.9.0 cut a 0.10.0 and restarts the freeze. The maintainer was asked, in a grilling round, whether the freeze was premature, and answered: "I would choose to run more validations before we cut a next release". The stopping rule followed: "middle option, and yes, only contract-bearing findings hold the cut".

## Options

- **(i) Fixed scope.** Every contract surface is probed once with a fixed battery.
- **(ii) Time-boxed.** A fixed window; whatever it finds.
- **(iii) Convergence.** Passes repeat until one finds no contract-bearing defect.
- **(middle)** (i) with combination probes, then a bounded re-probe of only the surfaces the fixes touch, then one independent spot check of a random sample.

## Decision

**Accepted on the maintainer's word (2026-11-09): the middle option.**

1. **The surfaces, listed once with their denominator:**
   - the 24 schemas under `harness/schemas/`;
   - the command-line tools, with their flags and exit codes: `gate_cli`, `trace`, `run`, `proposal_impact`, `upward`, `register_nodes`, `preload_check`, `check_instance`, `capture` and `connector`;
   - the MCP reader's 17 tools and 2 prompts, on both transports and both protocol eras;
   - the runs server's 3 tools;
   - the 20 documented `KG_*` settings;
   - the page's 4 HTTP routes;
   - `instance/ci`'s gate script, GitHub action, GitLab include, pre-load and proposal scripts, and the two hooks with their settings files;
   - the input formats: `subject.toml` with its scenarios, plants, queries and register map; `code_map`; `connectors`; captures; reviews; the proposal overlay;
   - the store port's reads on both adapters;
   - the image's name and tag scheme.
2. **The battery, applied to each surface:**
   - wrong type, missing, empty, boundary, non-finite and oversized values;
   - Unicode and path forms;
   - **the combination probes:**
     - every task class on every tool that takes one;
     - every subject (CargoQuote, J-F, the minimal subject, an example instance with its own register) on every subject-scoped tool;
     - every coverage rule the vendored register defines, on every reader of coverage;
     - both stores, alone and under racing writers.
3. **Findings are classified.**
   - **Contract-bearing:** fixing it changes a contract's shape or meaning (a schema field, an exit code, a flag, a setting, a format, a route, a documented behaviour).
   - **Fix-only:** a wrong result behind an unchanged contract.
   - **Only contract-bearing findings hold the cut.** Fix-only findings are tasked and ship in 0.9.x.
4. **The bounded re-probe.** After the contract-bearing fixes, only the surfaces those fixes touched are probed again with the same battery. There is no new open pass.
5. **The independent spot check.** One reviewer who ran no part of the pass probes a random sample of surfaces, as a check on the battery's blind spots.
6. **The pass is done** when every listed surface is ticked, every contract-bearing finding is fixed and re-probed, and the spot check is in. The pass's report is a backlog doc, with the surface list and its denominator.
7. **Independence.** The probers are sessions that did not build the code they probe.

## Opportunity canvas

| Element | Content |
|---|---|
| Problem | Each fresh reader found a contract-bearing defect; after the freeze each would cost a 0.10.0 and a restarted freeze while the lighthouse runs |
| Users | The lighthouse and every adopter who builds on the 0.9 contracts; the maintainer, whose 1.0 waits on the 0.9 contracts running unchanged |
| Proposal | The middle option |
| Unique value | A finite, checkable pass with a denominator, aimed at the defect classes the reviews kept finding, with a guard on its own blind spots |
| Cost | Several parallel probing sessions for some hours, the fixes they lead to, the bounded re-probe, and one spot check. The cut moves later by that much |
| Risk | The battery misses a class; the spot check is the guard. Fix-only findings piling up; they do not hold the cut |

## Fit/gap

| Must satisfy | Middle | (i) | (ii) | (iii) |
|---|---|---|---|---|
| decision-0016 point 4: no contract change between 0.9.0 and 1.0.0 | Fit: contract-bearing findings land before the cut | Fit, but semantic gaps may slip | Partial | Fit |
| Bounded in time and cost | Fit: fixed scope, re-probe only what fixes touch | Fit | Fit | **Gap** |
| Coverage reported with its denominator (knowgov's own rule) | Fit | Fit | **Gap** | **Gap** |
| Catches the semantic class (slice keys, C4) | Fit: combination probes | **Gap** without them | Partial | Partial |
| A guard on the pass's blind spots | Fit: the spot check | **Gap** | **Gap** | Partial |

## SWOT

| | Helpful | Harmful |
|---|---|---|
| **Internal** | **S:** finite, checkable, aimed at the observed defect classes, guarded by an independent sample | **W:** the cut moves; the surface list must be kept honest |
| **External** | **O:** the surface list and battery become a reusable release check for every later minor | **T:** a class outside the battery and the sample; fix-only findings mistaken for cut blockers |

## Advice

The middle option, as the maintainer chose. It is the only option that is bounded, carries a denominator and has a guard on its blind spots. Holding the cut only for contract-bearing findings keeps the validation from becoming an open-ended delay.

## Consequences

- **doc-0028** gains G9-17: the contract validation pass done, as point 6 defines it.
- **The pass is a task, task-0256.** The probing sessions are dispatched by the coordinator.
- **The SNAP-04 investigation**, already under way, is part of the pass's store surface.
- **Fix-only findings** are tasked for 0.9.x and do not hold the cut.
