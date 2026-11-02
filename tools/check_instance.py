"""Check a directory against the instance layout (task-0006; instance/README.md).

    python tools/check_instance.py <instance> [--json]

An instance is an organisation's own folder, mounted read-only by docker-compose.instance.yml:

    register/           the organisation's register, an ieam-register checkout (its exports inside it)
    artefacts/<kind>/   the authored artefacts, one folder per kind of instance/kinds.toml
    subjects/<id>/      subject roots; a manifest names its artefacts by path, ../../artefacts/...
    record/<subject>/   the instance's own results, a subject's [record] dir

The check reads and never writes. It reports, per kind, the files present and the mapper that
reads each; a file of a kind no mapper reads, or a store artefact a manifest gives no mapper, is
reported *absent*: the store will not hold its statements, and the report says so rather than
skipping it. A file under artefacts/ that no subject names is listed as unread.

Exit 0 when the layout holds (absent and unread files are findings to read, not errors), 1 when
it does not (no register, an unknown kind folder, a subject that does not load, an artefact path
that does not exist), 2 when the check cannot run (no such directory, an unreadable kinds table).
Standard library plus the harness's subject reader.
"""
from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness"))
from subject import Subject  # noqa: E402

KINDS_TABLE = ROOT / "instance" / "kinds.toml"
REGISTER_TREES = ("metamodel", "relationships", "decisions", "glossary", "exports")
SKIP = {"__pycache__", ".git", ".DS_Store"}


def kinds(path: Path = KINDS_TABLE) -> dict[str, dict]:
    """folder -> {row, mappers}, in the table's order."""
    rows = tomllib.loads(path.read_text(encoding="utf-8")).get("kind", [])
    return {k["folder"]: {"row": k["row"], "mappers": list(k.get("mappers", []))} for k in rows}


def mapper_kind(table: dict[str, dict]) -> dict[str, str]:
    return {m: folder for folder, k in table.items() for m in k["mappers"]}


def _files(p: Path) -> list[Path]:
    if p.is_file():
        return [p]
    return sorted(f for f in p.rglob("*") if f.is_file() and not (set(f.parts) & SKIP))


def check(instance: Path, table: dict[str, dict] | None = None) -> dict:
    """The report: errors (the layout does not hold), absent (read by nothing), unread (named by no
    subject), and per kind the files and what reads them. Never writes."""
    table = table or kinds()
    by_mapper = mapper_kind(table)
    inst = instance.resolve()
    errors: list[str] = []
    rep: dict = {"instance": str(inst), "register": None, "subjects": [], "kinds": {}, "absent": [], "unread": [], "errors": errors}

    reg = inst / "register"
    if not reg.is_dir():
        errors.append("register/: missing; an instance holds its organisation's register checkout there")
    else:
        missing = [t for t in REGISTER_TREES if not (reg / t).is_dir()]
        if missing:
            errors.append(f"register/: not an ieam-register checkout, missing {', '.join(missing)}")
        rep["register"] = {"trees": sorted(p.name for p in reg.iterdir() if p.is_dir() and p.name not in SKIP)}

    arte = inst / "artefacts"
    present: dict[str, str] = {}   # file (relative to the instance) -> its kind folder
    if arte.is_dir():
        for d in sorted(p for p in arte.iterdir() if p.name not in SKIP):
            if not d.is_dir():
                errors.append(f"artefacts/{d.name}: a file at the top of artefacts/; files go under a kind folder")
            elif d.name not in table:
                errors.append(f"artefacts/{d.name}/: not a kind of instance/kinds.toml")
            else:
                for f in _files(d):
                    present[f.relative_to(inst).as_posix()] = d.name

    read: dict[str, list[dict]] = {}   # file -> who reads it
    subs = inst / "subjects"
    if not subs.is_dir():
        errors.append("subjects/: missing; an instance holds at least one subject root there")
    else:
        for root in sorted(p for p in subs.iterdir() if p.is_dir() and p.name not in SKIP):
            try:
                s = Subject(root)
            except Exception as e:  # noqa: BLE001 — a subject that does not load is the finding
                errors.append(f"subjects/{root.name}: does not load: {e}")
                continue
            srep = {"id": s.id, "root": root.relative_to(inst).as_posix(), "artefacts": [],
                    "record": s.record_dir.is_dir() and any(s.record_dir.iterdir())}
            for a in s.artefacts:
                if not a.get("path"):
                    continue   # added by a plant: no bytes on disk
                p = (s.root / a["path"]).resolve()
                if not p.exists():
                    errors.append(f"subjects/{root.name}: artefact {a['key']}: {a['path']} does not exist")
                    continue
                mapper = a.get("mapper") or ""
                store = a.get("store", True)
                inside = p.is_relative_to(inst / "artefacts")
                kind = p.relative_to(inst / "artefacts").parts[0] if inside else by_mapper.get(mapper, "")
                if mapper and mapper not in by_mapper:
                    errors.append(f"subjects/{root.name}: artefact {a['key']}: mapper {mapper!r} is in no kind of instance/kinds.toml")
                elif mapper and inside and kind in table and mapper not in table[kind]["mappers"]:
                    errors.append(f"subjects/{root.name}: artefact {a['key']}: mapper {mapper!r} does not read {kind}/ (it reads {by_mapper[mapper]}/)")
                state = "read" if mapper else ("not stored" if not store else "absent")
                srep["artefacts"].append({"key": a["key"], "kind": kind, "mapper": mapper, "state": state,
                                          "path": p.relative_to(inst).as_posix() if p.is_relative_to(inst) else str(p)})
                if state == "absent":
                    rep["absent"].append({"subject": s.id, "key": a["key"], "kind": kind,
                                          "why": f"no mapper reads {kind or 'this kind'}: the store holds no statement from it"})
                for f in _files(p):
                    if f.is_relative_to(inst):
                        read.setdefault(f.relative_to(inst).as_posix(), []).append({"subject": s.id, "key": a["key"], "mapper": mapper, "state": state})
            rep["subjects"].append(srep)

    for folder, k in table.items():
        files = sorted(f for f, kd in present.items() if kd == folder)
        if not files:
            continue
        rows = []
        for f in files:
            by = read.get(f, [])
            rows.append({"file": f, "read_by": by})
            if not by:
                rep["unread"].append({"file": f, "kind": folder})
                if not k["mappers"]:
                    rep["absent"].append({"subject": None, "key": f, "kind": folder,
                                          "why": f"no mapper reads {folder}: the store holds no statement from it"})
        rep["kinds"][folder] = {"row": k["row"], "mappers": k["mappers"], "files": rows}
    return rep


def render(rep: dict) -> str:
    out = [f"instance {rep['instance']}"]
    out.append("register: " + (", ".join(rep["register"]["trees"]) if rep["register"] else "missing"))
    for s in rep["subjects"]:
        out.append(f"subject {s['id']} ({s['root']}): {len(s['artefacts'])} artefacts, record {'present' if s['record'] else 'empty'}")
        for a in s["artefacts"]:
            out.append(f"  {a['state']:10s} {a['key']}  [{a['kind'] or '-'}] {a['mapper'] or '(no mapper)'}  {a['path']}")
    for folder, k in rep["kinds"].items():
        out.append(f"kind {folder} ({k['row']}): {len(k['files'])} file(s), mappers {', '.join(k['mappers']) or 'none'}")
    for a in rep["absent"]:
        out.append(f"ABSENT {a['key']} [{a['kind']}]: {a['why']}" + (f" (subject {a['subject']})" if a["subject"] else ""))
    for u in rep["unread"]:
        out.append(f"UNREAD {u['file']}: no subject names it")
    for e in rep["errors"]:
        out.append(f"ERROR {e}")
    out.append("layout holds" if not rep["errors"] else f"layout does not hold: {len(rep['errors'])} error(s)")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Check a directory against the instance layout.")
    ap.add_argument("instance", type=Path)
    ap.add_argument("--json", action="store_true", help="print the report as JSON")
    args = ap.parse_args(argv)
    if not args.instance.is_dir():
        print(f"cannot run: {args.instance} is not a directory", file=sys.stderr)
        return 2
    try:
        table = kinds()
    except (OSError, tomllib.TOMLDecodeError, KeyError) as e:
        print(f"cannot run: instance/kinds.toml: {e}", file=sys.stderr)
        return 2
    rep = check(args.instance, table)
    print(json.dumps(rep, indent=1) if args.json else render(rep))
    return 1 if rep["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
