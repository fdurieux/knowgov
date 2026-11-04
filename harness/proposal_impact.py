"""A proposed addition read against the register as if approved, without approving it (task-0130,
doc-0017 candidate 1), with its deterministic link candidates D1 to D5 (task-0131, candidate 3).

    python harness/proposal_impact.py PROPOSAL.json [--children] [--task NAME] [--as-of DATE]
                                      [--scenario ID] [--no-store] [-f text|json] [-o FILE]

A proposal is an overlay on the register ``KG_REGISTER`` names (``cadence.register_root``, at its tag):
register-shaped ``nodes`` (a provisional id, kind, name, parent, owner, an optional ``source``),
``links`` (type, source, target, rationale, an optional owner), the ``reused`` register nodes, each
``as_is`` or ``changed``, and optional proposed ``exceptions`` (rule, scope, expires, rationale). A
JSON or TOML file on the command line; the same object as the MCP tool's ``proposal``.

Only the register's own functions decide, loaded by path from the register as ``register_impact``
loads them (``tools/register.py``, ``tools/impact.py``, ``tools/check_register.py``): there is no
second walk semantics here.

- Placement: ``check_nodes``, ``check_relationships`` and ``check_glossary`` on the register plus the
  overlay held as the proposal it is (state ``proposed``, so the approval a register pull request
  adds is not asked); only the findings on overlay elements are reported. A node with no ``source``
  is "in no tool yet" (info). A forbidden synonym in a name is D5.
- Read: the overlay's nodes, links and exceptions as ``approved``; the register's own draft and
  proposed elements keep their states. ``check_coverage`` before and after, with denominators;
  ``impact.walk`` (or ``walk_children`` with ``children``) from every reused node before and after,
  the ``changed`` ones flagged; what each new node rests on, through ``requires`` targets and the
  ``realisers`` walk (decision 0012).
- Keys: per reused node, the register-map rows ``register_impact`` lands on the base register for that
  node, and with a scenario held each key's level, stale statements, suspect derived outputs and
  findings, as the MCP tool ``register_impact`` reports them for the same node, task class and as_of.
  A new node has no row in any map and no statement: it is listed ``unmapped``, never ``unknown``.
- Candidates, in order: D1 a register id the input names (``authored``); D2 an external id
  (``aris_guid``, ``archi_id``, ``edm_id``, the systems' ``id_field``) matched through a register
  node's ``[source]``, or through the newest landed export's MANIFEST ``[guids]`` (``authored``); D3 an
  exact normalised name match with an approved node of the same kind, its live links offered to the
  new node (``inferred``; decision-0007: "same step as JRN-..."); D4 for a step or touchpoint with no
  support and no D3 support, the realisers of its product's required capabilities as a pool, listed
  and never chosen (``inferred``). Every candidate's status is ``proposed``: a candidate never closes
  a gap; only a link the proposal states counts.

Every overlay element and edge is ``hypothetical``. The report names the register's tag and commit
and the overlay's digest, and is never stored: nothing is written to the register, the store or a
file, save ``-o``'s report. Provisional ids that are well formed for their kind and free are used as
they are; any other is given the next free id of its prefix in memory, and the report names the
provisional one throughout. knowgov never mints an id: a register pull request does.

Exit 0 a report, 2 the proposal cannot be read (malformed, a kind the metamodel lacks, an id that
names an existing node, a link end that names nothing). Standard library only.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import importlib.util
import json
import re
import sys
import threading
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import register_impact as ri  # noqa: E402

SCHEMA_VERSION = 1
TOOL = "knowgov proposal_impact"
MODES = ("as_is", "changed")
STEP_KINDS = ("step", "touchpoint")
NODE_FIELDS = {"id", "kind", "name", "parent", "owner", "source"}
LINK_FIELDS = {"id", "type", "source", "target", "rationale", "owner"}
EXC_FIELDS = {"id", "rule", "scope", "expires", "rationale"}
LIMITS = [
    "decision-0007: journey reuse shows through shared processes and the name match (D3) only; a change to "
    "the base journey that is not a process change does not reach the derived one",
    "a new node has no row in any register map and no statement: its keys are unmapped until a subject declares them",
    "candidates are deterministic; their precision is not yet measured on a real register (doc-0017 candidate 4 parked)",
]

_checks: dict[str, object] = {}
_lock = threading.Lock()


class ProposalError(ValueError):
    """The proposal cannot be read: the report is refused, never half made."""


def check_module(root: Path):
    """The register's ``tools/check_register.py``, imported by path once per root, after
    ``register_impact.load_tools`` has put that root's ``register`` in ``sys.modules``."""
    root = root.resolve()
    ri.load_tools(root)
    with _lock:
        if str(root) not in _checks:
            spec = importlib.util.spec_from_file_location(f"check_register_{len(_checks)}", root / "tools" / "check_register.py")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            _checks[str(root)] = mod
        return _checks[str(root)]


def digest(proposal: dict) -> str:
    return hashlib.sha256(json.dumps(proposal, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                                     default=str).encode("utf-8")).hexdigest()


def normalise(name: str) -> str:
    """D3's comparison: case folded, runs of white space one space, outer space and full stops dropped."""
    return re.sub(r"\s+", " ", str(name).casefold()).strip(" .")


def _date(v, what: str) -> dt.date:
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    try:
        return dt.date.fromisoformat(str(v))
    except ValueError as e:
        raise ProposalError(f"{what}: {v!r} is not a date (YYYY-MM-DD)") from e


def _str(v, what: str) -> str:
    if not isinstance(v, str) or not v.strip() or len(v) > 200:
        raise ProposalError(f"{what}: a non-empty string")
    return v


# ---- the overlay, read into the register's own dict shape ----

class Overlay:
    """The proposal checked and given in-memory ids; ``out`` maps an in-memory id back to the
    provisional one the report names."""

    def __init__(self, proposal: dict, reg: dict, T: dict):
        if not isinstance(proposal, dict):
            raise ProposalError("the proposal is an object with nodes, links, reused and exceptions")
        extra = set(proposal) - {"nodes", "links", "reused", "exceptions", "title"}
        if extra:
            raise ProposalError(f"the proposal has no field(s) {sorted(extra)}")
        k2t = T["register"].kind_taxonomy(reg)
        prefixes = {tax: spec["prefix"] for tax, spec in reg["types"]["taxonomy"].items()}
        nodes, links = proposal.get("nodes") or [], proposal.get("links") or []
        reused, excs = proposal.get("reused") or [], proposal.get("exceptions") or []
        for what, xs in (("nodes", nodes), ("links", links), ("reused", reused), ("exceptions", excs)):
            if not isinstance(xs, list) or not all(isinstance(x, dict) for x in xs):
                raise ProposalError(f"{what}: a list of objects")
        if not nodes and not links:
            raise ProposalError("the proposal adds no node and no link")
        self.ids: dict[str, str] = {}   # provisional -> in memory
        used = set(reg["nodes"])
        taken: dict[str, set[int]] = {}
        for nid in used:
            p, _, num = nid.partition("-")
            if num.isdigit():
                taken.setdefault(p, set()).add(int(num))
        self.nodes: list[dict] = []
        for i, n in enumerate(nodes):
            bad = set(n) - NODE_FIELDS
            if bad:
                raise ProposalError(f"nodes[{i}]: no field(s) {sorted(bad)}; a node is {sorted(NODE_FIELDS)}")
            pid = _str(n.get("id"), f"nodes[{i}].id")
            if pid in reg["nodes"]:
                raise ProposalError(f"nodes[{i}]: {pid} names an existing register node; list it under reused instead")
            if pid in self.ids:
                raise ProposalError(f"nodes[{i}]: {pid} is named twice")
            _str(n.get("name"), f"nodes[{i}].name")
            for f in ("parent", "owner"):
                if n.get(f) is not None and not isinstance(n[f], str):
                    raise ProposalError(f"nodes[{i}].{f}: a string, a register id or a proposed node's")
            if n.get("source") is not None and not isinstance(n["source"], dict):
                raise ProposalError(f"nodes[{i}].source: a table, as a register node's [source]")
            kind = n.get("kind")
            if kind not in k2t:
                raise ProposalError(f"nodes[{i}] {pid}: kind {kind!r} is not one of the metamodel's {sorted(k2t)}")
            tax = k2t[kind]
            prefix = prefixes[tax]
            if re.fullmatch(rf"{prefix}-\d{{4,}}", pid) and pid not in used:
                mem = pid
            else:
                nxt = max(taken.get(prefix, {0}) | {0}) + 1
                mem = f"{prefix}-{nxt:04d}"
            taken.setdefault(prefix, set()).add(int(mem.split("-")[1]))
            used.add(mem)
            self.ids[pid] = mem
            self.nodes.append({**{k: v for k, v in n.items() if k != "id"}, "id": mem, "_taxonomy": tax,
                               "_path": Path(tax) / f"{mem}.toml", "_provisional": pid})
        for n in self.nodes:   # a parent may be a register node or another overlay node
            if n.get("parent") is not None:
                n["parent"] = self.ids.get(n["parent"], n["parent"])
        self.out = {v: k for k, v in self.ids.items()}
        rel_types = set(reg["relationships"])
        nums = [int(ln["id"].split("-")[1]) for r in reg["relationships"].values() for ln in r["links"]
                if re.fullmatch(r"REL-\d+", str(ln.get("id", "")))]
        nxt = max(nums or [0]) + 1
        self.links: list[dict] = []
        seen_links = set()
        for i, ln in enumerate(links):
            bad = set(ln) - LINK_FIELDS
            if bad:
                raise ProposalError(f"links[{i}]: no field(s) {sorted(bad)}; a link is {sorted(LINK_FIELDS)}")
            typ = ln.get("type")
            if typ not in rel_types:
                raise ProposalError(f"links[{i}]: type {typ!r} is not one of the register's {sorted(rel_types)}")
            ends = []
            for end in ("source", "target"):
                x = _str(ln.get(end), f"links[{i}].{end}")
                x = self.ids.get(x, x)
                if x not in reg["nodes"] and x not in self.out:
                    raise ProposalError(f"links[{i}]: {end} {ln.get(end)!r} names neither a register node nor a proposed one")
                ends.append(x)
            pid = ln.get("id") or f"link-{i + 1}"
            if pid in seen_links:
                raise ProposalError(f"links[{i}]: id {pid} is named twice")
            seen_links.add(pid)
            src = self.node(ends[0], reg)
            mem = f"REL-{nxt:05d}"
            nxt += 1
            self.links.append({"id": mem, "source": ends[0], "target": ends[1], "rationale": ln.get("rationale", ""),
                               "owner": ln.get("owner") or (src or {}).get("owner"), "_type": typ, "_provisional": pid})
            self.out[mem] = pid
        self.reused: list[dict] = []
        named = set()
        for i, r in enumerate(reused):
            rid = r.get("id")
            if rid not in reg["nodes"]:
                raise ProposalError(f"reused[{i}]: {rid!r} is not a register node")
            mode = r.get("mode", "as_is")
            if mode not in MODES:
                raise ProposalError(f"reused[{i}] {rid}: mode is one of {list(MODES)}")
            if set(r) - {"id", "mode"}:
                raise ProposalError(f"reused[{i}]: a reused node is id and mode")
            if rid not in named:
                named.add(rid)
                self.reused.append({"id": rid, "mode": mode, "declared": True})
        for ln in self.links:   # a register node a stated link names is reused, as it is, unless declared
            for x in (ln["source"], ln["target"]):
                if x in reg["nodes"] and x not in named:
                    named.add(x)
                    self.reused.append({"id": x, "mode": "as_is", "declared": False})
        self.exceptions: list[dict] = []
        for i, e in enumerate(excs):
            bad = set(e) - EXC_FIELDS
            if bad:
                raise ProposalError(f"exceptions[{i}]: no field(s) {sorted(bad)}")
            scope = e.get("scope")
            if not isinstance(scope, list) or not scope:
                raise ProposalError(f"exceptions[{i}]: scope is a non-empty list of ids")
            pid = e.get("id") or f"exception-{i + 1}"
            self.exceptions.append({"id": pid, "rule": e.get("rule"), "scope": [self.ids.get(s, s) for s in scope],
                                    "expires": _date(e.get("expires"), f"exceptions[{i}].expires"),
                                    "rationale": e.get("rationale", ""), "_path": Path("exceptions") / f"{pid}.toml",
                                    "_provisional": pid})

    def node(self, nid: str, reg: dict) -> dict | None:
        return next((n for n in self.nodes if n["id"] == nid), None) or reg["nodes"].get(nid)

    def name(self, x):
        """An in-memory id as the report names it."""
        return self.out.get(x, x)

    def is_new(self, x) -> bool:
        return x in self.out

    def merged(self, reg: dict, state: str, today: dt.date) -> dict:
        """A copy of the register with the overlay added in ``state``; the register itself is untouched."""
        m = copy.deepcopy(reg)
        for n in self.nodes:
            m["nodes"][n["id"]] = {**copy.deepcopy(n), "state": state}
        for ln in self.links:
            m["relationships"][ln["_type"]]["links"].append(
                {k: v for k, v in ln.items() if not k.startswith("_")} | {"state": state})
        if state == "approved":
            for e in self.exceptions:
                m["exceptions"].append({**e, "approved": {"by": "(proposed)", "on": today, "record": "(proposed)"}})
        return m


# ---- the report ----

def _wheres(ov: Overlay) -> dict[str, str]:
    """Each overlay element's ``where`` as the register's checks write it -> its provisional id."""
    out = {f"{n['_taxonomy']}/{n['id']}.toml": n["_provisional"] for n in ov.nodes}
    out.update({f"[{ln['id']}]": ln["_provisional"] for ln in ov.links})
    return out


def placement(ov: Overlay, reg: dict, CR, today: dt.date) -> list[dict]:
    m = ov.merged(reg, "proposed", today)
    f = CR.Findings()
    CR.check_nodes(m, f, today)
    CR.check_relationships(m, f, today)
    CR.check_glossary(m, f)
    wheres = _wheres(ov)
    out = []
    for it in f.items:
        hit = next((p for w, p in wheres.items() if w in it["where"]), None)
        if hit is None:
            continue
        where, msg = it["where"], it["message"]
        for mem, pid in sorted(ov.out.items(), key=lambda kv: -len(kv[0])):
            where, msg = where.replace(mem, pid), msg.replace(mem, pid)
        out.append({"level": it["level"], "check": it["check"], "element": hit, "where": where, "message": msg,
                    "rule": "D5" if it["check"] == "glossary" else None})
    for n in ov.nodes:
        if not n.get("source"):
            out.append({"level": "info", "check": "source", "element": n["_provisional"],
                        "where": f"{n['_taxonomy']}/{n['_provisional']}", "message": "in no tool yet: no [source] names a system of record",
                        "rule": None})
    return out


def _cov(CR, reg: dict, ov: Overlay, today: dt.date) -> dict:
    f = CR.Findings()
    s = CR.check_coverage(reg, f, today)
    return {r: {"denominator": s[r]["denominator"], "covered": s[r]["covered"], "excepted": s[r]["excepted"],
                "uncovered": [{"id": ov.name(x), "hypothetical": ov.is_new(x)} for x in s[r]["uncovered"]]}
            for r in ("C1", "C2", "C3")}


def coverage(CR, base: dict, read: dict, ov: Overlay, today: dt.date) -> dict:
    before, after = _cov(CR, base, ov, today), _cov(CR, read, ov, today)
    gaps = []
    for r in ("C1", "C2", "C3"):
        had = {x["id"] for x in before[r]["uncovered"]}
        gaps += [{"rule": r, **x} for x in after[r]["uncovered"] if x["id"] not in had]
    return {"before": before, "after": after, "new_gaps": gaps}


def _walk(T, reg: dict, start: str, rows, children: bool) -> tuple[list[dict], set[str]]:
    if children:
        got = T["impact"].walk_children(reg, start, rows)
        return got["edges"], set(got["reached"])
    edges = T["impact"].walk(reg, start, rows)
    return edges, T["impact"].reached(edges)


def reach(T, base: dict, read: dict, ov: Overlay, children: bool) -> list[dict]:
    rows = T["impact"].WALKS["dependants"]
    link_of = {(ln["source"], ln["_type"], ln["target"]) for ln in ov.links}
    out = []
    for r in ov.reused:
        e0, r0 = _walk(T, base, r["id"], rows, children)
        e1, r1 = _walk(T, read, r["id"], rows, children)
        before_keys = {(e["from"], e["rel"], e["to"]) for e in e0}
        new_edges = []
        for e in e1:
            if (e["from"], e["rel"], e["to"]) in before_keys:
                continue
            rel = e["rel"].replace(" (inverse)", "")
            pair = (e["from"], rel, e["to"]) if not e["rel"].endswith("(inverse)") else (e["to"], rel, e["from"])
            new_edges.append({"from": ov.name(e["from"]), "rel": e["rel"], "to": ov.name(e["to"]), "live": e["live"],
                              "hypothetical": pair in link_of or ov.is_new(e["from"]) or ov.is_new(e["to"])})
        n = base["nodes"][r["id"]]
        out.append({"node": r["id"], "name": n.get("name", ""), "kind": n.get("kind"), "state": n.get("state"),
                    "owner": n.get("owner"), "mode": r["mode"], "declared": r["declared"], "changed": r["mode"] == "changed",
                    "before": sorted(r0), "after": sorted(ov.name(x) for x in r1),
                    "added": [{"id": ov.name(x), "hypothetical": ov.is_new(x)} for x in sorted(r1 - r0)],
                    "removed": sorted(r0 - r1), "new_edges": new_edges})
    return out


def _targets(reg: dict, rel: str, source: str) -> list[str]:
    return sorted({ln["target"] for ln in reg["relationships"].get(rel, {}).get("links", [])
                   if ln.get("source") == source and ln.get("state") == "approved" and ln.get("target")})


def _realisers(T, reg: dict, cap: str) -> list[str]:
    edges = T["impact"].walk(reg, cap, T["impact"].WALKS["realisers"])
    return sorted(T["impact"].reached(edges))


def rests_on(T, read: dict, ov: Overlay) -> list[dict]:
    """What each new node rests on: a product its required capabilities and their realisers; a
    capability its realisers; a step or touchpoint the processes that support it."""
    out = []
    for n in ov.nodes:
        kind, nid = n["kind"], n["id"]
        if n["_taxonomy"] == "products":
            caps = _targets(read, "requires", nid)
            via = [{"node": ov.name(c), "hypothetical": ov.is_new(c), "realisers": [ov.name(x) for x in _realisers(T, read, c)]} for c in caps]
            out.append({"node": n["_provisional"], "kind": kind, "through": "requires, then realisers", "via": via,
                        "gap": not caps or any(not v["realisers"] for v in via)})
        elif n["_taxonomy"] == "capabilities":
            rs = [ov.name(x) for x in _realisers(T, read, nid)]
            out.append({"node": n["_provisional"], "kind": kind, "through": "realisers",
                        "via": [{"node": n["_provisional"], "hypothetical": True, "realisers": rs}], "gap": not rs})
        elif kind in STEP_KINDS:
            ps = _targets(read, "is_supported_by", nid)
            out.append({"node": n["_provisional"], "kind": kind, "through": "is_supported_by",
                        "via": [{"node": ov.name(p), "hypothetical": ov.is_new(p), "realisers": []} for p in ps], "gap": not ps})
    return out


# ---- candidates D1 to D4 (D5 is a placement finding) ----

def _id_fields(reg: dict) -> dict[str, str]:
    return {name: spec["id_field"] for name, spec in reg["sources"].get("system", {}).items()}


def _newest_guids(root: Path, system: str) -> tuple[str, dict]:
    """The newest landed export of ``system`` under the register (``exports/<system>/<date>/``) and its
    MANIFEST's ``[guids]`` (GUID -> register id), as the connector writes it (task-0063)."""
    d = root / "exports" / system
    folders = sorted(p for p in d.iterdir() if p.is_dir() and (p / "MANIFEST.toml").is_file()) if d.is_dir() else []
    if not folders:
        return "", {}
    man = tomllib.loads((folders[-1] / "MANIFEST.toml").read_text(encoding="utf-8"))
    return f"exports/{system}/{folders[-1].name}", man.get("guids") or {}


def candidates(T, root: Path, base: dict, read: dict, ov: Overlay) -> list[dict]:
    out = []
    stated = {(ln["_type"], ln["source"], ln["target"]) for ln in ov.links}

    def link(typ, s, t):
        return {"type": typ, "source": ov.name(s), "target": ov.name(t)}

    # D1: a register id the input names, on a stated link or in reused
    on_links = set()
    for ln in ov.links:
        for x in (ln["source"], ln["target"]):
            if x in base["nodes"]:
                on_links.add(x)
                out.append({"rule": "D1", "basis": "authored", "kind": "link", "element": ov.name(ln["source"] if x != ln["source"] else ln["target"]),
                            "link": link(ln["_type"], ln["source"], ln["target"]), "same_as": None, "pool": None, "stated": True,
                            "status": "proposed", "reason": f"the proposal names {x} on its link {ln['_provisional']}"})
    for r in ov.reused:
        if r["declared"] and r["id"] not in on_links:
            out.append({"rule": "D1", "basis": "authored", "kind": "reuse", "element": r["id"], "link": None, "same_as": r["id"],
                        "pool": None, "stated": True, "status": "proposed", "reason": f"the proposal reuses {r['id']} {r['mode']}"})
    # D2: an external id matched through a register node's [source], else the newest landed export
    fields = _id_fields(base)
    for n in ov.nodes:
        src = n.get("source") or {}
        if not isinstance(src, dict):
            continue
        for system, field in sorted(fields.items()):
            val = src.get(field)
            if not isinstance(val, str) or not val or field == "kit_path":
                continue
            hit = sorted(nid for nid, x in base["nodes"].items() if (x.get("source") or {}).get(field) == val)
            where = "a register node's [source]"
            if not hit:
                folder, guids = _newest_guids(root, system)
                if val in guids and guids[val] in base["nodes"]:
                    hit, where = [guids[val]], f"{folder}/MANIFEST.toml [guids]"
            for h in hit:
                out.append({"rule": "D2", "basis": "authored", "kind": "same_as", "element": n["_provisional"], "link": None,
                            "same_as": h, "pool": None, "stated": False, "status": "proposed",
                            "reason": f"{field} {val} is {h}'s, through {where}: the proposed node may be {h} itself"})
    # D3: an exact normalised name match with an approved node of the same kind; its live links offered
    d3_support = set()
    for n in ov.nodes:
        key = normalise(n.get("name", ""))
        for nid, x in sorted(base["nodes"].items()):
            if x.get("kind") != n["kind"] or x.get("state") != "approved" or normalise(x.get("name", "")) != key:
                continue
            what = "step" if n["kind"] in STEP_KINDS else n["kind"].replace("_", " ")
            out.append({"rule": "D3", "basis": "inferred", "kind": "same_as", "element": n["_provisional"], "link": None,
                        "same_as": nid, "pool": None, "stated": False, "status": "proposed",
                        "reason": f"same {what} as {nid}: {x.get('name')!r}"})
            for typ, rel in sorted(base["relationships"].items()):
                for ln in rel["links"]:
                    if ln.get("state") != "approved" or nid not in (ln.get("source"), ln.get("target")):
                        continue
                    far = ln["target"] if ln["source"] == nid else ln["source"]
                    if far is None or (base["nodes"].get(far) or {}).get("state") in ("deprecated", "retired"):
                        continue
                    s, t = (n["id"], far) if ln["source"] == nid else (far, n["id"])
                    if typ == "is_supported_by" and s == n["id"]:
                        d3_support.add(n["id"])
                    out.append({"rule": "D3", "basis": "inferred", "kind": "link", "element": n["_provisional"],
                                "link": link(typ, s, t), "same_as": nid, "pool": None, "stated": (typ, s, t) in stated,
                                "status": "proposed", "reason": f"{nid}'s approved link {ln['id']} ({typ}), offered to the step that matches it"
                                if n["kind"] in STEP_KINDS else f"{nid}'s approved link {ln['id']} ({typ}), offered to the node that matches it"})
    # D4: a step or touchpoint with no support, stated or D3's: the realisers of its product's capabilities
    for n in ov.nodes:
        if n["kind"] not in STEP_KINDS or n["id"] in d3_support or _targets(read, "is_supported_by", n["id"]):
            continue
        chain, cur = [], n["id"]
        while cur is not None and cur not in chain:
            chain.append(cur)
            cur = (read["nodes"].get(cur) or {}).get("parent")
        prods = sorted({p for j in chain for p in _targets(read, "concerns", j)})
        caps = sorted({c for p in prods for c in _targets(read, "requires", p)})
        pool = sorted({x for c in caps for x in _realisers(T, read, c) if x.startswith("PROC-")})
        out.append({"rule": "D4", "basis": "inferred", "kind": "pool", "element": n["_provisional"], "link": None,
                    "same_as": None, "pool": [ov.name(x) for x in pool], "stated": False, "status": "proposed",
                    "reason": (f"no support stated or matched: the processes realising {', '.join(ov.name(c) for c in caps)}, the "
                               f"capabilities {', '.join(ov.name(p) for p in prods)} requires, listed and none chosen")
                    if caps else "no support stated or matched, and no product it concerns requires a capability: no pool"})
    return out


# ---- keys and approvals ----

def landed_keys(register_map: dict, node: str, root: Path, children: bool) -> list[dict]:
    """The rows ``register_impact`` lands for ``node`` on the base register, as the MCP tool computes them."""
    w = ri.walk(node, "dependants", root, children=children)
    reached = [x["id"] for xs in w["reached"].values() for x in xs]
    walked = [c["id"] for c in w["children"] if c["walked"]]
    withdrawn = [c["id"] for c in w["children"] if c.get("withdrawn")]
    return ri.landed_rows(register_map, node, reached, walked, withdrawn)


def approvals(base: dict, ov: Overlay) -> list[dict]:
    """Who must approve what: a new node's owner; a stated link's owner and the owners of both its ends
    (the register's README asks both on a cross-domain link); a changed reused node's owner; the owners
    of an exception's scope."""
    units: dict[str, list[dict]] = {}

    def add(unit, what, ref, why):
        if unit:
            xs = units.setdefault(unit, [])
            if not any(x["what"] == what and x["id"] == ref for x in xs):
                xs.append({"what": what, "id": ref, "why": why, "hypothetical": what != "change"})
    for n in ov.nodes:
        add(n.get("owner"), "node", n["_provisional"], "owns the proposed node")
    for ln in ov.links:
        ends = [(ov.node(x, base) or {}).get("owner") for x in (ln["source"], ln["target"])]
        add(ln.get("owner"), "link", ln["_provisional"], "owns the proposed link")
        cross = len({e for e in ends if e}) > 1
        for e in ends:
            add(e, "link", ln["_provisional"], "owns an end of a cross-domain link" if cross else "owns an end of the link")
    for r in ov.reused:
        if r["mode"] == "changed":
            add(base["nodes"][r["id"]].get("owner"), "change", r["id"], "owns a reused node the proposal changes")
    for e in ov.exceptions:
        for s in e["scope"]:
            add((ov.node(s, base) or {}).get("owner"), "exception", e["_provisional"], f"owns {ov.name(s)}, in the exception's scope")
    return [{"unit": u, "name": (base["nodes"].get(u) or {}).get("name", ""), "approve": xs} for u, xs in sorted(units.items())]


def evaluate(proposal: dict, root: Path | None = None, today: dt.date | None = None, children: bool = False,
             register_map: dict | None = None) -> dict:
    """The report, without the store: everything but the keys' levels (``with_levels`` adds those).
    ``today`` is the date exceptions and reviews are read on (the as_of)."""
    if not isinstance(children, bool):
        raise ProposalError("children must be true or false")
    root = (root or ri.register_root()).resolve()
    if today is None:
        import cadence
        today = cadence.as_of("today")
    T = ri.load_tools(root)
    CR = check_module(root)
    base = T["register"].load_register(root)
    ov = Overlay(proposal, base, T)
    read = ov.merged(base, "approved", today)
    if register_map is None:
        from subject import SUBJECT
        register_map = SUBJECT.register_map()
    mapped = {x for row in register_map.get("row", []) for x in row.get("nodes") or []}
    keys = [{"node": r["id"], "mode": r["mode"], "keys": landed_keys(register_map, r["id"], root, children)} for r in ov.reused]
    return {
        "schema_version": SCHEMA_VERSION, "tool": TOOL,
        "register": ri.source(root),
        "overlay": {"digest": digest(proposal), "title": proposal.get("title", ""), "nodes": len(ov.nodes), "links": len(ov.links),
                    "reused": len(ov.reused), "exceptions": len(ov.exceptions)},
        "as_of": today.isoformat(), "children_walked": children, "stored": False,
        "nodes": [{"id": n["_provisional"], "kind": n["kind"], "taxonomy": n["_taxonomy"], "name": n.get("name", ""),
                   "parent": ov.name(n["parent"]) if n.get("parent") else None, "owner": n.get("owner"),
                   "read_as": "approved", "hypothetical": True} for n in ov.nodes],
        "links": [{"id": ln["_provisional"], "type": ln["_type"], "source": ov.name(ln["source"]), "target": ov.name(ln["target"]),
                   "rationale": ln["rationale"], "owner": ln["owner"], "read_as": "approved", "hypothetical": True} for ln in ov.links],
        "exceptions": [{"id": e["_provisional"], "rule": e["rule"], "scope": [ov.name(s) for s in e["scope"]],
                        "expires": e["expires"].isoformat(), "read_as": "approved", "hypothetical": True} for e in ov.exceptions],
        "placement": placement(ov, base, CR, today),
        "candidates": candidates(T, root, base, read, ov),
        "coverage": coverage(CR, base, read, ov, today),
        "reach": reach(T, base, read, ov, children),
        "rests_on": rests_on(T, read, ov),
        "keys": {"task": None, "scenario": None, "store": None, "gate": None, "by_node": keys},
        "unmapped": [{"id": n["_provisional"], "why": "no register-map row names it and no subject has asked about it: unmapped, not unknown"}
                     for n in ov.nodes if n["id"] not in mapped],
        "approvals": approvals(base, ov),
        "limits": list(LIMITS),
    }


def with_levels(report: dict, st, *, task: str, as_of: str, scenario: str | None = None) -> dict:
    """Each reused node's keys with their levels, as the MCP tool ``register_impact`` reads them: one
    ``gate_cli.evaluate`` per node over its landed keys under ``task`` on ``as_of``. Reads only."""
    import gate_cli
    from subject import SUBJECT
    from tasks import TASKS
    acts = st.extraction_activities()
    held = acts[0].split(":")[2] if acts else None
    report["keys"]["store"] = st.name
    if held is None:
        return report
    if scenario and scenario != held:
        raise ProposalError(f"the store holds {held}, not {scenario!r}")
    report["keys"].update(task=task, scenario=held)
    verdicts = []
    for entry in report["keys"]["by_node"]:
        if not entry["keys"]:
            continue
        spec = dict(TASKS[task], keys=[k["key"] for k in entry["keys"]])
        rep = gate_cli.evaluate(st, subject=SUBJECT.id, scenario=held, task="keys", spec=spec, threshold="blocker",
                                baseline=None, loaded=False, version=gate_cli.held_version(st), as_of=as_of, route_task=task)
        entry["keys"] = ri.with_levels(entry["keys"], rep)
        entry["gate"] = {"task": task, "verdict": rep["verdict"], "why": rep["why"], "exit_code": rep["exit_code"]}
        verdicts.append(rep["verdict"])
    report["keys"]["gate"] = {"task": task, "verdicts": sorted(set(verdicts))}
    return report


# ---- the command ----

def read_proposal(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        raise ProposalError(f"{path}: {e}") from e
    try:
        return tomllib.loads(text) if path.suffix == ".toml" else json.loads(text)
    except (ValueError, tomllib.TOMLDecodeError) as e:
        raise ProposalError(f"{path}: {e}") from e


def render_text(r: dict) -> str:
    lines = [f"proposal {r['overlay']['title'] or r['overlay']['digest'][:12]} on the register {r['register']['tag'] or '?'} "
             f"({r['register']['commit'][:12]}), as of {r['as_of']}: read as if approved, every element hypothetical, nothing stored",
             f"  {r['overlay']['nodes']} node(s), {r['overlay']['links']} link(s), {r['overlay']['reused']} reused node(s)"]
    for c in ("C1", "C2", "C3"):
        b, a = r["coverage"]["before"][c], r["coverage"]["after"][c]
        lines.append(f"  {c}: {b['covered']}/{b['denominator']} -> {a['covered']}/{a['denominator']} covered; "
                     f"uncovered {[x['id'] for x in a['uncovered']] or 'none'}")
    for p in r["placement"]:
        lines.append(f"  placement {p['level']} {p['check']}{' ' + p['rule'] if p['rule'] else ''} {p['where']}: {p['message']}")
    for c in r["candidates"]:
        what = c["link"] and f"{c['link']['source']} {c['link']['type']} {c['link']['target']}" or (
            c["pool"] is not None and f"pool {c['pool'] or 'empty'}, none chosen") or f"same as {c['same_as']}"
        lines.append(f"  candidate {c['rule']} {c['basis']}{' stated' if c['stated'] else ''}: {c['element']}: {what}")
    for x in r["reach"]:
        lines.append(f"  reach from {x['node']}{' (changed)' if x['changed'] else ''}: +{[a['id'] for a in x['added']] or 'nothing'}")
    for x in r["rests_on"]:
        shown = [v["node"] + (" <- " + ",".join(v["realisers"] or ["nothing"]) if "realisers" in x["through"] else "") for v in x["via"]]
        lines.append(f"  {x['node']} rests on {shown or 'nothing'}"
                     f"{' (gap)' if x['gap'] else ''}")
    for k in r["keys"]["by_node"]:
        lines.append(f"  {k['node']}: {len(k['keys'])} key(s)" + (
            f", levels {sorted({x['level'] for x in k['keys'] if 'level' in x})}" if any('level' in x for x in k["keys"]) else ""))
    lines.append(f"  unmapped: {[u['id'] for u in r['unmapped']] or 'none'}")
    for a in r["approvals"]:
        lines.append(f"  {a['unit']} {a['name']} approves {', '.join(x['what'] + ' ' + x['id'] for x in a['approve'])}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="proposal_impact.py", description="A proposed addition read against the register as if "
                                 "approved, without approving it (task-0130). Nothing is written.")
    ap.add_argument("proposal", type=Path, help="the overlay, JSON or TOML")
    ap.add_argument("--children", action="store_true", help="walk every approved descendant by parent too (the register's decision 0014)")
    ap.add_argument("--task", default=None, help="the task class each reused node's keys are read under (default: codegen)")
    ap.add_argument("--scenario", default=None, help="the scenario the store must hold (default: whatever it holds)")
    ap.add_argument("--as-of", default=None, help="YYYY-MM-DD, record or today (default: KG_AS_OF, else today)")
    ap.add_argument("--no-store", action="store_true", help="do not open the store: the keys carry no level")
    ap.add_argument("-f", "--format", choices=("text", "json"), default="text")
    ap.add_argument("-o", "--output", type=Path, default=None, help="write the report here instead of stdout")
    a = ap.parse_args(argv)
    import os

    import cadence
    from tasks import TASKS
    try:
        on = cadence.as_of(a.as_of or os.environ.get("KG_AS_OF") or "today")
    except ValueError as e:
        print(f"proposal_impact: as_of: {e}", file=sys.stderr)
        return 2
    task = a.task or ("codegen" if "codegen" in TASKS else next(iter(TASKS), None))
    if task is not None and task not in TASKS:
        print(f"proposal_impact: no task {task!r}; the subject declares {sorted(TASKS)}", file=sys.stderr)
        return 2
    try:
        report = evaluate(read_proposal(a.proposal), today=on, children=a.children)
    except (ProposalError, ri.ImpactError) as e:
        print(f"proposal_impact: {e}", file=sys.stderr)
        return 2
    if not a.no_store and task is not None:
        try:
            from mcp_server import open_read_only
            st = open_read_only()
        except Exception as e:  # noqa: BLE001 - the register answers without a store
            report["keys"]["store_unavailable"] = f"{type(e).__name__}: {e}"
        else:
            try:
                with_levels(report, st, task=task, as_of=on.isoformat(), scenario=a.scenario)
            except ProposalError as e:
                print(f"proposal_impact: {e}", file=sys.stderr)
                return 2
            finally:
                st.release()
    text = json.dumps(report, indent=1, ensure_ascii=False, default=str) + "\n" if a.format == "json" else render_text(report)
    if a.output:
        a.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
