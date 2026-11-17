"""Every list read the rules, the gate and the SHACL projection rest on answers in one total order, the same on
every store (task-0369).

    python tools/check_read_order.py [--stores neo4j,rdflib] [--scenarios C,D3]

For each scenario of the subject (``KG_SUBJECT``): load it fresh into each named store kind with ``gate_cli.py``'s
own load (the rules run, as a deterministic run runs them), then call each read in ``READS``. Each answer must equal
itself sorted by the read's named order (by id, or by id then a second field: ``store.by_id``, ``store.by_fields``),
and every store must give the same answer. Before task-0369 the Neo4j adapter answered R-VAGUE's and R-REQ's reads
in plan order and the rdflib adapter in graph order, so three Neo4j runs of one record gave three orders while the
comparator, which reads lists without order, saw nothing.

The free Neo4j edition serves one database, so each Neo4j load replaces the last: every answer is read before the
next load. An rdflib store here lives in memory only. Exit 0 when every check holds, 1 when one does not.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness"))


def _key(*fields):
    def k(r):
        if not isinstance(r, dict):
            return (r is None, str(r))
        return tuple(x for f in fields for x in (r.get(f) is None, str(r.get(f))))
    return k


def _reads(st) -> dict[str, tuple[list, object]]:
    """{read: (its answer, the sort key its order is named by)}: the reads ``harness/rules.py``, the gate and
    ``harness/shacl.py`` take a list from."""
    from rules import VAGUE
    keys = sorted({r["key"] for r in st.vague_fragments(VAGUE)} | {r["key"] for r in st.unresolved_assertions()})
    out = {
        "structural_violations": (st.structural_violations(), None),
        "vague_fragments": (st.vague_fragments(VAGUE), _key("id", "fid")),
        "unresolved_assertions": (st.unresolved_assertions(), _key("id")),
        "declared_open(specified)": (st.declared_open("specified"), _key("id", "entity")),
        "declared_open(authored)": (st.declared_open("authored"), _key("id", "entity")),
        "requirements_without(verified_by)": (st.requirements_without("verified_by"), _key()),
        "silent_entities": (st.silent_entities(["decision_row", "pricing_step"]), _key()),
        "assertion_rows": (st.assertion_rows(), _key("id")),
        "supported_by": (st.supported_by(), _key("x", "f")),
        "candidate_for": (st.candidate_for(), _key("x", "g")),
        "fragments_with_version": (st.fragments_with_version(), _key("f", "v")),
        "requirements_verified_by": (st.requirements_verified_by(), _key("e")),
        "derived_rows": ([{k: v for k, v in r.items() if k != "recorded"} for r in st.derived_rows()], _key("id")),
    }
    for k in keys[:5]:
        out[f"assertions_on_key({k})"] = (st.assertions_on_key(k, ["proposed", "validated", "verified", "approved"]), _key("id"))
    return out


def _in_order(name: str, rows: list, key) -> list[str]:
    if key is None:   # structural_violations: each check's rows by id, the checks in their fixed order
        groups: dict[str, list] = {}
        for r in rows:
            groups.setdefault(r["why"], []).append(r["id"])
        bad = [w for w, ids in groups.items() if ids != sorted(ids)]
        return [f"{name}: the rows of {w!r} are not ordered by id" for w in bad]
    if rows != sorted(rows, key=key):
        return [f"{name}: not in its named order"]
    if name == "requirements_verified_by" and any(r["by"] != sorted(r["by"], key=str) for r in rows):
        return [f"{name}: a requirement's verifying values are not sorted"]
    return []


def read(kind: str, scenario: str) -> dict:
    import gate_cli
    from store import open_store
    from subject import SUBJECT
    st = open_store(kind, instance=SUBJECT.id, access="write", **({"path": ""} if kind == "rdflib" else {}))
    try:
        gate_cli._load(st, scenario)
        return _reads(st)
    finally:
        st.close()


def check(scenario: str, stores: list[str]) -> tuple[list[str], int]:
    failures, seen = [], {}
    for kind in stores:
        got = read(kind, scenario)
        seen[kind] = {n: rows for n, (rows, _k) in got.items()}
        for n, (rows, key) in got.items():
            failures += [f"{scenario} {kind}: {f}" for f in _in_order(n, rows, key)]
    first = stores[0]
    for kind in stores[1:]:
        for n in seen[first]:
            if seen[kind].get(n) != seen[first][n]:
                failures.append(f"{scenario}: {n} answers differently on {kind} and {first}")
    return failures, sum(len(v) for v in seen[first].values())


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--stores", default="rdflib,rdflib", help="the store kinds to load into, comma-separated (default rdflib,rdflib)")
    ap.add_argument("--scenarios", help="comma-separated scenario ids (default: every scenario of the subject)")
    args = ap.parse_args(argv)
    import cadence
    from subject import SUBJECT
    os.environ.update(cadence.pin_record({}))   # the record's day, the wall clock refused (task-0075)
    stores = [s.strip() for s in args.stores.split(",") if s.strip()]
    scenarios = args.scenarios.split(",") if args.scenarios else list(SUBJECT.order)
    failures = []
    for sc in scenarios:
        f, n = check(sc, stores)
        failures += f
        print(f"{sc}: {n} row(s) over the ordered reads, one order on {', '.join(stores)}" + ("" if not f else f"; {len(f)} failure(s)"))
    for f in failures:
        print("FAIL " + f, file=sys.stderr)
    print("read order: " + ("every check holds" if not failures else f"{len(failures)} failure(s)"))
    return 1 if failures else 0


if __name__ == "__main__":
    import _outcomes   # task-0159: the outcome recorded when KG_OUTCOMES names a file
    sys.exit(_outcomes.run(main))
