"""A proposed addition read against the register as if approved, without approving it (task-0130,
doc-0017 candidate 1), with its deterministic link candidates D1 to D5 (task-0131, candidate 3).

    python harness/proposal_impact.py PROPOSAL.json [--children] [--task NAME] [--as-of DATE]
                                      [--scenario ID] [--no-store] [-f text|json] [-o FILE]
    python harness/proposal_impact.py --register-branch DIR --base REF [the same options]

A proposal is an overlay on the register ``KG_REGISTER`` names (``cadence.register_root``, at its tag):
register-shaped ``nodes`` (a provisional id, kind, name, parent, owner, an optional ``source``),
``links`` (type, source, target, rationale, an optional owner), the ``reused`` register nodes, each
``as_is`` or ``changed``, optional proposed ``exceptions`` (rule, scope, expires, rationale), and an optional
``format``, the overlay's format version (task-0280: missing reads as 1, a newer one is refused, exit 2). A
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
- Slices (task-0152, doc-0022 K1): the slice map, by the register's ``THREAD`` walk with parent
  descent (decision 0018) and its rule A1 (``check_alignment``), both on the read register. One slice
  per approved step of a journey that concerns a product in scope, or, for a product no journey
  concerns, per process that delivers it; each overlay element in the one slice whose thread holds it,
  else in a named remainder (shared, required_not_reached, frame, exceptions, outside), with the
  denominator. Facts only: no label, estimate or rank.
- Keys: per reused node, the register-map rows ``register_impact`` lands on the base register for that
  node, and with a scenario held each key's level, stale statements, suspect derived outputs and
  findings, as the MCP tool ``register_impact`` reports them for the same node, task class and as_of.
  A new node has no row in any map and no statement: it is listed ``unmapped``, never ``unknown``.
- Candidates, in order: D1 a register id the input names (``authored``); D2 an external id
  (``aris_guid``, ``archi_id``, ``edm_id``, the systems' ``id_field``) matched through a register
  node's ``[source]``, or through the newest landed export's MANIFEST ``[register_ids]`` (``authored``); D3 an
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

Branch mode (task-0132, doc-0017 candidate 2): with ``--register-branch DIR --base REF`` the overlay is
the register checkout's own diff: every node file added under a taxonomy, every link whose id is new
in a relationship file, every exception file added, between the merge base of REF and HEAD and HEAD;
ids are the branch's own. A node file changed on the branch is a reused node ``changed``; any other
change (a deleted or renamed file, a link changed in place) is listed under ``branch.not_read``. The
register read is the merge base's, taken with ``git archive`` into a temporary directory; the
checkout is read and never written, and the report names the base and head commits. A register pull
request's what-if: ``instance/ci/proposal-impact.sh`` runs it and prints nothing but its report.

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

import dates  # noqa: E402  (task-0262: one strict YYYY-MM-DD parse)
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
            with ri.no_bytecode():   # the register's file, never written (doc-0030 M11)
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
    if not dates.is_date(v):   # task-0262: YYYY-MM-DD only
        raise ProposalError(f"{what}: {v!r} is not a date (YYYY-MM-DD)")
    return dates.parse(v)


def _str(v, what: str) -> str:
    if not isinstance(v, str) or not v.strip() or len(v) > 200:
        raise ProposalError(f"{what}: a non-empty string")
    return v


# ---- the overlay, read into the register's own dict shape ----

def _check_format(proposal: dict, where: str = "the proposal") -> None:
    """task-0280 (decision-0033 choice 6): the overlay's optional ``format``; missing reads as 1, a newer one or one
    that is not a version is refused as the proposal's error, naming ``where`` (the file, on the command line)."""
    import formats
    try:
        formats.version(proposal, where, formats.PROPOSAL)
    except formats.FormatError as e:
        raise ProposalError(str(e)) from None


class Overlay:
    """The proposal checked and given in-memory ids; ``out`` maps an in-memory id back to the
    provisional one the report names."""

    def __init__(self, proposal: dict, reg: dict, T: dict, scoped: bool = False):
        if not isinstance(proposal, dict):
            raise ProposalError("the proposal is an object with nodes, links, reused and exceptions")
        extra = set(proposal) - {"nodes", "links", "reused", "exceptions", "title", "format"}
        if extra:
            raise ProposalError(f"the proposal has no field(s) {sorted(extra)}")
        _check_format(proposal)
        k2t = T["register"].kind_taxonomy(reg)
        prefixes = {tax: spec["prefix"] for tax, spec in reg["types"]["taxonomy"].items()}
        nodes, links = proposal.get("nodes") or [], proposal.get("links") or []
        reused, excs = proposal.get("reused") or [], proposal.get("exceptions") or []
        for what, xs in (("nodes", nodes), ("links", links), ("reused", reused), ("exceptions", excs)):
            if not isinstance(xs, list) or not all(isinstance(x, dict) for x in xs):
                raise ProposalError(f"{what}: a list of objects")
        if not nodes and not links and not scoped:   # a named scope reads the approved register alone (task-0191)
            raise ProposalError("the proposal adds no node and no link; name a scope (a journey, a step or a product) "
                                "to read the approved register's slices")
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


def coverage_rules(CR) -> tuple[str, ...]:
    """Every coverage rule the register's own checker defines, in its order (C1 to C4 at ieam-register v0.2.13,
    decision 0020): read from its ``COVERAGE_RULES``, so a later rule needs no code here (task-0241)."""
    return tuple(CR.COVERAGE_RULES)


def _cov(CR, reg: dict, ov: Overlay, today: dt.date) -> dict:
    f = CR.Findings()
    s = CR.check_coverage(reg, f, today)
    return {r: {"denominator": s[r]["denominator"], "covered": s[r]["covered"], "excepted": s[r]["excepted"],
                "uncovered": [{"id": ov.name(x), "hypothetical": ov.is_new(x)} for x in s[r]["uncovered"]]}
            for r in coverage_rules(CR)}


def coverage(CR, base: dict, read: dict, ov: Overlay, today: dt.date) -> dict:
    before, after = _cov(CR, base, ov, today), _cov(CR, read, ov, today)
    gaps = []
    for r in coverage_rules(CR):
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


# ---- the slice map (task-0152, doc-0022 K1) ----

LAYERS = (("processes", "process"), ("capabilities", "capability"), ("applications", "application"), ("information", "information"))
FRAME_LINKS = ("concerns", "delivers", "requires")
GROUPS = {
    "shared": "on the thread of more than one slice",
    "required_not_reached": "a capability a product in scope requires that no slice's thread reaches (the register's A1 for "
                            "a product a journey concerns, the process slices' thread walk otherwise), what realises it by "
                            "the realisers walk and each realising process's thread",
    "frame": "a product in scope, a journey element above its slices, or a concerns, delivers or requires link of a product "
             "in scope, on no slice's thread",
    "exceptions": "a proposed exception: it scopes a rule and is on no thread",
    "outside": "on no slice's thread, no required capability's realisers and no product's frame",
}


def _approved(reg: dict, rel: str) -> list[dict]:
    return [ln for ln in reg["relationships"].get(rel, {}).get("links", []) if ln.get("state") == "approved" and ln.get("target")]


def _triples(edges: list[dict]) -> set[tuple[str, str, str]]:
    """The links a walk followed, as (source, type, target): an inverse edge is its link read backwards."""
    out = set()
    for e in edges:
        if not e.get("live"):
            continue
        rel = e["rel"].removesuffix(" (inverse)")
        out.add((e["to"], rel, e["from"]) if e["rel"] != rel else (e["from"], rel, e["to"]))
    return out


SCOPE_KINDS = ("product", "variant")   # and every node of the journeys taxonomy: a journey, a step, a touchpoint


def scope_of(read: dict, scope: str | None) -> dict | None:
    """The named scope (task-0191): an approved product or variant, or an approved node of the journeys
    taxonomy; anything else is refused."""
    if scope is None:
        return None
    if not isinstance(scope, str) or scope not in read["nodes"]:
        raise ProposalError(f"scope {scope!r}: not a register node")
    n = read["nodes"][scope]
    if n.get("state") != "approved":
        raise ProposalError(f"scope {scope}: {n.get('state')}, not approved; only an approved journey or product is sliced")
    if n.get("kind") not in SCOPE_KINDS and n.get("_taxonomy") != "journeys":
        raise ProposalError(f"scope {scope}: a {n.get('kind')}; a scope is a journey, a step, a touchpoint or a product")
    return {"id": scope, "kind": n.get("kind"), "taxonomy": n.get("_taxonomy"), "name": n.get("name", "")}


def slices(T, CR, read: dict, ov: Overlay, scope: str | None = None, register_map: dict | None = None,
           task: str | None = None, task_keys: list[str] | None = None) -> dict:
    """The overlay grouped into vertical slices, one per approved step of a journey that concerns a
    product in scope (a touchpoint under no step is its own), or, for a product no journey concerns,
    one per process that delivers it. A slice is the register's thread walk with parent descent from
    its start (decision 0018), as A1 walks; the required capabilities no slice reaches are A1's own
    finding. A product is in scope when its footprint (itself, its journeys and their descendants,
    its slices' threads, its required capabilities and their realisers) holds an overlay node or both
    ends of an overlay link. Every overlay element is placed once: in the one slice whose thread holds
    it, else in a named remainder. Facts only: no label, estimate or order beyond the register's ids.
    With ``task`` and its ``task_keys`` (task-0252), a slice's keys are the class's keys among the rows
    landing on its thread, and the class's keys that land on no slice are the named key remainder
    ``task_keys``, the class's key count its denominator."""
    imp, nodes = T["impact"], read["nodes"]
    withdrawn = imp.WITHDRAWN
    changed = {r["id"] for r in ov.reused if r["mode"] == "changed"}

    def status(x):
        return "new" if ov.is_new(x) else "changed" if x in changed else "reused"

    def cell(x):
        n = nodes.get(x) or {}
        return {"id": ov.name(x), "kind": n.get("kind"), "name": n.get("name", ""), "owner": n.get("owner"), "status": status(x)}

    def key(x):
        return ov.name(x)

    a1 = CR.check_alignment(read, CR.Findings())
    walked: dict[str, dict] = {}

    def thread(start):
        if start not in walked:
            got = imp.walk_children(read, start, imp.THREAD)
            live = [d["id"] for d in got["descendants"] if d["live"]]
            walked[start] = {**got, "live": live, "nodes": {start, *live, *got["reached"]}, "triples": _triples(got["edges"])}
        return walked[start]

    def realisers(cap):
        edges = imp.walk(read, cap, imp.WALKS["realisers"])
        return imp.reached(edges), _triples(edges)

    def is_step_start(d, top):
        n = nodes[d]
        if n.get("state") != "approved" or n.get("kind") not in STEP_KINDS:
            return False
        if n["kind"] == "step":
            return True
        p = n.get("parent")   # a touchpoint is its own slice only under no step
        while p and p != top:
            if (nodes.get(p) or {}).get("kind") == "step":
                return False
            p = (nodes.get(p) or {}).get("parent")
        return True

    products = sorted((nid for nid, n in nodes.items() if n.get("kind") in ("product", "variant") and n.get("state") == "approved"), key=key)
    plan = {}
    for pid in products:
        journeys = sorted({ln["source"] for ln in _approved(read, "concerns") if ln["target"] == pid
                           and (nodes.get(ln["source"]) or {}).get("state") not in withdrawn}, key=key)
        required = sorted({ln["target"] for ln in _approved(read, "requires") if ln["source"] == pid}, key=key)
        frame, starts, not_walked = {pid}, [], []
        if journeys:
            axis = "step"
            for j in journeys:
                frame.add(j)
                if nodes[j].get("kind") in STEP_KINDS and nodes[j].get("state") == "approved":
                    starts.append(j)
                for d in imp.descendants(read, j):
                    if is_step_start(d, j):
                        starts.append(d)
                    elif nodes[d].get("state") != "approved":
                        not_walked.append(d)
                    frame.add(d)
            axis_nodes = journeys
        else:
            axis = "process"
            axis_nodes = sorted({ln["source"] for ln in _approved(read, "delivers") if ln["target"] == pid
                                 and (nodes.get(ln["source"]) or {}).get("state") not in withdrawn}, key=key)
            starts = list(axis_nodes)
        starts = list(dict.fromkeys(starts))
        reached_caps = sorted({x for s in starts for x in thread(s)["reached"] if nodes.get(x, {}).get("_taxonomy") == "capabilities"}, key=key)
        if journeys:
            missing = [c for p, c in a1["required_not_reached"] if p == pid]
            extra = [c for p, c in a1["reached_not_required"] if p == pid]
        else:
            missing = [c for c in required if c not in reached_caps]
            extra = [c for c in reached_caps if c not in required]
        foot = set(frame) | set(required)
        for s in starts:
            foot |= thread(s)["nodes"]
        for c in required:
            got = realisers(c)[0]
            foot |= got
            for x in got:
                if nodes.get(x, {}).get("_taxonomy") == "processes":
                    foot |= thread(x)["nodes"]
        frame -= {x for s in starts for x in thread(s)["nodes"]}
        plan[pid] = {"journeys": journeys, "axis": axis, "axis_nodes": axis_nodes, "required": required, "starts": starts,
                     "reached": reached_caps, "missing": missing, "extra": extra, "frame": frame, "foot": foot,
                     "not_walked": sorted(set(not_walked), key=key)}
    named = None if scope is None else read["nodes"][scope]
    if named is not None and named.get("_taxonomy") == "journeys":   # task-0191: a journey's own steps, whatever product it concerns
        own = [scope] if is_step_start(scope, None) else []
        own += [d for d in imp.descendants(read, scope) if is_step_start(d, None)]   # a touchpoint rides a step above it, the scope included
        own = list(dict.fromkeys(own))
        in_scope = [pid for pid in products if set(own) & set(plan[pid]["starts"])]
        starts = {s: [pid for pid in in_scope if s in plan[pid]["starts"]] for s in own}
    else:
        if named is not None:   # a product or variant, named
            in_scope = [scope] if scope in plan else []
        else:
            in_scope = [pid for pid in products
                        if any(n["id"] in plan[pid]["foot"] for n in ov.nodes)
                        or any(ln["source"] in plan[pid]["foot"] and ln["target"] in plan[pid]["foot"] for ln in ov.links)]
        starts = {}
        for pid in in_scope:
            for s in plan[pid]["starts"]:
                starts.setdefault(s, []).append(pid)

    elements = [("node", n["id"], n["_provisional"]) for n in ov.nodes] + \
               [("link", (ln["source"], ln["_type"], ln["target"]), ln["_provisional"]) for ln in ov.links]
    home: dict[str, list[dict]] = {s: [] for s in starts}
    groups: dict[str, list[dict]] = {g: [] for g in GROUPS}
    enabler_nodes, enabler_links, frame_nodes = set(), set(), set()
    enablers: dict[str, list[str]] = {}
    for pid in in_scope:
        frame_nodes |= plan[pid]["frame"]
        for c in plan[pid]["missing"]:
            enablers.setdefault(c, []).append(pid)
            got, links = realisers(c)
            enabler_nodes |= {c, *got}
            enabler_links |= links | {(pid, "requires", c)}
            for x in got:   # a realising process's own thread: what it uses, down to the data
                if nodes.get(x, {}).get("_taxonomy") == "processes":
                    enabler_nodes |= thread(x)["nodes"]
                    enabler_links |= thread(x)["triples"]
    for what, ref, pid in elements:
        on = [s for s in starts if (ref in thread(s)["nodes"] if what == "node" else ref in thread(s)["triples"])]
        item = {"id": pid, "element": what}
        if len(on) == 1:
            home[on[0]].append(item)
        elif on:
            groups["shared"].append({**item, "slices": [ov.name(s) for s in on]})
        elif (ref in enabler_nodes) if what == "node" else (ref in enabler_links):
            groups["required_not_reached"].append(item)
        elif (ref in frame_nodes) if what == "node" else (ref[1] in FRAME_LINKS and (ref[0] in in_scope or ref[2] in in_scope)):
            groups["frame"].append(item)
        else:
            groups["outside"].append(item)
    groups["exceptions"] = [{"id": e["_provisional"], "element": "exception"} for e in ov.exceptions]

    layer_of = dict(LAYERS)
    rows_all = (register_map or {}).get("row", [])
    wanted = list(dict.fromkeys(task_keys)) if task_keys is not None else None
    of = len(wanted) if wanted is not None else len({r["key"] for r in rows_all})
    items = []
    for s, pids in starts.items():
        t = thread(s)
        axis = plan[pids[0]]["axis"] if pids else "step"
        by_layer = {name: [] for _, name in LAYERS}
        for x in sorted({*t["live"], *t["reached"]}, key=key):
            tax = (nodes.get(x) or {}).get("_taxonomy")
            if tax in layer_of:
                by_layer[layer_of[tax]].append(cell(x))
        own = layer_of.get((nodes.get(s) or {}).get("_taxonomy"))
        shown = [s, *t["live"], *t["reached"]]
        live_edges = [e for e in t["edges"] if e["live"]]
        handoffs = [{"from": ov.name(e["from"]), "rel": e["rel"], "to": ov.name(e["to"]), "owners": [a, b]}
                    for e in live_edges
                    for a, b in [((nodes.get(e["from"]) or {}).get("owner"), (nodes.get(e["to"]) or {}).get("owner"))]
                    if a and b and a != b]
        items.append({
            "start": cell(s), "axis": axis, "products": [ov.name(p) for p in pids],
            "descendants": [cell(d) for d in t["live"]],
            "thread": by_layer, "empty": [name for name, xs in by_layer.items() if not xs and name != own],
            "withdrawn": [{"from": ov.name(e["from"]), "rel": e["rel"], "to": ov.name(e["to"]), "state": e["state"]}
                          for e in t["edges"] if not e["live"]],
            "owners": sorted({o for o in ((nodes.get(x) or {}).get("owner") for x in shown) if o}),
            "handoffs": handoffs,
            "elements": home[s],
            "keys": slice_keys(register_map, s, t, of, wanted, task) if register_map is not None else None,
        })
    caps = [{"capability": cell(c), "required_by": [ov.name(p) for p in pids],
             "realisers": [cell(x) for x in sorted(realisers(c)[0], key=key)]}
            for c, pids in sorted(enablers.items(), key=lambda kv: key(kv[0]))]
    in_slices = sum(len(i["elements"]) for i in items)
    in_rest = sum(len(xs) for xs in groups.values())
    return {
        "walk": "thread", "register_rule": "A1", "children": True,
        "scope": scope_of(read, scope),
        "products": [{"id": ov.name(p), "name": nodes[p].get("name", ""), "status": status(p), "axis": plan[p]["axis"],
                      "journeys": [ov.name(j) for j in plan[p]["journeys"]],
                      "processes": [ov.name(x) for x in plan[p]["axis_nodes"]] if plan[p]["axis"] == "process" else [],
                      "slices": [ov.name(s) for s in plan[p]["starts"]], "not_walked": [ov.name(x) for x in plan[p]["not_walked"]],
                      "required": [ov.name(c) for c in plan[p]["required"]], "reached": [ov.name(c) for c in plan[p]["reached"]],
                      "required_not_reached": [ov.name(c) for c in plan[p]["missing"]],
                      "reached_not_required": [ov.name(c) for c in plan[p]["extra"]],
                      "alignment_by": "A1" if plan[p]["axis"] == "step" else "thread walk from the process slices"}
                     for p in in_scope],
        "map": items,
        "remainder": [{"group": g, "why": why, "elements": groups[g], **({"capabilities": caps} if g == "required_not_reached" else {})}
                      for g, why in GROUPS.items()],
        "elements": {"denominator": len(elements) + len(ov.exceptions), "in_slices": in_slices, "in_remainder": in_rest},
        "task_keys": key_remainder(register_map, items, wanted, task) if register_map is not None else None,
    }


# ---- keys per slice (task-0191, doc-0024 J1) ----

CELL_WHY = {
    "of": "the task class's keys (the subject's register-map keys when no class is named): every slice's denominator",
    "landed": "distinct keys the slice's rows land, the rows on a withdrawn descendant left out",
    "unread": "keys whose level was not read: no scenario held, or the slice not read",
    "worst": "the lowest level read, by the gate's order; null when none was read. Not a score",
    "unknown": "keys read at absent: no statement, the three-valued unknown",
    "gaps": "keys read at declared_gap: a documented gap",
    "lapsed": "keys with a lapsed review on the date read (decision-0005)",
    "behind_withdrawn": "rows naming the far node of a thread edge the walk does not follow; only_behind, those landed no other way",
}


def slice_keys(register_map: dict, start: str, t: dict, of: int, wanted: list[str] | None = None,
               task: str | None = None) -> dict:
    """A slice's keys: the register-map rows ``register_impact.landed_rows`` lands for the slice's start, its
    walked descendants and every node its thread reaches, as register_impact computes them for the same
    nodes (task-0191), kept to the task class's keys when ``wanted`` names them (task-0252: the class's
    keys, never every key a change reaches, which is register_impact's question); the rows behind each
    edge the thread does not follow; the cells, unread until ``with_levels`` reads a store. Facts only,
    with the denominator."""
    live = list(t["live"])
    withdrawn = [d["id"] for d in t["descendants"] if not d["live"]]
    keep = None if wanted is None else set(wanted)
    rows = [r for r in ri.landed_rows(register_map, start, sorted(t["reached"]), live, withdrawn)
            if keep is None or r["key"] in keep]
    landed = {r["key"] for r in rows if not r.get("withdrawn")}
    behind = []
    for e in t["edges"]:
        if e["live"]:
            continue
        ks = sorted({r["key"] for r in register_map.get("row", []) if e["to"] in (r.get("nodes") or [])
                     and (keep is None or r["key"] in keep)})
        behind.append({"from": e["from"], "rel": e["rel"], "to": e["to"], "state": e["state"], "keys": ks,
                       "only_behind": [k for k in ks if k not in landed]})
    return {"task": task, "of": of, "landed": len(landed), "rows": rows, "behind_withdrawn": behind, "gate": None,
            "cells": cells(rows, read=False)}


KEY_REMAINDER_WHY = ("the task class's keys (the subject's register-map keys when no class is named) that land on no "
                     "slice's thread: mapped onto register nodes no slice reaches, or on no register-map row (mapped "
                     "false, owner null); the class's key count is the denominator, every key in a slice or here")


def key_remainder(register_map: dict, items: list[dict], wanted: list[str] | None, task: str | None) -> dict:
    """The keys of ``task`` (every register-map key when none is named) that no slice lands (task-0252), each
    with its rows' owner, anchor and nodes; ``mapped`` false when no register-map row names it. With the
    denominator, so every one of the class's keys is in a slice or here. ``with_levels`` reads their levels."""
    rows_all = register_map.get("row", [])
    universe = wanted if wanted is not None else list(dict.fromkeys(r["key"] for r in rows_all))
    on = {r["key"] for i in items for r in (i.get("keys") or {}).get("rows", []) if not r.get("withdrawn")}
    rest = []
    for k in universe:
        if k in on:
            continue
        mine = [r for r in rows_all if r["key"] == k]
        rest.append({"key": k, "owner": next((r.get("owner") for r in mine if r.get("owner")), None),
                     "anchor": next((r.get("anchor") for r in mine if r.get("anchor")), None), "via": [],
                     "mapped": bool(mine), "nodes": sorted({x for r in mine for x in r.get("nodes") or []})})
    return {"task": task, "group": "on_no_slice", "why": KEY_REMAINDER_WHY, "denominator": len(universe),
            "in_slices": len(on & set(universe)), "on_no_slice": len(rest), "keys": rest, "gate": None,
            "cells": cells(rest, read=False)}


def cells(rows: list[dict], read: bool) -> dict:
    """The facts a slice's rows give: counts per level read, the keys unread, the lowest level by the gate's
    order (never a score), the keys at absent (unknown) and at declared_gap, and those whose review lapsed."""
    from gate import ORDER
    keyed = {}
    for r in rows:
        if not r.get("withdrawn"):
            keyed.setdefault(r["key"], r)
    levels = {}
    for r in keyed.values():
        if read and "level" in r:
            levels[r["level"]] = levels.get(r["level"], 0) + 1
    unread = sorted(k for k, r in keyed.items() if not read or "level" not in r)
    read_levels = [lv for lv in levels if lv in ORDER]
    return {"read": read, "levels": dict(sorted(levels.items(), key=lambda kv: ORDER.index(kv[0]) if kv[0] in ORDER else len(ORDER))),
            "unread": unread, "worst": min(read_levels, key=ORDER.index) if read_levels else None,
            "unknown": sorted(k for k, r in keyed.items() if r.get("level") == "absent"),
            "gaps": sorted(k for k, r in keyed.items() if r.get("level") == "declared_gap"),
            "lapsed": sorted(k for k, r in keyed.items() if any(f.get("kind") == "lapsed" for f in r.get("findings") or [])),
            "why": dict(CELL_WHY)}


# ---- candidates D1 to D4 (D5 is a placement finding) ----

def _id_fields(reg: dict) -> dict[str, str]:
    return {name: spec["id_field"] for name, spec in reg["sources"].get("system", {}).items()}


def _newest_guids(root: Path, system: str) -> tuple[str, str, dict]:
    """The newest landed export of ``system`` under the register (``exports/<system>/<date>/``), the
    MANIFEST table it read and that table (GUID -> register id): ``[register_ids]`` as the connector
    writes it (task-0063, decision-0010), or ``[guids]`` in a folder landed before decision-0010."""
    d = root / "exports" / system
    folders = sorted(p for p in d.iterdir() if p.is_dir() and (p / "MANIFEST.toml").is_file()) if d.is_dir() else []
    if not folders:
        return "", "", {}
    man = tomllib.loads((folders[-1] / "MANIFEST.toml").read_text(encoding="utf-8"))
    table = "register_ids" if "register_ids" in man else "guids"
    return f"exports/{system}/{folders[-1].name}", table, man.get(table) or {}


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
                folder, table, guids = _newest_guids(root, system)
                if val in guids and guids[val] in base["nodes"]:
                    hit, where = [guids[val]], f"{folder}/MANIFEST.toml [{table}]"
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


DEFAULT_TASK = "default"   # the command's and the tool's default class: codegen where declared, else the first


def _task(task: str | None, tasks: dict) -> str | None:
    """The class ``task`` names (task-0252): ``DEFAULT_TASK`` is codegen where the subject declares it, else its
    first class, else none; None is no class, every register-map key read."""
    if task != DEFAULT_TASK:
        return task
    return "codegen" if "codegen" in tasks else next(iter(tasks), None)


def _task_keys(task: str | None, tasks: dict) -> list[str] | None:
    """The keys ``tasks[task]`` requires, or None when no class is named (task-0252)."""
    if task is None:
        return None
    if task not in tasks:
        raise ProposalError(f"no task {task!r}; the subject declares {sorted(tasks)}")
    return list(tasks[task].get("keys", []))


def evaluate(proposal: dict | None, root: Path | None = None, today: dt.date | None = None, children: bool = False,
             register_map: dict | None = None, scope: str | None = None, task: str | None = DEFAULT_TASK,
             tasks: dict | None = None) -> dict:
    """The report, without the store: everything but the keys' levels (``with_levels`` adds those).
    ``today`` is the date exceptions and reviews are read on (the as_of). ``scope`` names a journey, a step
    or a product (task-0191): the slices are its own, and the overlay may add nothing, so the approved
    register is read alone. ``task`` names the class whose keys the slices read (task-0252); none, every
    register-map key; by default the command's own default class. ``tasks`` is the class table those keys come
    from, ``{class: {"keys": [...]}}``, and must be the same subject's as ``register_map``: both default to
    the process's subject (``KG_SUBJECT``: ``SUBJECT.register_map()`` and ``tasks.TASKS``), which is what the
    command and the MCP tool read, so a caller passing another subject's map passes its tasks too."""
    if not isinstance(children, bool):
        raise ProposalError("children must be true or false")
    root = (root or ri.register_root()).resolve()
    if today is None:
        import cadence
        today = cadence.as_of("today")
    T = ri.load_tools(root)
    CR = check_module(root)
    base = T["register"].load_register(root)
    if proposal is None:
        if scope is None:
            raise ProposalError("give a proposal, a scope, or both")
        proposal = {"title": f"the approved register, scoped by {scope}"}
    ov = Overlay(proposal, base, T, scoped=scope is not None)
    read = ov.merged(base, "approved", today)
    scope_of(read, scope)   # refused before anything is read
    if register_map is None:
        from subject import SUBJECT
        register_map = SUBJECT.register_map()
    if tasks is None:
        from tasks import TASKS as tasks
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
        "slices": slices(T, CR, read, ov, scope=scope, register_map=register_map, task=_task(task, tasks),
                         task_keys=_task_keys(_task(task, tasks), tasks)),
        "keys": {"task": None, "scenario": None, "store": None, "gate": None, "by_node": keys},
        "unmapped": [{"id": n["_provisional"], "why": "no register-map row names it and no subject has asked about it: unmapped, not unknown"}
                     for n in ov.nodes if n["id"] not in mapped],
        "approvals": approvals(base, ov),
        "limits": list(LIMITS),
        "branch": None,
    }


def with_levels(report: dict, st, *, task: str, as_of: str, scenario: str | None = None) -> dict:
    """Each reused node's keys with their levels, as the MCP tool ``register_impact`` reads them: one
    ``gate_cli.evaluate`` per node over its landed keys under ``task`` on ``as_of``. Reads only."""
    import gate_cli
    from subject import SUBJECT
    from tasks import TASKS
    import held as held_state
    h = st.held()   # whose load and which scenario, as the load recorded them (task-0195)
    report["keys"]["store"] = st.name
    if h is None:
        return report
    why = held_state.refusal(h, SUBJECT.id, scenario)
    if why:
        raise ProposalError(why)
    held = h["scenario"]
    sl_task = ((report.get("slices") or {}).get("task_keys") or {}).get("task")
    if sl_task is not None and sl_task != task:
        raise ProposalError(f"the slices were read under the task {sl_task!r}, not {task!r}")
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
    for sl in (report.get("slices") or {}).get("map", []):   # task-0191: each slice's keys, as register_impact reads them
        k = sl.get("keys")
        if not k or not k["rows"]:
            continue
        spec = dict(TASKS[task], keys=list(dict.fromkeys(r["key"] for r in k["rows"])))
        rep = gate_cli.evaluate(st, subject=SUBJECT.id, scenario=held, task="keys", spec=spec, threshold="blocker",
                                baseline=None, loaded=False, version=gate_cli.held_version(st), as_of=as_of, route_task=task)
        k["rows"] = ri.with_levels(k["rows"], rep)
        k["gate"] = {"task": task, "verdict": rep["verdict"], "why": rep["why"], "exit_code": rep["exit_code"]}
        k["cells"] = cells(k["rows"], read=True)
        verdicts.append(rep["verdict"])
    rest = (report.get("slices") or {}).get("task_keys")
    if rest and rest["keys"]:   # task-0252: the class's keys on no slice, read as the slices' are
        spec = dict(TASKS[task], keys=[r["key"] for r in rest["keys"]])
        rep = gate_cli.evaluate(st, subject=SUBJECT.id, scenario=held, task="keys", spec=spec, threshold="blocker",
                                baseline=None, loaded=False, version=gate_cli.held_version(st), as_of=as_of, route_task=task)
        rest["keys"] = ri.with_levels(rest["keys"], rep)
        rest["gate"] = {"task": task, "verdict": rep["verdict"], "why": rep["why"], "exit_code": rep["exit_code"]}
        rest["cells"] = cells(rest["keys"], read=True)
    report["keys"]["gate"] = {"task": task, "verdicts": sorted(set(verdicts))}
    return report


# ---- branch mode (task-0132) ----

def _git(repo: Path, *args: str, binary: bool = False):
    import subprocess
    try:
        r = subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)
    except (OSError, subprocess.CalledProcessError) as e:
        err = getattr(e, "stderr", b"") or b""
        raise ProposalError(f"git {' '.join(args)} in {repo}: {err.decode('utf-8', 'replace').strip() or e}") from e
    return r.stdout if binary else r.stdout.decode("utf-8").strip()


def _toml_at(repo: Path, rev: str, path: str) -> dict:
    try:
        return tomllib.loads(_git(repo, "show", f"{rev}:{path}"))
    except tomllib.TOMLDecodeError as e:
        raise ProposalError(f"{rev}:{path}: {e}") from e


def branch_overlay(checkout: Path, base: str, taxonomies: tuple[str, ...]) -> tuple[dict, dict]:
    """The proposal a register branch makes against ``base``, and what the report says of the branch.
    Reads git only: the diff between the merge base and HEAD (committed work, never the working tree)."""
    checkout = checkout.resolve()
    head = _git(checkout, "rev-parse", "HEAD")
    mb = _git(checkout, "merge-base", base, "HEAD")
    rows = [ln.split("\t") for ln in _git(checkout, "diff", "--name-status", "--no-renames", mb, head).splitlines() if ln]
    nodes, links, reused, excs, not_read = [], [], [], [], []
    for row in sorted(rows, key=lambda r: r[-1]):
        st, path = row[0], row[-1]
        top = path.split("/", 1)[0]
        if not path.endswith(".toml") or "/" not in path:
            continue
        if top in taxonomies and path.count("/") == 1:
            if st == "A":
                n = _toml_at(checkout, head, path)
                nodes.append({k: n[k] for k in ("id", "kind", "name", "parent", "owner", "source") if k in n})
            elif st == "M":
                n = _toml_at(checkout, head, path)
                reused.append({"id": n.get("id", Path(path).stem), "mode": "changed"})
            else:
                not_read.append({"path": path, "status": st, "why": "a node file deleted: retiring is register_impact's question"})
        elif top == "relationships" and path.count("/") == 1:
            old = {} if st == "A" else _toml_at(checkout, mb, path)
            new = {} if st == "D" else _toml_at(checkout, head, path)
            typ = (new.get("type") or old.get("type") or {}).get("name", Path(path).stem)
            before = {ln.get("id"): ln for ln in old.get("link", [])}
            for ln in new.get("link", []):
                if ln.get("id") not in before:
                    links.append({"id": ln.get("id"), "type": typ,
                                  **{k: ln[k] for k in ("source", "target", "rationale", "owner") if k in ln}})
                elif ln != before[ln.get("id")]:
                    not_read.append({"path": f"{path} [{ln.get('id')}]", "status": "M", "why": "a link changed in place is not an addition"})
            after = {ln.get("id") for ln in new.get("link", [])}
            for lid in sorted(set(before) - after):
                not_read.append({"path": f"{path} [{lid}]", "status": "D", "why": "a link removed is not an addition"})
        elif top == "exceptions" and path.count("/") == 1 and st == "A":
            e = _toml_at(checkout, head, path)
            excs.append({k: e[k] for k in ("id", "rule", "scope", "expires", "rationale") if k in e})
        elif top in (*taxonomies, "relationships", "exceptions"):
            not_read.append({"path": path, "status": st, "why": "not a node, link or exception addition"})
    proposal = {"title": f"register branch at {head[:12]} against {base}", "nodes": nodes, "links": links,
                "reused": reused, "exceptions": excs}
    info = {"checkout": str(checkout), "base": base, "merge_base": mb, "head": head, "not_read": not_read}
    return proposal, info


def evaluate_branch(checkout: Path, base: str, today: dt.date | None = None, children: bool = False,
                    register_map: dict | None = None, scope: str | None = None, task: str | None = DEFAULT_TASK,
                    tasks: dict | None = None) -> dict:
    """The report for a register branch: the merge base's register, from ``git archive`` into a
    temporary directory, read with the branch's additions as the overlay. Nothing in the checkout is
    written; the temporary copy is removed."""
    import io
    import shutil
    import tarfile
    import tempfile
    checkout = Path(checkout).resolve()
    if not (checkout / "metamodel" / "types.toml").is_file():
        raise ProposalError(f"{checkout}: not a register checkout (no metamodel/types.toml)")
    T = ri.load_tools(checkout)
    taxonomies = tuple(T["register"].TAXONOMIES)
    proposal, info = branch_overlay(checkout, base, taxonomies)
    tmp = Path(tempfile.mkdtemp(prefix="kg-proposal-base-"))
    try:
        data = _git(checkout, "archive", "--format=tar", info["merge_base"], binary=True)
        with tarfile.open(fileobj=io.BytesIO(data)) as tar:
            tar.extractall(tmp, filter="data")
        report = evaluate(proposal, root=tmp, today=today, children=children, register_map=register_map, scope=scope,
                          task=task, tasks=tasks)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        _checks.pop(str(tmp.resolve()), None)
        ri._tools.pop(str(tmp.resolve()), None)
    try:
        tag = _git(checkout, "describe", "--tags", "--exact-match", info["merge_base"])
    except ProposalError:
        tag = report["register"]["tag"]   # a vendored copy's SOURCE.md, as register_impact.source reads it
    report["register"] = {"tag": tag, "commit": info["merge_base"]}
    report["branch"] = info
    return report


# ---- the command ----

def read_proposal(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        raise ProposalError(f"{path}: {e}") from e
    try:
        doc = tomllib.loads(text) if path.suffix == ".toml" else json.loads(text)
    except (ValueError, tomllib.TOMLDecodeError) as e:
        raise ProposalError(f"{path}: {e}") from e
    if isinstance(doc, dict):
        _check_format(doc, str(path))   # task-0280: the refusal names the file
    return doc


def render_text(r: dict) -> str:
    sc = r["slices"].get("scope")
    lines = [f"scope {sc['id']} ({sc['kind']}, {sc['name']})"] if sc else []
    o = r["overlay"]
    read_as = "read as it is: no overlay" if sc and not (o["nodes"] or o["links"] or o["exceptions"]) else \
        "read as if approved, every element hypothetical"
    lines += [f"proposal {r['overlay']['title'] or r['overlay']['digest'][:12]} on the register {r['register']['tag'] or '?'} "
             f"({r['register']['commit'][:12]}), as of {r['as_of']}: {read_as}, nothing stored",
             f"  {r['overlay']['nodes']} node(s), {r['overlay']['links']} link(s), {r['overlay']['reused']} reused node(s)"]
    if r.get("branch"):
        b = r["branch"]
        lines.append(f"  branch {b['head'][:12]} against {b['base']} (merge base {b['merge_base'][:12]}); not read: "
                     f"{[x['path'] for x in b['not_read']] or 'nothing'}")
    for c in r["coverage"]["after"]:   # every rule the register's checker defines, in its order (task-0241)
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
    sl = r["slices"]
    for p in sl["products"]:
        lines.append(f"  product {p['id']} ({p['status']}): slices by {p['axis']} {p['slices'] or 'none'}; required not reached "
                     f"{p['required_not_reached'] or 'none'}; reached not required {p['reached_not_required'] or 'none'}")
    for s in sl["map"]:
        layers = "; ".join(f"{k} {','.join(c['id'] + ('*' if c['status'] != 'reused' else '') for c in v) or '-'}" for k, v in s["thread"].items())
        lines.append(f"  slice {s['start']['id']} ({s['start']['status']} {s['axis']}): {layers}; holds {[e['id'] for e in s['elements']] or 'nothing'}")
        k = s.get("keys")
        if k is not None:
            c = k["cells"]
            lv = ", ".join(f"{n} {lvl}" for lvl, n in c["levels"].items()) or "none read"
            lines.append(f"    keys {k['landed']} of {k['of']}; levels {lv}; unread {len(c['unread'])}; worst {c['worst'] or '-'}; "
                         f"unknown {len(c['unknown'])}; gaps {len(c['gaps'])}; lapsed {len(c['lapsed'])}; behind withdrawn "
                         f"{sum(len(b['keys']) for b in k['behind_withdrawn'])} ({sum(len(b['only_behind']) for b in k['behind_withdrawn'])} "
                         f"only behind); owner handoffs {len(s['handoffs'])}")
    for g in sl["remainder"]:
        if g["elements"] or g.get("capabilities"):
            caps = f" capabilities {[c['capability']['id'] for c in g['capabilities']]}" if g.get("capabilities") else ""
            lines.append(f"  remainder {g['group']}:{caps} holds {[e['id'] for e in g['elements']] or 'nothing'}")
    tk = sl.get("task_keys")
    if tk is not None:
        lines.append(f"  task keys{' (' + tk['task'] + ')' if tk['task'] else ''}: {tk['in_slices']} in slices, {tk['on_no_slice']} "
                     f"on no slice, of {tk['denominator']}" + (f": {[k['key'] for k in tk['keys']]}" if tk["keys"] else "")
                     + (f"; gate {tk['gate']['verdict']}" if tk.get("gate") else ""))
    e = sl["elements"]
    lines.append(f"  slices: {e['in_slices']} in slices, {e['in_remainder']} in the remainder, of {e['denominator']} overlay element(s)")
    for k in r["keys"]["by_node"]:
        lines.append(f"  {k['node']}: {len(k['keys'])} key(s)" + (
            f", levels {sorted({x['level'] for x in k['keys'] if 'level' in x})}" if any('level' in x for x in k["keys"]) else ""))
    lines.append(f"  unmapped: {[u['id'] for u in r['unmapped']] or 'none'}")
    for a in r["approvals"]:
        lines.append(f"  {a['unit']} {a['name']} approves {', '.join(x['what'] + ' ' + x['id'] for x in a['approve'])}")
    return "\n".join(lines) + "\n"


def _require_registers(a) -> None:
    """task-0279 (decision-0033 choice 5): the register this process reads, and a branch checkout named by
    ``--register-branch``, must be readable; ``register_impact.RegisterUnreadable`` names the one that is not."""
    ri.require()
    if a.register_branch is not None:
        ri.require(a.register_branch, "--register-branch", tools=False)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="proposal_impact.py", description="A proposed addition read against the register as if "
                                 "approved, without approving it (task-0130). Nothing is written.")
    ap.add_argument("proposal", type=Path, nargs="?", help="the overlay, JSON or TOML (or --register-branch, or --scope alone)")
    ap.add_argument("--scope", default=None, help="a journey, step or product id: its slices, with each slice's keys; with no "
                                                  "proposal, read on the approved register alone (task-0191)")
    ap.add_argument("--register-branch", type=Path, default=None, help="a register checkout whose branch is the proposal (task-0132)")
    ap.add_argument("--base", default=None, help="with --register-branch: the ref the branch is read against, such as origin/main")
    ap.add_argument("--children", action="store_true", help="walk every approved descendant by parent too (the register's decision 0014)")
    ap.add_argument("--task", default=None, help="the task class whose keys each slice reads, and each reused node's keys are read under (default: codegen)")
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
    if (a.proposal is not None and a.register_branch is not None) or (a.register_branch is not None) != (a.base is not None) \
            or (a.proposal is None and a.register_branch is None and a.scope is None):
        print("proposal_impact: give a proposal file, --scope ID, or --register-branch DIR with --base REF", file=sys.stderr)
        return 2
    try:
        _require_registers(a)   # task-0279: an ImpactError, so the message below names the register and exits 2
        if a.register_branch is not None:
            report = evaluate_branch(a.register_branch, a.base, today=on, children=a.children, scope=a.scope, task=task)
        else:
            report = evaluate(read_proposal(a.proposal) if a.proposal else None, today=on, children=a.children, scope=a.scope,
                              task=task)
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
