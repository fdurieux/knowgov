"""What retiring a register node touches (task-0111): the register's own impact walk, the map rows
it lands on, and, with a scenario held, each key's level, stale statements and suspect derived outputs.

The walk is the vendored register's (``tools/impact.py``, loaded by path from ``KG_REGISTER``, the
register ``cadence.register_root`` reads, as ``demo/app/register_view`` loads it): approved links only,
a deprecated or retired node is not expanded, a withdrawn edge is listed and not followed. By default
a node's ``parent`` is not descended: its children are listed, each with its state, as not walked. With
``children`` (task-0118) the descent is the register's own (its decision 0014, ``impact.walk_children``,
v0.2.8 on): the walk also starts from every descendant by ``parent``, recursively, each by its own
taxonomy's row; an approved one is walked, any other is listed withdrawn and not walked from, and what
is reached is the union less the start and its descendants. Either way the start is never counted
reached (decision 0016, v0.2.9 on: an edge back to it is listed, ``to_start``, and ``impact.reached``
drops it). ``parent`` is never climbed. The rows are
the subject's ``register_map.toml``: a row whose nodes name the start, a walked descendant or a reached
node lands, with the nodes it came through; with ``children``, a row that names only a withdrawn
descendant lands after them, flagged ``withdrawn`` (task-0120). Its owner is the row's, as the gate's
findings name it.

The levels come from the gate itself, ``gate_cli.evaluate`` over the landed keys on one ``as_of``
under one declared task class (its block levels, bar and route; codegen by default, task-0120), the
report ``gate_verdict --task`` makes for that key set, so a key reads here as ``gate_verdict`` reports it.
Only the store port's reads are used; nothing is written. Standard library only.
"""
from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
import threading
from pathlib import Path

NODE_ID = re.compile(r"^[A-Z]+-\d{4,}$")
WALKS = ("dependants", "realisers")
OWNED = ("key", "stale", "lapsed")   # the findings that concern one key (gate_cli.OWNED)

_tools: dict[str, dict] = {}
_lock = threading.Lock()


class ImpactError(ValueError):
    """The question cannot be answered: a malformed or unknown id, a walk the register lacks."""


def register_root() -> Path:
    import cadence
    return cadence.register_root()


def load_tools(root: Path | None = None) -> dict:
    """The register's ``register`` and ``impact`` modules, imported once per root, by path, from the
    register itself (``impact.py`` imports ``register`` by name, so both are put in ``sys.modules``)."""
    root = (root or register_root()).resolve()
    with _lock:
        if str(root) not in _tools:
            tools = root / "tools"
            if str(tools) not in sys.path:
                sys.path.insert(0, str(tools))
            mods = {}
            for name in ("register", "impact"):
                spec = importlib.util.spec_from_file_location(name, tools / f"{name}.py")
                mod = importlib.util.module_from_spec(spec)
                sys.modules[name] = mod
                spec.loader.exec_module(mod)
                mods[name] = mod
            _tools[str(root)] = mods
        return _tools[str(root)]


def source(root: Path) -> dict:
    """The register's tag and commit: a vendored copy's SOURCE.md, else what git says of a checkout."""
    note = root / "SOURCE.md"
    if note.exists():
        text = note.read_text(encoding="utf-8")
        commit = re.search(r"\| commit \| `([0-9a-f]{40})`", text)
        tag = re.search(r"^\| tag \| `(v[0-9][^`]*)`", text, re.M)
        return {"tag": tag.group(1) if tag else "", "commit": commit.group(1) if commit else ""}

    def git(*args: str) -> str:
        try:
            return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return ""
    return {"tag": git("describe", "--tags", "--exact-match"), "commit": git("rev-parse", "HEAD")}


def owning_unit(reg: dict, nid: str) -> dict:
    """The unit its owner field names, that unit's name, and the sources of the approved owns links
    to the node, sorted: the impact panel's three (``register_view.owning_unit``)."""
    unit = (reg["nodes"].get(nid) or {}).get("owner", "") or ""
    owns = sorted({ln["source"] for ln in reg["relationships"].get("owns", {}).get("links", [])
                   if ln.get("target") == nid and ln.get("state") == "approved"})
    return {"unit": unit, "name": (reg["nodes"].get(unit) or {}).get("name", ""), "owns": owns}


def walk(node: str, which: str = "dependants", root: Path | None = None, children: bool = False) -> dict:
    """The register part of the answer, without the store: the node, its children, the edges, what
    they reach. With ``children``, every descendant by ``parent`` with its parent, its state, whether
    it was walked (approved) and, if not, ``withdrawn``; the edges and what is reached are
    ``impact.walk_children``'s. Raises ImpactError on a malformed or unknown id, a walk the register
    lacks, or ``children`` asked of a register without the descent."""
    if not isinstance(node, str) or not NODE_ID.match(node):
        raise ImpactError(f"node {node!r}: a register id, such as an upper-case prefix, a hyphen and four or more digits")
    if which not in WALKS:
        raise ImpactError(f"walk must be one of {list(WALKS)}")
    if not isinstance(children, bool):
        raise ImpactError("children must be true or false")
    root = (root or register_root()).resolve()
    T = load_tools(root)
    reg = T["register"].load_register(root)
    if node not in reg["nodes"]:
        raise ImpactError(f"{node}: no such node in the register")
    rows = getattr(T["impact"], "WALKS", {}).get(which)
    if rows is None and which != "dependants":
        raise ImpactError(f"the register at {source(root)['tag'] or root} offers no {which} walk")
    if children:
        if not hasattr(T["impact"], "walk_children"):
            raise ImpactError(f"the register at {source(root)['tag'] or root} does not descend parent (its decision 0014, v0.2.8 on)")
        got = T["impact"].walk_children(reg, node, rows)
        edges, reached = got["edges"], sorted(got["reached"])
        listed = [{"id": d["id"], "name": reg["nodes"][d["id"]].get("name", ""), "state": d["state"],
                   "parent": reg["nodes"][d["id"]].get("parent"), "walked": d["live"], "withdrawn": not d["live"]}
                  for d in got["descendants"]]
    else:
        edges = T["impact"].walk(reg, node) if rows is None else T["impact"].walk(reg, node, rows)
        reached = sorted(T["impact"].reached(edges))
        listed = [{"id": c, "name": reg["nodes"][c].get("name", ""), "state": reg["nodes"][c].get("state", ""), "walked": False}
                  for c in sorted(nid for nid, c in reg["nodes"].items() if c.get("parent") == node)]
    n = reg["nodes"][node]
    by_prefix: dict[str, list[dict]] = {}
    for x in reached:
        r = reg["nodes"].get(x) or {}
        by_prefix.setdefault(x.split("-", 1)[0], []).append(
            {"id": x, "name": r.get("name", ""), "state": r.get("state", ""), "owning_unit": owning_unit(reg, x)})
    return {"register": source(root), "walk": which,
            "node": {"id": node, "taxonomy": n.get("_taxonomy"), "kind": n.get("kind"), "name": n.get("name"),
                     "state": n.get("state"), "owner": n.get("owner"), "parent": n.get("parent"),
                     "owning_unit": owning_unit(reg, node)},
            "children_walked": children, "children": listed,
            "edges": edges, "reached": by_prefix, "reached_ids": reached}


def landed_rows(register_map: dict, node: str, reached: list[str], walked: list[str] = (),
                withdrawn: list[str] = ()) -> list[dict]:
    """The map's rows that name the start, a walked descendant or a reached node, each with the nodes it
    came through (``via``: the start first when the row names it, then the walked descendants, then the
    reached nodes it names, as ``walk`` lists them). Then (task-0120) every other row that names a
    withdrawn descendant, flagged ``withdrawn: true`` with the withdrawn descendants it names as ``via``:
    a key that rests on what the descent reached but did not walk, listed and walked no further. A
    withdrawn edge's far node is not touched."""
    touched = [node, *walked, *reached]
    out, flagged = [], []
    for row in register_map.get("row", []):
        names = row.get("nodes") or []
        via = [x for x in touched if x in names]
        if via:
            out.append({"key": row["key"], "owner": row.get("owner"), "anchor": row.get("anchor"), "via": via})
        elif any(x in names for x in withdrawn):
            flagged.append({"key": row["key"], "owner": row.get("owner"), "anchor": row.get("anchor"),
                            "via": [x for x in withdrawn if x in names], "withdrawn": True})
    return out + flagged


def with_levels(keys: list[dict], report: dict) -> list[dict]:
    """Each landed key with its level, its key, stale and lapsed findings, the ids of its stale
    statements and the suspect derived outputs that used one of them, all read off ``report``: the
    gate's report over the landed keys (``gate_cli.evaluate``, as ``gate_verdict`` makes it for a
    key set), so a key reads here exactly as ``gate_verdict`` reports it on the same as_of."""
    fs = report["findings"]
    suspect = [f for f in fs if f["kind"] == "suspect_derived"]
    out = []
    for k in keys:
        mine = [f for f in fs if f["kind"] in OWNED and f["key"] == k["key"]]
        stale = sorted(f["ref"] for f in mine if f["kind"] == "stale")
        out.append({**k, "level": report["levels"][k["key"]], "stale": stale,
                    "suspect": sorted(f["ref"] for f in suspect if set(f["related"]) & set(stale)), "findings": mine})
    return out
