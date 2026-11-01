# Vendored copy of the Legible systemic impact model, v0.3

| | |
|---|---|
| source repository | `fdurieux/fdurieux.github.io` |
| file | `model/model.json` (generated there from `model/model-data.py`; never edited by hand) |
| version | 0.3, dated 2026-10-29 (`"version": "0.3"` in the file) |
| commit | `099a7373e5c7817953709e8a0af45f050fc67a5c` — "Systemic impact model v0.3: review corrections, degradation refinements, knowledge source (#2)", merged 2026-10-29 as that repository's #2 |
| sha256 of `model.json` | `42e6be8aa9a906a0af8a4db926c0ac1358ffaf5a35e5f9f6358f1cb5f911d992` |
| copied | 2026-10-30, byte for byte, by the session that built the demo in pumllint; carried here with the demo (decision-0001) |

The demo's systemic-model view draws the model's reduced knowledge view
(five knowledge nodes, nine edges, four practices P9–P12) with the layout
tables of `cascade_layout.py` beside this file, which reads this JSON for
the edges' polarity and evidence class.

## The layout tables

| | |
|---|---|
| source repository | `fdurieux/pumllint` |
| file | `recreate_experiment/knowledge-transfer/deck/tools/gen_cascade_slide.py`, the deck generator whose module-level tables (lanes, nodes, edges, geometry, colours) the view imports |
| commit | `fd8bef42b9cfebc3969f58ca2ce484c3305ee10e`, 2026-11-01 |
| sha256 of `cascade_layout.py` | `77a05697e60ec334ca73deebc9b120345ad2f4303fd81b07bbe94eb1b30e2a0b` |
| copied | 2026-11-01, byte for byte, with the demo (decision-0001); `tests/test_demo.py` holds it to this digest | The
copy is not fetched at build time: the image carries it. To refresh it,
copy the file from the source repository at the commit you want, update
this table, and regenerate the deck slide to see that the drawing still
holds.
