"""The register projected into the demo's Neo4j, in its own namespace, at the vendored tag.

Derived, rebuilt on demand, never the record (docs/ieam-register-demo-integration.md §3.5).
The harness's labels (Artefact, Version, Fragment, Entity, Assertion, Activity, Agent,
Verification, Approval, Gap, Derived) stay untouched: every projected node carries the label
Register plus one of RegNode, RegLink, RegType, RegException, RegDocument, RegExternal, and
every relationship is REG_<NAME>. Every node and relationship carries the tag, the commit,
the export date, the digest of the TOML file it came from and the load time. A deterministic
run wipes the whole store ("first deletes everything in the store"), so the projection
vanishes with it and is loaded again on demand; loading deletes only the Register namespace.
The loader derives nothing: no inferred edge, no coverage verdict; those stay the checker's.
"""
from __future__ import annotations

import datetime as dt
import hashlib
from pathlib import Path

import register_view

REGISTER = register_view.REGISTER
NODE_LABELS = ("RegNode", "RegLink", "RegType", "RegException", "RegDocument", "RegExternal")


def _iso(v) -> str:
    return v.isoformat() if hasattr(v, "isoformat") else ("" if v is None else str(v))


def _digest(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _approval(a: dict | None) -> dict:
    a = a or {}
    return {"approval_by": a.get("by", ""), "approval_on": _iso(a.get("on")), "approval_record": a.get("record", "")}


def _doc_key(anchor: str, files: dict) -> str | None:
    """The manifest key a kit evidence anchor names: kit:requirements.md#REQ-05 is the manifest's
    kit/requirements.md, kit:contract/decision_table.md#DT-P its contract/decision_table.md."""
    a = anchor[4:] if anchor.startswith("kit:") else anchor
    a = a.split("#", 1)[0]
    for key in (a, "kit/" + a):
        if key in files:
            return key
    return None


@register_view.takes_subject
def rows(loaded_at: str | None = None) -> dict:
    """Every node and relationship row of the projection, as flat property maps (strings, numbers,
    booleans and lists of strings only: what a store property can hold), with the counts."""
    T = register_view._load_tools()
    reg = T["register"].load_register(REGISTER)
    src = register_view.source_info()
    manifest = T["register"].load_toml(REGISTER / register_view._ps().export_manifest)   # the export the current subject names, read per call (task-0032.01)
    files = manifest.get("files", {})
    stamp = {"tag": src["tag"], "commit": src["commit"], "export_date": _iso(manifest.get("exported_on"))[:10],
             "loaded_at": loaded_at or dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    nodes, parents, owners = [], [], []
    for nid, n in reg["nodes"].items():
        nodes.append({"reg_id": nid, "taxonomy": n["_taxonomy"], "kind": n.get("kind", ""), "name": n.get("name", ""),
                      "state": n.get("state", ""), "owner": n.get("owner", ""), "parent": n.get("parent", ""),
                      "review_due": _iso(n.get("review_due")), **_approval(n.get("approval")), "digest": _digest(n["_path"]), **stamp})
        if n.get("parent"):
            parents.append({"child": nid, "parent": n["parent"]})
        if n.get("owner") in reg["nodes"]:
            owners.append({"owner": n["owner"], "node": nid})
    types, links, typed, maps_to, link_of, of_type, cites = [], [], {}, [], [], [], []
    externals: dict[str, dict] = {}
    for rname, rel in reg["relationships"].items():
        t = rel["type"]
        types.append({"reg_id": rname, "source_kind": list(t.get("source_kind", [])), "target_kind": list(t.get("target_kind", [])),
                      "direction": t.get("direction", ""), "inverse_label": t.get("inverse_label", ""), "owner": t.get("owner", ""),
                      "evidence_class": t.get("evidence_class", ""), "aris_status": t.get("aris_status", ""), "archi_status": t.get("archi_status", ""),
                      "note": t.get("note", ""), "digest": _digest(rel["_path"]), **stamp})
        for ln in rel["links"]:
            props = {"reg_id": ln["id"], "type": rname, "state": ln.get("state", ""), "owner": ln.get("owner", ""),
                     "mode": ",".join(ln.get("mode", [])), **_approval(ln.get("approval")), "derived": False, "rule": "", **stamp}
            links.append({**props, "source": ln["source"], "target": ln.get("target", ""), "target_external": ln.get("target_external", ""),
                          "rationale": ln.get("rationale", ""), "evidence": list(ln.get("evidence", [])), "review_due": _iso(ln.get("review_due")),
                          "digest": _digest(rel["_path"])})
            link_of.append({"reg_id": ln["id"], "node": ln["source"], "role": "source"})
            of_type.append({"reg_id": ln["id"], "type": rname})
            if ln.get("target"):
                typed.setdefault("REG_" + rname.upper(), []).append({"source": ln["source"], "target": ln["target"], "props": props})
                link_of.append({"reg_id": ln["id"], "node": ln["target"], "role": "target"})
            else:
                ext = ln.get("target_external", "")
                externals.setdefault(ext, {"reg_id": ext, "path": _doc_key(ext, files) or "", "digest": files.get(_doc_key(ext, files) or "", ""), **stamp})
                maps_to.append({"source": ln["source"], "external": ext, "props": props})
            for ev in ln.get("evidence", []):
                key = _doc_key(ev, files) if ev.startswith("kit:") else None
                if key:
                    cites.append({"reg_id": ln["id"], "path": key, "anchor": ev})
    documents = [{"reg_id": key, "path": key, "digest": sha, **stamp} for key, sha in files.items()]
    exceptions, excepts = [], []
    for e in reg["exceptions"]:
        a = e.get("approved") or {}
        exceptions.append({"reg_id": e["id"], "rule": e.get("rule", ""), "scope": list(e.get("scope", [])), "rationale": e.get("rationale", ""),
                           "expires": _iso(e.get("expires")), "approval_by": a.get("by", ""), "approval_on": _iso(a.get("on")),
                           "approval_record": a.get("record", ""), "digest": _digest(e["_path"]), **stamp})
        for nid in e.get("scope", []):
            excepts.append({"reg_id": e["id"], "node": nid, "rule": e.get("rule", ""), "expires": _iso(e.get("expires"))})
    out = {"stamp": stamp, "nodes": nodes, "types": types, "links": links, "documents": documents, "externals": list(externals.values()),
           "exceptions": exceptions, "parents": parents, "owners": owners, "typed": typed, "maps_to": maps_to, "link_of": link_of,
           "of_type": of_type, "cites": cites, "excepts": excepts}
    out["counts"] = {"nodes": len(nodes), "links": len(links), "types": len(types), "documents": len(documents), "externals": len(externals),
                     "exceptions": len(exceptions),
                     "relationships": sum(len(v) for v in typed.values()) + len(maps_to) + len(link_of) + len(of_type) + len(cites)
                     + len(parents) + len(owners) + len(excepts)}
    return out


def project(store) -> dict:
    """Load the projection through the store port and return its census. Raises on an
    unreachable store or a missing driver; the caller turns that into a status code."""
    r = rows()
    with store as s:
        s.project_register(r)
        out = s.register_census()
    out["counts"] = r["counts"]
    return out
