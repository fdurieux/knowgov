---
id: doc-0004
title: 'AI-native SDLC playbook: opportunity canvas, fit/gap, sense and nonsense'
type: specification
created_date: '2026-11-02T12:37:00Z'
updated_date: '2026-11-02T12:37:00Z'
tags:
  - canvas
  - fit-gap
  - brief
  - sdlc
---
*2026-11-02. Maintainer register. An outside text read against the five repositories, written before anything is built: Anthropic's "The AI-Native SDLC Playbook" (Claude Code, 54 pages, L. Claxton), supplied by the maintainer as a PDF and not vendored here. The trigger was the maintainer's ask of this date: its relevance to knowgov, pumllint and Legible as an opportunity canvas, a fit/gap, a sense/nonsense reading, and its fit with Backlog.md. Nothing queued; every item below waits for pull.*

## Verdict

Sense, and the strongest outside corroboration of Legible's thesis to date, with the same blind spot pumllint's `docs/spec-stack-evaluation.md` (2026-07-29) found in another recommendation. The playbook says code is no longer the bottleneck and the work moves to the stages around build; it then gives deterministic controls (hooks, tests, evals) only from build onward, while `intent.md`, `spec.md` and `plan.md` get a human review and skills, which it calls advisory itself (p26). pumllint, knowgov's gate and ieam-register are the deterministic layer it leaves out upstream of build. What it adds is packaging (skills, hooks, evals) and a vocabulary an adopter already holds. No architecture moves, no never-build is touched, no trigger fires.

## The text, compressed

- Six stages as a loop: Plan, Design, Build, Test, Deploy, Maintain. Each stage commits an artefact the next reads: `intent.md` → `spec.md` → `plan.md` → diff and tests → PR findings → incident record → a new `intent.md`. The chain of commits is the audit trail.
- A skill is an advisory control; a hook is the deterministic one behind it (exit 2 blocks the action). Evals run in CI on any change to `CLAUDE.md`, skills or hooks.
- "The agent may act up to the production gate and cannot pass it." Detection stays deterministic; the model is invoked once a band is breached, and the tier sets what it may do.
- Sidebar, p22: one named source of truth per artefact; linkage (ids both ways between repo and legacy tool) as the minimum bar.

## Opportunity canvas

| Element | Reading |
|---|---|
| Problem | Each project's evidence argues for gating what is upstream of code in its own terms. No frame an adopter already holds shows where those gates plug in. |
| What the playbook adds | A vendor-published lifecycle with named slots: skill, hook, eval, approval gate, an "independent confidence gate between stages, a deterministic check or an adversarial reviewing agent" (p48), and the source-of-truth sidebar. Each project here maps to one of them. |
| Users | The maintainer, packaging the gates. An adopter's platform team, which owns hooks and managed settings. The operator of a private instance (m-2). |
| How it is done today | pumllint `docs/agents.md` carries a paste-ready instruction block for `CLAUDE.md`. No repository has `.claude/` skills or hooks. Rules such as "never edit a vendored file by hand" live as prose in `CLAUDE.md`. |
| What a user gets | pumllint as a hook on `.puml` edits and a check on a spec's pull request; knowgov's gate as the confidence gate between design and build; the register as the linkage layer the sidebar asks for. |
| Measures | Pull for the skill or hook packaging (demand, not supply). Count of agent sessions here that break a `CLAUDE.md` "never" rule, which says whether a hook pays. |
| How it starts | 1. Hooks on each repository's own protected paths (dogfood, no adopter needed). 2. A pumllint `SKILL.md` from `docs/agents.md` plus a hook recipe. 3. task-0007/task-0016, the gate CLI, framed as the confidence gate. 4. A dated Legible ROADMAP entry mapping the six stages onto the pipeline map. |
| Risks | Coupling the gate contract to one vendor's hook protocol. Re-deriving shipped work, as `docs/sdd-manifest-evaluation.md` recorded of another recommendation. A second record through `intent/`, `spec/`, `plan/` folders. |
| Gains | A frame adopters already recognise for Legible's thesis; measured evidence to set where the playbook makes untagged claims. |
| Cost | Hook scripts and a `SKILL.md`: hours. The gate CLI is queued already (task-0007, task-0016). No new dependency on pumllint's product path. |

## Fit and gap, play by play

| Play | Here today | Gap | Reading |
|---|---|---|---|
| Capture `intent.md` | knowgov's user-story tasks; briefs doc-0001 to doc-0003 (richer than an intent); ROADMAP items with triggers | Intents carry no register id (`CAP-`, `PROC-`); nothing checks their wording | Fit. Evidence for Legible's "Requirements wording linter" (planned) and "User-story quality" (open) rows, not a trigger. |
| Requirements and design, `spec.md` | pumllint `score`, `--profile codegen`, `trace`; the J-F kit (EARS requirements, contracts, Gherkin) | `spec.md` is prose; pumllint covers only its diagrams | Fit on the diagram part, measured: below Level 2 costs about 21 points of executed correctness (`docs/agents.md`, EVIDENCE.md). |
| Plan mode, `plan.md` | Backlog.md's implementation plan on a task | Plan against diff is unchecked; the playbook only measures it after the fact | Open gap, the same as Legible's "Diagram-versus-code drift" row. |
| `CLAUDE.md` | All five repositories, used heavily | The playbook says under a page; aris2puml's is 365 lines, pumllint's 131, this one 113 | Tension. Investigation-saving context could become skills loaded on demand. The maintainer's call. |
| Skills | None | A pumllint skill (score, gap report, repair, re-score) is `docs/agents.md` repackaged | Cheap. pumllint's demand scan already saw steering and skills files teaching agents PlantUML. |
| Hooks, build guardrails | None; the rules are prose | Here: "never edit a vendored file or its note", "Backlog files only through the CLI". pumllint: `kg_experiment/` frozen. aris2puml: "never edit the expected file by hand". All are the playbook's protected paths | Best fit: deterministic, dogfoodable, no adopter needed. |
| Feedback loop | `tests/run_tests.py`, the comparator, golden tests, the oracle | None | Ahead of the playbook. |
| Continuous evals | The arms, the oracle and the comparator are an eval harness for "does governed context change the agent's output" | No eval when `CLAUDE.md` or a skill changes | Fit as "evals of governed context". A hypothesis until a subject is built from a repository's own `CLAUDE.md`. |
| AI in the review loop | Standing merge-on-green; PR subscription | No `REVIEW.md` | Minor. |
| Hooks as approval gates | ieam-register: `approval = { by, on, record }`, approver never the author, checked in CI | None | Stronger than the playbook: approval of content, not of an action. |
| Agent stops at the production gate | A hosted session's tag push is refused; the owner publishes the Release | None | Literal match, already in place. |
| Closing the loop | aris2puml `drift.yml`, a scheduled deterministic detector | A red run writes no intent | Small; low value for one maintainer. |
| Claude Tag, Claude Design, managed review, managed settings | None | Not relevant to the public repositories | Relevant to m-2: a regulated client's managed settings should keep artefacts off hosted models, as the endpoint off by default already does (task-0005, task-0013). |

**Exit codes.** A Claude Code hook blocks on exit 2. The gate contract uses 1 for findings and 2 for "cannot run" (task-0007 AC #1: 1 on BLOCKED). A hook calling pumllint or the gate CLI therefore needs a three-line adapter, findings 1 → 2, cannot-run 2 → a non-blocking error. The contract stays: `action.yml` and both pre-commit hooks depend on it.

## Sense and nonsense

**Sense**
- The bottleneck moved upstream and downstream of build: Legible's thesis, reached independently by pumllint's `docs/sdlc-tooling-landscape.md`.
- Skill advisory, hook deterministic: the gate contract's "covered only when it exits non-zero" in the vendor's words.
- Detection deterministic; the agent proposes and never promotes; it acts only through gated routes. knowgov already holds model output at `inferred` or `proposed`.
- One named source of truth per artefact: "one record per thing" here, and the register's `[source]` pointer.
- Write the failing test first; the agent may not weaken the check. Matches "never skip a test to get green".

**Nonsense or weak**
- "Machine actionable" `intent.md` and `spec.md` carry no schema, no ids and no checker: actionable only in that a model can read them. The blind spot itself.
- Requirements and design in one agent session the product owner "reviews but doesn't write". The proof of concept measured the risk (pumllint `docs/neo4j-governed-knowledge-evaluation.md`, one model, n = 5): the documents-only arm adopted an unreviewed machine note as a decision in 4 of 5 runs and resolved an undeclared contradiction by a precedence it invented in 4 of 5; the governed arm never generated under BLOCKED, 20 of 20 cells. The degradation test: six of fifteen planted defects reached the code, each through the highest-ranked layer that stated the behaviour (Legible `model/v0.3-change-note.md`, D1). The playbook declares no precedence between intent, spec and plan and detects no conflict; an agent-written `spec.md` a product owner skims is that unreviewed note.
- Its measures are speed (time to intent, time to spec); quality appears only as later rework. No claim carries evidence: in Legible's tags all of it is mechanism or hypothesis.
- No decision artefact: the "why" survives only in PR threads. `backlog/decisions/` and ieam-register's `decisions/` hold it here.
- No false-assurance case. J-F's data-lane set lints clean, scores Level 5 100/100, traces fully and carries 25 claims the code contradicts (J-F #309, quoted in Legible's v0.3 change note, C4). A passing gate over a drifted artefact is worse than none; the playbook's `plan.md` drift advice ("consider a hook") does not see it.
- Stage 6 control bands (5xx rate, Western Electric rules) have no target here: no production service. PR cycle time would.

## Fit with Backlog.md

Backlog.md is the playbook's "repo as the source of truth" configuration with more structure: statuses, dependencies, milestones, stable ids, decisions.

| Playbook artefact | Its home in this backlog |
|---|---|
| `intent.md` | A task's description (the "As a … I want … so that" tasks) or a brief under `backlog/docs/` |
| `spec.md` | A `specification` document under `backlog/docs/`, as doc-0001 to doc-0004 are, plus the task's acceptance criteria |
| `plan.md` | The task's implementation plan, recorded before code |
| Review findings and outcome | The task's implementation notes and final summary |
| Incident becoming an intent | A new task, type `bug` |
| (absent from the playbook) | `backlog/decisions/` |
| Audit trail | Git history of `backlog/`, with created and updated dates |

- No `intent/`, `spec/` or `plan/` folders: they would be a second record beside the backlog, against "one record per thing" and against the playbook's own sidebar.
- Where the backlog falls short of the playbook: a status change triggers nothing (not needed with one maintainer); nothing checks a task's content, neither acceptance-criteria quality nor a missing register id. This backlog is a public corpus of agent-written user stories with acceptance criteria, which is evidence for Legible's "User-story quality" row.
- The playbook's leading and lagging indicators can be read from `backlog/` history: creation to plan, plan to Done, plan edits after In Progress.
- The record is split by repository: `ROADMAP.md` in pumllint, aris2puml and Legible; the backlog here; `decisions/` in ieam-register. Each is consistent and the artifact pages are views; a playbook-style `intent/` folder would be a third kind.

## Shape

Nothing queued. If pulled, in this order, none on pumllint's product path:

1. `.claude/settings.json` hooks on each repository's own protected paths, each repository by its own pull request.
2. A pumllint `SKILL.md` from `docs/agents.md` and a documented hook adapter for the exit codes.
3. task-0007/task-0016 described as the playbook's deterministic confidence gate between stages, with the same adapter.
4. A dated Legible ROADMAP entry mapping the six stages onto the pipeline map and recording the blind spot; the page quotes it.
