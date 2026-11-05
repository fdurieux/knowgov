"""Walk the typed edges from a node and print each with its state, owner and evidence. The walk
follows approved links only and never expands a deprecated or retired node; an edge whose link
is not approved, or whose far node is deprecated or retired, is reported and marked withdrawn,
not followed and not counted among what was reached (decision 0007). It starts from any node
kind that something rests on (decision 0010). The IEAM's own question: which journeys and products
would be affected by retiring this module, changing this capability or this information entity?

A second, named walk (decision 0012) answers what implements a capability: the processes
that realise it and the applications that support those processes. Same rule, other rows.

With --children (decision 0014), the walk also starts from every descendant reached by `parent`,
recursively: approved ones are walked, each by its own taxonomy's row; any other is reported,
marked withdrawn, and not walked from. `parent` adds starts, never steps; off by default.

The start is never counted among what a walk reaches (decision 0016): an edge back to it is reported
and marked ``to_start``, not counted; below a withdrawn descendant the descent continues to approved ones.

A third, named walk (decision 0018), `thread`, answers what a journey step uses, down to the
data: the process that supports it, the capability that process realises, the application that
supports it and the information the process and the application read, write or manage.

    python tools/impact.py --from APP-0002
    python tools/impact.py --from CAP-0002 --walk realisers
    python tools/impact.py --from JRN-0002 --walk thread
    python tools/impact.py --from CAP-0001 --children
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from register import ROOT, load_register  # noqa: E402

# how impact travels: (relationship, follow from source to target?) per step. Every step points from
# the thing changed to what rests on it (decision 0010): a process that reads an entity rests on it
# (crud inverse), an application that manages it too (manages inverse); a product rests on the
# capability it requires (requires inverse); the journeys and processes around a product rest on it
# (concerns, delivers inverse); a journey step rests on the process that supports it (is_supported_by).
# owns and maps_to are never walked: the owner is shown, not reached, and maps_to leaves the register.
FORWARD = {
    "applications": [("supports", True)],
    "processes": [("delivers", True), ("is_supported_by", False), ("realizes", True)],
    "journeys": [("concerns", True), ("is_supported_by", True)],
    "capabilities": [("requires", False)],
    "information": [("crud", False), ("manages", False)],
    "products": [("concerns", False), ("delivers", False)],
}


# what implements a capability (decision 0012): the processes that realise it (realizes
# inverse), then the applications that support those processes (supports inverse). It stops there:
# an application has no row, so the walk never turns back towards what rests on the capability.
REALISERS = {
    "capabilities": [("realizes", False)],
    "processes": [("supports", False)],
}

# what a journey step uses, down to the data (decision 0018): the step to the process that supports it
# (is_supported_by forward); the process to the capability it realises (realizes forward), the
# application that supports it (supports inverse) and the information it reads or writes (crud
# forward); the application to the information it manages (manages forward). Every step points away
# from the journey; capabilities and information have no row, so the walk ends there and never turns
# back towards the product. owns and maps_to are never walked; parent adds starts, never steps.
THREAD = {
    "journeys": [("is_supported_by", True)],
    "processes": [("realizes", True), ("supports", False), ("crud", True)],
    "applications": [("manages", True)],
}

WALKS = {"dependants": FORWARD, "realisers": REALISERS, "thread": THREAD}

WITHDRAWN = ("deprecated", "retired")


def walk(reg: dict, start: str, rows: dict | None = None) -> list[dict]:
    """Every edge the walk met, in order, each with ``live``: True when the link is approved and the
    far node is neither deprecated nor retired; a withdrawn edge is reported and not followed. An edge
    whose far node is the start is reported with ``to_start`` and never counted (decision 0016)."""
    seen, out, frontier = {start}, [], [start]
    while frontier:
        nxt = []
        for nid in frontier:
            n = reg["nodes"].get(nid)
            if n is None or n.get("state") in WITHDRAWN:
                continue
            for rel, forward in (FORWARD if rows is None else rows).get(n["_taxonomy"], []):
                for ln in reg["relationships"].get(rel, {}).get("links", []):
                    a, b = (ln["source"], ln.get("target")) if forward else (ln.get("target"), ln["source"])
                    if a != nid or b is None:
                        continue
                    far = reg["nodes"].get(b) or {}
                    live = ln.get("state") == "approved" and far.get("state") not in WITHDRAWN
                    out.append({"from": nid, "rel": rel if forward else f"{rel} (inverse)", "to": b, "state": ln.get("state"), "owner": ln.get("owner"),
                                "evidence": ln.get("evidence", []), "live": live, "to_start": b == start})
                    if live and b not in seen:
                        seen.add(b)
                        nxt.append(b)
        frontier = nxt
    return out


def reached(edges: list[dict]) -> set[str]:
    """What the walk reached: the far ends of live edges only, never the start (decision 0016)."""
    return {e["to"] for e in edges if e.get("live") and not e.get("to_start")}


def descendants(reg: dict, start: str) -> list[str]:
    """Every node below ``start`` by ``parent``, recursively, depth first in id order."""
    kids: dict[str, list[str]] = {}
    for nid, n in reg["nodes"].items():
        if n.get("parent") is not None:
            kids.setdefault(n["parent"], []).append(nid)
    out, stack = [], sorted(kids.get(start, []), reverse=True)
    while stack:
        nid = stack.pop()
        if nid in out or nid == start:
            continue
        out.append(nid)
        stack.extend(sorted(kids.get(nid, []), reverse=True))
    return out


def walk_children(reg: dict, start: str, rows: dict | None = None) -> dict:
    """Decision 0014: the walk from ``start`` and from each approved descendant, each by its own
    taxonomy's row of ``rows``. Returns ``descendants`` (id, state, ``live``: approved, so walked),
    ``edges`` (every edge met, from every start walked) and ``reached``: the union of the live far
    ends, less the start and its descendants. ``walk`` itself is unchanged."""
    desc = descendants(reg, start)
    listed = [{"id": d, "state": reg["nodes"][d].get("state"), "live": reg["nodes"][d].get("state") == "approved"} for d in desc]
    edges = list(walk(reg, start, rows))
    for d in listed:
        if d["live"]:
            edges.extend(walk(reg, d["id"], rows))
    return {"descendants": listed, "edges": edges, "reached": reached(edges) - {start, *desc}}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from", dest="start", required=True)
    ap.add_argument("--walk", choices=sorted(WALKS), default="dependants",
                    help="dependants: what rests on the node (decision 0010, the default); realisers: what implements a capability (decision 0012); "
                         "thread: what a journey step uses, down to the data (decision 0018)")
    ap.add_argument("--children", action="store_true",
                    help="also walk from every approved descendant by parent, recursively (decision 0014); off by default")
    ap.add_argument("--root", type=Path, default=ROOT)
    a = ap.parse_args(argv)
    reg = load_register(a.root)
    if a.start not in reg["nodes"]:
        print(f"{a.start}: no such node")
        return 2
    if a.children:
        got = walk_children(reg, a.start, WALKS[a.walk])
        edges, live = got["edges"], got["reached"]
        print(f"{a.start}: descendants by parent")
        for d in got["descendants"]:
            n = reg["nodes"][d["id"]]
            print(f"  {d['id']} {n['name']!r} ({d['state']}){'' if d['live'] else ' WITHDRAWN, not walked'}")
        if not got["descendants"]:
            print("  none")
        print()
    else:
        edges = walk(reg, a.start, WALKS[a.walk])
        live = reached(edges)
    for e in edges:
        n = reg["nodes"][e["to"]]
        mark = "" if e["live"] else " WITHDRAWN, not followed"
        print(f"{e['from']} -[{e['rel']}, {e['state']}, owner {e['owner']}]-> {e['to']} {n['name']!r} ({n['state']}){mark}; evidence: {', '.join(e['evidence']) or 'none'}")
    withdrawn = sum(1 for e in edges if not e["live"])
    if a.walk == "realisers":
        procs = sorted(x for x in live if x.startswith("PROC-"))
        apps = sorted(x for x in live if x.startswith("APP-"))
        print(f"\n{a.start}: {len(edges)} edges walked, {withdrawn} withdrawn; processes reached {procs or 'none'}; applications reached {apps or 'none'}")
        return 0
    if a.walk == "thread":
        got = {p: sorted(x for x in live if x.startswith(p)) for p in ("PROC-", "CAP-", "APP-", "ENT-")}
        print(f"\n{a.start}: {len(edges)} edges walked, {withdrawn} withdrawn; processes reached {got['PROC-'] or 'none'}; "
              f"capabilities reached {got['CAP-'] or 'none'}; applications reached {got['APP-'] or 'none'}; information reached {got['ENT-'] or 'none'}")
        return 0
    prods = sorted(x for x in live if x.startswith("PRD-"))
    jrns = sorted(x for x in live if x.startswith("JRN-"))
    print(f"\n{a.start}: {len(edges)} edges walked, {withdrawn} withdrawn; products reached {prods or 'none'}; journey elements reached {jrns or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
