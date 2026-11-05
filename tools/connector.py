"""The connector for a system of record (task-0063): an export read into an instance's register as a
dated, append-only mirror, in ieam-register's own export format (its exports/README.md).

    python tools/connector.py <instance> --system <name> <export>... [--exported-on DATE] [--json]

<export> is a folder (every file under it) or files. The system is named only by the instance: a
[system.<name>] table in <instance>/connectors.toml, and the same name in the register's
metamodel/sources.toml. Nothing here defaults a system.

    [system.<name>]
    id_attribute = "AT_ID"   # the AML attribute that carries the register id (the default)

The export lands in <instance>/register/exports/<name>/<date>/: its files byte for byte, a
MANIFEST.toml in ieam-register's format (decision-0010, task-0138): exported_on, source,
source_version, tool, tool_version, previous, a sha256 per file, and [ids], every AML object the
export holds keyed by its GUID (the system's id_field, aris_guid for ARIS) with its name, whether or
not it carries a register id; beside them, knowgov's own tables, never mixed into [ids]:
[register_ids], GUID -> register id for the objects that carry one, and [bpmn_ids], register id ->
name for the ids a BPMN file carries (a BPMN part has no GUID, so it adds nothing to [ids]).
A RECONCILE.json is written by ieam-register's own tools/reconcile.py, imported from the vendored
copy: files and ids (by GUID) added, updated or renamed, deleted against the previous folder;
stale_nodes, the nodes whose [source] GUID the export no longer carries; unregistered (its decision
0017, v0.2.10), the objects no node's [source] carries. Two additions read the register-id tables:
a register node whose id the previous export carried and this one does not is stale too (redundant
once the instance's nodes carry [source] aris_guid, when the register's own rule finds it), and a
carried register id the register does not hold is listed under unknown_ids. A stale node is a finding: the connector never
deletes or edits a node, never removes or rewrites a folder, and refuses (exit 1) a date that is
not after the newest folder already there. Exit 0 landed, 1 refused, 2 cannot run.

Identity, from three places only (task-0119's evidence of what survives an ARIS round trip):
  AML    the configured attribute of an ObjDef (its GUID recorded beside it);
  BPMN   a process's @id and an element's <documentation> text, when either is a register id.
Element ids, DI coordinates and any extension attribute are never identity. Namespaces are
matched by URI, never by prefix. The ARIS dialect of BPMN is told by its URIs; it reads the same.
The date is --exported-on, else the AML header's CreateDate and CreateTime; the wall clock never.
Standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tomllib
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ID_ATTRIBUTE = "AT_ID"
CONFIG = "connectors.toml"
REGISTER_ID = re.compile(r"[A-Z][A-Z0-9]*-\d+")
BPMN_MODEL = "http://www.omg.org/spec/BPMN/20100524/MODEL"
# ARIS's own namespaces (a real 10.0 export's): a file declaring one is in ARIS's BPMN dialect
ARIS_DIALECT = ("http://www.softwareag.com/aris/attributes", "http://www.softwareag.com/aris/ebpmn")
# what the BPMN reader takes a name and a documentation from: flow nodes of any kind, by URI
_DOC = f"{{{BPMN_MODEL}}}documentation"


class Refused(Exception):
    """The connector will not land this export (exit 1)."""


def _register_tool(name: str):
    """One of ieam-register's own tools, imported from the vendored copy (import, never copy)."""
    path = ROOT / "demo" / "register" / "tools" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"ieam_register_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


REG = _register_tool("register")
REC = _register_tool("reconcile")   # its comparison, run on the folder as it lands (task-0121)


# ---- configuration ----

def system_config(instance: Path, system: str) -> dict:
    p = instance / CONFIG
    if not p.is_file():
        raise FileNotFoundError(f"{p}: no connector configuration; the instance names its systems there")
    cfg = tomllib.loads(p.read_text(encoding="utf-8")).get("system", {})
    if system not in cfg:
        raise Refused(f"{p}: no [system.{system}]; configured: {', '.join(sorted(cfg)) or 'none'}")
    out = dict(cfg[system])
    out.setdefault("id_attribute", DEFAULT_ID_ATTRIBUTE)
    return out


# ---- readers ----

def _text(el) -> str:
    return (el.text or "").strip() if el is not None else ""


def read_aml(data: bytes, id_attribute: str) -> dict:
    """{ids: {register id: name}, guids: {GUID: register id}, objects: {GUID: name}, version,
    exported}. objects is every ObjDef with a GUID, register id or not (decision-0010). The AML file
    has no namespace (its DTD is ARIS-Export.dtd); every ObjDef is read wherever its group nests it."""
    root = ET.fromstring(data)
    if root.tag != "AML":
        raise ValueError("not an AML file")
    ids, guids, objects = {}, {}, {}
    for o in root.iter("ObjDef"):
        attrs = {}
        for a in o.findall("AttrDef"):
            vals = [_text(v) for v in a.findall("AttrValue") if _text(v)]
            if vals:
                attrs.setdefault(a.get("AttrDef.Type"), vals[0])
        name = attrs.get("AT_NAME", "")
        g = _text(o.find("GUID"))
        if g:
            if g in objects:
                raise Refused(f"{g}: two objects carry this GUID")
            objects[g] = name
        rid = attrs.get(id_attribute, "")
        if not REGISTER_ID.fullmatch(rid):
            continue
        if rid in ids and ids[rid] != name:
            raise Refused(f"{rid}: two objects carry it, named {ids[rid]!r} and {name!r}")
        ids[rid] = name
        if g:
            guids[g] = rid
    h = root.find("Header-Info")
    exported = None
    if h is not None and h.get("CreateDate"):
        exported = f"{h.get('CreateDate')}T{h.get('CreateTime') or '00:00:00'}Z"
    version = h.get("ArisExeVersion", "") if h is not None else ""
    return {"ids": ids, "guids": guids, "objects": objects, "version": version, "exported": exported}


def read_bpmn(data: bytes) -> dict:
    """{ids: {register id: name}, guids: {}, version, dialect}: a process's @id, an element's
    <documentation>, when either is a register id; nothing else."""
    uris = {uri for _, (_, uri) in ET.iterparse(io.BytesIO(data), events=("start-ns",))}
    root = ET.fromstring(data)
    if root.tag != f"{{{BPMN_MODEL}}}definitions":
        raise ValueError("not a BPMN 2.0 model")
    ids = {}

    def carry(rid: str, name: str, where: str):
        if rid in ids and ids[rid] != name:
            raise Refused(f"{rid}: {where} names it {name!r}, another element {ids[rid]!r}")
        ids[rid] = name
    for proc in root.iter(f"{{{BPMN_MODEL}}}process"):
        pid = proc.get("id", "")
        if REGISTER_ID.fullmatch(pid):
            carry(pid, proc.get("name", ""), "a process")
        for el in proc.iter():
            if el is proc:
                continue
            for d in el.findall(_DOC):
                if REGISTER_ID.fullmatch(_text(d)):
                    carry(_text(d), el.get("name", ""), "an element")
    dialect = "aris" if uris & set(ARIS_DIALECT) else "bpmn"
    version = " ".join(x for x in (root.get("exporter", ""), root.get("exporterVersion", "")) if x)
    return {"ids": ids, "guids": {}, "objects": {}, "version": version, "dialect": dialect, "exported": None}


def read_file(data: bytes, id_attribute: str) -> tuple[str, dict]:
    """(format, reading) for an AML or a BPMN file, told by its root element; Refused otherwise."""
    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        raise Refused(f"not XML: {e}") from None
    if root.tag == "AML":
        return "aml", read_aml(data, id_attribute)
    if root.tag == f"{{{BPMN_MODEL}}}definitions":
        return "bpmn", read_bpmn(data)
    raise Refused(f"neither AML nor BPMN 2.0 (root {root.tag})")


# ---- the mirror ----

def _files(export: list[Path]) -> dict[str, Path]:
    out = {}
    for e in export:
        if e.is_dir():
            for p in sorted(e.rglob("*")):
                if p.is_file():
                    out[p.relative_to(e).as_posix()] = p
        elif e.is_file():
            out[e.name] = e
        else:
            raise FileNotFoundError(e)
    if not out:
        raise Refused("the export holds no file")
    return out


def read_export(export: list[Path], id_attribute: str) -> dict:
    """What an export carries: files (relative path -> bytes, sha256), ids (register id -> name),
    guids (GUID -> register id), objects (GUID -> name, every AML object), bpmn_ids (register id ->
    name, as the BPMN files carry them), versions, the AML's export time; AML names win over BPMN
    names for one id (an id's name is the AML's)."""
    files = _files(export)
    out = {"files": {}, "digests": {}, "ids": {}, "guids": {}, "objects": {}, "bpmn_ids": {},
           "versions": [], "exported": None, "conflicts": []}
    readings = []
    for rel, p in files.items():
        data = p.read_bytes()
        try:
            fmt, r = read_file(data, id_attribute)
        except Refused as e:
            raise Refused(f"{rel}: {e}") from None
        out["files"][rel], out["digests"][rel] = data, hashlib.sha256(data).hexdigest()
        readings.append((0 if fmt == "aml" else 1, rel, r))
    for fmt, rel, r in sorted(readings, key=lambda t: (t[0], t[1])):
        if fmt == 1:
            for rid, name in r["ids"].items():
                out["bpmn_ids"].setdefault(rid, name)
        for g, name in r["objects"].items():
            if g in out["objects"] and out["objects"][g] != name:
                raise Refused(f"{rel}: {g}: two objects carry this GUID")
            out["objects"][g] = name
        for rid, name in r["ids"].items():
            if rid in out["ids"] and out["ids"][rid] != name:
                out["conflicts"].append({"id": rid, "kept": out["ids"][rid], "file": rel, "name": name})
                continue
            out["ids"].setdefault(rid, name)
        out["guids"].update(r["guids"])
        if r["version"] and r["version"] not in out["versions"]:
            out["versions"].append(r["version"])
        out["exported"] = out["exported"] or r["exported"]
    return out


def _exported_on(given: str | None, read: str | None) -> str:
    s = given or read
    if not s:
        raise Refused("no export time: the export carries none (no AML header); pass --exported-on")
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        s += "T00:00:00Z"
    t = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _q(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)   # a TOML basic string: JSON's escapes are TOML's


def manifest_text(m: dict) -> str:
    lines = [f"exported_on = {m['exported_on']}", f"source = {_q(m['source'])}",
             f"source_version = {_q(m['source_version'])}", f"tool = {_q(m['tool'])}",
             f"tool_version = {_q(m['tool_version'])}", f"previous = {_q(m['previous'])}",
             "# Written by the connector (task-0063, decision-0010). [ids] is every object the export holds,",
             "# keyed by its GUID, with its name (ieam-register's format); [register_ids] the register id of",
             "# each object that carries one; [bpmn_ids] each register id a BPMN file carries, with its name.",
             "# Never edited by hand.", "", "[files]"]
    lines += [f"{_q(k)} = {_q(v)}" for k, v in sorted(m["files"].items())]
    lines += ["", "[ids]"] + [f"{_q(k)} = {_q(v)}" for k, v in sorted(m["ids"].items())]
    lines += ["", "[register_ids]"] + [f"{_q(k)} = {_q(v)}" for k, v in sorted(m["register_ids"].items())]
    lines += ["", "[bpmn_ids]"] + [f"{_q(k)} = {_q(v)}" for k, v in sorted(m["bpmn_ids"].items())]
    return "\n".join(lines) + "\n"


def carried_register_ids(man: dict) -> set[str]:
    """The register ids a MANIFEST says its export carries: [register_ids] values and [bpmn_ids]
    keys; a folder landed before decision-0010 (a [guids] table, [ids] keyed by register id), its
    [ids] keys."""
    if "guids" in man and "register_ids" not in man:
        return set(man.get("ids", {}))
    return set(man.get("register_ids", {}).values()) | set(man.get("bpmn_ids", {}))


def reconcile(reg_root: Path, landing: Path, folder: str, man: dict) -> dict:
    """ieam-register's reconcile.py on the folder as it lands (its comparison by GUID, its stale
    rule, its unregistered list, imported), named as the folder it becomes; plus the connector's
    additions, read from the register-id tables: a register id the previous export carried and this
    one does not is stale, and a carried register id the register lacks is listed."""
    out = REC.reconcile(landing, root=reg_root)
    out["folder"] = folder
    stale = {n["id"]: n for n in out["stale_nodes"]}
    reg = REG.load_register(reg_root)
    now = carried_register_ids(man)
    if out["previous"]:
        before = carried_register_ids(REG.load_toml(reg_root / out["previous"] / "MANIFEST.toml"))
        for nid in sorted(before - now):   # carried last time, by the register id itself, and gone now
            if nid in reg["nodes"] and nid not in stale:
                stale[nid] = {"id": nid, "previous": out["previous"]}
    out["stale_nodes"] = [stale[k] for k in sorted(stale)]
    out["unknown_ids"] = sorted(k for k in now if k not in reg["nodes"])
    return out


def land(instance: Path, system: str, export: list[Path], exported_on: str | None = None) -> dict:
    """Land one export; returns the RECONCILE dict (with "manifest" beside it for the caller)."""
    instance = Path(instance).resolve()
    cfg = system_config(instance, system)
    reg_root = instance / "register"
    sources = REG.load_toml(reg_root / "metamodel" / "sources.toml").get("system", {})
    if system not in sources:
        raise Refused(f"the register's metamodel/sources.toml has no [system.{system}]")
    got = read_export([Path(e) for e in export], cfg["id_attribute"])
    stamp = _exported_on(exported_on, got["exported"])
    day = stamp[:10]
    date.fromisoformat(day)
    base = reg_root / "exports" / system
    dest = base / day
    if dest.exists():
        raise Refused(f"{dest.relative_to(instance)} exists: an export is never landed over another")
    older = sorted(p.name for p in base.glob("*") if p.is_dir() and re.fullmatch(r"\d{4}-\d{2}-\d{2}", p.name)) if base.is_dir() else []
    if older and older[-1] > day:
        raise Refused(f"{day} is before the newest export, {older[-1]}: exports land in date order")
    folder = f"exports/{system}/{day}"
    man = {"exported_on": stamp, "source": system, "source_version": "; ".join(got["versions"]),
           "tool": "knowgov tools/connector.py (AML, BPMN 2.0); digests by hashlib",
           "tool_version": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
           "previous": f"exports/{system}/{older[-1]}" if older else "",
           "files": got["digests"], "ids": got["objects"], "register_ids": got["guids"], "bpmn_ids": got["bpmn_ids"]}
    text = manifest_text(man)
    assert tomllib.loads(text)["ids"] == got["objects"]
    base.mkdir(parents=True, exist_ok=True)
    tmp = base / f".{day}.partial-{os.getpid()}"
    if tmp.exists():
        shutil.rmtree(tmp)
    try:
        for rel, data in got["files"].items():
            (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
            (tmp / rel).write_bytes(data)
        (tmp / "MANIFEST.toml").write_text(text, encoding="utf-8")
        rec = reconcile(reg_root, tmp, folder, tomllib.loads(text))
        if got["conflicts"]:
            rec["name_conflicts"] = got["conflicts"]
        (tmp / "RECONCILE.json").write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
        if dest.exists():
            raise Refused(f"{dest} appeared while landing")
        tmp.rename(dest)
    finally:
        if tmp.exists():
            shutil.rmtree(tmp)
    return {**rec, "manifest": man}


def summary(r: dict) -> str:
    f, i = r["files"], r["ids"]
    return (f"{r['folder']}: files +{len(f['added'])} ~{len(f['updated'])} -{len(f['deleted'])}; "
            f"ids +{len(i['added'])} ~{len(i['renamed'])} -{len(i['deleted'])}; stale nodes {len(r['stale_nodes'])}"
            + (f" ({', '.join(n['id'] for n in r['stale_nodes'])})" if r["stale_nodes"] else "")
            + (f"; unknown ids {len(r['unknown_ids'])}" if r["unknown_ids"] else "")
            + (f"; unregistered {len(r['unregistered'])}" if r.get("unregistered") else ""))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Land a system of record's export in an instance's register as a dated mirror.")
    ap.add_argument("instance", type=Path)
    ap.add_argument("export", type=Path, nargs="+", help="the export: a folder, or files")
    ap.add_argument("--system", required=True, help="a [system.<name>] of the instance's connectors.toml")
    ap.add_argument("--exported-on", help="the export time (a date or an ISO time); default the AML header's")
    ap.add_argument("--json", action="store_true", help="print RECONCILE.json")
    a = ap.parse_args(argv)
    try:
        r = land(a.instance, a.system, a.export, a.exported_on)
    except Refused as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1
    except (OSError, ValueError, tomllib.TOMLDecodeError) as e:
        print(f"cannot run: {e}", file=sys.stderr)
        return 2
    r.pop("manifest")
    print(json.dumps(r, indent=2) if a.json else summary(r))
    return 0


if __name__ == "__main__":
    sys.exit(main())
