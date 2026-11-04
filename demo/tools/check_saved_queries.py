"""Run every saved query the page lists against the store, as Neo4j Browser would.

    python check_saved_queries.py

The page's console list is the adapter's generic queries (store_neo4j.SAVED_QUERIES)
followed by the subject's (queries.toml). Nothing else runs them: they are text for the
viewer to paste, so a syntax error in one reaches the viewer's console and no test. This
tool runs each statement of each query (a query may hold several, separated by ``;``)
through the store port's ``console_query`` and reports the rows it returns or the error
it raises. A query that needs a scenario or the register not loaded still runs: it
returns no rows, and a syntax error shows either way.

``register-cites`` is held to the join ``register_node_statements`` makes (task-0088): when it
returns rows, every cited document the subject loads (``KG_SUBJECT``: a file artefact of that path,
or a file of a directory artefact, J-F's ``contracts/chain.md`` in ``contracts/``) has a version in
the store, a file artefact's compared by digest, a directory part's counted by its fragments. Exit
0 iff every statement ran and that holds.

Runs where the harness and the driver are, with the store's settings from the
environment: in the stack job, ``docker compose exec -T app python
demo/tools/check_saved_queries.py`` after a scenario is loaded and the register
projected. Standard library beside the harness.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "demo" / "app")]


def statements(text: str) -> list[str]:
    """The statements of one saved query: split on ``;``, comment-only pieces dropped."""
    out = []
    for piece in text.split(";"):
        lines = [ln.strip() for ln in piece.splitlines() if ln.strip()]
        if lines and not all(ln.startswith("//") for ln in lines):
            out.append(piece.strip())
    return out


def loaded(path: str, keys) -> bool:
    """Whether the subject loads ``path``: a file artefact of it, or a directory artefact holding it."""
    return path in keys or any(k.endswith("/") and path.startswith(k) for k in keys)


def cites_failures(rows: list[dict], keys) -> list[str]:
    """register-cites' rows against the subject's artefact keys: every loaded document cited has a
    version in the store, a directory part's naming its directory (task-0088)."""
    out = []
    for r in rows:
        doc, vs = r["document"], r["versions_in_store"]
        if not loaded(doc, keys):
            continue
        if not vs:
            out.append(f"{doc}: the subject loads it and register-cites finds no version in the store")
        elif doc not in keys and not all(": in " in v and v.endswith(", no file digest in the store") for v in vs):
            out.append(f"{doc}: a file of a directory artefact compared by digest: {vs}")
    return out


def main() -> int:
    import server
    import subject as subject_mod
    from store import open_store

    keys = set(subject_mod.load().store_keys)
    failures = 0
    with open_store() as store:
        for q in server.cypher_list():
            for i, stmt in enumerate(statements(q["text"]), 1):
                label = q["id"] if i == 1 else f"{q['id']} ({i})"
                try:
                    rows = store.console_query(stmt)
                except Exception as e:   # the driver's error, whatever its class
                    failures += 1
                    first = str(e).strip().splitlines()[0] if str(e).strip() else type(e).__name__
                    print(f"FAIL {label:22} {first}")
                    continue
                print(f"ok   {label:22} {len(rows)} rows")
                if q["id"] == "register-cites" and rows:
                    bad = cites_failures(rows, keys)
                    parts = sum(1 for r in rows if r["document"] not in keys and loaded(r["document"], keys))
                    files = sum(1 for r in rows if r["document"] in keys)
                    print(f"     register-cites: {len(rows)} documents, {files} file artefacts, {parts} files of a directory artefact, "
                          f"{len(rows) - files - parts} the subject does not load")
                    for b in bad:
                        print(f"FAIL register-cites   {b}")
                    failures += len(bad)
    print(f"{failures} failing statement(s)" if failures else "every saved query ran")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
