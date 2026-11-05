"""The upward joins with no store (task-0143, doc-0020 C2): a knowledge key to the register nodes it
concerns, and a code path to its application, the keys its header cites and its trace ledger entry.

    python harness/upward.py key KEY
    python harness/upward.py code PATH [--instance DIR] [--ledger FILE]

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
               one that does not hold, no ledger configured, missing or malformed. Unchecked is never
               empty: ``app``, ``keys`` and ``entry`` are null then, and an empty list or a null entry
               under ``read`` means the file cites nothing or the ledger holds no entry for it.

Configuration (the MCP server's, read once at its start): the instance is ``--instance`` or
``KG_INSTANCE``, the ledger ``--ledger`` or ``KG_LEDGER``, the same variables the CI wrappers map
(``instance/ci/knowgov-gate.sh``). PATH must stay inside the code map's root: an absolute path, a
``..`` segment or a link out of it is refused, so the tool reads only the instance's code headers.

Then the chain up composes: ``code_path`` names the application; ``register_impact walk=dependants``
from it (with ``children`` for an application whose modules carry its links) reaches the processes and
capabilities; ``register_nodes node=`` names a capability's ancestors. Standard library only; reads,
never writes. Reports pinned by ``harness/schemas/key-nodes.schema.json`` and ``code-path.schema.json``.
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
    if cfg["instance"] is None:
        why = "no instance configured (KG_INSTANCE or --instance)"
        out["code_map"] = _unchecked(why, app=None, node=None)
        out["citation"] = _unchecked(why + ", so no code root to read the file from", keys=None)
    else:
        inst = Path(cfg["instance"])
        errors: list[str] = []
        rep = code_map.code_map(inst, code_map.register_apps(inst / "register"), errors) if inst.is_dir() else None
        if rep is None or errors:
            why = (f"no instance at {inst}" if not inst.is_dir() else f"{inst}/code_map.toml: missing" if rep is None
                   else "code_map.toml does not hold: " + "; ".join(errors))
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
    out["ledger"] = _ledger(cfg["ledger"], rel, file)
    return out


def _ledger(ledger: str | None, rel: str, file: Path | None) -> dict:
    import trace
    if ledger is None:
        return _unchecked("no ledger configured (KG_LEDGER or --ledger)", entry=None)
    try:
        led = trace.read_ledger(Path(ledger), missing_ok=False)
    except trace.CannotRun as e:
        return _unchecked(str(e), entry=None)
    hit = [e for e in led["entries"] if e.get("path") == rel]
    if not hit:
        return {"status": "read", "entries": len(led["entries"]), "entry": None}
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
    a = ap.parse_args(argv)
    try:
        rep = key_nodes(a.key) if a.cmd == "key" else code_path(a.path, config(a.instance, a.ledger))
    except UpwardError as e:
        print(f"upward: {e}", file=sys.stderr)
        return 2
    print(json.dumps(rep, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
