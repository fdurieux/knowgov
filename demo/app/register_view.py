"""The register view: what the demo shows of the vendored IEAM register
(``demo/register/``, a byte-for-byte copy of fdurieux/ieam-register
at the commit its SOURCE.md names).

The register's TOML at that commit is the record of identities, links, states,
approvals and exceptions; SOURCE.md and its digests are the record of which bytes
the demo carries; the register's own checker, run on those bytes at the pinned
date, is the record of findings and coverage. This module reads all three and
arranges them for the page. It never writes to the register, never rewords a
name, a rationale or a finding (those are data), and adds no field the TOML
lacks. Standard library only; the register's tools are imported from the copy.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import threading
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
# One register per organisation, shared by every subject of it: the instance's own checkout when
# KG_REGISTER names one, else the public register vendored under demo/register at a tag.
REGISTER = Path(os.environ.get("KG_REGISTER") or (HERE.parent / "register")).resolve()

sys.path.insert(0, str(HERE))
import views  # noqa: E402  (the controlled-English registry and glossary live there)
import page_subject  # noqa: E402  (the subject as a value: how its requirements are cited, its slice's source system; task-0032.01)
from page_subject import takes_subject  # noqa: E402
_ps = page_subject.current   # the subject of the call in progress; the environment's when no call names one

_tools: dict | None = None
_tools_lock = threading.Lock()   # the page's first requests arrive together on the threading server


def _load_tools() -> dict:
    """Import the vendored register tools once, from the copy, by path. Under the lock: two
    requests importing at once would see each other's half-built modules (task-0025)."""
    with _tools_lock:
        return _load_tools_locked()


def _load_tools_locked() -> dict:
    global _tools
    if _tools is None:
        tools = REGISTER / "tools"
        if str(tools) not in sys.path:
            sys.path.insert(0, str(tools))
        mods = {}
        for name in ("register", "check_register", "impact"):
            spec = importlib.util.spec_from_file_location(name, tools / f"{name}.py")
            mod = importlib.util.module_from_spec(spec)
            sys.modules[name] = mod
            spec.loader.exec_module(mod)
            mods[name] = mod
        _tools = mods
    return _tools


def _git(*args: str) -> str:
    try:
        return subprocess.run(["git", "-C", str(REGISTER), *args], check=True, capture_output=True, text=True,
                              encoding="utf-8").stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def source_info() -> dict:
    """What the register root is. A vendored copy (``SOURCE.md`` present): the note's table, and
    whether every file still matches its digest. An instance's own checkout (no note): what git
    says of it when it is a repository, no digest to check, no pinned date."""
    files = [p for p in REGISTER.rglob("*") if p.is_file() and p.name != "SOURCE.md" and "__pycache__" not in p.parts and ".git" not in p.parts]
    actual = {p.relative_to(REGISTER).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    if not (REGISTER / "SOURCE.md").exists():
        remote = _git("remote", "get-url", "origin")
        m = re.search(r"[:/]([^/:]+/[^/]+?)(?:\.git)?/?$", remote)
        commit = _git("rev-parse", "HEAD")
        return {"kind": "checkout", "repo": m.group(1) if m else "", "commit": commit, "commit_short": commit[:7],
                "tag": _git("describe", "--tags", "--exact-match"), "describe": _git("describe", "--tags", "--always", "--dirty"),
                "copied": "", "pinned_date": "", "files": len(actual), "digest_ok": None, "mismatched": []}
    note = (REGISTER / "SOURCE.md").read_text(encoding="utf-8")
    def cell(label: str) -> str:
        m = re.search(r"^\| " + re.escape(label) + r" \| (.+?) \|$", note, re.M)
        return m.group(1) if m else ""
    commit = re.search(r"\| commit \| `([0-9a-f]{40})`", note)
    tag = re.search(r"^\| tag \| `(v[0-9][^`]*)`", note, re.M)
    pinned = re.search(r"pinned date for the checker \| `(\d{4}-\d{2}-\d{2})`", note)
    listed = dict(re.findall(r"^\| `([^`]+)` \| `([0-9a-f]{64})` \|$", note, re.M))
    mismatched = sorted(k for k in set(listed) | set(actual) if listed.get(k) != actual.get(k))
    return {"kind": "copy", "repo": "fdurieux/ieam-register", "commit": commit.group(1) if commit else "",
            "commit_short": commit.group(1)[:7] if commit else "", "tag": tag.group(1) if tag else "", "describe": "",
            "copied": cell("copied").split(",")[0],
            "pinned_date": pinned.group(1) if pinned else "", "files": len(actual),
            "digest_ok": not mismatched, "mismatched": mismatched}


def _coverage_lines(summary: dict) -> list[str]:
    """The checker's own coverage print format, verbatim: data, not prose."""
    return [f"{rule}: {s['covered']}/{s['denominator']} covered, {s['excepted']} excepted, {len(s['uncovered'])} uncovered"
            + (f" ({', '.join(s['uncovered'])})" if s["uncovered"] else "")
            for rule, s in ((r, summary[r]) for r in ("C1", "C2", "C3"))]


def _node_panel(nid: str, n: dict, reg: dict, C, D) -> dict:
    tax = n["_taxonomy"]
    kind_words = n.get("kind", "").replace("_", " ")
    intro = C(f"State {n.get('state')}, owner {n.get('owner')}.") + " " + D(f"Name: {n.get('name')}.")
    if n.get("parent"):
        intro += " " + D(f"Parent: {n['parent']}.")
    secs = []
    appr = n.get("approval")
    if appr:
        secs.append({"heading": C("Approval"), "text": D(f"By {appr.get('by')} on {appr.get('on')}, record {appr.get('record')}; review due {n.get('review_due')}.")})
    else:
        secs.append({"heading": C("Approval"), "text": C("No approval is recorded, so the node is not approved.")})
    src = n.get("source") or {}
    if src:
        secs.append({"heading": C("Source of record"), "text": C("The register points at the system that authors the content; it copies nothing but the name."),
                     "table": {"cols": ["field", "value"], "rows": [[k, str(v)] for k, v in src.items()]}})
    outs, ins = [], []
    for rname, rel in reg["relationships"].items():
        for ln in rel["links"]:
            if ln.get("source") == nid:
                outs.append([R("link", ln["id"]), rname, _target_ref(ln), ln.get("state", ""), ln.get("owner", ""), ln.get("rationale", "")])
            if ln.get("target") == nid:
                ins.append([R("link", ln["id"]), rname, R("node", ln["source"]), ln.get("state", ""), ln.get("owner", ""), ln.get("rationale", "")])
    secs.append({"heading": C(f"Links out: {len(outs)}"), "table": {"cols": ["link", "relationship type", "target", "state", "owner", "rationale"], "rows": outs}})
    secs.append({"heading": C(f"Links in: {len(ins)}"), "table": {"cols": ["link", "relationship type", "source", "state", "owner", "rationale"], "rows": ins}})
    return {"id": nid, "taxonomy": tax, "kind": n.get("kind"), "name": n.get("name"), "state": n.get("state"), "owner": n.get("owner"),
            "parent": n.get("parent"), "links_out": len(outs), "links_in": len(ins), "system": src.get("system", ""),
            "subject": src.get("system", "") == _ps().system,   # a node of this subject's slice, or of another subject of the organisation
            "panel": {"title": C(f"{nid}, a {kind_words} in {tax}"), "intro": intro, "sections": secs}}


@takes_subject
def impact(start: str) -> dict | None:
    """The register's own impact walk from one node (tools/impact.py, vendored), each edge
    with its state, owner, evidence and whether the walk followed it, and what it reached. None
    for an unknown id. The walk follows approved links only, stops at a deprecated or retired
    node and does not climb a node's parent (the register's decision 0007, v0.2.2); from each node
    it takes the steps its kind has, toward what rests on it (decision 0010, v0.2.6): a withdrawn
    edge is listed and not followed, and only the far ends of live edges count as reached. That
    is the register tool's behaviour, shown as it is."""
    T = _load_tools()
    reg = T["register"].load_register(REGISTER)
    if start not in reg["nodes"]:
        return None
    edges = T["impact"].walk(reg, start)
    reg_sentences: list[dict] = []
    C = lambda *s: views._reg(reg_sentences, "controlled", *s)  # noqa: E731
    D = lambda *s: views._reg(reg_sentences, "data", *s)  # noqa: E731
    names = {nid: n.get("name", "") for nid, n in reg["nodes"].items()}
    owners = {nid: owning_unit(reg, nid) for nid in {start} | {e["to"] for e in edges}}
    rows = [[e["from"], e["rel"], e["to"], names.get(e["to"], ""), unit_text(owners[e["to"]]), reg["nodes"].get(e["to"], {}).get("state", ""), e["state"],
             "yes" if e["live"] else "no, withdrawn", e["owner"], ", ".join(e["evidence"])] for e in edges]
    reached = sorted(T["impact"].reached(edges))
    withdrawn = sum(1 for e in edges if not e["live"])
    by_prefix = lambda p: [x for x in reached if x.startswith(p + "-")]  # noqa: E731
    products, journeys, processes = by_prefix("PRD"), by_prefix("JRN"), by_prefix("PROC")
    start_node = reg["nodes"][start]
    intro = C(f"The walk starts at {start}, a {start_node.get('kind', '').replace('_', ' ')} in state {start_node.get('state')}.",
              "It follows approved links toward what rests on each node, by the node's kind.",
              "An application leads to its processes; a process to its products, capabilities and journey steps.",
              "A capability leads to the products that require it.",
              "An information entity leads to the processes and applications that use it.",
              "A product leads to its journeys and processes; a journey step to its process and product.",
              "It stops at a deprecated or retired node.", "A withdrawn edge is listed and not followed.",
              "Its link is not approved, or its far node is deprecated or retired.",
              "It does not climb a node's parent, so a module's application is not reached.")
    intro += " " + D(f"Name: {names.get(start, '')}.")
    summary = C(f"{views._plural(len(edges), 'edge')} walked, {withdrawn} withdrawn; {views._plural(len(processes), 'process', 'processes')}, "
                f"{views._plural(len(products), 'product')} and {views._plural(len(journeys), 'journey element')} reached.")
    if not products and (processes or journeys):
        summary += " " + C("No product is reached: no approved link leads from a reached node to a product.")
    if not edges:
        summary += " " + C("No link starts at this node in a direction the walk follows.")
    # who to inform (task-0047): the unit that owns each reached node, by the node's owner field; the
    # owns links are shown, not walked, and one that names another unit is said beside it
    units: dict[str, list[str]] = {}
    for x in reached:
        units.setdefault(owners[x]["unit"] or "", []).append(x)
    inform = [f"{unit_text(owners[xs[0]]) if u else 'no owner field'}: {', '.join(xs)}" for u, xs in sorted(units.items())]
    inform_text = C("The owning unit of a node is the unit its owner field names.",
                    "An approved owns link to the node names a unit too; the walk does not follow it.",
                    "Inform each unit of the change to its reached nodes.")
    if any(o["owns"] and o["owns"] != [o["unit"]] for o in owners.values()):
        inform_text += " " + C("An owns link that names another unit is shown beside the owning unit.")
    return {"from": start, "edges": edges, "rows": rows, "owners": owners,
            "reached": {"products": products, "journeys": journeys, "processes": processes, "all": reached},
            "panel": {"title": C(f"Impact of retiring {start}"), "intro": intro,
                      "sections": [{"heading": C("Edges walked"), "text": summary,
                                    "table": {"cols": ["from", "relationship", "to", "name", "owning unit", "node state", "link state", "followed", "owner", "evidence"], "rows": rows}},
                                   {"heading": C("Reached"), "list": [f"{x}: {names.get(x, '')}, owned by {unit_text(owners[x])}" for x in reached] or ["nothing"]},
                                   {"heading": C("Who to inform"), "text": inform_text, "list": inform or ["nobody: nothing is reached"]}]},
            "text_registry": reg_sentences}


def owning_unit(reg: dict, nid: str) -> dict:
    """The unit that owns register node ``nid`` (task-0047): ``unit``, the node's owner field; ``name``,
    that unit's name in the register; ``owns``, the sources of the approved owns links to the node,
    sorted. The impact walk's saved Cypher returns the same three (IMPACT_ROWS: unit, unit name, owns links)."""
    unit = (reg["nodes"].get(nid) or {}).get("owner", "") or ""
    owns = sorted({ln["source"] for ln in reg["relationships"].get("owns", {}).get("links", [])
                   if ln.get("target") == nid and ln.get("state") == "approved"})
    return {"unit": unit, "name": (reg["nodes"].get(unit) or {}).get("name", ""), "owns": owns}


def unit_text(o: dict) -> str:
    """The owning unit as the panel shows it: its id and name, and any approved owns link naming another unit."""
    text = f"{o['unit']} {o['name']}".strip() if o["unit"] else "none"
    other = [u for u in o["owns"] if u != o["unit"]]
    return text + (f" (owns link: {', '.join(other)})" if other else "")


def with_cypher(walk: dict, cypher: dict, needs_text: str, browser: dict | None = None, guide: dict | None = None) -> dict:
    """The impact panel with the walk's Cypher beside it (task-0024): a code section carrying both
    forms, the rows form and the paths form, with what they need in the store, and for each a
    Browser link when the server gives one: it opens a guide the server serves, whose block fills
    the editor on a click (task-0025). The query text is data; the sentences around it are
    controlled. The page runs nothing."""
    reg_sentences = walk["text_registry"]
    C = lambda *s: views._reg(reg_sentences, "controlled", *s)  # noqa: E731
    text = C("The rows form gives one row per edge, the table above.", "The paths form gives the paths, which the Browser draws as a graph.",
             "The Browser draws every relationship among the shown nodes, so a parent edge can appear that the walk never followed.",
             "A run wipes the projection, so project it again before pasting.")
    if browser:
        text += " " + C("The Browser link opens a guide beside the editor, connected to the store.",
                        "A click on the guide's query puts it in the editor; nothing runs until you press play.")
    walk["cypher"] = dict(cypher, needs="register", needs_text=needs_text, browser=browser, guide=guide)
    code = [{"label": C("Rows, one per edge"), "text": cypher["rows"]}, {"label": C("Paths, for the graph view"), "text": cypher["paths"]}]
    for item, key in zip(code, ("rows", "paths")):
        if browser:
            item["browser"] = browser[key]
    walk["panel"]["sections"].append({"heading": C("The walk in Cypher"), "text": text, "needs": "register", "needs_text": needs_text, "code": code})
    return walk


STATEMENT_COLS = ["assertion", "status", "document", "anchors", "links", "versions", "fragments", "derived"]


def with_statements(walk: dict, read: dict, needs_text: str) -> dict:
    """The impact panel with the assertions the start's cited anchors name beside the walk (task-0047):
    the port's register_node_statements (task-0046) at the grain of the cited anchor, every version,
    with the derived outputs that used each. ``read`` is the server's: rows, or what is missing."""
    reg_sentences = walk["text_registry"]
    C = lambda *s: views._reg(reg_sentences, "controlled", *s)  # noqa: E731
    rows = read.get("rows")
    walk["statements"] = {"rows": rows, "missing": read.get("missing"), "needs": "register+scenario", "needs_text": needs_text}
    text = C(f"These assertions are those the approved links of {walk['from']} cite, at the grain of the cited anchor.",
             "An anchor such as #DT-P names only the fragments under it; a citation without one names the whole document.",
             "Every version is read, so an invalidated assertion still shows the derived code that used it.")
    missing = {"driver": C("The store driver is not installed here, so no assertion is shown."),
               "store": C("The store is not reachable, so no assertion is shown."),
               "register": C("The register is not projected in the store, so no assertion is shown."),
               "scenario": C("No scenario is loaded in the store, so no assertion is shown.")}
    sec = {"heading": C("Assertions its cited anchors name"), "needs": "register+scenario", "needs_text": needs_text}
    if rows is None:
        sec["text"] = text + " " + missing.get(read.get("missing"), missing["store"])
    else:
        sec["text"] = text + " " + C(f"{views._plural(len(rows), 'assertion')} found in the loaded scenario.")
        sec["table"] = {"cols": STATEMENT_COLS, "rows": [[r["statement"], r["status"], r["document"]] + [", ".join(r[k]) for k in
                                                         ("anchors", "links", "versions", "fragments", "derived")] for r in rows]}
    walk["panel"]["sections"].append(sec)
    return walk


def with_statements_cypher(walk: dict, text: str, browser: str | None = None, guide: str | None = None) -> dict:
    """The statements view with its Cypher (task-0078): the saved query register-node-statements from
    the start, as text to paste, and a Browser link when the server gives one, opening a guide the
    server serves whose block fills the editor on a click, as the walk's does (task-0025)."""
    reg_sentences = walk["text_registry"]
    C = lambda *s: views._reg(reg_sentences, "controlled", *s)  # noqa: E731
    sec = next(x for x in walk["panel"]["sections"] if x.get("needs") == "register+scenario" and x["heading"] == C("Assertions its cited anchors name"))
    walk["statements"]["cypher"] = {"text": text, "browser": browser, "guide": guide}
    item = {"label": C("Rows, one per assertion and cited document"), "text": text}
    if browser:
        item["browser"] = browser
        sec["text"] += " " + C("The Browser link opens a guide beside the editor, connected to the store.",
                               "A click on the guide's query puts it in the editor; nothing runs until you press play.")
    sec["code"] = [item]
    return walk


@takes_subject
def impact_default() -> str:
    """The start the page offers first: this subject's application with the most links out, else
    the register's first node. The register's default, not any subject's id (task-0002)."""
    T = _load_tools()
    reg = T["register"].load_register(REGISTER)
    out = {}
    for rname, rel in reg["relationships"].items():
        for ln in rel["links"]:
            out[ln.get("source")] = out.get(ln.get("source"), 0) + 1
    apps = sorted(((nid, n) for nid, n in reg["nodes"].items() if n["_taxonomy"] == "applications" and (n.get("source") or {}).get("system", "") == _ps().system),
                  key=lambda kv: (-out.get(kv[0], 0), kv[0]))
    return apps[0][0] if apps else (next(iter(reg["nodes"]), ""))


@takes_subject
def start_default(taxonomy: str) -> str:
    """The start a saved query from ``taxonomy`` is listed with: for applications the walk's default;
    otherwise this subject's node of that taxonomy that the most links point at, ties by id, else the
    register's first node of it. The register's own, not any subject's id (task-0002)."""
    if taxonomy == "applications":
        return impact_default()
    T = _load_tools()
    reg = T["register"].load_register(REGISTER)
    into = {}
    for rel in reg["relationships"].values():
        for ln in rel["links"]:
            into[ln.get("target")] = into.get(ln.get("target"), 0) + 1
    of = [(nid, n) for nid, n in reg["nodes"].items() if n["_taxonomy"] == taxonomy]
    mine = [kv for kv in of if (kv[1].get("source") or {}).get("system", "") == _ps().system] or of
    mine.sort(key=lambda kv: (-into.get(kv[0], 0), kv[0]))
    return mine[0][0] if mine else ""


sys.path.insert(0, str(HERE.parent.parent / "harness"))


@takes_subject
def has_map() -> bool:
    """Whether the subject maps its keys onto the register; without a map there is no footprint."""
    return bool(_ps().subject.register.get("map"))


@takes_subject
def load_map() -> dict:
    """The approved key-to-node map, the subject's register_map.toml."""
    return _ps().subject.register_map()


@takes_subject
def changed_artefact(scenario: str) -> str:
    """The artefact a scenario's stage 2 changes, or '' when it has none."""
    return _ps().subject.scenarios.get(scenario, {}).get("stage2", {}).get("artefact", "")


# ------------------------------------------------------------ references: what a cell opens

REF_KINDS = ("node", "link", "req", "key", "doc")
LEVEL_TIP = {
    "approved": "Verified and approved by the owner; the gate may build on it.",
    "validated": "Two documents agree and nobody has verified it; the gate counts it below approved.",
    "proposed": "One document states it and nobody has verified it.",
    "declared_gap": "The documents themselves say this knowledge is not there yet.",
    "absent": "No document states it at all.",
    "disputed": "Two documents give different values; the gate blocks the key.",
}
DECLARED_TIP = {"yes": "The authors declared the gap themselves.", "no": "The rules found the gap; nobody had declared it."}


def R(kind: str, ident: str, text: str | None = None) -> dict:
    """A reference cell: the page renders it as a click that opens the subject's panel under the table."""
    return {"ref": f"{kind}:{ident}", "text": text or ident}


def _tip(text: str, tip: str) -> dict:
    return {"text": text, "tip": tip}


def _join(parts: list, sep: str = ", ") -> list | str:
    out: list = []
    for i, p in enumerate(parts):
        if i:
            out.append(sep)
        out.append(p)
    return out or ""


def _norm(anchor: str) -> str:
    """One spelling for a kit anchor: the register writes <system>:requirements.md#REQ-05, the map
    <system>/requirements.md#REQ-05 or contract/decision_table.md#DT-V; all become kit-relative paths."""
    a = anchor[len(_ps().sys):] if anchor.startswith(_ps().sys) else anchor
    return a[len(_ps().system) + 1:] if a.startswith(_ps().system + "/") else a


def _anchor_ref(anchor: str) -> dict:
    """A kit anchor opens the requirement panel when it names a requirement, else the document card."""
    a = _norm(anchor)
    if a.startswith(_ps().req_doc_anchor) and "#" in a and _ps().req_id.fullmatch(a.split("#", 1)[1]):
        return R("req", a.split("#", 1)[1], anchor)
    return R("doc", a.split("#", 1)[0], anchor)


def _target_ref(ln: dict) -> dict:
    return R("node", ln["target"]) if ln.get("target") else _anchor_ref(ln.get("target_external", ""))


def _kind_tip(kind: str, declared: bool) -> str:
    if kind == "missing":
        return views.GAP_KIND_TEXT["declared missing" if declared else "undeclared missing"][0]
    return views.GAP_KIND_TEXT.get(kind, [""])[0]


def _state_tip(state: str, lifecycle: dict) -> str:
    nxt = lifecycle.get("transitions", {}).get(state, [])
    return f"From {state} a node or link may move to {', '.join(nxt)}." if nxt else f"{state} is final: no transition leaves it."


def _type_tip(t: dict) -> str:
    return (f"{t.get('name')}: {', '.join(t.get('source_kind', []))} to {', '.join(t.get('target_kind', []))}, {t.get('direction', '')}; "
            f"inverse label '{t.get('inverse_label', '')}'; ARIS {t.get('aris_status')}, Archi {t.get('archi_status')}.")


def _requirement_line(req: str) -> str:
    """The requirement's own text from the kit's requirements document, verbatim: a markdown
    table's row, or a JSON list's statement."""
    if _ps().requirements is None:
        return ""
    if _ps().requirements.suffix == ".json":
        for item in json.loads(_ps().requirements.read_text(encoding="utf-8")):
            if item.get("id") == req:
                return item.get("statement", "")
        return ""
    for line in _ps().requirements.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"| {req} |"):
            return line.split("|")[2].strip()
    return ""


class _Ctx:
    """Everything a reference panel reads: the vendored register, the map, and the scenario's record when given."""

    def __init__(self, view: dict | None):
        T = _load_tools()
        self.T = T
        self.reg = T["register"].load_register(REGISTER)
        self.map = load_map()
        self.rows = {r["key"]: r for r in self.map["row"]}
        self.lifecycle = T["register"].load_toml(REGISTER / "metamodel" / "lifecycle.toml")
        # the export the subject names, when the register copy carries it (a copy vendored before the
        # subject's slice does not; the footprint says so)
        self.manifest = T["register"].load_toml(REGISTER / _ps().export_manifest) if _ps().export_manifest and (REGISTER / _ps().export_manifest).exists() else {}
        self.links = [dict(ln, type=rname) for rname, rel in self.reg["relationships"].items() for ln in rel["links"]]
        self.by_id = {ln["id"]: ln for ln in self.links}
        self.view = view
        self.scenario = view["scenario"] if view else None
        self.det = json.loads((Path(view["source_dir"]) / "deterministic.json").read_text(encoding="utf-8")) if view else None
        self.reg_sentences: list[dict] = []
        self.C = lambda *s: views._reg(self.reg_sentences, "controlled", *s)
        self.D = lambda *s: views._reg(self.reg_sentences, "data", *s)

    def name(self, nid):
        return self.reg["nodes"].get(nid, {}).get("name", "")

    def state(self, nid):
        return self.reg["nodes"].get(nid, {}).get("state", "")

    def state_cell(self, state):
        return _tip(state, self.C(_state_tip(state, self.lifecycle)))

    def level_cell(self, level):
        return _tip(level, self.C(LEVEL_TIP.get(level, "")))

    def link_cell(self, ln):
        return R("link", ln["id"], f"{ln['id']} ({ln['type']}, {ln.get('state')})")

    def citing(self, anchor: str) -> list:
        """The links whose evidence or external target cites the anchor (a kit path or path#section)."""
        return [ln for ln in self.links
                if any(ev == anchor or ev.startswith(anchor + "#") or ev == _ps().sys + anchor or ev.startswith(_ps().sys + anchor + "#") for ev in ln.get("evidence", []))
                or (ln.get("target_external") or "").startswith(_ps().sys + anchor)]

    def rows_anchored(self, anchor: str) -> list:
        n = _norm(anchor)
        return [r for r in self.map["row"] if _norm(r["anchor"]) == n or _norm(r["anchor"]).startswith(n + "#")]

    def level_of(self, key):
        return self.det["gate_keys"].get(key, {}).get("level", "") if self.det else ""


def _link_panel(cx: _Ctx, ln: dict) -> dict:
    C, D = cx.C, cx.D
    t = cx.reg["relationships"][ln["type"]]["type"]
    intro = C(f"A {ln['type']} link, state {ln.get('state')}, owner {ln.get('owner')}.") + " " + D(f"Rationale: {ln.get('rationale', '')}")
    ends = [["source", R("node", ln["source"]), cx.name(ln["source"]), cx.state_cell(cx.state(ln["source"]))]]
    if ln.get("target"):
        ends.append(["target", R("node", ln["target"]), cx.name(ln["target"]), cx.state_cell(cx.state(ln["target"]))])
    else:
        ends.append(["target (external)", _target_ref(ln), "", ""])
    secs = [{"heading": C("Ends"), "text": C("Each end opens its node; an external target opens its document."),
             "table": {"cols": ["role", "node", "name", "state"], "rows": ends}},
            {"heading": C("Relationship type"), "text": D(_type_tip(t)) + (" " + D(f"Note: {t['note']}") if t.get("note") else "")},
            {"heading": C(f"Evidence: {len(ln.get('evidence', []))}"), "text": C("A kit entry opens its document or requirement; an export entry is the manifest."),
             "table": {"cols": ["entry"], "rows": [[_anchor_ref(ev) if ev.startswith(_ps().sys) else ev] for ev in ln.get("evidence", [])]}}]
    appr = ln.get("approval")
    if appr:
        secs.append({"heading": C("Approval"), "text": D(f"By {appr.get('by')} on {appr.get('on')}, record {appr.get('record')}; review due {ln.get('review_due')}.")})
    else:
        secs.append({"heading": C("Approval"), "text": C("No approval is recorded, so the link is not approved.")})
    return {"title": C(f"{ln['id']}, a {ln['type']} link"), "intro": intro, "sections": secs}


def _req_panel(cx: _Ctx, req: str) -> dict | None:
    C, D = cx.C, cx.D
    line = _requirement_line(req)
    if not line:
        return None
    anchor = _ps().req_doc_anchor + req
    intro = D(f"{req}: {line}") + " " + C("The id is the experiment's; the kit's text is quoted as data.")
    secs = []
    hits = [h for h in cx.det["rules"]["R-REQ"] if h.get("req") == req] if cx.det else []
    if cx.det:
        secs.append({"heading": C(f"Rule hits in {cx.scenario}: {len(hits)}"),
                     "text": C("Each hit is one gap the rules found on this requirement.") if hits else C("The rules found no gap on this requirement in this scenario."),
                     "table": {"cols": ["kind", "declared", "key"], "rows": [[_tip(h.get("kind", ""), C(_kind_tip(h.get("kind", ""), bool(h.get("declared"))))),
                               _tip("yes" if h.get("declared") else "no", C(DECLARED_TIP["yes" if h.get("declared") else "no"])),
                               R("key", h["key"]) if h.get("key") else ""] for h in hits]}})
    citing = cx.citing(anchor)
    secs.append({"heading": C(f"Links citing it: {len(citing)}"),
                 "text": C("Each link opens its own panel.") if citing else C("No link cites it: the register does not yet carry this requirement."),
                 "table": {"cols": ["link", "type", "source", "target", "state"],
                           "rows": [[R("link", ln["id"]), ln["type"], R("node", ln["source"]), _target_ref(ln), cx.state_cell(ln.get("state", ""))] for ln in citing]}})
    rows = cx.rows_anchored(_ps().sys + anchor)
    secs.append({"heading": C(f"Map rows anchored on it: {len(rows)}"),
                 "text": C("Each row names the nodes its key concerns; the level is the gate's in this scenario.") if cx.det else C("Each row names the nodes its key concerns."),
                 "table": {"cols": ["key", "level", "nodes"], "rows": [[R("key", r["key"]), cx.level_cell(cx.level_of(r["key"])) if cx.det else "", _join([R("node", n) for n in r["nodes"]])] for r in rows]}})
    return {"title": C(f"Requirement {req}"), "intro": intro, "sections": secs}


def _key_panel(cx: _Ctx, key: str) -> dict | None:
    C, D = cx.C, cx.D
    row = cx.rows.get(key)
    if row is None:
        return None
    secs = []
    if cx.det:
        g = cx.det["gate_keys"].get(key, {})
        blocked = key in set(cx.det["D6_gate"].get("blocked_keys") or [])
        intro = C(f"In {cx.scenario} the gate holds this key at level {g.get('level', 'unknown')}" + (", and it blocks the verdict." if blocked else "."))
        secs.append({"heading": C("The gate's record"), "text": D(f"Level {g.get('level')}, {g.get('n', 0)} assertions, flags {', '.join(g.get('flags') or []) or 'none'}."),
                     "table": {"cols": ["level", "blocked"], "rows": [[cx.level_cell(g.get("level", "")), "yes" if blocked else "no"]]}})
        gv = views.gaps_view(cx.det, [])
        gaps = [r for rows in gv["groups"].values() for r in rows
                if any(c.get("id") == key for c in r.get("concerns", [])) or (r.get("assertion") or {}).get("key") == key or (r.get("sides") or {}).get("key") == key]
        secs.append({"heading": C(f"Gaps on this key: {len(gaps)}"),
                     "text": C("Each gap is one of the Gaps panel's rows.") if gaps else C("The rules found no gap on this key."),
                     "table": {"cols": ["gap", "what it says"], "rows": [[r["id"], r["text"]] for r in gaps]}})
    else:
        intro = C("No scenario is on screen, so the gate's level is not shown.")
    secs.append({"heading": C("The map row"), "text": C("The maintainer-approved reading of this key onto the register.") + " " + D(f"Note: {row.get('note', '')}"),
                 "table": {"cols": ["anchor", "nodes"], "rows": [[_anchor_ref(row["anchor"]), _join([R("node", n) for n in row["nodes"]])]]}})
    secs.append({"heading": C("Nodes named, with their states"),
                 "table": {"cols": ["node", "name", "state"], "rows": [[R("node", n), cx.name(n), cx.state_cell(cx.state(n))] for n in row["nodes"]]}})
    return {"title": C(f"Key {key}"), "intro": intro, "sections": secs}


def _doc_panel(cx: _Ctx, path: str) -> dict | None:
    C, D = cx.C, cx.D
    digest = cx.manifest.get("files", {}).get(path, "")
    if not digest:
        return None
    intro = C("A kit document the register's export carries.") + " " + D(f"Manifest digest at the register's commit: {digest[:12]}.")
    secs = []
    if cx.det and "stage2" in cx.det and path == changed_artefact(cx.scenario):
        s2 = cx.det["stage2"]
        secs.append({"heading": C("Changed in the second stage"),
                     "text": C("Every link that cites this document is a link to review.") + " "
                             + D(f"The result file records the second load ({s2['load_v2']['fragments']} new fragments, {s2['load_v2']['fragments_reused']} reused) and no document digest.")})
    citing = cx.citing(path)
    secs.append({"heading": C(f"Links citing it: {len(citing)}"),
                 "table": {"cols": ["link", "type", "source", "target", "state", "evidence"],
                           "rows": [[R("link", ln["id"]), ln["type"], R("node", ln["source"]), _target_ref(ln), cx.state_cell(ln.get("state", "")),
                                     ", ".join([ev for ev in ln.get("evidence", []) if path in ev] + ([ln["target_external"]] if path in (ln.get("target_external") or "") else []))] for ln in citing]}})
    rows = cx.rows_anchored(_ps().sys + path)
    secs.append({"heading": C(f"Map rows anchored on it: {len(rows)}"),
                 "table": {"cols": ["key", "level", "nodes"], "rows": [[R("key", r["key"]), cx.level_cell(cx.level_of(r["key"])) if cx.det else "", _join([R("node", n) for n in r["nodes"]])] for r in rows]}})
    return {"title": C(f"Document {path}"), "intro": intro, "sections": secs}


@takes_subject
def ref(kind: str, ident: str, view: dict | None = None) -> dict | None:
    """The panel a reference cell opens. node, link and doc need no scenario; req and key read the
    scenario's record when a view is given and say so when it is not. None for an unknown subject."""
    if kind not in REF_KINDS:
        return None
    cx = _Ctx(view)
    if kind == "node":
        n = cx.reg["nodes"].get(ident)
        panel = _node_panel(ident, n, cx.reg, cx.C, cx.D)["panel"] if n else None
    elif kind == "link":
        ln = cx.by_id.get(ident)
        panel = _link_panel(cx, ln) if ln else None
    elif kind == "req":
        panel = _req_panel(cx, ident)
    elif kind == "key":
        panel = _key_panel(cx, ident)
    else:
        panel = _doc_panel(cx, ident)
    if panel is None:
        return None
    return {"kind": kind, "id": ident, "scenario": cx.scenario, "panel": panel, "text_registry": cx.reg_sentences}


@takes_subject
def footprint(view: dict) -> dict:
    """The register footprint of one scenario: the map rows its keys below approved hit and the
    nodes they touch, the requirement gaps joined to the links whose evidence cites them, and
    for a stage-2 scenario the links whose evidence cites the changed artefact. Read from the scenario's
    deterministic.json (view["source_dir"]), the approved map and the vendored register."""
    cx = _Ctx(view)
    T, reg, m, det, rows, links = cx.T, cx.reg, cx.map, cx.det, cx.rows, cx.links
    names = {nid: n.get("name", "") for nid, n in reg["nodes"].items()}
    states = {nid: n.get("state", "") for nid, n in reg["nodes"].items()}
    reg_sentences = cx.reg_sentences
    C, D = cx.C, cx.D
    # keys below approved, and the nodes their rows name
    below = {k: v["level"] for k, v in det["gate_keys"].items() if v["level"] != "approved"}
    blocked = set(det["D6_gate"].get("blocked_keys") or [])
    key_rows = [(k, lvl, rows[k]) for k, lvl in below.items() if k in rows]
    touched: dict[str, list[str]] = {}
    for k, _lvl, r in key_rows:
        for nid in r["nodes"]:
            touched.setdefault(nid, []).append(k)
    not_in_copy = sorted(nid for nid in touched if nid not in states)   # the register copy predates this subject's slice
    not_approved = sorted(nid for nid in touched if nid in states and states[nid] != "approved")
    # requirement gaps joined to the links that cite them
    req_rows = []
    req_cells = []
    uncited = 0
    for h in det["rules"]["R-REQ"]:
        subject = h.get("req") or h.get("artefact") or h.get("entity") or ""
        anchor = _ps().req_anchor + subject if h.get("req") else _ps().sys + subject
        citing = [ln for ln in links if any(ev == anchor or ev.startswith(anchor + "#") for ev in ln.get("evidence", []))] if h.get("req") else []
        if not citing:
            uncited += 1
        declared = "yes" if h.get("declared") else "no"
        req_rows.append((subject, h.get("kind", ""), declared, ", ".join(f"{ln['id']} ({ln['type']}, {ln.get('state')})" for ln in citing) or "none"))
        req_cells.append([R("req", subject) if h.get("req") else (R("doc", subject) if subject in cx.manifest.get("files", {}) else subject),
                          _tip(h.get("kind", ""), C(_kind_tip(h.get("kind", ""), bool(h.get("declared"))))), _tip(declared, C(DECLARED_TIP[declared])),
                          _join([cx.link_cell(ln) for ln in citing]) or "none"])
    # a stage-2 scenario: the changed artefact and the links that cite it
    table_links = []
    table_path = changed_artefact(view["scenario"])
    if "stage2" in det and table_path:
        for ln in links:
            evs = [ev for ev in ln.get("evidence", []) if table_path in ev] + ([ln["target_external"]] if table_path in (ln.get("target_external") or "") else [])
            if evs:
                table_links.append((ln["id"], ln["type"], ln["source"], ln.get("target") or ln.get("target_external", ""), ln.get("state", ""), ", ".join(evs)))
    manifest = cx.manifest
    table_digest = manifest.get("files", {}).get(table_path, "")
    colour = "bad" if not_approved or uncited or not_in_copy else "warn" if key_rows or table_links else "ok"
    lines = [f"{views._plural(len(key_rows), 'key')} below approved {'touches' if len(key_rows) == 1 else 'touch'} {views._plural(len(touched), 'node')}" if key_rows else "no key below approved",
             f"{views._plural(len(req_rows), 'requirement gap')}, {uncited} cited by no link"]
    if table_links:
        lines.append(f"{views._plural(len(table_links), 'link cites', 'links cite')} the changed table")
    if not_approved:
        lines.append(f"{views._plural(len(not_approved), 'touched node')} not approved: {', '.join(not_approved)}")
    if not_in_copy:
        lines.append(f"{views._plural(len(not_in_copy), 'touched node')} not in the register copy: {', '.join(not_in_copy)}")
    if _ps().export_manifest and not manifest:
        lines.append("the register copy carries no export of this subject")
    approved_on = str(m["map"].get("approved_on", ""))
    intro = C((f"The footprint is the demo's reading of the gate's keys onto the register, approved by the maintainer on {approved_on}."
               if m["map"].get("status") == "approved" else
               "The footprint is the demo's reading of the gate's keys onto the register, drafted and not yet approved."),
              "A key below approved touches the nodes its map row names.",
              "A requirement gap is joined to the links whose evidence cites it.",
              "An underlined cell opens its subject's panel under the table; a dotted one explains itself on hover.",
              "Nothing here is written back to the register.")
    secs = []
    if key_rows:
        secs.append({"heading": C(f"Keys below approved: {len(key_rows)}"),
                     "text": C(f"They touch {views._plural(len(touched), 'node')}, {len(not_approved)} of them not approved.") + (" " + C("A blocked key is marked.") if blocked else ""),
                     "table": {"cols": ["key", "level", "blocked", "nodes", "anchor"],
                               "rows": [[R("key", k), cx.level_cell(lvl), "yes" if k in blocked else "", _join([R("node", n) for n in r["nodes"]]), _anchor_ref(r["anchor"])] for k, lvl, r in key_rows]}})
        secs.append({"heading": C("Nodes touched"), "text": C("Each node with its state and the keys that touch it."),
                     "table": {"cols": ["node", "name", "state", "keys"],
                               "rows": [[R("node", nid), names.get(nid, ""), cx.state_cell(states.get(nid, "")), _join([R("key", k) for k in ks])] for nid, ks in sorted(touched.items())]}})
    else:
        secs.append({"heading": C("Keys below approved: none"), "text": C("Every key the task needs is approved, so no map row is hit.")})
    secs.append({"heading": C(f"Requirement gaps and the links that cite them: {len(req_rows)}"),
                 "text": C(f"{len(req_rows) - uncited} {'is' if len(req_rows) - uncited == 1 else 'are'} cited by a link, {uncited} by none.") + (" " + C("A gap no link cites is one the register does not yet carry.") if uncited else ""),
                 "table": {"cols": ["requirement or document", "kind", "declared", "links citing it"], "rows": req_cells}})
    if "stage2" in det:
        s2cfg = _ps().subject.scenarios.get(view["scenario"], {}).get("stage2", {})
        label, short = s2cfg.get("label", "document"), s2cfg.get("short_label", s2cfg.get("label", "document"))
        secs.append({"heading": C(f"Links citing the changed {label}: {len(table_links)}"),
                     "text": C(f"The {short} changed in the second stage, so every link that cites it is a link to review.") + " "
                             + D(f"The manifest digest of {table_path} at the register's commit is {table_digest[:12]}; the result file records the second load ({det['stage2']['load_v2']['fragments']} new fragments, {det['stage2']['load_v2']['fragments_reused']} reused) and no document digest."),
                     "table": {"cols": ["link", "type", "source", "target", "state", "evidence"],
                               "rows": [[R("link", lid), _tip(ty, D(_type_tip(reg["relationships"][ty]["type"]))), R("node", src), _target_ref(cx.by_id[lid]), cx.state_cell(st),
                                         _join([_anchor_ref(ev) for ev in evs.split(", ")])] for lid, ty, src, _tg, st, evs in table_links]}})
    return {"scenario": view["scenario"], "map": {"status": m["map"].get("status"), "approved_by": m["map"].get("approved_by"), "approved_on": approved_on, "rows": len(m["row"])},
            "keys_below": {k: lvl for k, lvl, _ in key_rows}, "touched": touched, "not_approved": not_approved,
            "requirements": [{"subject": r[0], "kind": r[1], "declared": r[2], "cited_by": r[3]} for r in req_rows], "uncited": uncited,
            "table_links": [r[0] for r in table_links],
            "box": {"id": "footprint", "label": "register footprint", "colour": colour, "lines": lines + ["click for the nodes and links"]},
            "panel": {"title": C(f"Register footprint of {view['scenario']}"), "intro": intro, "sections": secs},
            "text_registry": reg_sentences}


@takes_subject
def build(today: str | None = None) -> dict:
    """The view model. ``today`` is None for the pinned date, "wall" for the wall clock,
    or an ISO date; the result says which run it is."""
    T = _load_tools()
    reg = T["register"].load_register(REGISTER)
    src = source_info()
    pinned = dt.date.fromisoformat(src["pinned_date"]) if src["pinned_date"] else None   # a checkout has none
    run_date = dt.date.today() if today == "wall" or (today is None and pinned is None) else dt.date.fromisoformat(today) if today else pinned
    findings, summary = T["check_register"].run(REGISTER, today=run_date)
    reg_sentences: list[dict] = []
    C = lambda *s: views._reg(reg_sentences, "controlled", *s)  # noqa: E731
    D = lambda *s: views._reg(reg_sentences, "data", *s)  # noqa: E731
    errors = [f for f in findings.items if f["level"] == "error"]
    warnings = [f for f in findings.items if f["level"] == "warning"]
    intro = C("The register is a copy of one commit of fdurieux/ieam-register, read only." if src["kind"] == "copy"
              else "The register is this instance's own checkout, read only.",
              "Its TOML is the record of identities, links, states, approvals and exceptions.",
              "A node is one record of one taxonomy.", "A link is one typed relationship between two nodes.",
              f"The checker ran at the wall-clock date, {run_date.isoformat()}; a checkout has no pinned date." if pinned is None
              else f"The checker ran at the pinned date, {run_date.isoformat()}." if today is None
              else f"The checker ran at today's date, {run_date.isoformat()}, which is the pinned date." if run_date == pinned
              else f"The checker ran at the wall-clock date, {run_date.isoformat()}, not the pinned date.",
              "The coverage lines are its own output, shown as data.")
    health = (C(f"The checker reports no errors and {len(warnings)} advisory warnings.") if not errors
              else C(f"The checker reports {len(errors)} errors and {len(warnings)} warnings."))
    nodes = [_node_panel(nid, n, reg, C, D) for nid, n in reg["nodes"].items()]
    # one register per organisation (ieam-register decision 0004): this subject's slice is the nodes of its
    # source system and the links that start or end on one; the rest belongs to the organisation's other subjects
    mine = {n["id"] for n in nodes if n["subject"]}
    slice_links = sum(1 for rel in reg["relationships"].values() for ln in rel["links"] if ln.get("source") in mine or ln.get("target") in mine)
    others = sorted({n["system"] for n in nodes if not n["subject"] and n["system"]})
    intro += " " + C(f"This subject's slice is the source system {_ps().system}: {len(mine)} nodes and {slice_links} links.",
                     f"The other {len(nodes) - len(mine)} nodes belong to the organisation's other subjects ({', '.join(others)})." if others
                     else "Every node is this subject's.")
    default_start = impact_default()
    by_tax: dict[str, list] = {}
    for n in nodes:
        by_tax.setdefault(n["taxonomy"], []).append(n)
    links = []
    for rname, rel in reg["relationships"].items():
        for ln in rel["links"]:
            links.append({"id": ln.get("id"), "type": rname, "source": ln.get("source"), "target": ln.get("target") or ln.get("target_external"),
                          "state": ln.get("state"), "owner": ln.get("owner"), "rationale": ln.get("rationale"), "evidence": ln.get("evidence", [])})
    rel_types = [{"name": rname, "aris_status": rel["type"].get("aris_status"), "archi_status": rel["type"].get("archi_status"),
                  "links": len(rel["links"]), "approved": sum(1 for ln in rel["links"] if ln.get("state") == "approved")}
                 for rname, rel in reg["relationships"].items()]
    exceptions = []
    for e in reg["exceptions"]:
        exceptions.append({"id": e.get("id"), "rule": e.get("rule"), "scope": e.get("scope", []), "expires": str(e.get("expires")),
                           "rationale": e.get("rationale"), "approved": {k: str(v) for k, v in (e.get("approved") or {}).items()},
                           "sentence": C(f"Exception {e.get('id')} excuses {', '.join(e.get('scope', []))} from rule {e.get('rule')} until {e.get('expires')}.")})
    matrix = T["register"].load_toml(REGISTER / "mapping" / "matrix.toml")
    mrows = matrix.get("node_kind", []) + matrix.get("relationship_type", [])
    unverified = sum(1 for r in mrows if r.get("status") == "unverified")
    matrix_sentence = (C(f"The mapping matrix has {len(mrows)} rows, and every row is unverified.") if unverified == len(mrows)
                       else C(f"The mapping matrix has {len(mrows)} rows, {unverified} of them unverified."))
    glossary = [{"term": t["term"], "meaning": t["meaning"], "forbidden": t.get("forbidden", [])} for t in reg["glossary"].get("term", [])]
    return {"source": src, "run_date": run_date.isoformat(), "pinned": today is None and pinned is not None,
            "pinned_date": pinned.isoformat() if pinned else "",
            "summary": {"nodes": summary["nodes"], "links": summary["links"], "errors": len(errors), "warnings": len(warnings)},
            "coverage": {r: summary[r] for r in ("C1", "C2", "C3")}, "coverage_lines": _coverage_lines(summary),
            "findings": findings.items, "intro": intro, "health": health,
            "subject_system": _ps().system, "slice": {"nodes": len(mine), "links": slice_links, "other_nodes": len(nodes) - len(mine), "other_systems": others},
            "impact_default": default_start,
            "nodes_by_taxonomy": by_tax, "links": links, "relationship_types": rel_types,
            "exceptions": exceptions, "matrix": {"rows": len(mrows), "unverified": unverified, "sentence": matrix_sentence},
            "glossary": glossary, "text_registry": reg_sentences}


_COMPAT = {"REQ_ANCHOR": "req_anchor", "REQ_DOC_ANCHOR": "req_doc_anchor", "SYSTEM": "system", "SYS": "sys", "REQ_ID": "req_id",
           "EXPORT_MANIFEST": "export_manifest", "REQUIREMENTS": "requirements", "SUBJECT": "subject"}


def __getattr__(name: str):
    """The names this module once filled at import, read from the current subject when asked for."""
    if name in _COMPAT:
        return getattr(_ps(), _COMPAT[name])
    raise AttributeError(f"module 'register_view' has no attribute {name!r}")
