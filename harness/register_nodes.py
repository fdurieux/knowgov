"""The register listed and filtered, and one node's lineage (task-0142, doc-0020 C1).

    python harness/register_nodes.py [--taxonomy T] [--kind K] [--state S] [--owner ORG-x] [--parent ID|--roots] [--limit N] [--offset N]
    python harness/register_nodes.py --node CAP-0002

Where an assistant starts without an id, and how it climbs the hierarchy. The listing is every node
of the register the server reads (``KG_REGISTER``, as ``register_impact`` reads it), sorted by id, each
with its taxonomy, kind, name, state, owner and parent, filtered by taxonomy, kind, state, owning unit
and parent, with a limit and the total. A unit owns a node by the node's ``owner`` field or an approved
``owns`` link from it (``register_impact.owning_unit``): "what does ORG-x own" is a listing, since the
register's decision 0010 never walks ``owns``.

With ``node``, the lineage: every ancestor by ``parent``, nearest first, up to the root, and the node's
children with their states. Lineage is an annotation, like the owner, never a reached node: the
register's decision 0014 keeps ``parent`` out of the walk, and nothing here walks a relationship.

Read with the register's own loader (``register_impact.load_tools``); no store. Standard library only.
Report pinned by ``harness/schemas/register-nodes.schema.json``.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import register_impact as ri  # noqa: E402

SCHEMA_VERSION = 1
TOOL = "register_nodes"
DEFAULT_LIMIT, MAX_LIMIT = 100, 1000
FILTERS = ("taxonomy", "kind", "state", "owner", "parent")


class NodesError(ValueError):
    """The question cannot be answered: an unknown filter value, a malformed or unknown id."""


def _entry(reg: dict, nid: str) -> dict:
    n = reg["nodes"][nid]
    return {"id": nid, "taxonomy": n.get("_taxonomy"), "kind": n.get("kind"), "name": n.get("name", ""),
            "state": n.get("state", ""), "owner": n.get("owner"), "parent": n.get("parent")}


def _brief(reg: dict, nid: str) -> dict:
    n = reg["nodes"].get(nid)
    if n is None:   # a parent the register names and does not hold: listed, never invented
        return {"id": nid, "kind": None, "name": None, "state": None, "missing": True}
    return {"id": nid, "kind": n.get("kind"), "name": n.get("name", ""), "state": n.get("state", "")}


def lineage(reg: dict, node: str) -> dict:
    """The ancestors of ``node`` by ``parent``, nearest first, to the root, and its children by id with
    their states. A parent the register does not hold ends the climb, marked ``missing``; a parent met
    twice ends it too, with ``cycle`` naming the repeated id (the register's checker refuses both)."""
    ancestors, seen, cycle = [], {node}, None
    at = reg["nodes"][node].get("parent")
    while at is not None:
        if at in seen:
            cycle = at
            break
        seen.add(at)
        ancestors.append(_brief(reg, at))
        if at not in reg["nodes"]:
            break
        at = reg["nodes"][at].get("parent")
    children = [_brief(reg, c) for c in sorted(nid for nid, n in reg["nodes"].items() if n.get("parent") == node)]
    return {"ancestors": ancestors, "root": ancestors[-1]["id"] if ancestors else node, "depth": len(ancestors),
            "children": children, "cycle": cycle}


def _owned_by(reg: dict, nid: str, unit: str) -> bool:
    own = ri.owning_unit(reg, nid)
    return own["unit"] == unit or unit in own["owns"]


def _check(reg: dict, args: dict) -> dict:
    """The filters, validated against the register itself; refused with what it holds otherwise."""
    allowed = {*FILTERS, "node", "limit", "offset"}
    extra = sorted(set(args) - allowed)
    if extra:
        raise NodesError(f"unknown argument(s) {extra}; register_nodes takes {sorted(allowed)}")
    got = {k: args.get(k) for k in FILTERS if k in args}
    taxonomies = sorted(reg["types"]["taxonomy"])
    kinds = sorted({k for spec in reg["types"]["taxonomy"].values() for k in spec["kinds"]})
    states = list(reg["lifecycle"].get("states", []))
    for name, values in (("taxonomy", taxonomies), ("kind", kinds), ("state", states)):
        if name in got and got[name] not in values:
            raise NodesError(f"{name} {got[name]!r}: the register's are {values}")
    if "owner" in got:
        unit = got["owner"]
        if not isinstance(unit, str) or unit not in reg["nodes"] or reg["nodes"][unit]["_taxonomy"] != "organisation":
            units = sorted(nid for nid, n in reg["nodes"].items() if n["_taxonomy"] == "organisation")
            raise NodesError(f"owner {unit!r}: a unit of the register's organisation, one of {units}")
    if "parent" in got and got["parent"] is not None:
        p = got["parent"]
        if not isinstance(p, str) or not ri.NODE_ID.match(p) or p not in reg["nodes"]:
            raise NodesError(f"parent {p!r}: a register id the register holds, or null for the nodes with no parent")
    for name, low, default in (("limit", 1, DEFAULT_LIMIT), ("offset", 0, 0)):
        v = args.get(name, default)
        if isinstance(v, bool) or not isinstance(v, int) or v < low or (name == "limit" and v > MAX_LIMIT):
            raise NodesError(f"{name}: an integer from {low}" + (f" to {MAX_LIMIT}" if name == "limit" else ""))
        got[name] = v
    return got


def report(args: dict | None = None, root: Path | None = None) -> dict:
    """The listing (``nodes``, ``total``, ``limit``, ``offset``, ``truncated``) under the filters, or with
    ``node`` that one node and its lineage. Raises NodesError on what the register does not hold."""
    args = dict(args or {})
    root = (root or ri.register_root()).resolve()
    reg = ri.load_tools(root)["register"].load_register(root)
    node = args.pop("node", None)
    if node is not None:
        if not isinstance(node, str) or not ri.NODE_ID.match(node):
            raise NodesError(f"node {node!r}: a register id, such as an upper-case prefix, a hyphen and four or more digits")
        if node not in reg["nodes"]:
            raise NodesError(f"{node}: no such node in the register")
        if set(args) & {*FILTERS, "limit", "offset"}:
            raise NodesError("node reads one node's lineage; the filters, limit and offset are the listing's, not its")
        entry = {**_entry(reg, node), "owning_unit": ri.owning_unit(reg, node)}
        return {"schema_version": SCHEMA_VERSION, "tool": TOOL, "register": ri.source(root), "filters": {},
                "total": 1, "limit": 1, "offset": 0, "truncated": False, "nodes": [entry],
                "lineage": {"node": node, **lineage(reg, node)}}
    got = _check(reg, args)
    match = []
    for nid in sorted(reg["nodes"]):
        n = reg["nodes"][nid]
        if "taxonomy" in got and n["_taxonomy"] != got["taxonomy"]:
            continue
        if "kind" in got and n.get("kind") != got["kind"]:
            continue
        if "state" in got and n.get("state") != got["state"]:
            continue
        if "parent" in got and n.get("parent") != got["parent"]:
            continue
        if "owner" in got and not _owned_by(reg, nid, got["owner"]):
            continue
        match.append(nid)
    lim, off = got.pop("limit"), got.pop("offset")
    page = match[off:off + lim]
    return {"schema_version": SCHEMA_VERSION, "tool": TOOL, "register": ri.source(root), "filters": got,
            "total": len(match), "limit": lim, "offset": off, "truncated": off + len(page) < len(match),
            "nodes": [_entry(reg, nid) for nid in page], "lineage": None}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="register_nodes.py", description=__doc__.splitlines()[0])
    for name in ("taxonomy", "kind", "state", "owner", "parent"):
        ap.add_argument(f"--{name}")
    ap.add_argument("--roots", action="store_true", help="the nodes with no parent")
    ap.add_argument("--node", help="one node and its lineage")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--offset", type=int)
    a = ap.parse_args(argv)
    args = {k: v for k, v in vars(a).items() if v is not None and k != "roots"}
    if a.roots:
        args["parent"] = None
    try:
        ri.require()   # task-0279: a register that cannot be read is a cannot-run, named, never a traceback
        print(json.dumps(report(args), indent=1, ensure_ascii=False))
    except ri.RegisterUnreadable as e:
        print(f"register_nodes: cannot run: {e}", file=sys.stderr)
        return 2
    except NodesError as e:
        print(f"register_nodes: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
