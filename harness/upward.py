"""The upward joins with no store (task-0143, doc-0020 C2): a knowledge key to the register nodes it
concerns, and a code path to its application, the keys its header cites and its trace ledger entry.

    python harness/upward.py key KEY
    python harness/upward.py code PATH [--instance DIR] [--ledger FILE]
    python harness/upward.py doc DOCUMENT

Two single hops, each read from files, never a walk and never the store:

``key_nodes``  the rows of the subject's ``register_map.toml`` whose key is KEY, each with the register
               nodes it names (taxonomy, kind, name, state, owner, from the register ``KG_REGISTER``
               holds), the row's owner, anchor and note. A key the subject knows (a map row or a task's
               key) with no row reads ``mapped: false``; a key it does not know is refused.
``code_path``  for PATH, relative to the root of the instance's ``code_map.toml``: the application or
               module the map assigns (``code_map.app_of``) and that node in the register, the keys
               the file's header cites (``citation.read``), each flagged when the subject does not know
               it, and the trace ledger's entry for the path (``trace.read_ledger``: derived id, keys
               used, statements, commit, digest, and the file's digest now). Each of the three legs
               says ``read`` or ``unchecked`` with the reason: no instance configured, no code map or
               one that does not hold, no ledger configured, missing or malformed; the ledger leg also
               when it holds an entry but there is no code root to read the file's digest from, never
               ``drift: false`` for a file not looked at (doc-0030 M7). Unchecked is never
               empty: ``app``, ``keys`` and ``entry`` are null then, and an empty list or a null entry
               under ``read`` means the file cites nothing or the ledger holds no entry for it.

``document_links``  the register links whose evidence cites DOCUMENT (a path of the subject's export
               manifest; the subject's prefix, ``kit:``, and an ``#anchor`` may be given), each with the
               evidence anchor, the link's type, state and owner, and the nodes at both ends with their
               owning units: what the Browser's ``register-cites`` query joins, from the register's
               files. A document the manifest does not hold is refused.

Configuration (the MCP server's, read once at its start): the instance is ``--instance`` or
``KG_INSTANCE``, the ledger ``--ledger`` or ``KG_LEDGER``, the same variables the CI wrappers map
(``instance/ci/knowgov-gate.sh``). PATH must stay inside the code map's root: an absolute path, a
``..`` segment or a link out of it is refused, so the tool reads only the instance's code headers.

Then the chain up composes: ``code_path`` names the application; ``register_impact walk=dependants``
from it (with ``children`` for an application whose modules carry its links) reaches the processes and
capabilities; ``register_nodes node=`` names a capability's ancestors. Standard library only; reads,
never writes. Reports pinned by ``harness/schemas/key-nodes.schema.json``, ``code-path.schema.json`` and
``document-links.schema.json``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import citation  # noqa: E402
import code_map  # noqa: E402
import register_impact as ri  # noqa: E402

SCHEMA_VERSION = 1
LEDGER_FIELDS = ("id", "path", "app", "sha256", "commit", "repo", "kind", "task", "assertions", "keys", "as_of")


class UpwardError(ValueError):
    """The question cannot be answered: an unknown key, a malformed or escaping path."""


def config(instance: str | Path | None = None, ledger: str | Path | None = None) -> dict:
    """The instance and the ledger the code leg reads: the arguments, else KG_INSTANCE and KG_LEDGER,
    else none (the leg then reads unchecked)."""
    inst = instance or os.environ.get("KG_INSTANCE") or None
    led = ledger or os.environ.get("KG_LEDGER") or None
    return {"instance": str(Path(inst).resolve()) if inst else None, "ledger": str(Path(led).resolve()) if led else None}


def _known() -> set[str]:
    import trace
    return trace.known_keys()


def _node(reg: dict, nid: str) -> dict:
    n = reg["nodes"].get(nid)
    if n is None:
        return {"id": nid, "taxonomy": None, "kind": None, "name": None, "state": None, "owner": None, "missing": True}
    return {"id": nid, "taxonomy": n.get("_taxonomy"), "kind": n.get("kind"), "name": n.get("name", ""),
            "state": n.get("state", ""), "owner": n.get("owner")}


def key_nodes(key, root: Path | None = None) -> dict:
    """The map rows on ``key`` with their register nodes; UpwardError on a key the subject does not know."""
    from subject import SUBJECT
    import key_rule
    key = key_rule.normalise(key)   # task-0301: the NFC form the register map's rows hold
    if not isinstance(key, str) or "|" not in key:
        raise UpwardError(f"key {key!r}: an entity|attribute key, as store_status and register_impact name them")
    if key not in _known():
        raise UpwardError(f"{key}: no key of {SUBJECT.id} (its register map's rows and its tasks' keys)")
    root = (root or ri.register_root()).resolve()
    reg = ri.load_tools(root)["register"].load_register(root)
    rows = [{"nodes": [_node(reg, x) for x in (r.get("nodes") or [])], "owner": r.get("owner"),
             "anchor": r.get("anchor"), "note": r.get("note", "")}
            for r in SUBJECT.register_map().get("row", []) if r.get("key") == key]
    return {"schema_version": SCHEMA_VERSION, "tool": "key_nodes", "subject": SUBJECT.id, "key": key,
            "register": ri.source(root), "mapped": bool(rows), "rows": rows,
            "nodes": sorted({n["id"] for r in rows for n in r["nodes"]})}


def _system() -> tuple[str, str]:
    """The prefix the subject's evidence anchors carry (``kit:``, ``jef_kit:``) and its export manifest:
    the subject's ``[register]`` table, read as the page's projection reads it (``page_subject``)."""
    from subject import SUBJECT
    anchor = SUBJECT.register.get("requirement_anchor", "")
    return (anchor.split(":", 1)[0] if ":" in anchor else "kit") + ":", SUBJECT.register.get("export_manifest", "")


def doc_key(anchor: str, files: dict, system: str) -> str | None:
    """The manifest key an evidence anchor names: the prefix and the #anchor dropped, then the path as
    written or under ``kit/`` (``demo/app/register_project._doc_key``'s rule; a test holds them equal)."""
    a = anchor[len(system):] if anchor.startswith(system) else anchor
    a = a.split("#", 1)[0]
    for key in (a, "kit/" + a):
        if key in files:
            return key
    return None


def document_links(document, root: Path | None = None) -> dict:
    """The register links whose evidence cites ``document`` (a path of the subject's export manifest, with
    or without the subject's prefix or an #anchor), each with its anchor and the nodes at both ends and
    their owners; UpwardError on a document neither the manifest holds nor a link cites."""
    from subject import SUBJECT
    if not isinstance(document, str) or not document.strip():
        raise UpwardError(f"document {document!r}: a document path, as the subject's export manifest names it")
    root = (root or ri.register_root()).resolve()
    T = ri.load_tools(root)
    reg = T["register"].load_register(root)
    system, manifest_rel = _system()
    manifest = T["register"].load_toml(root / manifest_rel) if manifest_rel and (root / manifest_rel).is_file() else {}
    files = manifest.get("files", {})
    key = doc_key(document if document.startswith(system) else system + document, files, system)
    links = []
    for rname, rel in reg["relationships"].items():
        for ln in rel["links"]:
            for ev in ln.get("evidence", []):
                if not ev.startswith(system) or doc_key(ev, files, system) != key or key is None:
                    continue
                tgt = ln.get("target")
                links.append({"id": ln["id"], "type": rname, "state": ln.get("state", ""), "owner": ln.get("owner"),
                              "evidence": ev, "anchor": ev.split("#", 1)[1] if "#" in ev else None,
                              "source": {**_node(reg, ln["source"]), "owning_unit": ri.owning_unit(reg, ln["source"])},
                              "target": None if not tgt else {**_node(reg, tgt), "owning_unit": ri.owning_unit(reg, tgt)},
                              "target_external": ln.get("target_external")})
    if key is None:
        raise UpwardError(f"{document}: no document of {SUBJECT.id}'s export manifest ({manifest_rel or 'none named'}) "
                          f"under the prefix {system}")
    links.sort(key=lambda x: (x["id"], x["evidence"]))
    return {"schema_version": SCHEMA_VERSION, "tool": "document_links", "subject": SUBJECT.id, "document": key,
            "system": system, "export_manifest": manifest_rel, "digest": files.get(key, ""), "register": ri.source(root),
            "links": links, "nodes": sorted({x["id"] for ln in links for x in (ln["source"], ln["target"]) if x})}


def _rel(path) -> str:
    if not isinstance(path, str) or not path or "\\" in path or "\0" in path:
        raise UpwardError(f"path {path!r}: a '/'-separated path relative to the code map's root")
    p = PurePosixPath(path)
    if p.is_absolute() or ".." in p.parts:
        raise UpwardError(f"path {path!r}: relative to the code map's root, without '..'")
    return p.as_posix()


def _unchecked(reason: str, **extra) -> dict:
    return {"status": "unchecked", "reason": reason, **extra}


def code_path(path, cfg: dict | None = None) -> dict:
    """The three legs for ``path``: the code map's application, the header's keys, the ledger's entry."""
    rel = _rel(path)
    cfg = cfg if cfg is not None else config()
    out = {"schema_version": SCHEMA_VERSION, "tool": "code_path", "path": rel,
           "instance": cfg["instance"], "ledger_file": cfg["ledger"]}
    file = None
    no_root = None   # why there is no code root to read the file from, when there is none (doc-0030 M7)
    if cfg["instance"] is None:
        no_root = why = "no instance configured (KG_INSTANCE or --instance)"
        out["code_map"] = _unchecked(why, app=None, node=None)
        out["citation"] = _unchecked(why + ", so no code root to read the file from", keys=None)
    else:
        inst = Path(cfg["instance"])
        errors: list[str] = []
        rep = code_map.code_map(inst, code_map.register_apps(inst / "register"), errors) if inst.is_dir() else None
        if rep is None or errors:
            why = (f"no instance at {inst}" if not inst.is_dir() else f"{inst}/code_map.toml: missing" if rep is None
                   else "code_map.toml does not hold: " + "; ".join(errors))
            no_root = why
            out["code_map"] = _unchecked(why, app=None, node=None)
            out["citation"] = _unchecked(why + ", so no code root to read the file from", keys=None)
        else:
            croot = (inst / rep["root"]).resolve()
            target = (croot / rel).resolve()
            if not target.is_relative_to(croot):
                raise UpwardError(f"path {rel!r}: resolves outside the code map's root")
            app = code_map.app_of(rep, rel)
            reg_root = ri.register_root().resolve()
            reg = ri.load_tools(reg_root)["register"].load_register(reg_root)
            out["code_map"] = {"status": "read", "root": rep["root"], "is_code": code_map.is_code(rep, rel), "app": app,
                               "node": None if app is None else _node(reg, app),
                               "rows": [{"glob": r["glob"], "app": r["app"], "note": r["note"]}
                                        for r in rep["rows"] if code_map.glob_re(r["glob"]).match(rel)],
                               "citations_required": rep["citations"]["require"] and app in rep["citations"]["apps"]}
            file = target if target.is_file() else None
            if file is None:
                out["citation"] = _unchecked(f"no file {rel} under the code map's root", keys=None)
            elif citation.language(file) is None:
                out["citation"] = _unchecked(f"{citation.MARK} covers {', '.join(sorted(citation.COMMENT))} files, not this one",
                                             keys=None)
            else:
                try:
                    keys = citation.read(file)
                except citation.Malformed as e:
                    out["citation"] = _unchecked(f"malformed citation: {e}", keys=None, malformed=True)
                else:
                    known = _known()
                    out["citation"] = {"status": "read", "keys": keys, "unknown": [k for k in keys if k not in known]}
    out["ledger"] = _ledger(cfg["ledger"], rel, file, no_root)
    return out


def _ledger(ledger: str | None, rel: str, file: Path | None, no_root: str | None = None) -> dict:
    """The ledger's entry for ``rel`` with the file's digest now. With no code root (``no_root``, the reason)
    the file was never looked at, so an entry the ledger holds cannot say whether it drifted: the leg reads
    unchecked rather than ``drift: false`` (doc-0030 M7, task-0208)."""
    import trace
    if ledger is None:
        return _unchecked("no ledger configured (KG_LEDGER or --ledger)", entry=None)
    import formats
    try:
        led = trace.read_ledger(Path(ledger), missing_ok=False)
    except trace.CannotRun as e:
        return _unchecked(str(e), entry=None)
    except formats.FormatError as e:   # task-0280: a ledger for a newer knowgov is refused, never read as unchecked
        raise UpwardError(str(e)) from None
    hit = [e for e in led["entries"] if e.get("path") == rel]
    if not hit:
        return {"status": "read", "entries": len(led["entries"]), "entry": None}
    if no_root is not None:
        return _unchecked(f"{no_root}, so no code root to read the file from: the ledger holds an entry for {rel}, "
                          "but its drift cannot be read", entries=len(led["entries"]), entry=None)
    e = {k: hit[-1][k] for k in LEDGER_FIELDS if k in hit[-1]}
    cur = hashlib.sha256(file.read_bytes()).hexdigest() if file is not None else None
    return {"status": "read", "entries": len(led["entries"]),
            "entry": {**e, "current_sha256": cur, "drift": cur is not None and cur != e["sha256"], "file_present": file is not None}}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="upward.py", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    k = sub.add_parser("key", help="a key's register nodes, from register_map.toml")
    k.add_argument("key")
    c = sub.add_parser("code", help="a code path's application, cited keys and ledger entry")
    c.add_argument("path")
    c.add_argument("--instance", help="the instance (default: KG_INSTANCE)")
    c.add_argument("--ledger", help="the trace ledger (default: KG_LEDGER)")
    d = sub.add_parser("doc", help="the register links whose evidence cites a document")
    d.add_argument("document")
    a = ap.parse_args(argv)
    try:
        ri.require()   # task-0279: a register that cannot be read is a cannot-run, named, never a traceback
    except ri.RegisterUnreadable as e:
        print(f"upward: cannot run: {e}", file=sys.stderr)
        return 2
    try:
        rep = (key_nodes(a.key) if a.cmd == "key" else document_links(a.document) if a.cmd == "doc"
               else code_path(a.path, config(a.instance, a.ledger)))
    except UpwardError as e:
        print(f"upward: {e}", file=sys.stderr)
        return 2
    print(json.dumps(rep, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
