"""Walk the typed edges from a node and print each with its state, owner and evidence. The walk
follows approved links only and never expands a deprecated or retired node; an edge whose link
is not approved, or whose far node is deprecated or retired, is reported and marked withdrawn,
not followed and not counted among what was reached (decision 0007). It starts from any node
kind that something rests on (decision 0010). The IEAM's own question: which journeys and products
would be affected by retiring this module, changing this capability or this information entity?

    python tools/impact.py --from APP-0002
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


WITHDRAWN = ("deprecated", "retired")


def walk(reg: dict, start: str) -> list[dict]:
    """Every edge the walk met, in order, each with ``live``: True when the link is approved and the
    far node is neither deprecated nor retired; a withdrawn edge is reported and not followed."""
    seen, out, frontier = {start}, [], [start]
    while frontier:
        nxt = []
        for nid in frontier:
            n = reg["nodes"].get(nid)
            if n is None or n.get("state") in WITHDRAWN:
                continue
            for rel, forward in FORWARD.get(n["_taxonomy"], []):
                for ln in reg["relationships"].get(rel, {}).get("links", []):
                    a, b = (ln["source"], ln.get("target")) if forward else (ln.get("target"), ln["source"])
                    if a != nid or b is None:
                        continue
                    far = reg["nodes"].get(b) or {}
                    live = ln.get("state") == "approved" and far.get("state") not in WITHDRAWN
                    out.append({"from": nid, "rel": rel if forward else f"{rel} (inverse)", "to": b, "state": ln.get("state"), "owner": ln.get("owner"),
                                "evidence": ln.get("evidence", []), "live": live})
                    if live and b not in seen:
                        seen.add(b)
                        nxt.append(b)
        frontier = nxt
    return out


def reached(edges: list[dict]) -> set[str]:
    """What the walk reached: the far ends of live edges only."""
    return {e["to"] for e in edges if e.get("live")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from", dest="start", required=True)
    ap.add_argument("--root", type=Path, default=ROOT)
    a = ap.parse_args(argv)
    reg = load_register(a.root)
    if a.start not in reg["nodes"]:
        print(f"{a.start}: no such node")
        return 2
    edges = walk(reg, a.start)
    for e in edges:
        n = reg["nodes"][e["to"]]
        mark = "" if e["live"] else " WITHDRAWN, not followed"
        print(f"{e['from']} -[{e['rel']}, {e['state']}, owner {e['owner']}]-> {e['to']} {n['name']!r} ({n['state']}){mark}; evidence: {', '.join(e['evidence']) or 'none'}")
    live = reached(edges)
    prods = sorted(x for x in live if x.startswith("PRD-"))
    jrns = sorted(x for x in live if x.startswith("JRN-"))
    withdrawn = sum(1 for e in edges if not e["live"])
    print(f"\n{a.start}: {len(edges)} edges walked, {withdrawn} withdrawn; products reached {prods or 'none'}; journey elements reached {jrns or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
