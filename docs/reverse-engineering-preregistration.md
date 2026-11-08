# A pre-registration for a reverse-engineering run

A *pre-registration* is a short document you write and freeze before a run measures anything. It fixes
what the run covers, who does what, what each role may read, and what result counts as success. Writing
it first is what makes a run's results mean something: a bar chosen after the results are in measures
whatever came out. It is step 1 of [the reverse-engineering process](reverse-engineering.md).

## How to use it

1. Make a folder for the run in your instance, such as `reverse-engineering/2026-11-20-billing/`.
2. Copy the skeleton at the end of this page into it as `PREREGISTRATION.md`.
3. Fill in every field. The section below explains each one and shows what J-F's first run wrote.
4. Commit the file, then write that commit and the file's SHA-256 digest into its freeze line, and commit
   again.
5. From then on, change nothing above the *Results* heading. Add each step's results below it, dated, as
   they come. If the scope must change, freeze a new version and say why.

The worked example is pumllint's recreation experiment of 2026-10-23, on J-F's daily data load. Its own
pre-registration is vendored in knowgov at
`subjects/jef_data_load/vendor/recreate_experiment/PREREGISTRATION.md`, and every value quoted below comes
from it. That run predates this template, so where the template asks for something it did not record
separately, the example says so.

## The fields, with J-F's first run

### 1. The question and what it decides

**What to write.** The one question the run answers, and the decision or work its answer feeds. If it
feeds none, say so.

**J-F's first run.** "Can a specification stack reverse-engineered from working code (requirements as
code, architecture and UML, contracts, Gherkin) carry enough information for an independent agent to
recreate the code, and where exactly does it fall short?" It fed no product decision: it was the first
measurement, on a real program, of an answer earlier measured on toy systems.

### 2. The original and its commit

**What to write.** The program, its repository, and the commit every role reads. Say who owns it, whether
its code is private, and that the run never changes it.

**J-F's first run.** J-F at commit `8f6d6b0`, read-only throughout: its working tree showed no tracked
change before or after. J-F's code is private. knowgov's subject carries a rebuild in its place, never
J-F's own code.

### 3. The lane's file set

**What to write.** The files in scope, by path, with their size. Then what is out of scope, and why, one
reason per exclusion.

**J-F's first run.** In scope: `src/jef/data/` (about 3,500 lines of Python and two TOML files) and the
acquisition half of `deploy/daily.sh`. Out of scope, by rule: `jef.binning` (frozen logic with its own
oracle), `jef.events` and `jef.dashboard` (treated as given externals), AWS and the venue (stubbed, as
the original's own tests stub them), and the data providers' networks (every
run replays recorded fixtures).

### 4. The roles

**What to write.** Who or what plays each of the three roles (extraction, recreation, validation), and
that each works in a context of its own. For an assistant, name the model and its settings here.

**J-F's first run.** Extraction: a fresh assistant session, given a stripped copy of the code tree.
Recreation: a second fresh session for each variant, never a copy of another session, given the kit
only. Validation: the session that planned the run. It ran the kit's checks, launched the recreations and
compared the results. It did not write the kit, because it had read parts of J-F's documentation while
planning.

### 5. The clean room

**What to write.** For each role, what it may read and what it is kept from, and how you will check
afterwards that it read nothing else. This is a parameter, not a fixed rule: a full clean room keeps the
extraction role to the code alone, while a run with no clean room for the author lets it read everything.

**J-F's first run.** A full clean room for extraction: it read `src/jef/data/`, `deploy/daily.sh`, the two
packaged TOML files and the pinned versions in `pyproject.toml`, and never `docs/`, the README, the
ROADMAP or `tests/`. The recreation role saw the kit only. Afterwards, each session's list of every path it
read was checked, and the kit was compared with the original's source for copied text: no line of 50
characters or more was shared. knowgov's own planned run (decision-0011, point A1) chooses the opposite for
its author, who reads everything, and keeps the clean room for the rebuild.

### 6. The existing artefacts

**What to write.** The documents the organisation already has about the lane, and when they are read:
gathered and loaded beside the kit (step 3 of the process), or held back until the results are in.

**J-F's first run.** J-F's eight existing data-load diagrams and its data contract. They were held back
and compared with the kit only after the rebuilds were scored, so that they could not influence it. Under
the process, they would be gathered and loaded beside the kit at step 3.

### 7. The kit

**What to write.** The layers the kit will have, the id pattern of its requirements, how each statement
records its claim (`observed`, `inferred` or `intended`), the rule for which layer wins when two disagree,
and the checks the kit must pass before it is frozen.

**J-F's first run.** Five layers: `requirements.json` (ids `JDL-NNN`, one statement each, with a `kind`
and a `basis` saying whether it was read from the code's logic, its comments, or both), contracts (prose
documents and two JSON Schemas), a decision table, eight PlantUML diagrams listing the requirement ids they
realise, and Gherkin scenarios tagged with those ids. The first run had no claim field: its `basis`
records where the evidence came from, not what the statement is. Checks before freezing: pumllint's lint
with no finding, every diagram at score Level 5, every requirement drawn in a diagram and tested by a
scenario (pumllint's trace), the suite passing on the original, and two planted changes to the code each
turning the suite red.

### 8. The bundle

**What to write.** Exactly what the recreation role receives: the kit, any named context beside it, the
instructions, and what it must hand back. Nothing of the original.

**J-F's first run.** Two variants: the full kit, and the kit without its diagrams. Each came with a brief
naming no repository or package but the kit's own, the target's name and pinned library versions, and two
obligations: a list of every point where the kit was silent and what was chosen (`ASSUMPTIONS.md`), and a
list of every path opened (`READ.log`).

### 9. The oracle

**What to write.** What knows the right answer, and how it is kept apart from the kit, so that the kit's
own scenarios do not simply replay the oracle's inputs.

**J-F's first run.** The original's own tests for the lane (about 4,000 lines), its recorded fixtures, and
one frozen CSV file, plus a comparison harness that runs the same scenarios on the original and the rebuild
and compares every output. The kit's scenarios used their own fixtures and their own clock. A kit scenario
reproducing a recorded fixture was to be declared; the target was none.

### 10. The bounded inventories

**What to write.** The lists you can count, against which every coverage figure will be stated: the
requirements, the scenarios, the compared outputs. Give the expected size of each, and name what the
checks cannot reach. Never state coverage as a share of all the knowledge.

**J-F's first run.** The requirements (expected 120 to 160), and the comparison's scenario set (expected 25
to 35 scenarios). Recorded at the freeze: 158 requirements, 24 scenario groups producing 157 compared
outputs. The kit also declared what its scenarios could not reach, such as the live network transport and
its retries.

### 11. The bars

**What to write.** Each measure, its unit, and whether it is gated (it must hold) or only reported. Then
each expectation, and what each outcome would mean, the failures included. A failed expectation is
recorded with the same prominence as a confirmed one.

**J-F's first run.** Eleven measures, M1 to M11. Eight carried a severity if they failed. The gravest
were M1, every exported table identical cell for cell; M2, the rebuild's health check never green where
the original's is red; and M8, the rebuild's store giving bit for bit the original's result on one frozen
file. Three were only reported:
the original's own tests run against the rebuild, the kit's suite on the rebuild, and how many of the
divergences the rebuild had already listed as assumptions. Seven expectations, E1 to E7, each with its
meaning if it failed: E1, for example, expected M1 to hold on every series, and read any shortfall as a
numeric rule the kit had lost.

### 12. The iteration and the budget

**What to write.** How many tries each role gets, and the ceiling of the whole run, after which it stops
and reports.

**J-F's first run.** The rebuild could run the kit's suite against its own code at most three times. The
ceiling: one reverse-engineering run, two rebuilds, and one closing round in which the kit's gaps were
fixed and a third rebuild was scored.

### 13. What the run never does, and what may be published

**What to write.** What the run must never change or call, and what of its results may leave your
organisation, decided by whom.

**J-F's first run.** No file under J-F changes, and no live call reaches a data provider. A defect found
in the original is reported to J-F as an issue, on the maintainer's go, and nothing more: six were filed
after the run. The kit, the results and a rebuild were published in pumllint; J-F's code never was.

### 14. Where the record lives

**What to write.** The folder the run's records go in, in your instance, and the files each step adds.

**J-F's first run.** pumllint's `recreate_experiment/` folder and its `docs/recreate-experiment.md`.
knowgov vendors that record at `subjects/jef_data_load/vendor/`, reads it, and never writes to it.

### 15. The freeze

**What to write.** The date, the commit at which this file was frozen, and the file's SHA-256 digest at
that commit.

**J-F's first run.** Frozen on 2026-10-23, at pumllint commit `5c1fa55`, digest `4f14e9a0…1982`.

## The skeleton

Copy this into your run's folder as `PREREGISTRATION.md`.

```markdown
# <run name>: pre-registration

*Frozen <date> at <commit>, sha256 <digest>. Nothing above the Results heading changes after this line.*

## 1. The question and what it decides

## 2. The original and its commit

## 3. The lane's file set

## 4. The roles

## 5. The clean room

## 6. The existing artefacts

## 7. The kit

## 8. The bundle

## 9. The oracle

## 10. The bounded inventories

## 11. The bars

## 12. The iteration and the budget

## 13. What the run never does, and what may be published

## 14. Where the record lives

## 15. The freeze

## Results

*Added as each step completes, dated; nothing above this heading changes.*
```
