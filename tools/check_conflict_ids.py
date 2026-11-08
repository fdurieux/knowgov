"""One id per conflict on every store (task-0223, decision-0020, doc-0030 S2).

    python tools/check_conflict_ids.py [--stores neo4j,rdflib] [--scenarios S4] [--require S4]

For each scenario of the subject (``KG_SUBJECT``): load it fresh into each named store kind with
``gate_cli.py``'s own load, then read ``conflict_gaps`` and ``candidate_pairs``. Every store must name the
same conflicts by the same ids in the same order; every id must be content-derived,
``gap:conflict:<key>:<a>~<b>`` with ``a`` below ``b`` (no positional ``:<n>`` is left); ``conflict_gaps``
must answer ordered by id and ``candidate_pairs`` by key, then a, then b. ``--require`` names scenarios
that must hold at least one conflict, so a run meant to show S4's cannot pass on a load that raised none.

The free Neo4j edition serves one database, so each Neo4j load replaces the last: every answer is read
before the next load. An rdflib store here lives in memory only. Exit 0 when every check holds, 1 when one
does not.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness"))

FORM = re.compile(r"^gap:conflict:(?P<key>.+?):(?P<a>A:[^~]+)~(?P<b>A:.+)$")


def read(kind: str, scenario: str) -> tuple[list[str], list[tuple]]:
    import gate_cli
    from store import open_store
    from subject import SUBJECT
    st = open_store(kind, instance=SUBJECT.id, access="write", **({"path": ""} if kind == "rdflib" else {}))
    try:
        gate_cli._load(st, scenario)
        gaps = [g["id"] for g in st.conflict_gaps()]
        pairs = [(str(p["key"]), p["a"], p["b"]) for p in st.candidate_pairs(across="elicited")]
    finally:
        st.close()
    return gaps, pairs


def check(scenario: str, stores: list[str]) -> tuple[list[str], int]:
    failures, seen = [], {}
    for kind in stores:
        gaps, pairs = read(kind, scenario)
        seen[kind] = gaps
        if gaps != sorted(gaps):
            failures.append(f"{scenario} {kind}: conflict_gaps not ordered by id: {gaps}")
        if pairs != sorted(pairs):
            failures.append(f"{scenario} {kind}: candidate_pairs not ordered by key, then id")
        for g in gaps:
            m = FORM.match(g)
            if not m or not m["a"] < m["b"]:
                failures.append(f"{scenario} {kind}: {g} is not gap:conflict:<key>:<a>~<b> with its ids sorted")
    first = stores[0]
    for kind in stores[1:]:
        if seen[kind] != seen[first]:
            failures.append(f"{scenario}: {kind} names its conflicts {seen[kind]}, {first} {seen[first]}")
    return failures, len(seen[first])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--stores", default="rdflib,rdflib", help="the store kinds to load into, comma-separated (default rdflib,rdflib)")
    ap.add_argument("--scenarios", help="comma-separated scenario ids (default: every scenario of the subject)")
    ap.add_argument("--require", default="", help="scenarios that must hold at least one conflict")
    args = ap.parse_args(argv)
    import cadence
    from subject import SUBJECT
    import os
    os.environ.update(cadence.pin_record({}))   # the record's day, the wall clock refused (task-0075)
    stores = [s.strip() for s in args.stores.split(",") if s.strip()]
    scenarios = args.scenarios.split(",") if args.scenarios else list(SUBJECT.order)
    required = {s for s in args.require.split(",") if s}
    failures = []
    for sc in scenarios:
        f, n = check(sc, stores)
        if sc in required and n == 0:
            f.append(f"{sc}: no conflict raised; the scenario is required to show one")
        failures += f
        print(f"{sc}: {n} conflict(s), one id each on {', '.join(stores)}" + ("" if not f else f"; {len(f)} failure(s)"))
    for f in failures:
        print("FAIL " + f, file=sys.stderr)
    print("conflict ids: " + ("every check holds" if not failures else f"{len(failures)} failure(s)"))
    return 1 if failures else 0


if __name__ == "__main__":
    import _outcomes   # task-0159: the outcome recorded when KG_OUTCOMES names a file
    sys.exit(_outcomes.run(main))
