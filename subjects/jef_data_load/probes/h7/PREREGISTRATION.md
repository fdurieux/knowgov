# H7's two mutants as the re-run step's first probe, on jef_data_load: pre-registration

task-0219 (decision-0018 point 8, doc-0032 §5). Written with `docs/reverse-engineering-preregistration.md`
and committed, in its own commit, before any mutant is applied or any instrument is run. The results
go to `RESULTS.md` beside this file; this file is not edited after it is frozen.

The question is OpenWiki's H7 (pumllint `recreate_experiment/openwiki-2026-10-27/PREREGISTRATION.md`
§4, never run there, M9), asked of knowgov's instruments for step 8 of the process (re-run on change):
staleness detection sees edits; does anything but execution see behaviour?

### 1. The code base and its commit

- **Repository:** knowgov, at the commit this file is frozen at (§10).
- **The code mutated:** the public rebuild knowgov vendors from pumllint,
  `subjects/jef_data_load/vendor/recreate_experiment/rebuilds/codex-2026-10-24/`. It is the J-F subject's
  `[reference] code` and passes the kit's suite 258 of 258 (`subject.toml`, `[oracle]`). Each mutant is a
  copy of it in a temporary directory. The vendored files are never edited.

### 2. The lane

- **In scope:** the rebuild's `src/jef/data/sync.py` (62 lines), the only file either mutant touches.
- **Out of scope:** every other file, and J-F's original. pumllint's `recreate_experiment/hidden/MUTANTS.md`
  (public, in pumllint's repository) describes the two mutants on J-F's original `sync.py` and quotes their
  diff. Its prose was read for each mutant's intent and for its calibration counts (§8). Nothing of its diff
  is copied here, and J-F's repository is never opened. The mutants below are written afresh against the
  public rebuild, each a transposition of the original's:
  - **m1, transposed to the rebuild:** in the rebuild's leg loop of `run_sync`, the bar fetch (`bars=... c.get_eod(...)`)
    moves above the block that refreshes the corporate actions, so a raw-basis leg fetches its bars
    before its splits and dividends are refreshed. The splits are still read after the refresh, so a green
    run stores the same cells. The change shows only when a fetch fails.
  - **m2, transposed to the rebuild:** the crypto end-guard is removed: the line that caps a crypto leg's `end` at
    the previous UTC day is deleted.

### 3. The roles

| role | played by | starts fresh |
|---|---|---|
| extraction | none: no kit is written; the subject's kit is the one vendored | n/a |
| recreation | none: no rebuild is made; the mutants are hand edits of the existing rebuild | n/a |
| validation | the testing-class session: applies the mutants and runs the three instruments, `tools/check_h7_probe.py` | no |

### 4. What the extraction role may read

Not applicable: nothing is extracted. The session reads the public rebuild, the vendored kit and
pumllint's public record. It never reads J-F's repository.

### 5. What the recreation role receives

Not applicable: nothing is rebuilt.

### 6. The bars

Three instruments, each run on the unmutated rebuild (the control) and on each mutant:

| instrument | what it is | what "flags" means |
|---|---|---|
| R-STALE | knowgov's stage-2 rule: the subject's documents re-ingested over a first load, in one rdflib store | at least one statement invalidated |
| trace `drift` | `harness/trace.py check --changed` on a small instance whose `code_map.toml` maps the rebuild's code to APP-0005 (`jef-data`), with `sync.py` registered beforehand | a `drift` finding on `sync.py` |
| the suite | the subject's oracle, `subjects/jef_data_load/oracle/jef_suite.py`, on the copy, under the J-F pins on CPython 3.12 | at least one case failing |

| measure | unit | gates or reported |
|---|---|---|
| each instrument's verdict per mutant against the expected table (§8) | flags or not, per cell | gates: a cell against expectation is the headline |
| the suite's failing cases, by feature | count | reported |
| the gate's verdict on scenario C with the mutant as reference code | PROCEED, QUALIFIED or BLOCKED | reported |

### 7. The bounded inventories

| inventory | what it lists | how many |
|---|---|---|
| mutants | m1, m2, and the unmutated control | 3 |
| instruments | R-STALE, trace drift, the suite | 3 |
| the suite's cases | the kit's acceptance suite, in 12 features | 258 |
| the subject's documents | the five artefacts R-STALE re-ingests | 5 |

### 8. Expectations

| | R-STALE | trace `drift` | the suite |
|---|---|---|---|
| control | not flagged | not flagged | 258 of 258 pass |
| m1 | not flagged | flagged; the behaviour is unknown to it | at least one failure |
| m2 | not flagged | flagged; the behaviour is unknown to it | at least one failure |

The reasons for these expectations:
- **R-STALE.** It reads documents, and a code change changes none. Its blindness to both is the expected
  result, not a failure of the probe.
- **trace `drift`.** It reads a registered file's whole digest, so it sees both edits alike and cannot tell
  a behaviour change from a refactoring.
- **The suite.** On J-F's original, H7's mutants failed 2 (m1) and 11 (m2) of a 178-case suite. Here the
  kit's revised suite has 258 cases, so the counts are not expected to match, only to be at least one.
- **The gate.** It is expected to read scenario C the same, PROCEED, with either mutant as the reference
  code. The execution evidence's digest is recorded on each verification, but nothing compares it with the
  code as it now stands.

What would surprise, and be the headline:
- the suite passing a mutant: then the kit does not pin that behaviour;
- R-STALE flagging a mutant;
- trace failing to flag one.

### 9. What this run never does

- It never reads, copies or commits J-F's private code.
- It never edits a vendored file: each mutant is a temporary copy.
- It makes no model call, and moves neither the record nor any pin.

### 10. Frozen

- **Date and commit:** 2026-11-08, at the commit that adds this file alone. `tools/check_h7_probe.py` was
  drafted beside it, outside the repository, and has been compiled but never run. It is committed after this
  file, and no mutant has been applied or instrument run before this commit.
- **Who froze it:** the testing-class session (`session_01HTAA1SeixnS7DTyTKp8JYZ`), under the coordinating
  session's dispatch of decision-0018 point 8.
