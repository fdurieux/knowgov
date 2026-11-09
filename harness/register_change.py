"""A register change invalidates (task-0122): what a register update withdrew, and what rested on it.

``diff(previous, current)`` compares two register roots (the previous vendored tag and the current
one; an instance's checkout before and after its update) and lists every node that became deprecated
or retired (or left the register) and every link withdrawn (approved before; not approved now, or
gone), each with its reason: the register's decision record for the change. ``resting(change,
register_map)`` lands them on the subject's keys: for a node, the map rows the register's own walk
lands (the dependants walk with the descent by ``parent``, decision 0014, the start never counted,
decision 0016, on the previous register, where what rested on the node still stood; a row naming only
a withdrawn descendant lands too, flagged, as ``register_impact`` lands it, task-0120; a descendant
the new register re-parented away from the node, in any state, is skipped with its subtree: it was
moved, not withdrawn, the maintainer's choice of 2026-11-04); for a link, the rows that name both its ends and the rows the dependants walk from either end
lands only through it. ``apply(store, landed)`` marks the live statements on those keys stale
(``invalidated_by``: the reason) and the derived outputs that used them suspect, through the store
port; the gate then reports them as it reports a source change (S6). A register update with no state
change lands nothing and writes nothing. Standard library only; nothing here names a subject.
"""
from __future__ import annotations

import copy
import re
from pathlib import Path

import register_impact as ri

WITHDRAWN = ("deprecated", "retired")
WALK = "dependants"   # decision 0016 point 3: the walk named; with the descent by parent for a node
LIVE = ("proposed", "validated", "verified", "approved", "disputed")   # what a register change can invalidate
_STATE_NOTE = re.compile(r'^\s*state\s*=\s*"(?:deprecated|retired)"\s*#[^\n]*?\bdecision\s+(\d{4})', re.M)


def _decision(root: Path, number: str) -> str | None:
    hits = sorted((root / "decisions").glob(f"{number}-*.md"))
    return f"decisions/{hits[0].name}" if hits else None


def _decisions(root: Path) -> set[str]:
    d = root / "decisions"
    return {f"decisions/{p.name}" for p in d.glob("*.md")} if d.is_dir() else set()


def _link_block(text: str, lid: str) -> str:
    """The ``[[link]]`` block of one link in a relationship file's text."""
    for block in re.split(r"^\[\[link\]\]\s*$", text, flags=re.M)[1:]:
        if re.search(rf'^\s*id\s*=\s*"{re.escape(lid)}"', block, re.M):
            return block
    return ""


def _record(item: dict) -> str | None:
    a = item.get("approval")
    return a.get("record") if isinstance(a, dict) else None


def _reason(root: Path, text: str, before: dict, after: dict, added: list[str], tag: str) -> str:
    """The register's decision record for one change: the decision its state line's note names (the
    register's own practice: ``state = "deprecated"   # decision 0006: ...``), else its approval
    record when the change moved it, else the decisions the update added, else the register's tag."""
    m = _STATE_NOTE.search(text)
    rec = _decision(root, m.group(1)) if m else None
    if rec is None and after and _record(after) and _record(after) != _record(before):
        rec = _record(after)
    if rec is None and added:
        rec = ", ".join(added)
    where = f"the register at {tag}" if tag else "the register"
    return f"{where}: {rec}" if rec else where


def diff(previous: Path, current: Path) -> dict:
    """What the update from ``previous`` to ``current`` withdrew: {from, to, nodes, links}, each item
    with its id, its state before and after (None when gone) and its reason."""
    previous, current = Path(previous).resolve(), Path(current).resolve()
    T = ri.load_tools(previous)
    before = T["register"].load_register(previous)
    after = ri.load_tools(current)["register"].load_register(current)
    tag = ri.source(current)["tag"] or ri.source(current)["commit"][:7]
    added = sorted(_decisions(current) - _decisions(previous))
    nodes = []
    for nid, n in sorted(before["nodes"].items()):
        if n.get("state") in WITHDRAWN:
            continue
        m = after["nodes"].get(nid)
        state = m.get("state") if m else None
        if m is not None and state not in WITHDRAWN:
            continue
        text = Path(m["_path"]).read_text(encoding="utf-8") if m else ""
        nodes.append({"id": nid, "from": n.get("state"), "to": state, "reason": _reason(current, text, n, m or {}, added, tag)})
    links = []
    for rel, spec in sorted(before["relationships"].items()):
        now = {ln.get("id"): ln for ln in after["relationships"].get(rel, {}).get("links", [])}
        for ln in spec.get("links", []):
            if ln.get("state") != "approved":
                continue
            m = now.get(ln.get("id"))
            if m is not None and m.get("state") == "approved":
                continue
            path = after["relationships"].get(rel, {}).get("_path")
            text = _link_block(Path(path).read_text(encoding="utf-8"), ln["id"]) if m and path else ""
            links.append({"id": ln.get("id"), "rel": rel, "source": ln.get("source"), "target": ln.get("target"),
                          "from": "approved", "to": m.get("state") if m else None,
                          "reason": _reason(current, text, ln, m or {}, added, tag)})
    return {"from": ri.source(previous), "to": ri.source(current), "nodes": nodes, "links": links}


def _lost(T, reg: dict, start: str, link: dict) -> list[str]:
    """What the dependants walk from ``start`` reached only through ``link``: its reach on ``reg``
    less its reach with the link withdrawn (decision 0016: never the start)."""
    rows = T["impact"].WALKS.get(WALK) if hasattr(T["impact"], "WALKS") else None
    walk = lambda r: T["impact"].reached(T["impact"].walk(r, start) if rows is None else T["impact"].walk(r, start, rows))  # noqa: E731
    without = copy.copy(reg)
    without["relationships"] = {k: dict(v, links=[dict(x, state="withdrawn") if x.get("id") == link["id"] else x for x in v.get("links", [])])
                                for k, v in reg["relationships"].items()}
    return sorted(walk(reg) - walk(without))


def descent(T, reg: dict, now: dict, node: str) -> dict:
    """The dependants walk from a withdrawn ``node`` with the descent by ``parent`` (decision 0014) on
    the previous register ``reg``, less what the update moved (the maintainer, 2026-11-04): a
    descendant the new register ``now`` no longer places below ``node``, in any state, is skipped with
    its subtree, since it was moved, not withdrawn; one still below it is descended as
    ``impact.walk_children`` does (approved: walked; any other: not followed, not walked from; task-0305: never
    called withdrawn, which is the change's own deprecated or retired). The start
    and every descendant are never counted reached (decision 0016)."""
    imp = T["impact"]
    rows = getattr(imp, "WALKS", {}).get(WALK)
    walk = (lambda start: imp.walk(reg, start)) if rows is None else (lambda start: imp.walk(reg, start, rows))  # noqa: E731
    desc = imp.descendants(reg, node)
    still = set(imp.descendants(now, node))
    moved = [x for x in desc if x not in still]
    below_moved = {y for x in moved for y in imp.descendants(reg, x)}
    kept = [x for x in desc if x in still and x not in below_moved]
    walked = [x for x in kept if reg["nodes"][x].get("state") == "approved"]
    edges = [e for start in [node, *walked] for e in walk(start)]
    return {"moved": sorted(set(moved) | below_moved), "walked": walked,
            "not_followed": [x for x in kept if x not in walked],
            "reached": sorted(imp.reached(edges) - {node, *desc})}


def resting(change: dict, register_map: dict, previous: Path, current: Path) -> list[dict]:
    """The subject's keys resting on what the change withdrew: one entry per key, with its owner, the
    causes (the node or link, how it landed, the nodes it came through) and the reasons. ``current``
    is the register after the update: a descendant it moved away from a withdrawn node is skipped
    (``descent``)."""
    previous = Path(previous).resolve()
    by_key: dict[str, dict] = {}
    import capture
    try:   # the one owner rule (task-0201, doc-0030 G8): routing, over the register after the update
        route = capture.routing(register_map, capture.register_nodes(Path(current).resolve()))
    except (OSError, ValueError):
        route = {}

    def land(row: dict, cause: dict) -> None:
        k = by_key.setdefault(row["key"], {"key": row["key"], "owner": (route.get(row["key"]) or {}).get("unit"), "causes": []})
        k["causes"].append({**cause, "via": row["via"]})

    T = ri.load_tools(previous)
    reg = T["register"].load_register(previous)
    now = ri.load_tools(Path(current).resolve())["register"].load_register(Path(current).resolve()) if change["nodes"] else None
    for n in change["nodes"]:
        d = descent(T, reg, now, n["id"])
        for row in ri.landed_rows(register_map, n["id"], d["reached"], d["walked"], d["not_followed"]):
            land(row, {"node": n["id"], "walk": WALK, "children": True, "reason": n["reason"], "moved": d["moved"],
                       **({"not_followed": True} if row.get("not_followed") else {})})
    if change["links"]:
        for ln in change["links"]:
            ends = [ln["source"], ln["target"]]
            for row in register_map.get("row", []):
                if all(e in (row.get("nodes") or []) for e in ends):
                    land({**row, "via": ends}, {"link": ln["id"], "walk": None, "reason": ln["reason"]})
            for start in ends:
                lost = _lost(T, reg, start, ln)
                for row in ri.landed_rows(register_map, "", lost):
                    land(row, {"link": ln["id"], "walk": WALK, "from": start, "reason": ln["reason"]})
    out = []
    for k in sorted(by_key.values(), key=lambda k: k["key"]):
        k["reasons"] = sorted({c["reason"] for c in k["causes"]})
        out.append(k)
    return out


def block(change: dict, landed: list[dict]) -> dict:
    """The register change as the gate reports it and the page shows it (task-0178): the two registers,
    what the update withdrew and the keys resting on it, each with its owner, reasons and causes. The
    gate adds what it wrote (``invalidated``, ``derived``); the page writes nothing."""
    return {"from": change["from"], "to": change["to"], "nodes": change["nodes"], "links": change["links"],
            "keys": [{"key": k["key"], "owner": k["owner"], "reasons": k["reasons"],
                      "causes": sorted({c.get("node") or c.get("link") for c in k["causes"]})} for k in landed]}


def apply(store, landed: list[dict], at: str | None = None) -> dict:
    """Mark the live statements on the landed keys stale and what used them suspect, through the port;
    ``at``, the change's instant, is their ``invalidated_at`` (doc-0030 S8)."""
    if not landed:
        return {"invalidated": []}
    return store.invalidate_keys({k["key"]: "; ".join(k["reasons"]) for k in landed}, at)
