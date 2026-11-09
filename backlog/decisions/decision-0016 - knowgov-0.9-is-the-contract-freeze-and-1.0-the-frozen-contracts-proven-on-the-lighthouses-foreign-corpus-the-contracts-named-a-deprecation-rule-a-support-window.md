---
id: decision-0016
title: >-
  knowgov 0.9 is the contract freeze and 1.0 the frozen contracts proven on the
  lighthouse's foreign corpus: the contracts named, a deprecation rule, a
  support window
date: '2026-11-06T09:04:00Z'
status: accepted
---
## Context

On 2026-11-06 the maintainer asked what a knowgov v1.0, or a v0.9, needs. The record defines neither (doc-0028 §1). decision-0003 covers 0.x only, and doc-0012 §6 places "1.0 contracts after a foreign corpus" at S3, 18–36 months out.

By decision-0003 §2, every contract change raises the minor version:
- 0.1.0 to 0.7.0 took four days;
- Unreleased already makes the next release 0.8.0;
- the next contract-changing release after it would be 0.9.0 by counting alone (doc-0028 §2).

decision-0003's contract list also leaves out surfaces adopters depend on (doc-0028 §3). doc-0012 §8: a version number moves E1 by one point; the lighthouse moves the rest.

## Options

- **(a) 1.0 by declaration,** once doc-0028's freeze list (G9) is met: weeks, by the maintainer alone.
- **(b) 0.9.0 the freeze, 1.0.0 at the lighthouse:** G9 for 0.9.0; G1-1 to G1-4 for 1.0.0.
- **(c) 1.0 at doc-0012 S3 only:** 0.x runs on (0.10, 0.11, …) until there are ten instances and a second maintainer.
- **(d) No decision:** the counter reaches 0.9 by arithmetic, and 1.0 is decided later.

## Opportunity canvas (of b)

| Box | Content |
|---|---|
| Problem | Nothing tells an adopter which of knowgov's interfaces will hold. There were six contract changes in four days; the version number counts changes and promises nothing. |
| Who, and when | The lighthouse pilot's platform team, at procurement and at every upgrade. An integrator embedding a connector (task-0058). The maintainer, at every release PR. |
| Today | decision-0003 §2: any contract change raises the minor. No deprecation rule, no support window, and a partial contract list. |
| Solution | 0.9.0 names and freezes the contracts, with a deprecation rule and a support window. 0.9.x carries fixes only. 1.0.0 follows once the pilot has run on those contracts unchanged. |
| Measure | Contract changes per release after 0.9.0 (target: none before 1.0.0, each one a 0.10.0 restart). The pilot's upgrades and breakages. The time from 0.9.0 to 1.0.0. |
| Cost | Mostly decisions: the name (task-0061), the licence (task-0058), the contract list. One contract change (format versions, doc-0028 P1). A docs pass. Contract changes held from 0.8.0 to 0.9.0, as 0.7.0 was held. |
| Risk | A freeze before the pilot's first instance may freeze the wrong thing, and the pilot's needs then restart the count (0.10.0). Batching delays fixes adopters want. |

## Fit/gap

| Must satisfy | How (b) meets it | Gap |
|---|---|---|
| SemVer 2.0.0: 1.0.0 defines the public API | 0.9.0 names it (point 3) | none |
| decision-0003 §2: a contract change raises the minor in 0.x | kept up to 0.9.0, and amended for 0.9.x (point 2) | it amends an accepted decision |
| doc-0012 §6 S3: "1.0 contracts after a foreign corpus" | kept, and brought forward to the first corpus | S3 meant more than one corpus; one pilot is the floor, not S3 |
| An adopter can tell what holds across an upgrade | the deprecation rule (point 5) | it applies from 1.0.0 only; 0.9.x relies on "fixes only" |
| One maintainer's capacity | support for the latest minor only, until task-0060 (point 6) | no long-term support |
| The register's and pumllint's own 0.x | pinned and vendored; the formats an instance may use are named (point 3) | the register's format can still change under an instance's own checkout |
| One record per thing | the gap lists stay doc-0028's and the scores doc-0012's | none |

## SWOT (of b)

- **Strengths.**
  - The number means something. 0.9 tells an adopter the contracts are named and held; 1.0, that a foreign corpus has run on them.
  - The maintainer reaches 0.9.0 alone.
  - It keeps doc-0012's condition and the external reviewers' "plug in first".
- **Weaknesses.**
  - 1.0.0 waits on a third party (task-0062 AC #2), so its date is not the maintainer's.
  - Holding contract changes between 0.8.0 and 0.9.0 slows a fast-moving project.
  - The contract list is wide (MCP tools, `KG_*` settings, CI inputs), so the freeze binds a lot.
- **Opportunities.**
  - The pilot's procurement will ask what holds; 0.9.0 answers before the first meeting.
  - The licence and name decisions (task-0058, task-0061), long open, gain a deadline.
  - Stable interfaces give the external pass (doc-0027) something firmer to score E1 on.
- **Threats.**
  - The pilot needs a contract change in its first week, 0.10.0 follows 0.9.0 at once, and the freeze reads as theatre.
  - 1.0 is read as product maturity while E2 to E4 stay low (doc-0012 §8).
  - Two upstream 0.x formats change under an instance.

## Advice

The drafter recommends **(b)**, for four reasons:
1. It is the only option where the number carries information an adopter can act on, at both steps.
   - (d) leaves 0.9 to arithmetic, within days.
   - (a) says "stable" before anyone but the maintainer has used an interface, so the pilot's first need becomes 2.0.0.
   - (c) withholds any promise for 18–36 months from the very pilot S1 needs.
2. It keeps the record's own condition (doc-0012 §6) and moves it to the first corpus, which is where the evidence will come from.
3. The maintainer can reach 0.9.0 alone, mostly through decisions already open (task-0058, task-0061).
4. The restart rule (0.10.0) is honest about the risk instead of hiding it.

Against it: 1.0's date depends on task-0062. If the maintainer wants a date under their own control, the fallback is (a) after 0.9.0, with the pilot's first breaking need taken as 2.0.0.

## Decision (proposed)

1. **0.9.0 is the contract freeze.** It is cut when doc-0028 §4's G9-1 to G9-10 are met:
   - this decision accepted;
   - format versions on the instance's inputs;
   - task-0157, task-0160 and task-0148 merged;
   - an image that runs every feature, published;
   - task-0163 merged;
   - each Known limit closed, tasked, or named a 1.0 limit;
   - the names (task-0061) and the licence boundary (task-0058) decided;
   - the adopter docs checked.
2. **0.9.x carries fixes only.** A fix, a documentation change or a dependency pin is a patch. Any contract change, additive or breaking, is 0.10.0 and restarts the freeze. This amends decision-0003 §2 from 0.9.0 on. Until 0.9.0, decision-0003 §2 stands, and contract changes after 0.8.0 gather for 0.9.0.
3. **The contracts at 1.0** are decision-0003 §2's list (the gate command's exit codes and flags, the JSON shapes under `harness/schemas/`, the instance layout, the store port, the subject manifest format), and also:
   - the MCP reader's and the runs server's tools, prompts, and their inputs and outputs;
   - the `KG_*` settings that `instance/README.md` or `docs/security.md` documents (an undocumented setting is not a contract);
   - the page's HTTP API, as `demo/README.md` documents it;
   - the inputs and outputs of `instance/ci/`: the action, the GitLab include, the shell wrappers, the hooks' settings snippets;
   - the image's name and tag scheme (decision-0003 §3);
   - the format versions of the instance's inputs, and the ieam-register format versions an instance's register may be in.
4. **1.0.0 is cut when** all of these hold:
   - the lighthouse's instance (task-0062) has run on the 0.9 contracts with no contract change;
   - the incumbent's route is verified on its installation (task-0063 AC #2, #5);
   - a counterparty that can offer support exists (task-0060).
5. **Deprecation, from 1.0.0.** A contract element is deprecated in a minor release, under a `### Deprecated` heading in `CHANGELOG.md`. It keeps working for at least one further minor and ninety days, and is removed only in a major. Ninety days is the drafter's figure.
6. **Support.** Until task-0060's entity exists, the latest minor only, on a best-effort basis; from then, the entity's support terms.
7. **After 1.0.0, SemVer proper:** an additive contract change raises the minor, a breaking one the major.

## Consequences

- 0.8.0 is unaffected.
- If accepted, contract changes after 0.8.0 are held for 0.9.0, as 0.7.0 was held (task-0141's notes).
- doc-0028's proposed tasks (§9) go to the coordinating session for review and minting. This record mints none.
- Once accepted, `instance/README.md` states the contracts at 1.0 in the adopter register (doc-0028 P4).
- doc-0012 §8's v1.0 rows read under this definition.
- If the maintainer chooses (a) instead, points 1 to 3 and 5 to 7 stand. Point 4 becomes: 1.0.0 is cut on 0.9.0's contracts after a stated time without a contract change.

## Acceptance (2026-11-06)

The maintainer, 2026-11-06 ~16:5x UTC: "approve decision-0016 option (b)". The decision is accepted as written, without amendment. Point 5's ninety days stand as the drafter's figure, accepted with the rest.

**In force from now (point 2):**
- Contract changes after 0.8.0 gather for 0.9.0.
- Unreleased already holds four:
  - B7, one reader for every subject (task-0157);
  - the raw-byte file Version digest (task-0160);
  - response sizes bounded (task-0177);
  - a Neo4j load refused over its transaction memory (task-0176).
- decision-0003 §2 stands until 0.9.0. From 0.9.0 on, 0.9.x carries fixes only, and any contract change is 0.10.0 and restarts the freeze.

**The freeze list (doc-0028 §4) at acceptance:**

| | gap | state |
|---|---|---|
| G9-1 | this decision | met |
| G9-2 | format versions | task-0174's plan filed, scheme the maintainer's |
| G9-3 | known contract changes | task-0157 and task-0160 merged; task-0148 waits on the maintainer's Claude Desktop test |
| G9-4 | a published image | v0.8.0; 0.9.0's own image follows its release |
| G9-5 | CI budget | `rdflib` 17.2 min over 12; task-0180 proposed |
| G9-6 | Known limits | task-0173 done, task-0175 to task-0178 closed; 13 proposed 1.0 limits are the maintainer's to name |
| G9-7 | the name | task-0061, the maintainer's |
| G9-8 | the licence boundary | task-0058, the maintainer's |
| G9-9 | adopter docs | #291; the guide's walk section to check |
| G9-10 | upstream formats | point 3 |

**Consequences, executed:**
- doc-0028 P4 is minted as task-0181: `instance/README.md` states the contracts at 1.0.
- CLAUDE.md's Releases paragraph names this decision.
- `CHANGELOG.md` gains an adopter line under Unreleased.

## Amendment A1 (2026-11-09; accepted 2026-11-09): 1.0.0 means ready for a lighthouse, not run by one

### Context

Point 4 cut 1.0.0 only when three conditions held:
- the lighthouse's instance had run on the 0.9 contracts unchanged (task-0062);
- the incumbent's route was verified on its installation (task-0063);
- a support counterparty existed (task-0060).

decision-0031 kept them. All three wait on third parties.

The maintainer, 2026-11-09, answered the open question of who the lighthouse is: "I do not have a confirmed lighthouse yet, so float 1.0 without one", then: 1.0 = "ready for lighthouse". Without a lighthouse, point 4 gives 1.0.0 no date and no condition knowgov controls.

### Options

- **(a) Readiness plus a soak.** The drafter's advice; see "What changes" below.
- **(b) Readiness, no soak.** 1.0.0 as soon as conditions 1, 3 and 4 below hold. That could be days after 0.9.0.
- **(c) A soak only.** 1.0.0 after a stated time on 0.9 without a contract change. This is the fallback the original record named for option (a).

### What changes

Point 4 now reads: **1.0.0 is cut when all of these hold.**
1. 0.9.0 is cut: doc-0028's G9 met, the validation pass (G9-17) included.
2. The 0.9 contracts have held for **30 days** from 0.9.0 with no contract change, across at least one 0.9.x patch release. Any contract change in that time is a 0.10.0 and restarts the freeze (point 2).
3. A lighthouse can start without the maintainer's hand. Its path is complete and proven on the example instance:
   - decision-0031's acceptance protocol (A07 to A14, AT01 to AT12) is in `docs/lighthouse-evaluation.md` and runnable;
   - task-0057's pre-registration template is ready;
   - the onboarding path works end to end, with G9-3's Desktop test done.
4. The release's Known limits name what only a lighthouse or a third party can prove:
   - no lighthouse has run on the contracts (task-0062);
   - the incumbent's route is unverified on a real installation (task-0063);
   - no support counterparty exists, so support stays best-effort on the latest minor (point 6, task-0060).

Points 1 to 3 and 5 to 7 stand. Point 5's deprecation rule and point 7's SemVer apply from 1.0.0, as before.

### Opportunity canvas

| Box | Content |
|---|---|
| Problem | 1.0.0 waited on a lighthouse that does not exist yet, so it had no date, and a prospective lighthouse is asked to adopt a 0.x |
| Users | A prospective lighthouse's platform team, which can now adopt a 1.0 with a deprecation promise. The maintainer, whose 1.0 no longer waits on a third party |
| Proposal | (a): 0.9.0, a 30-day soak with no contract change, a lighthouse path proven on the example instance, and the third-party items named as Known limits |
| Unique value | 1.0 means what it promises: the contracts held, a lighthouse can start, and what is still unproven is stated |
| Cost | The soak (30 days after 0.9.0), and making decision-0031's protocol runnable before a pilot exists (task-0285) |
| Risk | A lighthouse later needs a contract change. After 1.0.0 that is a minor or a major under point 7, with point 5's deprecation window, not a restarted freeze |

### Fit/gap

| Must satisfy | (a) | (b) | (c) |
|---|---|---|---|
| The maintainer's "1.0 = ready for lighthouse" | Fit | Fit | **Gap:** time says nothing about readiness |
| Conditions knowgov controls | Fit | Fit | Fit |
| Stability shown before the contracts are promised (SemVer 2.0.0 §5) | Fit: 30 days and a patch | **Gap:** frozen with no time in use | Fit |
| Honesty about what is unproven (decision-0016 point 6, decision-0031) | Fit: the Known limits | Fit | Partial |
| decision-0031's protocol as the lighthouse's | Fit: made ready now, run at the pilot | Fit | Gap: not required |

### SWOT

| | Helpful | Harmful |
|---|---|---|
| **Internal** | **S:** a date the maintainer controls; a checkable list; the soak catches a contract change before the promise | **W:** the soak delays 1.0 by 30 days; the protocol work moves before a pilot |
| **External** | **O:** a prospective lighthouse can sign on to a 1.0; the matrix's tests become a sales asset | **T:** the first real corpus finds a contract gap after 1.0. That is a minor or a major, with point 5's window, not a 0.10 restart |

### Advice

(a). It is the only option that makes 1.0 mean what the maintainer said, keeps a stability proof the record can measure, and states plainly what a lighthouse has yet to prove. The 30 days are the drafter's figure, as point 5's ninety days were.

### Acceptance of A1 (2026-11-09)

The maintainer, 2026-11-09: "I do not have a confirmed lighthouse yet, so float 1.0 without one"; then: 1.0 = "ready for lighthouse"; and, on the options the coordinator set out, "A1 as advised". **A1 is accepted: (a), with a 30-day soak.** It replaces point 4's three conditions with the four above. decision-0031's choice stands: the matrix is the lighthouse's acceptance protocol. Its note that "point 4's three conditions stay" is superseded by A1, and its "minted at the pilot's go" becomes "made ready before 1.0" (task-0285).
