"""The store survives a round trip through Turtle (task-0070, doc-0013 P4).

    python tools/check_round_trip.py [--chain rdflib,rdflib] [--scenarios S1,S2] [--no-stage2] [--expect-preload] [--expect-parts]

For each scenario of the subject (``KG_SUBJECT``): load it into the chain's first store with
``gate_cli.py``'s own load, then hand it on, hop by hop, as Turtle: ``export_turtle`` on one store,
``import_turtle`` into a fresh store of the next kind. On every store of the chain ask the same
questions through the MCP server's tools (harness/mcp_server.py, on a read-only view): the gate's
report for every task the subject declares, and the three-valued answer, with provenance, for every
key the subject names and every key a task requires. Every answer must equal the first store's,
the store's own name and the order of its lists aside (``canonical``); the census must too; and the last store's Turtle must hold the same
nodes and edges, by id, label, type and property, as the first's. A scenario with a later version
(``[scenario.stage2]``) is checked again after the change, before re-verification, as
``gate_cli.py --stage 2`` loads it.

The pre-load verdicts (task-0064, task-0085) are compared too: every Version's preload_* verdict
(``preload_verdicts``) and, per task, the gate's preload bundle (the documents behind the keys whose
form was unchecked or had findings), as well as the info findings of kind preload the gate reports
carry. So are the file digests a directory artefact's versions carry (``part_digests``, task-0094),
row for row; ``--expect-parts`` fails a scenario whose first store recorded none (a subject with a
directory artefact, J-F). A subject inside an instance with a pre-load report (``tools/preload_check.py -o
<instance>/preload-report.json``) records them; ``--expect-preload`` fails a scenario whose first
store recorded none, so a run meant to prove they survive cannot pass on a store that never held one.

The chain names store kinds (``KG_STORE``'s values), first the one loaded: ``rdflib,rdflib`` needs
no database (harness.yml); ``neo4j,rdflib,neo4j`` is Neo4j to Turtle to rdflib and back, the stack
job's. The free Neo4j edition serves one database, so a later Neo4j hop wipes the store the first
was read from: every answer is taken before the hop. An rdflib store here lives in memory only.
Exit 0 when every check holds, 1 when one does not.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / "harness"
sys.path.insert(0, str(HARNESS))


def open_kind(kind: str, instance: str):
    from store import open_store
    return open_store(kind, instance=instance, **({"path": ""} if kind == "rdflib" else {}))


def answers(st, scenario: str) -> dict:
    """What a client reads: the MCP server's gate report per task and three-valued answer per key."""
    import gate
    import mcp_server
    from subject import SUBJECT
    from tasks import TASKS

    class Held(mcp_server.ReadOnlyStore):
        def release(self) -> None:   # the chain closes its stores itself
            pass

    tools = mcp_server.Tools(opener=lambda: Held(st))
    keys = list(dict.fromkeys([*SUBJECT.three_valued, *(k for t in TASKS.values() for k in t["keys"])]))
    strip = lambda d: {k: v for k, v in d.items() if k != "store"}  # noqa: E731
    reports = {t: strip(tools.gate_verdict({"scenario": scenario, "task": t})) for t in sorted(TASKS)}
    view = Held(st)
    return {"gate": reports,
            "three_valued": {k: strip(tools.three_valued_answer({"key": k, "scenario": scenario})) for k in keys},
            "census": st.census(),
            # task-0094: the file digests a directory artefact's versions carry
            "parts": st.part_digests(),
            # task-0085: each Version's pre-load verdict, and per task the gate's preload bundle and its info findings
            "preload": {"verdicts": view.preload_verdicts(),
                        "bundle": {t: gate.resolve(view, t).get("preload") for t in sorted(TASKS)},
                        "findings": {t: [f for f in r["findings"] if f["kind"] == "preload"] for t, r in reports.items()}}}


def shape(turtle: str) -> tuple[list, list]:
    """The graph a Turtle export holds, by id, independent of store order and edge naming."""
    from store_rdflib import RdflibStore
    g = RdflibStore(path="")
    g.import_turtle(turtle)
    dump = lambda d: json.dumps(d, sort_keys=True, default=str)  # noqa: E731
    nodes = sorted((nid, g.labels(n), dump(g.props(n))) for nid, n in g._nodes.items())
    key = {n: nid for nid, n in g._nodes.items()}
    edges = sorted((key[n], g._edge(e)[1], key[t], dump(g.props(e))) for n in key for e, t in g.edges_out(n))
    return nodes, edges


def canonical(v):
    """``v`` with every list sorted: a list's order is the store's order (Neo4j's collect() walks a
    node's relationships in its own order), never what the answer means, as the deterministic
    comparator treats lists of scalars; the gate's findings are sorted by the gate itself."""
    if isinstance(v, dict):
        return {k: canonical(x) for k, x in v.items()}
    if isinstance(v, list):
        return sorted((canonical(x) for x in v), key=lambda x: json.dumps(x, sort_keys=True, default=str))
    return v


def differences(a: dict, b: dict, where: str) -> list[str]:
    out = []
    a, b = canonical(a), canonical(b)
    for part in ("gate", "three_valued"):
        for k in sorted(set(a[part]) | set(b[part])):
            x, y = a[part].get(k), b[part].get(k)
            if x != y:
                fields = sorted(f for f in set(x or {}) | set(y or {}) if (x or {}).get(f) != (y or {}).get(f))
                out.append(f"{where}: {part} {k} differs on {fields}")
    for part in ("verdicts", "bundle", "findings"):
        if a.get("preload", {}).get(part) != b.get("preload", {}).get(part):
            out.append(f"{where}: preload {part} differs")
    if a.get("parts") != b.get("parts"):
        out.append(f"{where}: part digests differ: {len(a.get('parts') or [])} -> {len(b.get('parts') or [])}")
    if a["census"] != b["census"]:
        out.append(f"{where}: census {a['census']} != {b['census']}")
    return out


def check(scenario: str, chain: list[str], stage2: bool, expect_preload: bool = False, expect_parts: bool = False) -> list[str]:
    import gate_cli
    from subject import SUBJECT
    label = f"{scenario}{' stage 2' if stage2 else ''}"
    first = open_kind(chain[0], SUBJECT.id)
    try:
        gate_cli._load(first, scenario)
        if stage2:
            gate_cli._change(first, SUBJECT, scenario, SUBJECT.scenario(scenario)["stage2"], False)
        base = answers(first, scenario)
        ttl0 = ttl = first.export_turtle()
    finally:
        first.close()
    failures = []
    if expect_preload and not base["preload"]["verdicts"]:
        failures.append(f"{label} {chain[0]}: the load recorded no pre-load verdict: is there a report at the instance's root or in KG_PRELOAD_REPORT?")
    if expect_parts and not base["parts"]:
        failures.append(f"{label} {chain[0]}: the load recorded no file digest of a directory artefact: does the subject load one?")
    for i, kind in enumerate(chain[1:], 1):
        st = open_kind(kind, SUBJECT.id)
        try:
            st.import_turtle(ttl)
            got = answers(st, scenario)
            failures += differences(base, got, f"{label} {'→'.join(chain[:i + 1])}")
            ttl = st.export_turtle()
        finally:
            st.close()
    if shape(ttl) != shape(ttl0):
        n0, e0 = shape(ttl0)
        n1, e1 = shape(ttl)
        failures.append(f"{label} {'→'.join(chain)}: the graph changed: nodes {len(n0)} -> {len(n1)} "
                        f"({len(set(n0) ^ set(n1))} differ), edges {len(e0)} -> {len(e1)} ({len(set(e0) ^ set(e1))} differ)")
    v = base["gate"].get("codegen", next(iter(base["gate"].values()), {}))
    print(f"{label}: {'→'.join(chain)}: {len(base['gate'])} gate report(s) (codegen {v.get('verdict')}), "
          f"{len(base['three_valued'])} three-valued answer(s), {base['census']['nodes']} nodes, "
          f"{base['census']['relationships']} relationships, "
          f"{len(base['parts'])} file digest(s) of directory artefacts, "
          f"{len(base['preload']['verdicts'])} pre-load verdict(s), {sum(map(len, base['preload']['findings'].values()))} preload finding(s): " + ("equal" if not failures else f"{len(failures)} difference(s)"))
    return failures


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--chain", default="rdflib,rdflib", help="store kinds, first the one loaded (default: rdflib,rdflib)")
    ap.add_argument("--scenarios", help="comma-separated scenario ids (default: every scenario of the subject)")
    ap.add_argument("--no-stage2", action="store_true", help="skip the later version of a scenario that has one")
    ap.add_argument("--expect-preload", action="store_true",
                    help="fail when the first store recorded no pre-load verdict (the subject's instance has no report)")
    ap.add_argument("--expect-parts", action="store_true",
                    help="fail when the first store recorded no file digest of a directory artefact (task-0094)")
    args = ap.parse_args(argv)
    chain = [k.strip().lower() for k in args.chain.split(",") if k.strip()]
    if len(chain) < 2:
        ap.error("--chain names at least two stores")
    import cadence
    from subject import SUBJECT
    os.environ.update(cadence.pin_record({}))   # the record's day, the wall clock refused (task-0075)
    scenarios = args.scenarios.split(",") if args.scenarios else list(SUBJECT.order)
    failures = []
    for sc in scenarios:
        failures += check(sc, chain, False, args.expect_preload, args.expect_parts)
        if not args.no_stage2 and SUBJECT.scenario(sc).get("stage2"):
            failures += check(sc, chain, True, args.expect_preload, args.expect_parts)
    for f in failures:
        print("FAIL " + f, file=sys.stderr)
    print(f"round trip {SUBJECT.id} {'→'.join(chain)}: " + ("every answer survives" if not failures else f"{len(failures)} failure(s)"))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
