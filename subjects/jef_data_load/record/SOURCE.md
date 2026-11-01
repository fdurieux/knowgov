# The record of the J-F data-load subject

The platform's own deterministic run (D1 to D6, no arm, no oracle) of the six scenarios on the
Neo4j store, written by `harness/run.py --deterministic` at knowgov commit `a79b7e6` on
2026-11-01, with the subject's `plants.toml` as written by `tools/plants_from_patch.py` from the
degradation test's patches. One `deterministic.json` per scenario; `tests/test_jef_subject.py`
holds the shape, `harness.yml` compares every rdflib re-run against it (D1, the Neo4j edition's
constraint measurement, is skipped across store kinds), and a future scored run with arms and an
oracle (task-0021.03) replaces this folder as the subject's record.

```bash
cd harness && KG_SUBJECT=../subjects/jef_data_load python run.py --deterministic --out ../subjects/jef_data_load/record
rm subjects/jef_data_load/record/{usage.json,summary.json,SHA256SUMS}
```
