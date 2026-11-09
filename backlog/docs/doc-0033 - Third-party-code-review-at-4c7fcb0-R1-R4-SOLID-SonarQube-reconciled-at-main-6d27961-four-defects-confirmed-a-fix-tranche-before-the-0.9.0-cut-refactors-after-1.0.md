---
id: doc-0033
title: >-
  Third-party code review at 4c7fcb0 (R1-R4, SOLID, SonarQube) reconciled at
  main 6d27961: four defects confirmed, a fix tranche before the 0.9.0 cut,
  refactors after 1.0
type: other
created_date: '2026-11-09T06:59:00Z'
updated_date: '2026-11-09T06:59:00Z'
---
*Filed by the coordinating session (session_01HTAA1UV2N6XGtCwCvVnB5t) on 2026-11-09. The maintainer asked for a review of the third-party handover "KnowGov v1.0 scope and code review", covering opportunity, SWOT, fit/gap and software quality, with a plan for the improvements, corrections and refactorings that would pay. The handover's own instruction, "do not modify … until that reconciliation has been reviewed", is the third party's, and the maintainer's request supersedes it. This doc and the tasks it names are that plan. Nothing here changes code.*

## What was read

The handover combines two parts.

- **Part 1**, the v1.0 scope and release acceptance proposal at `ec4e693`: S01–S15, A01–A18, AT01–AT12 and GAP-01 to GAP-06. It is **word for word the handover reconciled on 2026-11-08**; only the heading levels differ, which a line diff confirms. Its questions are answered:
  - decision-0023 A1 (R1) and decisions 0028 to 0031 were accepted 2026-11-09 ("all as advised");
  - GAP-06 is task-0239;
  - GAP-03 to GAP-05 wait for the pilot's go (decision-0031).

  Nothing in Part 1 is reopened here.
- **Part 2**, an implementation, SOLID and SonarQube review at `4c7fcb0` (9 November):
  - four reproduced findings, R1 to R4;
  - a feature verification over S01 to S15;
  - a SOLID assessment;
  - a SonarQube Community Build scan, with its triage;
  - a test run.

Part 2 is new. Every finding was re-verified at `main` `6d27961`.

## Reconciliation of Part 2 at `6d27961`

| Item | Verdict at `6d27961` | Evidence | Disposition |
|---|---|---|---|
| **R1** A malformed `block_levels` passes validation and weakens the gate | **Confirmed** | `tools/check_subject.py` checks each level only `if isinstance(bl, list)`, so a string or an integer passes. `harness/tasks.py` builds `set(spec.get("block_levels", …))`, so `"absent"` becomes `{'a','b','s','e','n','t'}`, nothing blocks, and the verdict is QUALIFIED with exit 0. `max_unverified_share` is coerced by `float()` at runtime, so a string the checker refuses still runs if the checker is skipped | task-0242 |
| **R2** Distinct numeric values corroborate | **Confirmed** | `harness/rules.py` `compatible`: `float(a) == float(b)`, so `9007199254740992`/`…993` and `1e309`/`2e309` compare equal. `_is_num` accepts what `float()` accepts, `inf` and `nan` included. One function serves R-CORROBORATE, R-CONFLICT, the review's dispute check, capture and load. Both adapters only supply candidate pairs, so one fix covers both stores | task-0243 |
| **R3** Mixed inference bases give a flag chosen by the hash seed | **Confirmed** | `harness/gate.py` `resolve_spec`: `flags.add(next(iter({r["basis"] for r in rows})))`. The verdict is unaffected, but the report's `flags` vary with `PYTHONHASHSEED` | task-0244 |
| **R4** `.env` files enter the image | **Confirmed** | `demo/Dockerfile` has `COPY . /repo`, and `demo/Dockerfile.dockerignore` has no `.env` rule. `demo/docker-compose.yml:11` invites a `.env` beside the compose file, which is inside the build context, so a key written there is baked into a locally built image's layers. CI's release image is built from a clean checkout, so the published image is not affected | task-0245 |
| Test failure `test_page_subject…request_names` | **Confirmed as a test leak, not a product defect** | The image sets `KG_PAGE_LISTEN=0.0.0.0` (`demo/Dockerfile:14`). A test run inside the image inherits it, and the wide-bind refusal (403) answers before subject routing (404). CI runs on the runner, where the variable is unset | task-0246 |
| SOLID: interface segregation | **Confirmed** | `Store` declares 91 methods (AST count). Consumers use small subsets; the `READS` allow-list gives a runtime permission, not a static interface | task-0247 (after 1.0) |
| SOLID: dependency inversion | **Confirmed** | `SUBJECT` and `TASKS` are built at import. 48 modules under `harness`, `demo/app`, `tools` and `instance/ci` import `subject`; the review's 43 used a narrower scope. decision-0013's child process per other subject depends on this | task-0247 (after 1.0) |
| SOLID: single responsibility | **Confirmed** | `harness/mcp_server.py` is 1,498 lines: tools, dispatch, both protocol eras and both transports. `proposal_impact.py` is 1,194 lines. Sonar's cognitive complexity is 148 (`review.check`), 127 (`proposal_impact`) and 111 (`preload_check`), against a threshold of 15 | task-0247 (after 1.0) |
| SOLID: Liskov, open/closed | **Agreed, as strengths** | Adapter parity, the round trip, the comparator and the order contract (task-0201) hold behaviour, not only signatures | none |
| Sonar: `index.html:547`, `const st = … ? null : null` | **Confirmed dead code** | `st` is unused | task-0246 |
| Sonar: `store.py:720`, `v != v` | **Intentional (NaN)** | It keeps its meaning; `math.isnan` would say it plainly | task-0246 |
| Sonar: MD5 in `harness/annotate.py:148,151` | **Not a vulnerability; one portability point** | It is a fingerprint GitLab compares, already marked `noqa: S324`. On a FIPS-mode Python, `hashlib.md5()` without `usedforsecurity=False` can raise | task-0246 |
| Sonar: HTTP in namespace constants | **False positive** | XML, BPMN and ARIS namespace identifiers | none |
| Sonar: HTTP in the page's URL construction; world-writable job folder | **Documented design** | Loopback default, `KG_PAGE_TOKEN`, and the TLS proxy for a wider bind (`demo/README.md`). The job folder is the worker's shared volume (`docs/security.md`, decision-0012) | none; stays named |
| Sonar: the app image runs as root | **Confirmed hardening point** | `demo/Dockerfile` has no `USER`; the worker runs as `65534:65534` (compose). Changing the app's user changes who owns `runs/` and the store volumes, so an upgrade needs a migration | task-0248 (decision first) |
| Sonar: regular expressions on runtime input | **Unproven risk** | No denial-of-service was reproduced. Patterns that read adopter documents and manifests deserve a bounded-time review | task-0249 |
| Sonar: 1,490 composite-assertion and 161 monkeypatch findings | **Style, by design** | The stdlib runner is the project's promise (CLAUDE.md) | none |
| Sonar quality gate FAILED | **Not a repository signal** | No coverage was imported, and the comparison baseline was the review's own earlier scan | see advice |

The feature verification (S01 to S15) agrees with the record and claims no more than it shows. Every accepted limit it names is a named limit or a tasked one: K21, the legacy unbound forms, one held scenario (U1), the shell-write bypass (K20), and independent-corpus acceptance.

## Software quality

Read against ISO/IEC 25010's characteristics.

- **Functional correctness.** R1, R2 and R3 are one class: **an input domain not closed at the boundary**.
  - R1: a configuration type not checked where it is consumed.
  - R2: a value domain (exact decimals, non-finite values) left to a float.
  - R3: an aggregation whose order the language does not define.

  Each is cheap to close and each has a precise regression case. None moved a recorded verdict, which is why the comparator never saw them. Records cover the values they hold, and no others.
- **Security.** R4 is real for locally built images, and closed by two ignore rules and a test. The rest of the scan's security list is either documented design or a false positive.
- **Reliability and testability.**
  - The test leak shows the suite assumes the runner's environment.
  - R3 shows determinism is held for the records, not for every input.

  A seed-varying regression test makes the second one structural.
- **Portability.** The FIPS-mode MD5 point is cheap to fix. The worker's Linux and Landlock floor stays K1.
- **Maintainability.**
  - **Mostly strengths:** duplication at 0.2%, a single Cypher module, adapter parity and the order contract.
  - **Weaknesses:** a wide port, import-time globals, and a few very complex functions. They raise the cost of change; they cause none of R1 to R4.

  decision-0016 makes the contracts stable from 0.9.0, so a refactor now risks the freeze for no adopter-visible gain.

## Opportunity canvas (of the plan)

| Element | Content |
|---|---|
| Problem | Four confirmed defects. One, R1, can silently weaken a configured block, and the freeze is about to make the surrounding code long-lived |
| Users | Adopters whose policies and values go beyond the public subjects; the lighthouse first; the maintainer, who needs the 0.9.0 contracts to be correct as frozen |
| Proposal | The fix tranche task-0242 to task-0246 lands before the 0.9.0 cut, beside the items the cut already waits on. The SOLID refactors wait until after 1.0 (task-0247). The image's user (task-0248) and the regex review (task-0249) are bounded follow-ups. SonarQube is not adopted as a gate |
| Unique value | Each defect gets a regression case taken from the reviewer's own probe, so the class stays closed. The freeze is spent on correctness, not structure |
| Cost | Five small tasks, each a module plus its tests; none touches a contract shape. A sub-session each, in parallel |
| Risk | R2 and R3 change outputs in edge cases; the comparator and the round trip must show the record unmoved. R1 turns a silently weak configuration into exit 2, which is the fail-closed direction |

## Fit/gap

| Must satisfy | The plan | Evidence |
|---|---|---|
| decision-0016 point 2: 0.9.x carries fixes only | Fit: task-0242 to task-0246 are fixes, and the refactors wait | task-0247 |
| decision-0016 point 4: no contract change between 0.9.0 and 1.0.0 | Fit: no schema, exit-code or setting changes shape. R1's exit 2 for a malformed policy is the gate contract's existing "cannot run" | the gate contract |
| The record does not move | Fit, by acceptance criterion on every task | the comparator and the round trip |
| The stdlib-only promise (CLAUDE.md) | Fit: no pytest and no new dependency; Sonar is not adopted | — |
| The reviewer's priorities (R1 and R2 P1, R3 and R4 P2) | Fit: all four before the cut | — |
| The reviewer's "refactor incrementally, avoid a broad rewrite during the freeze" | Fit: after 1.0, and only the refactor a fix needs before then (task-0242's single validator) | — |
| The accepted limits stay honest | Fit: none is closed by this plan | — |
| Gap: Sonar's coverage and new-code gate | Left open by choice. The repository measures its own coverage with a declared denominator (task-0159); the Sonar baseline is the maintainer's call (question 3) | — |

## SWOT (of the plan)

| | Helpful | Harmful |
|---|---|---|
| **Internal** | **S:** every finding was re-verified on current `main`; each fix is small and has a ready regression case; the cut does not wait on the refactors | **W:** the wide port and the import-time globals stay through 1.0; complex functions stay complex until touched |
| **External** | **O:** the third-party probes become permanent regression tests. A narrow store protocol later helps any third adapter. A tuned, advisory Sonar run could follow 1.0 | **T:** the lighthouse brings policies and values the records never held. R1 and R2 are exactly that class, so a cut without them would ship the defects under the freeze |

## Advice

1. **Hold the 0.9.0 cut for task-0242 to task-0246, as G9-16.** They are fixes, so they could ship in 0.9.x, but R1 weakens a block silently and R2 promotes a false corroboration. Both should be right in the first frozen release. All five run in parallel with what the cut already waits on (#397, task-0241 and the Desktop test), so they cost no time.
2. **The SOLID refactors wait until after 1.0** (task-0247, parked):
   - narrow store-consumer protocols with an AST guard, as the Cypher guard does;
   - an explicit validated context in place of the import-time globals, within decision-0013's process isolation;
   - `mcp_server.py` split into transport and use-case modules;
   - the three complexity hotspots, each behind characterisation tests.

   Before then, a refactor only where a fix needs it.
3. **SonarQube is not adopted as a gate.** The stdlib runner makes its test-style rules noise, and its coverage gate would need an import the project does not produce. An advisory scan with a tuned profile can be weighed after 1.0.
4. **The app image's user, task-0248: decide first.** Running as a non-root user is right in principle. It changes who owns `runs/` and the store volumes, so it needs a migration note, and it belongs with the first release that can carry an upgrade step.
5. **task-0249**, the bounded-time review of the regular expressions run on adopter input, is a 0.9.x item and not a cut condition.

## Questions for the maintainer

1. Do task-0242 to task-0246 join doc-0028's G9 list as G9-16, so that 0.9.0 is not cut without them? Advice: yes.
2. Do the SOLID refactors wait until after 1.0, as task-0247? Advice: yes.
3. Is SonarQube left out as a gate, with an advisory scan reconsidered after 1.0? Advice: yes.
4. Does the app image's non-root user (task-0248) wait for a decision, after the cut? Advice: yes.
