# The record of the J-F data-load subject

The platform's own deterministic run (D1 to D6, no arm, no oracle) of the six scenarios on the
Neo4j store, written by `harness/run.py --deterministic` at knowgov commit `a79b7e6` on
2026-11-01, with the subject's `plants.toml` as written by `tools/plants_from_patch.py` from the
degradation test's patches. One `deterministic.json` per scenario; `tests/test_jef_subject.py`
holds the shape, `harness.yml` compares every rdflib re-run against it (D1, the Neo4j edition's
constraint measurement, is skipped across store kinds), and a future scored run with arms and an
oracle (task-0021.03) replaces this folder as the subject's record.

Re-recorded on 2026-11-17 at knowgov commit `9116c13` (task-0357; maintainer, 2026-11-16, option (b): "could we
not do (b) now as we are restarting the soak anyway"), by the same command, on a Neo4j 5.26.24 community tarball
started directly with the stack's heap and page-cache settings, driver 6.4.1. `dmn_decisions` now reads
`actions_gate`'s own citation of JDL-088. Against the 2026-11-01 files, 78 leaves moved over the six scenarios
(`tools/check_run_order.py`, sha256 `e46adcfcaec8a46af9d0177dbbb46d6e66a095f2e41f027fe4984b17505489fb`): 66 from
JDL-088 (10 a scenario the comparator reads, one SHACL sample line it does not) and 12 the run has written since
2026-11-01 (`as_of`, `D6_gate.lapsed`). No list moved order: task-0369's sorted order equals the order the
2026-11-01 run happened to write. Two Neo4j runs of this code differ in no leaf.

```bash
cd harness && KG_SUBJECT=../subjects/jef_data_load python run.py --deterministic --out ../subjects/jef_data_load/record
rm subjects/jef_data_load/record/{usage.json,summary.json,SHA256SUMS}
```
