# exports/

Dated, append-only mirrors of the sources of record. Each folder holds a `MANIFEST.toml`
(export time, source, source version, tool and version, the previous folder, sha256 per file,
the external ids the export carries) and, once `tools/reconcile.py` has run, a `RECONCILE.json`
(adds, updates and deletes against the previous folder, plus register nodes whose external id
no longer appears). A later export is a new folder, never an overwrite.

`kit/` is this test case's synthetic source: the manifest names the pumllint commit and the
digests of the CargoQuote kit files; the files themselves stay in pumllint. A second subject of
the organisation is a second `<system>/` folder with its own manifests (decision 0004). `aris/`, `archi/`
and `edm/` are empty until an export route is tested on a target installation.
