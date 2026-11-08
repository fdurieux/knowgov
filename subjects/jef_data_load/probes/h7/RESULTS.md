# H7's two mutants as the re-run step's first probe, on jef_data_load: results

task-0219 (decision-0018 point 8). The run is against `PREREGISTRATION.md`, frozen in 370b76d before the
probe's script was committed (dff0b4f) or run.

```bash
KG_CLOCK=pinned python tools/check_h7_probe.py OUT_DIR
```

- **Ran on:** 2026-11-08, on the tree of fa4648b.
- **Interpreter and pins:** CPython 3.12.3 with the J-F pins (pandas 3.0.5, numpy 2.4.6, requests 2.34.2,
  pyarrow 25.0.1, pytest 9.1.1, pytest-bdd 9.0.1) and the record's (rdflib 7.6.0, pumllint 0.33.0, PyYAML 6.0.3).
- **Exit:** 0, every cell as pre-registered.

## Against the expected table (§8)

| | R-STALE | trace `drift` | the suite |
|---|---|---|---|
| control | not flagged: 0 invalidated, as expected | not flagged: no finding, as expected | 258 of 258 pass, as expected |
| m1 | not flagged: 0 invalidated, as expected | flagged: `drift` on `jef/data/sync.py`, as expected | 2 failing, 256 of 258 pass: at least one, as expected |
| m2 | not flagged: 0 invalidated, as expected | flagged: `drift` on `jef/data/sync.py`, as expected | 19 failing, 239 of 258 pass: at least one, as expected |

None of the surprises §8 names happened: the suite failed both mutants, R-STALE flagged neither, and trace
flagged both.

## What each instrument reported

**R-STALE.** On every variant, scenario C was loaded and each of the five documents re-ingested over it
(`requirements.json`, `contracts/`, `contracts/dmn/`, `uml/`, `features/`), with 0 statements invalidated. The
probe has no positive control of its own. That R-STALE sees a document edit on this subject through the same
stage-2 path is shown by `tools/check_stage2_reload.py` (I6: one `@JDL-001` tag removed moves
`JDL-001|verified_by`), and on CargoQuote by S6's record.

**trace.** `sync.py` was registered from the control, in a temporary instance whose `code_map.toml` maps `jef/**`
to APP-0005 (`jef-data`). On both mutants, `trace.py check --changed jef/data/sync.py` gave one finding, the
same text for both:

> `drift`, minor: `jef/data/sync.py (APP-0005) changed since derived:code@control:jef/data/sync.py: it rested on
> 163 statement(s): 163 approved; register the new version`

The command exited 0 on both mutants. `drift` is minor, and `trace.py check` fails only at `--fail-on blocker`
by default. A pipeline therefore stops on a changed registered file only with `--fail-on minor`. The finding
cannot tell m1 from m2, or either from a refactoring: it compares the file's digest, not its behaviour.

**The suite**, by feature. The oracle names at most six failing cases per feature (`results.json`):

| | feature | cases passing | failing cases |
|---|---|---|---|
| m1 | collectors | 20 of 22 | a 404 on the bars fails the leg after the corporate actions were refreshed; when both the actions and the bars would fail, the actions failure is what the leg reports |
| m2 | adjustment | 7 of 9 | an EODHD crypto series is stored as served, end-guarded at the previous UTC day; the declared class, never the `.CC` suffix, decides basis, actions and guard |
| m2 | collectors | 18 of 22 | four: a bar endpoint answering something other than a JSON list; Binance klines dated by their UTC open time; Binance pages ascending until a short page; a first fill landing on the page limit |
| m2 | decisions | 53 of 61 | eight; the oracle names the first six: the provider and the class deciding basis and actions (×2); volume rawised only for EODHD raw-basis series; the fetch end as the ISO minimum of the universe end and the crypto end-guard; a leg not actions-eligible; a measured spread's notes |
| m2 | status | 36 of 40 | the cross-venue close spread warning or alerting (×4) |
| m2 | sync | 20 of 21 | a dry run plans every leg shape from local state only |

m1's two failures are the two scenarios pumllint's `hidden/MUTANTS.md` names as catching m1 on J-F's original,
so the transposition reaches the behaviour the original's mutant did. m2 fails 19 of the revised suite's 258
cases here, against 11 of 178 on the original. §8 expected the counts to differ, and the probe does not say why
they do.

**The gate.** Scenario C read PROCEED with each variant as the reference code, as expected. A verification
records its execution evidence's digest, but nothing compares that digest with the code as it now stands.

## What this means for step 8

H7 holds in knowgov. The document instrument, R-STALE, sees neither mutant, because neither changes a document.
The file instrument, trace `drift`, sees both alike and cannot rank them. Only execution, the kit's suite, sees
the change in behaviour, and it separates the two mutants (2 cases against 19). m1 shows only when a fetch
fails, and the kit pins exactly that through two scenarios. `docs/reverse-engineering.md` step 8 therefore runs
all three and notes which caught what. It says a pipeline must pass `--fail-on minor` for drift to fail it.

## Deviations from the pre-registration

- **The first run** stopped at `trace.py register` with exit 2: the temporary instance had no `register/`, so
  `code_map.toml`'s APP-0005 could not be checked. No instrument had reported. fa4648b copies the subject's
  register (`demo/register`, `KG_REGISTER`'s default) into the instance. The mutants, the instruments and the
  expected table are unchanged, and the second run is the one reported here.
- **None otherwise.**

## What was read (AC 3)

- **Read:**
  - the public codex rebuild vendored here (`vendor/recreate_experiment/rebuilds/codex-2026-10-24/`);
  - the vendored kit and the subject's oracle;
  - pumllint's public `recreate_experiment/openwiki-2026-10-27/PREREGISTRATION.md` (§3 M9, §4 H7);
  - the prose of `recreate_experiment/hidden/MUTANTS.md`, for each mutant's intent and its calibration counts.
- **Not read:** J-F's repository was never opened.
- **Not copied or committed:** nothing of the original's diff that MUTANTS.md quotes. The mutants are exact-text
  edits of the rebuild's own lines (`tools/check_h7_probe.py`: `FETCH`, `ACTIONS`, `GUARD`), applied to temporary
  copies outside the repository. No vendored file was edited, and no model was called.
