# Pre-registration template: one run of the reverse-engineering process

Step 1 of `docs/reverse-engineering.md`. Copy this file into your run's folder, fill in every field,
and commit it **before** step 2 starts. After that, the fields are fixed: a change is a new version
of this file, dated, with its reason, and the old one stays beside it. Fixing them first is what makes
the run's results mean something. A bar chosen after the numbers are in tends to be the one the
numbers pass.

The second half of this file is the template filled in for the process's first run: pumllint's
recreation experiment on J-F's daily asset load, 2026-10-23. Its own pre-registration, the record
this example cites, is pumllint's `recreate_experiment/PREREGISTRATION.md`.

## The template

### 1. The code base and its commit

- **Repository:** where the code lives.
- **Commit:** the one commit every role reads. Note how you checked that nothing changed it during
  the run (for example, the working tree clean before and after).

### 2. The lane

- **In scope:** the files and folders described, as a list, with their size in lines.
- **Out of scope, and why:** what is deliberately left out (code someone else owns, generated code,
  external services), and what stands in for it (a stub, a recorded fixture).

### 3. The roles

For each role, who plays it (a person, or an assistant session with its model and settings), and
whether it starts fresh, with no memory of the others.

| role | played by | starts fresh |
|---|---|---|
| extraction (writes the kit) | | |
| recreation (rebuilds from the kit; step 7, optional) | | |
| validation (compares and sorts the differences) | | |

### 4. What the extraction role may read

The clean-room parameter. Choose one, and list exactly what it covers:

- **a full clean room:** a copy of the code with tests, documents, READMEs and roadmaps removed;
- **no clean room:** the code, its tests and its documents, when the aim is the most accurate kit,
  not a test of what the code alone carries. knowgov's own lane chose this for the kit's author
  (decision-0011, amendment A1). The rebuilder then still works from a bundle only, so the
  rebuild measures what the kit carries, not what was copied;
- something in between, named file by file.

Say also how you will check afterwards what it read (a read log, a list of every path opened).

### 5. What the recreation role receives

The bundle: the frozen kit and anything else named here, file by file. It never receives the
original code, its tests, the provenance map or an earlier rebuild. Say how you will check that it
read nothing else.

### 6. The bars

What counts as success, fixed now. For each measure, its unit, and whether it **gates** (failing it
fails the run) or is only **reported**:

| measure | unit | gates or reported |
|---|---|---|
| | | |

Name the reference outputs the rebuild is compared with, how they are frozen (a digest per file),
and which differences are excluded on purpose (clock times, paths), before any run.

### 7. The bounded inventories

Every coverage figure in the results is a count against one of these lists, written down now: the
requirements, the reference outputs, the scenarios, the people to ask. Never a percentage of all the
knowledge, which has no denominator.

| inventory | what it lists | how many |
|---|---|---|
| | | |

### 8. Expectations

What you expect each measure to show, stated so that it can fail. A result against an expectation is
reported as prominently as one for it.

### 9. What this run never does

The limits, so nobody reads more into the result: for example, never changing the code it reads,
never giving the rebuilder the original, never repairing the code from what the kit says.

### 10. Frozen

- **Date and commit** of this file when it was frozen, and its digest.
- **Who froze it.**

## Worked example: J-F's daily asset load, 2026-10-23

Every value below is quoted or summarised from pumllint's `recreate_experiment/PREREGISTRATION.md`
(sections named in brackets). J-F's code is private and appears nowhere here. knowgov carries the run's
kit and its public rebuild as the subject `jef_data_load`.

### 1. The code base and its commit

- **Repository:** J-F, the maintainer's own program, read-only throughout.
- **Commit:** `8f6d6b0`, its `origin/main`; the working tree showed no tracked change before and after
  the reference run [Results, Phase 0].

### 2. The lane

- **In scope:** `src/jef/data/`, about 3 500 lines of Python and two TOML files, plus the acquisition
  half of `deploy/daily.sh` [§2].
- **Out of scope:** the binning logic, telemetry and publishing (given externals), cloud storage and
  the trading venue (stubbed as the original's own tests stub them), and the provider networks (every
  run replays recorded fixtures) [§2].

### 3. The roles

| role | played by | starts fresh |
|---|---|---|
| extraction | a fresh assistant agent at its highest effort setting, briefed in one call | yes |
| recreation | two fresh agents, one per arm: the kit with diagrams (K) and without (K−UML) | yes, never a fork of another session |
| validation | the orchestrating session, which had read parts of J-F's documentation while planning and so wrote no kit content | no, and that is why it only validates |

[§3, Results Phase 0]

### 4. What the extraction role may read

A full clean room: a copy of `src/jef/data/`, `deploy/daily.sh`, the two sourced scripts as marked
externals and a reduced `pyproject.toml` with the pins; no `docs/`, no `tests/`, no README, no
ROADMAP. Each statement in the kit records whether it rests on code logic, on comment prose, or on
both. The agent's read log was checked afterwards: it stayed inside the clean room [§3, Results
Phase 0 and Phase 1].

### 5. What the recreation role receives

One directory, the kit, copied outside every repository, with a prompt naming no repository, URL or
package name but the kit's own. The original's tests and recorded fixtures never enter the kit; its
scenarios carry their own small fixtures. Leakage is checked on both sides: each agent lists every path
it read, and the rebuilt source is compared with the original for copied comments [§3].

### 6. The bars

| measure | unit | gates or reported |
|---|---|---|
| the exported frame identical cell for cell | per series per scenario | gates |
| the health check never says green where the original says red | count | gates |
| the store's raw columns, partitions and action files equal | per series | gates |
| exit codes and refusal messages identical on every refusal | per scenario | gates |
| the rebuilt store reproduces the original's CSV path bit for bit | pass or fail | gates |
| the original's own tests on the rebuild | pass rate | reported |
| the kit's scenarios on the rebuild after at most three rounds | pass rate | reported |

Reference outputs: 157 artefacts over 24 scenario groups, frozen with a digest each; clock times and
store paths excluded, two reference runs identical after that [§6, Results Phase 0].

### 7. The bounded inventories

| inventory | what it lists | how many |
|---|---|---|
| reference outputs | the frozen artefacts the rebuild is compared with | 157 |
| scenario groups | the situations the reference was run through | 24 |
| requirements | the kit's statements with ids, written in Phase 1 | 158 |

[Results, Phase 0 and Phase 1]

### 8. Expectations

Each fixed before the first scored run, with how a failure would be read [§7]. The results section of
the same file records which held.

### 9. What this run never does

J-F is never changed; nothing from the lab enters it; the existing diagrams are not inputs to the kit
and are compared with it only after the rebuilds are scored [§1, §8].

### 10. Frozen

At pumllint commit `5c1fa55`, 2026-10-23, before any kit, recreation or comparison run [header,
Results Phase 0].

### What came of it

The kit carried 158 requirements; three rebuilds from the kit alone matched the original cell for cell
on every exported frame, stored series and exit code; and the diagrams beside J-F's own existing set showed 12 claims the code contradicts
in the kit, 25 in the existing set. pumllint's `docs/recreate-experiment.md` tells the whole story.
