"""Run every saved query the page lists against the store, as Neo4j Browser would.

    python check_saved_queries.py

The page's console list is the adapter's generic queries (store_neo4j.SAVED_QUERIES)
followed by the subject's (queries.toml). Nothing else runs them: they are text for the
viewer to paste, so a syntax error in one reaches the viewer's console and no test. This
tool runs each statement of each query (a query may hold several, separated by ``;``)
through the store port's ``console_query`` and reports the rows it returns or the error
it raises. A query that needs a scenario or the register not loaded still runs: it
returns no rows, and a syntax error shows either way. Exit 0 iff every statement ran.

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


def main() -> int:
    import server
    from store import open_store

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
                else:
                    print(f"ok   {label:22} {len(rows)} rows")
    print(f"{failures} failing statement(s)" if failures else "every saved query ran")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
