"""The instance's code_map.toml (task-0050; instance/README.md, "Mapping code to the register"):
code path globs to the register application or module (APP id) each implements. Read by
tools/check_instance.py, which checks the file, and by harness/trace.py, which names the APP a
changed or registered path belongs to. Standard library only; reads, never writes.
"""
from __future__ import annotations

import re
import tomllib
from pathlib import Path

CODE_MAP = "code_map.toml"
SKIP = {"__pycache__", ".git", ".DS_Store"}


def _files(p: Path) -> list[Path]:
    return sorted(f for f in p.rglob("*") if f.is_file() and not (set(f.relative_to(p).parts) & SKIP))


def glob_re(glob: str) -> re.Pattern:
    """A path glob, '/'-separated: ** any number of whole segments, * and ? within one segment."""
    out, i = [], 0
    while i < len(glob):
        if glob.startswith("**/", i):
            out.append("(?:[^/]+/)*"); i += 3
        elif glob.startswith("**", i):
            out.append(".*"); i += 2
        elif glob[i] == "*":
            out.append("[^/]*"); i += 1
        elif glob[i] == "?":
            out.append("[^/]"); i += 1
        else:
            out.append(re.escape(glob[i])); i += 1
    return re.compile("".join(out) + r"\Z")


def register_apps(reg: Path) -> dict[str, dict]:
    """APP id -> {kind, name}: the register's applications and modules, one file per id."""
    apps = {}
    for f in sorted((reg / "applications").glob("*.toml")) if (reg / "applications").is_dir() else []:
        row = tomllib.loads(f.read_text(encoding="utf-8"))
        if row.get("id"):
            apps[row["id"]] = {"kind": row.get("kind", ""), "name": row.get("name", "")}
    return apps


def code_map(inst: Path, apps: dict[str, dict], errors: list[str]) -> dict | None:
    """The instance's code_map.toml read against its register; None when there is none.
    [code] root (relative to the instance, default ".") and include (the globs that say what is
    code, relative to root); [[map]] rows glob -> app. Errors go to errors; unmapped and unmatched
    are findings."""
    f = inst / CODE_MAP
    if not f.is_file():
        return None
    try:
        doc = tomllib.loads(f.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as e:
        errors.append(f"{CODE_MAP}: does not parse: {e}")
        return {"root": None, "rows": [], "unmapped": [], "unmatched": [], "citations": {"require": False, "apps": []}}
    code = doc.get("code", {})
    root = (inst / code.get("root", ".")).resolve()
    include = list(code.get("include", ["**"]))
    rows = []
    for n, r in enumerate(doc.get("map", []), 1):
        if not isinstance(r.get("glob"), str) or not isinstance(r.get("app"), str):
            errors.append(f"{CODE_MAP}: map row {n}: needs a glob and an app")
            continue
        rows.append({"glob": r["glob"], "app": r["app"], "note": r.get("note", ""), "files": []})
        if r["app"] not in apps:
            errors.append(f"{CODE_MAP}: {r['glob']}: {r['app']} is no application or module of register/applications")
    rep = {"root": root.relative_to(inst).as_posix() if root.is_relative_to(inst) else str(root),
           "include": include, "rows": rows, "unmapped": [], "unmatched": [], "citations": citations(doc, rows, errors)}
    if not root.is_dir():
        errors.append(f"{CODE_MAP}: root {code.get('root', '.')}: not a directory")
        return rep
    res = [glob_re(r["glob"]) for r in rows]
    overlap: dict[tuple[int, int], str] = {}   # one glob covering another's text overlaps whatever files exist
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            if res[i].match(rows[j]["glob"]) or res[j].match(rows[i]["glob"]):
                overlap[i, j] = "one covers the other"
    inc = [glob_re(g) for g in include]
    for p in _files(root):
        rel = p.relative_to(root).as_posix()
        if not any(r.match(rel) for r in inc):
            continue
        hit = [k for k, r in enumerate(res) if r.match(rel)]
        for k in hit:
            rows[k]["files"].append(rel)
        if not hit:
            rep["unmapped"].append(rel)
        for i, j in ((i, j) for i in hit for j in hit if i < j):
            overlap.setdefault((i, j), f"both match {rel}")
    for (i, j), why in sorted(overlap.items()):
        a, b = rows[i], rows[j]
        errors.append(f"{CODE_MAP}: {a['glob']} ({a['app']}) and {b['glob']} ({b['app']}) overlap: {why}")
    rep["unmatched"] = [r["glob"] for r in rows if not r["files"]]
    return rep




def citations(doc: dict, rows: list[dict], errors: list[str]) -> dict:
    """[citations] (task-0124): whether the governed APPs' code files must cite the keys they rest on."""
    cit = doc.get("citations", {})
    named = sorted({r["app"] for r in rows})
    if not isinstance(cit, dict):
        errors.append(f"{CODE_MAP}: [citations] must be a table")
        return {"require": False, "apps": named}
    req = cit.get("require", False)
    if not isinstance(req, bool):
        errors.append(f"{CODE_MAP}: [citations] require must be true or false")
        req = False
    apps = cit.get("apps", named)
    if not isinstance(apps, list) or not all(isinstance(a, str) for a in apps):
        errors.append(f"{CODE_MAP}: [citations] apps must be a list of APP ids")
        apps = named
    for a in apps:
        if a not in named:
            errors.append(f"{CODE_MAP}: [citations] apps: {a} is named by no [[map]] row")
    return {"require": req, "apps": sorted(set(apps))}


def app_of(rep: dict, path: str) -> str | None:
    """The APP id of the one row whose glob matches path (relative to the map's root), else None."""
    hit = [r["app"] for r in rep["rows"] if glob_re(r["glob"]).match(path)]
    return hit[0] if len(hit) == 1 else None


def is_code(rep: dict, path: str) -> bool:
    return any(glob_re(g).match(path) for g in rep["include"])
